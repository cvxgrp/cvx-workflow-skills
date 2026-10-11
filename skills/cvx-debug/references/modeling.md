# Requirements, results, and statuses

Compare supplied intent with implemented variables, domains, units, objective
direction/factors/constants, and each constraint. Look for a budget equality
versus cap, reversed demand, omitted bounds, borrowing assumptions, missing
conservation, or loss normalization. A sum of absolute residuals differs from
the absolute value of their sum. These are errors only relative to the intended
problem; do not invent missing application meaning.

Check data-dependent construction branches and implicit variable/atom domains.
Describe auxiliaries literally before proposing elimination. For a candidate
repair, account for every original requirement and label equivalence assumptions.
Do not infer equivalence from one matching optimum.

## Unexpected or incorrect results

Check status before using `.value`. Evaluate the original objective and constraint
residuals at the returned raw point with scale-aware tolerances; rounded printing
does not establish feasibility. Include implicit domains and transformation
recovery. A DCP model with a successful solve can still implement the wrong task.
For nonunique optima, compare objective and applicable optimality conditions rather
than insisting on a particular solution vector.

## Infeasible or unbounded

Check actual data for conflicting bounds, inconsistent conservation, unit
mismatches, absent constraints, and objective signs. Substitute a supplied known
feasible point directly. An empty interval lower>upper proves infeasibility; min
-c*x with x>=0 and c>0 has an improving ray. Give the concrete argument when one
exists. Adding arbitrary bounds or dropping constraints changes the problem.

For an ambiguous infeasible-or-unbounded status, a diagnostic feasibility solve
can use the same constraints and zero objective, or compare a compatible solver.
Label it as a diagnostic problem. Preserve domains implicit in the original
objective when removing that objective; otherwise even the feasible set changes.
A numerically uncertain feasibility result does not resolve the ambiguity.
Solver statuses alone are not independently checked certificates.

## Multipliers and accuracy

Missing `.dual_value` can follow from failed solves or attributes instead of
explicit constraints. Duplicate restrictions can split multipliers. Check row
indexing, inequality signs, objective/row scaling, and missing/nonfinite values
before interpreting them. Returned duals alone prove neither strong duality nor
an optimality certificate. Symbolic dual derivation is out of scope.
Some versions expose dual rays/certificate arrays after infeasible solves; check
status even when arrays are present and never interpret them as optimal multipliers.

Treat `optimal_inaccurate`, iteration limits, and invalid data separately. Check
original residuals, coefficient ranges, application units, and solver settings.
Changing scaling needs consistent primal recovery; do not delete a difficult row
or silently alter data. A request for more decimals is not evidence of accuracy.

Sources: [CVXPY problems](https://www.cvxpy.org/tutorial/intro/index.html),
[dual variables](https://www.cvxpy.org/tutorial/advanced/index.html#dual-variables).
