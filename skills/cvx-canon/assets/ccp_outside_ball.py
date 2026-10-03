"""Ordinary native CCP: min 0.5*||x-a||^2 subject to ||x||>=radius.

Requires a feasible nonzero start. Returns a local candidate, not a global proof.
"""

import numpy as np
from scipy import sparse


def solve_ccp(a, radius, x0, backend="moreau", max_iter=50, tol=1e-7):
    a, x = np.asarray(a, dtype=float), np.array(x0, dtype=float, copy=True)
    if a.ndim != 1 or not a.size or x.shape != a.shape:
        raise ValueError("a and x0 must be same-length nonempty vectors")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(x)):
        raise ValueError("Vectors must be finite")
    if not np.isfinite(radius) or radius <= 0 or np.linalg.norm(x) < radius:
        raise ValueError("Require a positive radius and an original-feasible start")
    if backend not in ("moreau", "scs"):
        raise ValueError("backend must be 'moreau' or 'scs'")
    if not isinstance(max_iter, int) or max_iter < 1 or not np.isfinite(tol) or tol <= 0:
        raise ValueError("Require a positive iteration count and tolerance")
    n = a.size
    P = sparse.eye(n, format="csr")
    if backend == "moreau":
        import moreau

        solver = moreau.CompiledSolver(
            n=n, m=1, P_row_offsets=P.indptr, P_col_indices=P.indices,
            A_row_offsets=np.array([0, n]), A_col_indices=np.arange(n),
            cones=moreau.Cones(num_nonneg_cones=1),
            settings=moreau.Settings(solver="ipm", device="cpu", batch_size=1),
        )
    history = []
    best_x, best_objective = x.copy(), float(0.5*np.dot(x-a, x-a))
    outcome = "outer_iteration_limit"
    for iteration in range(max_iter):
        # Inner approximation: 2*xk'x >= radius^2 + ||xk||^2.
        coefficients, b = -2*x, np.array([-(radius**2 + x@x)])
        if backend == "moreau":
            solver.setup(P_values=P.data, A_values=coefficients)
            inner = solver.solve(qs=(-a)[None, :], bs=b[None, :])
            inner_status = solver.info.status[0]
            inner_ok = inner_status == moreau.SolverStatus.Solved
            candidate = np.array(inner.x[0], copy=True) if inner_ok else None
        else:
            import scs

            # A changes at each iteration; SCS b/c updates cannot update it.
            inner = scs.SCS(
                {"P":P.tocsc(), "A":sparse.csc_matrix(coefficients[None, :]), "b":b, "c":-a},
                {"l":1}, eps_abs=1e-9, eps_rel=1e-9, verbose=False,
            ).solve()
            inner_status = inner["info"]["status"]
            inner_ok = inner["info"]["status_val"] == 1
            candidate = np.array(inner["x"], copy=True) if inner_ok else None
        if not inner_ok:
            outcome = f"inner_failure:{inner_status}"
            break
        violation = float(max(0.0, radius-np.linalg.norm(candidate)))
        objective = float(0.5*np.dot(candidate-a, candidate-a))
        previous_objective = float(0.5*np.dot(x-a, x-a))
        step = float(np.linalg.norm(candidate-x)/(1+np.linalg.norm(x)))
        change = abs(objective-previous_objective)/(1+abs(previous_objective))
        history.append({"iteration":iteration, "objective":objective, "violation":violation, "step":step})
        if violation <= tol and objective <= best_objective:
            best_x, best_objective = candidate.copy(), objective
        x = candidate
        if violation <= tol and step <= tol and change <= tol:
            outcome = "converged_local"
            break
    return {
        "status":outcome, "x":best_x, "objective":best_objective,
        "violation":float(max(0.0, radius-np.linalg.norm(best_x))),
        "method":"local CCP", "history":history,
    }
