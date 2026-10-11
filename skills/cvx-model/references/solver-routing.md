# Lightweight solver routing

Select within the requested modeling interface. Inspect the installed CVXPY
version and `cp.installed_solvers()` when execution is available; installation
alone does not establish compatibility with the concrete formulation. Respect a
requested compatible solver. Otherwise give a short reason for one suitable
choice; suggest a comparison only when the workload warrants it. No package
installation or benchmarking is required by an ordinary construction request.

## Structure before solver choice

Classify the objective separately from constraints and all implicit domains.
Report polyhedrality as established, nonpolyhedral, or undetermined, with the
reason and assumptions. All affine equalities/inequalities and box bounds give
a polyhedron. L1/infinity-norm bounds and finite piecewise-linear convex bounds
can also have exact polyhedral lifts. A Euclidean ball of positive radius in at
least two dimensions is nonpolyhedral. A nonlinear-looking constraint alone
does not prove nonpolyhedrality: scalar, redundant, zero-radius, or restricted
cases can differ. Use undetermined when the available reasoning is insufficient.

Distinguish the original feasible set from a lifted solver representation. A
norm in the objective can introduce cone constraints even when original
constraints are affine. Conversely, a quadratic objective can stay quadratic
on a QP solver path. A polyhedral feasible set with a general nonlinear objective
is not automatically an LP or QP. `is_dcp()` certifies DCP composition, not
polyhedrality; `is_qp()` is a useful CVXPY representation check, not a universal
geometric classifier. Include objective-domain restrictions when relevant.

## Candidate choices for continuous LP/QP/SOCP

| Structure/workload | Useful candidates and reason |
|---|---|
| LP, especially sparse rows/bounds | HiGHS provides specialized LP methods; compare simplex and IPM when useful. Clarabel is an available conic baseline. |
| Convex QP with polyhedral constraints | OSQP is a useful operator-splitting baseline, particularly for repeated solves. HiGHS offers an active-set QP path; DAQP is another active-set candidate for suitable small/dense QPs. Verify interface support and restrictions. |
| SOCP or quadratic constraints requiring SOC representation | Clarabel is a useful conic baseline. SCS is a candidate for large/modest-accuracy conic workloads; check achieved residuals. LP/QP-only solvers cannot handle general SOC constraints. |

Active-set methods can be attractive for some QPs; polyhedrality does not prove
they outperform interior-point or splitting methods. Consider sparsity, fill-in,
conditioning, problem size, tolerances, available licenses, and repeated updates.
Do not copy native-backend defaults into CVXPY routing automatically.

For comparisons, match original-problem feasibility and objective accuracy.
Measure construction, compilation/update, setup, and solve separately, including
first and subsequent calls. DPP compilation caching, warm starts, and matrix
factorization reuse are distinct. Keep matrix/factor changes in the measurement.
Record versions, data, settings, and timing boundaries; no universal speed claim
follows from a solver family or fewer rows.

If a candidate is missing or incompatible, explain that and choose an available
compatible alternative. Do not silently fall back after an infeasible/unbounded
status or treat a successful API call as acceptable accuracy. Out-of-scope cones,
integrality, and nonconvexity require an explicit scope statement rather than a
silent relaxation. Native deployment and custom algorithms are separate requests.

Sources: [CVXPY solver features](https://www.cvxpy.org/tutorial/solvers/index.html),
[HiGHS](https://highs.dev/), [DAQP](https://darnstrom.github.io/daqp/),
[OSQP](https://osqp.org/docs/).
