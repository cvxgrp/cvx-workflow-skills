"""CasADi/IPOPT exact abs epigraph in a smooth nonconvex NLP.

min (x**2-1)**2 + tilt*x + lam*abs(x-.25) + offset, -2 <= x <= 2.
lam >= 0 makes the lift exact for optimal x/values; lam=0 need not make t tight.
"""
import numpy as np


class DoubleWell:
    def __init__(self):
        import casadi as ca

        w = ca.SX.sym("w", 2)  # w[0]=original x, w[1]=epigraph t
        p = ca.SX.sym("p", 3)  # tilt, lam, objective offset
        x, t = w[0], w[1]
        f = (x*x-1)**2 + p[0]*x + p[1]*t + p[2]
        g = ca.vertcat(t-(x-.25), t+(x-.25))
        self.solver = ca.nlpsol("double_well", "ipopt", {"x": w, "p": p, "f": f, "g": g},
                               {"print_time": False, "ipopt.print_level": 0,
                                "ipopt.sb": "yes", "ipopt.tol": 1e-9,
                                "ipopt.bound_relax_factor": 0.0})

    def solve(self, tilt=0.1, lam=0.2, offset=0.0, x0=1.0):
        if not np.isfinite([tilt, lam, offset, x0]).all() or lam < 0 or abs(x0) > 2:
            raise ValueError("Finite data, lam >= 0, and -2 <= x0 <= 2 required")
        r = self.solver(p=[tilt, lam, offset], x0=[x0, abs(x0-.25)+.1],
                        lbx=[-2, 0], ubx=[2, np.inf], lbg=[0, 0], ubg=[np.inf, np.inf])
        stats = self.solver.stats()
        status = stats["return_status"]
        if not stats["success"] or status != "Solve_Succeeded":
            return {"status": status, "x": None, "guarantee": "no accepted local result"}
        x, t = np.asarray(r["x"]).reshape(-1)
        if not np.isfinite([x, t]).all() or abs(x) > 2+1e-7 or t < abs(x-.25)-1e-7:
            raise RuntimeError("Original bounds or lifted constraints failed")
        objective = (x*x-1)**2 + tilt*x + lam*abs(x-.25) + offset
        if abs(float(r["f"])-objective) > 1e-7*(1+abs(objective)):
            raise RuntimeError("Original and lifted objectives disagree")
        return {"status": status, "x": float(x), "objective": float(objective),
                "guarantee": "local NLP candidate"}
