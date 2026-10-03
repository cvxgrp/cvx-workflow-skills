"""Shor spin relaxation: min z'Qz, z in {-1,1}^n, then feasible rounding.

Keep the bundled scripts/cone_layout.py beside the assets directory when copying,
or copy its small functions into the generated application.
"""

from pathlib import Path
import importlib.util

import numpy as np
from scipy import sparse

_spec = importlib.util.spec_from_file_location(
    "cone_layout", Path(__file__).resolve().parents[1] / "scripts" / "cone_layout.py"
)
_layout = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_layout)
svec, smat = _layout.svec, _layout.smat


def solve_relaxation(Q, backend="moreau", seed=0):
    Q = np.asarray(Q)
    c = svec(Q, backend)  # Also checks real, finite, square, and symmetric.
    Q = np.asarray(Q, dtype=float)
    n, width = Q.shape[0], c.size
    # diag(Z)=1; PSD slack equals the packed native variable vector itself.
    diagonal_rows = np.vstack([svec(np.diag(np.eye(n)[i]), backend) for i in range(n)])
    A = sparse.vstack([sparse.csc_matrix(diagonal_rows), -sparse.eye(width)], format="csc")
    b = np.r_[np.ones(n), np.zeros(width)]
    if backend == "moreau":
        import moreau

        solver = moreau.Solver(
            sparse.csr_matrix((width, width)), c, A, b,
            moreau.Cones(num_zero_cones=n, psd_dims=[n]),
            settings=moreau.Settings(solver="ipm", device="cpu"),
        )
        solution = solver.solve()
        status = solver.info.status
        if status != moreau.SolverStatus.Solved:
            return {"status":str(status), "Z":None}
        packed = solution.x
    else:
        import scs

        solution = scs.SCS(
            {"A":A, "b":b, "c":c}, {"z":n, "s":[n]},
            eps_abs=1e-8, eps_rel=1e-8, verbose=False,
        ).solve()
        status = solution["info"]["status"]
        if solution["info"]["status_val"] != 1:
            return {"status":status, "Z":None}
        packed = solution["x"]
    Z = smat(packed, n, backend)
    eigenvalues, eigenvectors = np.linalg.eigh(Z)
    # Projection is only for candidate sampling; it does not certify a bound.
    factor = eigenvectors * np.sqrt(np.maximum(eigenvalues, 0.0))[None, :]
    directions = np.random.default_rng(seed).normal(size=(n, 128))
    candidates = np.where(factor@directions >= 0, 1.0, -1.0)
    costs = np.einsum("ik,ij,jk->k", candidates, Q, candidates)
    best = int(np.argmin(costs))
    return {
        "status":str(status), "Z":Z,
        "estimated_relaxation_optimum":float(np.sum(Q*Z)),
        "z":candidates[:, best], "feasible_objective":float(costs[best]),
        "diagonal_violation":float(np.max(np.abs(np.diag(Z)-1))),
        "psd_violation":float(max(0.0, -eigenvalues[0])),
    }
