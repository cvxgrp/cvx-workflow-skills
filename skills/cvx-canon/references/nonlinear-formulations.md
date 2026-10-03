# Formulating smooth nonlinear problems for IPOPT

An exact expression can still be a poor numerical formulation. Separate the
mathematical identity, domains, and initialization from a measured solver outcome.
Improve the formulation before tuning iteration limits. Use sparse symbolic AD
in CasADi/Pyomo or checked native callbacks, then evaluate the original problem.

## Exact nonsmooth lifts and domains

[Disciplined Nonlinear Programming](https://arxiv.org/abs/2606.02896)
(Cederberg, Zhang, Nobel, Boyd, 2026), sections 3–4, motivates two patterns:
monotonicity-justified epigraph/hypograph lifts for nonsmooth atoms, and bounded
auxiliary arguments for restricted-domain smooth atoms. Apply these identities
directly in the selected frontend; no DNLP/CVXPY runtime is needed. The discipline
supports smooth representations, not global optimization guarantees.

- Replace an absolute value in a nondecreasing minimization context by t with
  `t>=r(x), t>=-r(x)`. For `sum(abs(r))`, use one t per component. For a maximum,
  use `t>=r_i(x)` for each branch. Concave minima use a hypograph in the matching
  monotone context. The residual expressions may themselves be smooth nonconvex.
  Prove that reducing/increasing t to its original atom preserves feasibility and
  does not worsen the objective. Negative weights, nonmonotone compositions, or
  an equality to the atom invalidate automatic exactness; inspect them explicitly.
- For `log(h(x))` or a reciprocal, introduce `u=h(x)` and put the domain on u as
  a native variable bound. Initialize u inside its domain even when that equality
  is initially infeasible. This makes domain-valid function evaluation easier;
  it does not guarantee eventual feasibility. Set bound-relaxation handling so
  trials cannot cross the domain. A numerical positive floor is a stated domain
  restriction unless already implied by the original problem; recheck sensitivity.
- A Euclidean norm epigraph has the exact smooth inequality
  `sum(r_i(x)**2)<=t**2, t>=0`, but its gradient vanishes at `(r,t)=(0,0)`.
  The paper's `sum(r_i**2)/t<=t, t>0` avoids that degeneracy in the interior but
  excludes the origin. A positive floor also changes the feasible set. Preserve
  this boundary distinction; prefer a conic solver for convex norm models when
  boundary exactness matters. Do not present squaring as a universal robustness fix.

Do not pass `abs`, `max`, branch-dependent derivatives, or clipping through AD and
assume a smooth NLP. Smooth approximations (softplus, pseudo-Huber, epsilon norms)
change the model; use only when requested or justified and label the approximation.

## Other formulation choices

These are problem-specific engineering choices, not claims that DNLP proves a
performance improvement for every NLP.

| Pattern | Benefit and condition |
|---|---|
| Scale `x=d+Dz`, positive diagonal D, and positively scale objectives/constraint rows | Bring typical values and derivatives to comparable magnitudes; recover x and check residuals in original units. Record scales for requested multipliers. |
| Keep sparse residual/trajectory variables with linking equalities | Avoid a dense reduced Hessian/Jacobian after eliminating states or intermediate expressions; compare setup and solves if speed matters. Extra variables alone do not establish improvement. |
| Use least-squares polynomials for an original squared loss | `sum(r_i**2)` is smooth even at zero. Replacing an unsquared norm objective with its square is justified only by monotonicity for that whole objective, not when added to other terms. |
| Keep native bounds and independent constraint rows | Remove genuinely duplicate equalities and avoid `h(x)**2<=0` to encode `h(x)=0`, which has zero gradient on the feasible set. Never remove a nonredundant constraint. |
| Domain reparameterization, e.g. `x=exp(z)` | Can enforce strict positivity, but excludes zero, can overflow, and can worsen conditioning. Check the original domain, bounds, and recovery; lifting may be preferable. |

Use physically meaningful starts, including all auxiliary variables; avoid a
symmetry point with zero gradient when it is a known saddle. For difficult local
problems, multistart, continuation from a simpler problem, or feasibility/restoration
initialization may help. State seeds/schedules, validate the final original
constraints and objective, and retain the best original-feasible candidate. A
penalty objective, intermediate continuation model, or feasible initialization
heuristic is not a proof of exactness or a global certificate.

For convex-concave outer iterations read [CCP](ccp.md); for a bound on a harder
problem read [relaxations](relaxations.md). These are distinct choices from a
smooth exact IPOPT formulation. Compare local candidates only after original
feasibility checks, and do not label every successful KKT termination a proven
local minimum without the required second-order evidence.
