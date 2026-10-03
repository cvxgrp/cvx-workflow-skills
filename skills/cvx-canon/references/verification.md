# Focused native-code verification

Scale checks to the actual transformation and API risks; do not build a general
evaluation framework for a single generated application. Use trusted user code
and an existing environment. Keep generated outputs in the user's designated
artifact directory. Record dependency versions and settings for numerical claims.

The packing helper requires NumPy. The conic and MILP examples require NumPy,
SciPy, and only their selected solver package (`moreau`, `scs`, or `highspy`).
The nonlinear example requires NumPy, plus `cyipopt` and its native IPOPT library
for solving; its derivative callbacks can be checked without either solver.
Tensor layers require the selected PyTorch/JAX integration; CasADi may bundle
IPOPT, while Pyomo needs a separate supported IPOPT executable/interface.
These are application dependencies, not a requirement to install every backend.

## Three separate checks

**Semantics:** trace original variables/domains, objective direction/constants,
every constraint, and parameter effects. Check original expressions, not copies
of assembled expressions that repeat the same mistake.

**Transformation:** verify feasible original points lift into native constraints
and native feasible points recover with the claimed relationship. Check signs,
quadratic factors, auxiliary domains, sparse row/index maps, and objective offsets.
For PSD test pack/unpack and Frobenius inner products using off-diagonal entries
in dimension at least three. For relaxations verify containment/bound direction;
for CCP verify tangency and upper-bound/inner-approximation direction.

**Numerics:** after a meaningful native status, recover the original variables
and evaluate the original objective, bounds, equality/inequality/cone residuals,
and integer distance when applicable. Use scale-aware tolerances. Requested dual
checks can include stationarity/complementarity after the original sign/scale map;
dual outputs are not required for ordinary primal recovery.

## Relevant probes

- Parametric paths: change costs, RHS, and any parameter affecting matrix values
  or offsets. Compare reused and freshly constructed instances; keep sparse
  structure fixed only where the backend permits it. Change a coefficient that
  was initially zero to exercise declared structural slots.
- Conic paths: use analytic small cases or an independent modeling reference,
  plus relevant infeasible/unbounded instances. Certificates are not primal
  solutions. Alternative correct representations need not match compiler matrices.
- HiGHS: check integer/bound/row feasibility, incumbent validity, objective offsets,
  and gap/bound handling at limits. Never manufacture optimality by rounding.
- IPOPT: compare objective directional derivatives and Jacobian products to finite
  differences at domain-safe points. If supplying Hessians, check Lagrangian
  Hessian-vector products with nonzero multipliers and objective factor. Evaluate
  original feasibility on returned points; local-infeasibility termination is not
  global infeasibility evidence.
- Frameworks/batches: check each returned status and original residual, compare
  batched with separate solutions, and verify gradients for shared and per-member
  P/A/q/b plus original parameters and recovery. Include active/inactive constraints
  away from transition points, sequential reuse, and the requested jit/vmap/autograd
  composition. A valid forward result does not prove a correct backward rule.
- NLP frontends: exercise symbolic parameters and changing numeric bounds without
  stale expressions; check domain-safe lifted initialization and exact epigraph
  tightness where required. Model construction or NL-file writing alone does not
  count as an IPOPT solve. Report the frontend and native backend availability.
- CCP: check gradients/linearizations at more than the current point, inner status,
  and original feasibility on accepted candidates. A small step or vanishing
  penalty change is insufficient when original constraints remain violated.
- Relaxations: test a known original feasible point's lifted membership; compare
  with a small enumerated binary optimum when practical. Check recovered candidates
  against original constraints separately from the relaxed objective.

CVXPY may be a development-time reference constructed independently from the
original formulation. Do not export its matrices/recovery maps to implement the
application. A matching optimum complements, but does not replace, semantic and
transformation checks. Check the assembled skill in isolation when validating its
bundled resources, rather than depending on checkout-relative imports.

Report actual checks and missing coverage. A CPU example does not qualify CUDA,
large-instance performance, all cone builds, every API version, or model selection.
Measure performance only at matched original-problem accuracy, separating setup,
updates, transfers, and solves. Keep generated applications free of validation
machinery that users do not need at runtime.
