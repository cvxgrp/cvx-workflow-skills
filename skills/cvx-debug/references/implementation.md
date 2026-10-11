# Implementation diagnosis

## Shapes before curvature

Inspect `.shape`, variable/parameter definitions, reduction axes, and operands.
An (m,) vector and an (m,1) column can broadcast into an unintended (m,m)
expression. Check `@` versus `cp.multiply`, row/column indexing, and explicit
reshape order. Preserve sparse data; `np.asarray` is not a sparse conversion.
Use CVXPY atoms rather than NumPy functions on symbolic expressions.

## DCP failure

Locate the first failed composition using subexpression `.sign`, `.curvature`,
and `.shape`. Check objective direction, inequality orientation, affine
equalities, and parameter domains. Mathematical convexity and DCP acceptance
are different: `sqrt(1 + square(x))` is exactly `norm(hstack([1, x]), 2)`.
An exact atom/reformulation can fix representation without changing the model.
Explicit sign constraints need not inform DCP analysis; suitable attributes or
known-sign expressions can, but never invent a domain solely to pass analysis.

Read [quadratic representations](quadratics.md) for `quad_form` failures. First
identify which argument varies: a variable vector with PSD data admits a factor
form; a fixed vector with a matrix variable gives an affine trace operator.
Check the replacement against the original expression, not only `is_dcp()`.
Do not treat all quadratic-form failures as one numerical bug.

## DPP and reuse

Check whether changing data is actually `cp.Parameter` data, whether the Problem
is built once, and whether `problem.is_dcp(dpp=True)` holds on the concrete path.
Products of parameters can be DCP but not DPP. A PSD matrix Parameter in
`quad_form` can fail DPP; an externally computed factor Parameter in
`sum_squares(R @ x)` can help. Preserve factor orientation and update validation.
Factoring costs, changing rank/shapes, and solver refactorization still matter.

Keep fixed builder inputs distinct from Parameters. Invalid input, infeasible
model, unavailable solver, DCP failure, and numerical failure are different
outcomes. A correct model can be infeasible; do not make input validation reject
instances just because their constraints have no feasible point.

Sources: [CVXPY DCP](https://www.cvxpy.org/tutorial/dcp/index.html),
[DPP](https://www.cvxpy.org/tutorial/dpp/index.html),
[constraints](https://www.cvxpy.org/tutorial/constraints/index.html).
