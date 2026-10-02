"""Minimal trusted model/callback example for the optional verification helper."""

import cvxpy as cp
import numpy as np


def build(data):
    a = np.asarray(data["a"], dtype=float)
    radius = float(data["radius"])
    if a.ndim != 1 or not a.size or not np.all(np.isfinite(a)):
        raise ValueError("a must be a finite nonempty vector")
    if not np.isfinite(radius) or radius < 0:
        raise ValueError("radius must be finite and nonnegative")
    x = cp.Variable(a.size, name="x")
    problem = cp.Problem(cp.Minimize(0.5 * cp.sum_squares(x-a)), [cp.norm(x, 2) <= radius])
    return problem, {"x": x}


def evaluate_original(data, values):
    x, a = np.asarray(values["x"]), np.asarray(data["a"])
    return {
        "objective": float(0.5*np.sum((x-a)**2)),
        "constraints": [{"name": "original_ball", "relation": "le",
                         "value": float(np.linalg.norm(x)-data["radius"]),
                         "scale": max(1, float(data["radius"]))}],
    }
