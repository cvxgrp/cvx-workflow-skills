# Formulation and semantic ledger

## Intake

Record original variables/shapes, units, data domains, objective direction,
normalizations, and all requirements. Ask about missing facts only when they
change the problem. Important examples: full investment versus a budget cap;
short positions versus unconstrained leverage; variance versus standard deviation;
expected versus worst-case requirements; entrywise versus spectral matrix norms.

For materially incomplete requests, return clarification questions, not a
certified default model. Conditional alternatives can be educational, but each
must be labeled and must not silently become the implementation's default.

A compact worksheet can be:

| Original meaning | Mathematical expression | Implementation / assumption |
|---|---|---|
| Meet each production requirement | A x >= d | Rows of A are requirements |
| Product capacity | 0 <= x <= u | Bounds or explicit constraints |
| Mean squared loss | ||A x-b||^2/(2m) | m is observation count |

Track domains introduced by atoms as well as explicit business constraints.
For a repair, state why the new formulation is equivalent, including constants,
auxiliary-variable recovery, parameter ranges, and boundary cases. If minimizing
an epigraph variable, explain why it is tight at optimum rather than declaring
all auxiliary constraints equalities. A relaxation has a bound direction and
is not an equivalence.

## Common semantic errors

- Prose hides constraints in ordinary words. Read the request once for the
  objective and again only for restrictions. A physical amount (load, flow,
  stock, mass) is usually nonnegative even when unstated; "cannot charge faster
  than C per period" is a rate bound; "end where we started" is a periodic
  boundary condition such as q_1 = q_T + c_T, easy to drop. Record each implicit
  constraint in the ledger as an assumption the user can see.
- Demand is generally a lower bound, capacity an upper bound. Translate the
  actual prose; do not infer directions from which constraint is easier.
- Sum of absolute residuals differs from absolute value of a sum.
- Mean loss differs from total loss unless the regularization coefficient is
  changed consistently. Preserve user coefficients instead of silently tuning.
- Matrix row/column sums represent different conservation laws.
- Variance and its square root can share an optimizer but not the reported
  objective, units, or tradeoffs with additional objective terms.
- Inequality versus equality budgets and sign restrictions change the feasible
  set even when a particular instance has the same optimum.
- A feasible point satisfying all original constraints establishes one-way
  recovery for that point, not equivalence of the entire model.

## Robust linear constraint

For all ||delta||_2 <= epsilon, (a+delta)^T x <= b is exactly

    a^T x + epsilon ||x||_2 <= b,   epsilon >= 0.

This follows from the support function of a Euclidean ball; at nonzero x the
worst delta points along x. At x=0 the added term is zero. Sampling uncertainty
vectors is not this universal constraint. For other uncertainty sets, derive
the correct support function and confirm the representation is in scope.

## Linear-fractional objective

A ratio of affine functions, such as profit per dollar spent, is quasilinear,
not convex: `cp.Maximize(num / den)` is not DCP. For

    maximize (c^T x + d) / (e^T x + f)   subject to  G x <= h,  A x = b,

with e^T x + f > 0 on the feasible set, the Charnes-Cooper substitution
y = x / (e^T x + f), t = 1 / (e^T x + f) gives the exact LP

    maximize c^T y + d t   subject to  G y <= h t,  A y = b t,  e^T y + f t = 1,  t >= 0.

A feasible x maps to a feasible (y, t) with t > 0 and the same objective; a
feasible (y, t) with t > 0 maps back through x = y / t. Scale bounds and sign
attributes the same way: 0 <= x <= u becomes 0 <= y <= u t. State the positive
denominator as an assumption and say what establishes it (for example f > 0,
e >= 0, and x >= 0); do not add an unrequested epsilon to force it.

At t = 0, y is a recession direction with e^T y = 1, and the LP value is a
supremum the original problem need not attain. A nonempty bounded feasible set
excludes t = 0. If a solve returns t near zero, report the unattained supremum
rather than dividing by t. Return the original x and evaluate the original ratio
at it. Minimization is the same with `Minimize`.

```python
y = cp.Variable(n, nonneg=True, name="y")      # x >= 0 carries over to y
t = cp.Variable(nonneg=True, name="t")
problem = cp.Problem(cp.Maximize(c @ y + d * t),
                     [G @ y <= h * t, e @ y + f * t == 1])
# After an optimal solve with t.value > 0: x = y.value / t.value
```

With data held in Parameters, products such as `h * t` are DPP when the
parameter multiplies the variable once; check `is_dcp(dpp=True)`. CVXPY's
`problem.solve(qcp=True)` on the original ratio (DQCP bisection) is a useful
cross-check of the optimal value, not a substitute for the LP model.
