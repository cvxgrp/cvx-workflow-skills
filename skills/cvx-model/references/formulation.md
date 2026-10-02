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
