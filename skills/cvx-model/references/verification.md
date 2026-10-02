# Verification protocol and optional helper

## Three separate questions

1. **Semantic:** does the formulation express the original request, including
   domains, signs, units, quantifiers, and objective normalization?
2. **Transformation:** are replacements/lifts exact under stated assumptions,
   with original-variable recovery? Is a relaxation labeled and bounded correctly?
3. **Numerical:** does the recovered point/status meet the original checks at
   the requested accuracy, with optimality evidence appropriate to the claim?

DCP checks only composition/representability. Solver success does not establish
semantic correctness. Matching one optimal value or feasible point does not
establish equivalence of two feasible sets. Use a derivation/ledger and
independent probes, not a generic "verified" flag.

## Construct first, without solving

The small [construction checker](../scripts/check_model.py) loads trusted Python
and calls only `build(data) -> (cp.Problem, dict of named CVXPY expressions)`.
It needs no original-expression callback, performs no solve, and reports DCP,
DPP, named shapes, parameters, exposed atom approximation errors, and construction
exceptions with traceback. Use an existing compatible environment:

    python /absolute/skill/path/scripts/check_model.py model.py --data example.json

Add `--require-dpp` when parameter reuse was promised and `--require-exact-atoms`
when nonzero atom approximation errors are unacceptable. `--output report.json`
saves the report. Exit 0 means the requested construction checks passed; exit 1
means they failed. Zero reported atom error does not establish equivalence to
the requested function; compare represented values to the original specification.
A passing construction check does not establish feasibility, semantics, solver
compatibility, or numerical correctness. Loading/building executes user code
with host authority; the checker does not prevent a builder from solving or
performing other side effects. It does not install dependencies.

Run on supplied data before adding complex validation. Fix a reported error
without weakening requirements or inventing stronger data domains. Keep invalid
input separate from an infeasible optimization instance. If execution is
unavailable, report that the construction check was not run.

## Numerical checks

After a solve, distinguish optimal, inaccurate, infeasible, unbounded, ambiguous,
and iteration-limited statuses. Only evaluate solution quantities when a
finite primal point exists. Verify variable shapes and original-domain
feasibility; for g<=0 use max(g,0), for h=0 use abs(h). A useful tolerance is
atol + rtol*scale, with scale/units justified by the original requirement.
Reconcile the modeled objective with the original expression, including
normalization and constants. Compare analytical cases or a separately written
small reference when available. Nonunique solutions need not match vectors.

For optimality, use valid lower/upper bounds, applicable KKT conditions, or
appropriate reference accuracy. Duals alone do not supply a certified bound.
For infeasible/unbounded outcomes, identify any independently checked
certificate or ray separately from solver status/reference agreement.

## Helper contract

The optional helper loads a trusted Python file providing:

- `build(data) -> (cp.Problem, dict of named original cp.Variable/Expression objects)`.
- `evaluate_original(data, values) -> {"objective": float, "constraints": list}`.

Each original constraint record has `name`, `relation` (`le` or `eq`), `value`
(scalar or array), and optional nonnegative scalar/array `scale` (default 1).
`value` means g(x) for g<=0 or h(x) for h=0. Include original domains and
constraints even when the model uses attributes or auxiliaries. Reject invalid
original-domain evaluations instead of silently projecting the solution.

Run with an existing compatible environment, or explicitly use uv and its
inline dependency declaration. Resolve the helper's path from the installed
skill directory and model/data paths from the user's workspace. Arguments are:

    python /absolute/skill/path/scripts/verify_model.py model.py --data data.json

Options include `--solver`, `--atol`, `--rtol`, `--include-duals`, `--check-only`, `--point`,
and `--output`. Normal operation solves the model; check-only does not solve.
No dependency install occurs inside the helper. Loading model.py executes its
Python code with host authority; it is not a sandbox.

The JSON report distinguishes DCP/DPP, solve status, finite values, modeled/
original objective reconciliation, and named original residuals. Missing original
callbacks, inaccurate statuses, and failure statuses cannot produce a numerical
"passed" result. `--include-duals` reports explicit constraint duals only.
The report does not automatically certify strong duality, KKT, or a gap.

The callback is itself part of the generated formulation. Audit it against the
original ledger; a callback that omits a requirement can pass its own residuals.
The helper cannot detect that semantic omission automatically.

## Check a stated example without solving

Use the same original-expression callback to check a supplied point. A point
file contains original named `values` and optionally `claimed_objective`:

```json
{"values": {"x": [1.2, 1.6]}, "claimed_objective": 4.5}
```

For the bundled ball example with a=[3,4], radius=2:

    python /absolute/skill/path/scripts/verify_model.py model.py --data data.json --point point.json

This mode executes `evaluate_original`, without calling `build` or a solver.
It checks finite values, original feasibility, and the difference between a
claimed and recomputed objective. It can disprove an incorrect example value;
passing checks establish neither optimality nor that the callbacks faithfully
represent the request. Include all domains and validate shapes in the callback.
The model module still executes when loaded. Solver, dual and check-only options
cannot be combined with point mode. Exit codes are 0 for passed checks, 1 for a
failure, and 2 for missing checks.
