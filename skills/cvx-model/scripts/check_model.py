#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["cvxpy>=1.7,<2"]
# ///
"""Construct a trusted CVXPY model with supplied data; no solve or callbacks."""

import argparse
import json
import math
from pathlib import Path
import runpy
import sys
import traceback

import cvxpy as cp


def check(namespace, data, *, require_dpp=False, require_exact_atoms=False):
    problem, names = namespace["build"](data)
    if not isinstance(problem, cp.Problem) or not isinstance(names, dict):
        raise TypeError("build must return (cp.Problem, dict of named CVXPY expressions)")
    if any(not isinstance(k, str) or not k or not isinstance(v, cp.Expression)
           for k, v in names.items()):
        raise TypeError("Return names must be nonempty strings mapped to CVXPY expressions")
    approximations, seen = [], set()
    stack = [problem.objective.expr, *problem.constraints]
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        stack.extend(getattr(node, "args", ()))
        error = getattr(node, "approx_error", None)
        if error is not None:
            error = float(error)
            if not math.isfinite(error) or error < 0:
                raise ValueError("Atom approximation error must be finite and nonnegative")
            entry = {"atom": type(node).__name__, "approximation_error": error}
            if hasattr(node, "w"):
                entry["represented_weights"] = [str(w) for w in node.w]
            approximations.append(entry)
    dcp, dpp = bool(problem.is_dcp()), bool(problem.is_dcp(dpp=True))
    failures = []
    if not dcp:
        failures.append("Problem is not DCP; this does not establish nonconvexity")
    if require_dpp and not dpp:
        failures.append("Promised parameter reuse requires DPP")
    if require_exact_atoms and any(a["approximation_error"] != 0 for a in approximations):
        failures.append("An atom reports a nonzero approximation error")
    return {
        "schema_version": 1, "mode": "construction", "cvxpy_version": cp.__version__,
        "construction_assessment": "failed" if failures else "passed",
        "dcp": dcp, "dpp": dpp,
        "named_expressions": {k: {"kind": type(v).__name__, "shape": list(v.shape)}
                              for k, v in names.items()},
        "parameters": [{"name": p.name(), "shape": list(p.shape)} for p in problem.parameters()],
        "atom_approximations": approximations, "failures": failures,
        "semantic_assessment": "requires_review", "numerical_assessment": "not_run",
        "exactness_assessment": "Exposed atom errors checked only; original specification requires review",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--require-dpp", action="store_true")
    parser.add_argument("--require-exact-atoms", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        # Loading and calling user Python executes it with host authority.
        sys.path.insert(0, str(args.model.resolve().parent))
        namespace = runpy.run_path(str(args.model.resolve()), run_name="__cvx_check__")
        data = json.loads(args.data.read_text())
        report = check(namespace, data, require_dpp=args.require_dpp,
                       require_exact_atoms=args.require_exact_atoms)
    except Exception as exc:
        report = {"schema_version": 1, "mode": "construction", "construction_assessment": "failed",
                  "semantic_assessment": "requires_review", "numerical_assessment": "not_run",
                  "error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc(limit=6)}
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0 if report["construction_assessment"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
