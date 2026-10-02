#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["cvxpy>=1.7,<2", "numpy>=1.26"]
# ///
"""Check a trusted model and its original-expression callbacks; not a sandbox."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import runpy
import sys

import cvxpy as cp
import numpy as np


def json_value(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    array = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(array)):
        raise ValueError("Nonfinite numerical output")
    return array.tolist()


def residual_checks(records, atol, rtol):
    if not isinstance(records, list):
        raise ValueError("Original constraints must be a list")
    checks, names = [], set()
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("name"), str) or not record["name"]:
            raise ValueError("Each original constraint needs a name")
        if record["name"] in names:
            raise ValueError("Original constraint names must be unique")
        names.add(record["name"])
        relation = record.get("relation")
        if relation not in ("le", "eq"):
            raise ValueError("Constraint relation must be le or eq")
        value = np.asarray(record["value"], dtype=float)
        scale = np.asarray(record.get("scale", 1), dtype=float)
        if scale.ndim != 0 and scale.shape != value.shape:
            raise ValueError("Constraint scale must be scalar or match residual shape")
        if not np.all(np.isfinite(value)) or not np.all(np.isfinite(scale)) or np.any(scale < 0):
            raise ValueError("Residuals/scales must be finite and scales nonnegative")
        violation = np.abs(value) if relation == "eq" else np.maximum(value, 0)
        threshold = atol + rtol * scale
        checks.append({
            "name": record["name"], "relation": relation,
            "maximum_violation": float(np.max(violation, initial=0)),
            "tolerance": json_value(threshold),
            "passed": bool(np.all(violation <= threshold)),
        })
    return checks


def check_point(namespace, data, point, *, atol=1e-6, rtol=1e-5):
    """Evaluate a supplied original point without building or solving a model."""
    if not all(math.isfinite(v) and v >= 0 for v in (atol, rtol)):
        raise ValueError("Tolerances must be finite and nonnegative")
    if not isinstance(point, dict) or not isinstance(point.get("values"), dict) or not point["values"]:
        raise ValueError("Point must contain a nonempty values object")
    if set(point) - {"values", "claimed_objective"}:
        raise ValueError("Point fields are values and optional claimed_objective")
    values = {}
    for name, value in point["values"].items():
        array = np.asarray(value, dtype=float)
        if not isinstance(name, str) or not name or not np.all(np.isfinite(array)):
            raise ValueError("Point values need names and finite numbers/arrays")
        values[name] = array.tolist()
    report = {
        "schema_version": 1, "mode": "point", "values": values,
        "numerical_assessment": "not_evaluated", "semantic_assessment": "requires_review",
        "optimality_certificate": "not_checked", "atol": atol, "rtol": rtol,
    }
    if "evaluate_original" not in namespace:
        report["reason"] = "Missing evaluate_original callback; point checks not performed"
        return report
    original = namespace["evaluate_original"](data, values)
    if not isinstance(original, dict) or "objective" not in original or "constraints" not in original:
        raise ValueError("evaluate_original must return objective and constraints")
    objective = float(original["objective"])
    if not math.isfinite(objective):
        raise ValueError("Nonfinite original objective")
    checks = residual_checks(original["constraints"], atol, rtol)
    report.update(original_objective=objective, original_constraints=checks)
    passed = all(check["passed"] for check in checks)
    if "claimed_objective" in point:
        claimed = float(point["claimed_objective"])
        if not math.isfinite(claimed):
            raise ValueError("Claimed objective must be finite")
        threshold = atol + rtol * max(1, abs(objective), abs(claimed))
        claim = {"claimed": claimed, "computed": objective, "difference": abs(objective-claimed),
                 "tolerance": threshold, "passed": abs(objective-claimed) <= threshold}
        report["claimed_objective_check"] = claim
        passed = passed and claim["passed"]
    report.update(numerical_assessment="passed" if passed else "failed",
                  reason="Supplied point callbacks and any objective claim checked; no solve or optimality certificate")
    return report


def verify(namespace, data, *, solver=None, atol=1e-6, rtol=1e-5, include_duals=False, check_only=False):
    if not all(math.isfinite(v) and v >= 0 for v in (atol, rtol)):
        raise ValueError("Tolerances must be finite and nonnegative")
    problem, variables = namespace["build"](data)
    if not isinstance(problem, cp.Problem) or not isinstance(variables, dict):
        raise ValueError("build must return (cp.Problem, named original expression dict)")
    if not variables or any(not isinstance(v, cp.Expression) for v in variables.values()):
        raise ValueError("Original variable values must be named CVXPY expressions")
    report = {
        "schema_version": 1, "cvxpy_version": cp.__version__,
        "dcp": bool(problem.is_dcp()), "dpp": bool(problem.is_dcp(dpp=True)),
        "status": None, "numerical_assessment": "not_evaluated",
        "semantic_assessment": "requires_review", "optimality_certificate": "not_checked",
        "atol": atol, "rtol": rtol,
    }
    if not report["dcp"]:
        report.update(numerical_assessment="failed", reason="Expression is not DCP; this alone is not proof of nonconvexity")
        return report
    if check_only:
        report["reason"] = "Check-only: no solver or original callbacks executed"
        return report
    if solver and solver not in cp.installed_solvers():
        report["reason"] = f"Requested solver {solver} is not installed"
        return report
    problem.solve(**({"solver": solver} if solver else {}))
    report["status"] = problem.status
    report["solver"] = problem.solver_stats.solver_name
    report["solve_time_seconds"] = problem.solver_stats.solve_time
    if problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
        report["reason"] = "No verified primal optimum: inspect status and original problem; certificates not checked"
        return report
    values = {}
    for name, expression in variables.items():
        if expression.value is None:
            raise ValueError(f"No recovered value for {name}")
        values[name] = json_value(expression.value)
    report["values"] = values
    report["modeled_objective"] = json_value(problem.value)
    if include_duals:
        report["explicit_constraint_duals"] = [
            {"index": i, "constraint": str(constraint), "value": json_value(constraint.dual_value)}
            for i, constraint in enumerate(problem.constraints)
        ]
        report["dual_checks"] = "not_checked; attributes have no separately named constraint duals"
    if "evaluate_original" not in namespace:
        report["reason"] = "Missing evaluate_original callback; semantic/original-domain checks not performed"
        return report
    original = namespace["evaluate_original"](data, values)
    if not isinstance(original, dict) or "objective" not in original or "constraints" not in original:
        raise ValueError("evaluate_original must return objective and constraints")
    objective = float(original["objective"])
    if not math.isfinite(objective):
        raise ValueError("Nonfinite original objective")
    checks = residual_checks(original["constraints"], atol, rtol)
    modeled = float(problem.value)
    threshold = atol + rtol * max(1, abs(objective), abs(modeled))
    objective_check = {"original": objective, "modeled": modeled, "difference": abs(objective-modeled),
                       "tolerance": threshold, "passed": abs(objective-modeled) <= threshold}
    report["original_constraints"] = checks
    report["objective_check"] = objective_check
    passed = all(c["passed"] for c in checks) and objective_check["passed"]
    if not passed:
        report.update(numerical_assessment="failed", reason="Original feasibility or objective reconciliation failed")
    elif problem.status == cp.OPTIMAL_INACCURATE:
        report.update(numerical_assessment="inaccurate", reason="Residual checks passed, but status is optimal_inaccurate, not a verified optimum")
    else:
        report.update(numerical_assessment="passed", reason="Supplied original callbacks passed; semantic equivalence and independent optimality remain separate checks")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--solver")
    parser.add_argument("--atol", type=float, default=1e-6)
    parser.add_argument("--rtol", type=float, default=1e-5)
    parser.add_argument("--include-duals", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--point", type=Path, help="Check supplied original values/objective; no build or solve")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.point and (args.check_only or args.solver or args.include_duals):
        parser.error("--point cannot be combined with solver, dual, or check-only options")
    try:
        # Loading user Python is an explicit trusted-code operation, not confinement.
        sys.path.insert(0, str(args.model.resolve().parent))
        namespace = runpy.run_path(str(args.model.resolve()), run_name="__cvx_model__")
        data = json.loads(args.data.read_text())
        if args.point:
            report = check_point(namespace, data, json.loads(args.point.read_text()), atol=args.atol, rtol=args.rtol)
        else:
            report = verify(namespace, data, solver=args.solver, atol=args.atol, rtol=args.rtol,
                            include_duals=args.include_duals, check_only=args.check_only)
    except Exception as exc:
        report = {"schema_version": 1, "numerical_assessment": "failed", "semantic_assessment": "requires_review",
                  "error": f"{type(exc).__name__}: {exc}"}
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")
    if args.check_only and report.get("dcp"):
        return 0
    return {"passed": 0, "failed": 1}.get(report["numerical_assessment"], 2)


if __name__ == "__main__":
    raise SystemExit(main())
