"""Exact min 0.5*||x-a||^2 subject to ||x||<=radius; native reuse example."""

import numpy as np
from scipy import sparse


def _inputs(a, radius):
    a = np.asarray(a, dtype=float)
    if a.ndim != 1 or not a.size or not np.all(np.isfinite(a)):
        raise ValueError("a must be a nonempty finite vector")
    if not np.isfinite(radius) or radius < 0:
        raise ValueError("radius must be finite and nonnegative")
    return a, float(radius)


class BallProjection:
    """Original x occupies every native coordinate; matrices stay fixed."""

    def __init__(self, a, radius, backend="moreau"):
        a, radius = _inputs(a, radius)
        self.n, self.backend = a.size, backend
        # Slack is [radius; x], so A has a zero scalar row followed by -I.
        P = sparse.eye(self.n, format="csr")
        A = sparse.vstack([sparse.csr_matrix((1, self.n)), -P], format="csr")
        if backend == "moreau":
            import moreau

            self.solver = moreau.CompiledSolver(
                n=self.n, m=self.n + 1,
                P_row_offsets=P.indptr, P_col_indices=P.indices,
                A_row_offsets=A.indptr, A_col_indices=A.indices,
                cones=moreau.Cones(so_cone_dims=[self.n + 1]),
                settings=moreau.Settings(solver="ipm", device="cpu", batch_size=1),
            )
            self.solver.setup(P_values=P.data, A_values=A.data)
        elif backend == "scs":
            import scs

            self.solver = scs.SCS(
                {"P":P.tocsc(), "A":A.tocsc(), "b":np.r_[radius, np.zeros(self.n)], "c":-a},
                {"q":[self.n + 1]}, eps_abs=1e-8, eps_rel=1e-8, verbose=False,
            )
        else:
            raise ValueError("backend must be 'moreau' or 'scs'")

    def solve(self, a, radius):
        a, radius = _inputs(a, radius)
        if a.size != self.n:
            raise ValueError("Changed dimension requires reconstruction")
        b = np.r_[radius, np.zeros(self.n)]
        if self.backend == "moreau":
            import moreau

            result = self.solver.solve(qs=(-a)[None, :], bs=b[None, :])
            status = self.solver.info.status[0]
            if status != moreau.SolverStatus.Solved:
                return {"status":str(status), "x":None}
            x = np.array(result.x[0], copy=True)
        else:
            self.solver.update(b=b, c=-a)
            result = self.solver.solve(warm_start=True)
            status = result["info"]["status"]
            if result["info"]["status_val"] != 1:
                return {"status":status, "x":None}
            x = np.array(result["x"], copy=True)
        return {
            "status":str(status), "x":x,
            "objective":float(0.5 * np.dot(x-a, x-a)),
            "native_objective_with_offset":float(0.5*np.dot(x, x)-np.dot(a, x)+0.5*np.dot(a, a)),
            "violation":float(max(0.0, np.linalg.norm(x)-radius)),
        }
