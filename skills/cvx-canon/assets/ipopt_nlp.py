"""Exact smooth nonconvex NLP, local solve; callbacks can be checked alone."""

import numpy as np


class DoubleWell:
    """min (x0^2-1)^2+(x1-0.5)^2+tilt*x0, subject to x0^2+x1^2<=2."""

    def __init__(self, tilt=0.1):
        if not np.isfinite(tilt):
            raise ValueError("tilt must be finite")
        self.tilt = float(tilt)

    def objective(self, x):
        return (x[0]**2-1)**2 + (x[1]-0.5)**2 + self.tilt*x[0]

    def gradient(self, x):
        return np.array([4*x[0]*(x[0]**2-1)+self.tilt, 2*(x[1]-0.5)])

    def constraints(self, x):
        return np.array([x@x])

    def jacobianstructure(self):
        return np.array([0, 0]), np.array([0, 1])

    def jacobian(self, x):
        return 2*x

    def hessianstructure(self):
        return np.array([0, 1]), np.array([0, 1])

    def hessian(self, x, lagrange, obj_factor):
        return obj_factor*np.array([12*x[0]**2-4, 2.0]) + 2*lagrange[0]


def solve_local(x0, tilt=0.1):
    import cyipopt

    callbacks = DoubleWell(tilt)
    x0 = np.asarray(x0, dtype=float)
    if x0.shape != (2,) or not np.all(np.isfinite(x0)):
        raise ValueError("x0 must be a finite length-two vector")
    problem = cyipopt.Problem(
        n=2, m=1, problem_obj=callbacks,
        lb=np.array([-2.0, -2.0]), ub=np.array([2.0, 2.0]),
        cl=np.array([-1e19]), cu=np.array([2.0]),
    )
    problem.add_option("tol", 1e-8)
    problem.add_option("max_iter", 200)
    problem.add_option("print_level", 0)
    x, info = problem.solve(x0)
    violation = float(max(0.0, x@x-2, np.max(np.abs(x))-2))
    return {
        "status":info["status"], "message":info["status_msg"],
        "x":x, "objective":float(callbacks.objective(x)), "violation":violation,
        "method":"local NLP", "converged":info["status"] == 0,
    }
