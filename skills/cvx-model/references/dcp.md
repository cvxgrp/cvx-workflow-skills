# DCP, domains, and matrix assumptions

## Problem-level rules

Minimize a convex expression or maximize a concave expression. An inequality
f(x) <= g(x) is DCP when f is convex and g concave; reverse roles for >=.
Equalities are affine. A nonlinear equality can have a special convex
reformulation, but justify that equivalence instead of treating general
nonlinear equalities as convex constraints.

Affine expressions are both convex and concave. Constants/parameters are
constant with respect to decision variables, but parameter signs matter to
composition rules and must remain valid on later assignments.

## Composition

For a convex outer function, each argument must be affine, convex where the
outer function is nondecreasing, or concave where it is nonincreasing. For a
concave outer function, use affine, concave/nondecreasing, or convex/nonincreasing
arguments. Monotonicity can depend on the argument's known sign and domain.

Do not reason "convex composed with convex is convex" without monotonicity.
Do not model variable products, quotients, or x*x as if ordinary algebra
established DCP. Read curvature/sign of subexpressions and identify the first
failed composition. Use appropriate named atoms or a justified exact lift.

Explicit constraints such as x>=0 need not propagate sign information to the
DCP analyzer. Use `cp.Variable(nonneg=True)` or a suitable known-sign atom when
the composition needs that information. A positive attribute represents a
closed/nonnegative sign restriction, not a strictly positive numerical margin.
To require a strict domain away from zero, use a justified explicit lower bound,
not an unexplained epsilon that changes the problem.

## Convexity versus representability

`sqrt(1 + square(x))` is mathematically convex but not DCP as written. Its exact
representation `norm(hstack([1, x]), 2)` is DCP. Likewise, the norm of an affine
residual should use a norm atom rather than a square root of sum-of-squares.

A Hessian proof must hold on the stated convex domain. A floating-point PSD test
is numerical evidence under a tolerance, not an exact symbolic proof. Random
convexity samples cannot prove a global property. DCP acceptance says nothing
about whether a demand constraint, loss coefficient, or business domain was
translated correctly.

## Quadratic forms

For real symmetric Q, x^T Q x is convex iff Q is PSD on the relevant full-space
domain. Validate symmetry and PSD assumptions before relying on them. For large
structured matrices, use a justified factor Q=R^T R and `sum_squares(R @ x)`
when appropriate. Check that a factorization's orientation reproduces Q.

Do not use `psd_wrap` or `assume_PSD=True` to make an indefinite matrix appear
convex. These bypass analysis; they do not alter eigenvalues. Do not silently
clip eigenvalues. If symmetry/PSD is only approximately true due to numerical
roundoff, quantify the discrepancy and obtain/justify the intended data policy.

For Q=[[1,2],[2,1]], the eigenvalues are 3 and -1. A full-dimensional box does
not make that quadratic objective convex. A justified restriction to an affine
subspace may change the relevant Hessian; analyze that restricted problem
explicitly rather than generalizing the full-space test.

Source: [CVXPY DCP tutorial](https://www.cvxpy.org/tutorial/dcp/index.html).
