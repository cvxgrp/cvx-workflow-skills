# Atoms and exact DCP repairs

Use these within the stated domains; do not replace an objective by a
monotone transformation when other terms or reported units would change.

| Meaning | CVXPY expression | Curvature / domain / common trap |
|---|---|---|
| Sum of squared residuals | `cp.sum_squares(A @ x-b)` | Convex; multiplying by 1/(2m) is not optional for mean loss |
| Square of scalar | `cp.square(z)` | Convex; affine z is safe; sign-dependent monotonicity for compositions |
| Euclidean residual norm | `cp.norm(A @ x-b, 2)` | Convex; fixes sqrt(sum(square(...))) |
| L1 residual / penalty | `cp.norm1(z)` | Convex; not the absolute value of the summed entries |
| Maximum absolute residual | `cp.norm(z, 'inf')` | Convex; both residual signs matter |
| Positive part | `cp.pos(z)` | Convex/nondecreasing; useful for convex hinge losses |
| Maximum / minimum | `cp.max(z)` / `cp.min(z)` | Maximum of convex expressions is convex; minimum of concave expressions is concave |
| Quadratic form | `cp.quad_form(x, Q)` | Convex for PSD Q; do not conceal indefinite data |
| Quadratic perspective | `cp.quad_over_lin(z, t)` | Jointly convex for affine z and positive t; sums numerator squares over all entries |
| Positive reciprocal | `cp.inv_pos(t)` | Convex/decreasing on positive domain; raw 1/t is not the right DCP expression |
| Geometric mean | `cp.geo_mean(x)`; weighted: `exact_geo_mean(x, weights)` below | Concave, nonnegative x; weighted exponents must be preserved exactly |
| Weighted absolute residuals | `cp.sum(cp.multiply(w, cp.abs(z)))` | Convex when weights are nonnegative; use elementwise multiply |
| Linear map / dot product | `A @ x`, `c @ x` | Affine; verify shapes and orientation |
| Stacking / reductions | `cp.hstack`, `cp.vstack`, `cp.sum(..., axis=...)` | Affine transformations; axis errors can produce valid but wrong models |

## Perspectives

For t>0, ||z||^2/t is the perspective of squared norm and is jointly convex.
Write `cp.quad_over_lin(z, t)` rather than `cp.sum_squares(z)/t`. If the original
problem requires t>=t_min>0, retain that condition. The closed perspective at
t=0 is 0 when z=0 and +infinity for nonzero z. Do not assume a generic numerical
division implements the closure or silently change a strict domain into its
closure. Specify the intended boundary and test the implementation if needed.

## Geometric means and epigraphs

`sqrt(x[0]*x[1])` is not a valid variable product in DCP. Use the concave
geometric-mean atom on nonnegative x, preserving all budget/weight constraints.
For weighted means, use the [exact geometric-mean helper](../scripts/exact_atoms.py)
or copy its function into the generated code. It accepts normalized, nonnegative
exponents summing exactly to one, constructs the SOC atom with rational inputs,
and verifies `g.w` against those exponents plus zero `g.approx_error`. Run this
inside `build`, not only on one example. The default `cp.geo_mean(x, p=weights)`
can approximate weights; a DCP result does not establish exponent preservation.

```python
# Copy exact_atoms.py beside the application, or inline its function.
from exact_atoms import exact_geo_mean

# Inside build(data), before converting exact weights to a float array:
g = exact_geo_mean(x, data["weights"], max_denom=1024)
problem = cp.Problem(cp.Maximize(g), constraints)
```

Retain explicit `Fraction` values, integer exponents, or exact fraction/decimal
strings such as `"2/7"` and `"5/7"`. JSON can carry these strings. Binary floats
are interpreted as their exact stored values; dyadic values such as 0.5 work,
but rounded rational inputs may be rejected. Do not use `limit_denominator` or
convert rounded floats to decimal strings to guess the intended specification.
If the request supplies relative weights, explicitly normalize exact fractions
before calling the helper; do not normalize stated exponents that should sum to
one. Do not add a runtime dependency on the installed skill directory.

`max_denom` is an explicit representation limit, not an accuracy guarantee. If
construction fails at that limit, retain the rational inputs and choose a
practical larger limit with the same checks, or explain the obstruction. Obtain
permission for any approximation. Do not silently switch to a power-cone
implementation outside the skill's LP/QP/SOCP scope.

For noninteger `power` and nonstandard `pnorm`, check the represented exponent
against the intended exponent and check `atom.approx_error` inside the
constructor. In the validated CVXPY 1.9.3 environment, use `power.p_used` and
`pnorm.p`; `power.p` is the input, not its rationalized representation. Inspect
the installed API on other versions. Preserve the atom's domain. A zero error
alone is insufficient if the input exponent was rounded or changed beforehand.
The construction checker reports exposed `approx_error` fields; its
`--require-exact-atoms` option fails on a nonzero error. It cannot prove that
an atom with zero reported error represents the user's intended function.

For min max_i ||x-a_i||^2, introduce t with `sum_squares(x-a_i) <= t` for every
i and minimize t, or use an equivalent maximum expression. Dropping a center
or using unsquared distances changes the requested model/objective.

These atoms cover common LP/QP/SOCP forms. Exponential/logarithmic objectives,
SDP matrix variables, and other cone families require additional capability
validation; their absence from v1 is not evidence of nonconvexity.

Source: [CVXPY atomic functions](https://www.cvxpy.org/tutorial/functions/index.html).
Approximation behavior: [CVXPY geometric-mean API](https://www.cvxpy.org/api_reference/cvxpy.atoms.other_atoms.html#geo-mean).
