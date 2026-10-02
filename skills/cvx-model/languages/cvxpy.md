# CVXPY implementation

Validated development environment: CVXPY 1.9.3 with Clarabel for small real
continuous LP/QP/SOCP cases. Do not assume another version/interface has identical
compilation, native-bound, or default-solver behavior. The optional helper uses
CVXPY >=1.7,<2; this compatibility range is a requirement, not a claim that every
version in it has been tested.

## Construct expressions and data carefully

Use `np.asarray(..., dtype=float)` for dense numerical data. Preserve SciPy
sparse matrices/arrays with `A.astype(float)`; `np.asarray` is not a sparse
conversion and can fail. Check finite sparse coefficients through `A.data`,
without converting the matrix to dense. Use a deliberate shape convention.
Prefer 1-D vectors where appropriate; an (m,) vector and an (m,1)
column can broadcast to an unintended (m,m) expression. For shipment matrices,
keep the matrix shape and choose row/column reduction axes explicitly.

Use `@` for linear maps/dot products and `cp.multiply` for elementwise products
with constants. Use `cp.sum_squares` for quadratic residuals and `cp.norm` for
norms. Default validation to shapes and finite values. Each additional rejection
must follow an explicit input requirement or a representation requirement, such
as PSD data for a convex quadratic form. A property of feasible solutions does
not automatically constrain the input bounds. Do not reject loose bounds,
screen feasibility, or add sign/normalization assumptions for convenience.
Return infeasible models unless screening was requested; do not clip, normalize,
or otherwise change user data.

Vectorize objectives and constraints rather than creating one scalar CVXPY
object per row/entry. Prefer `cp.sum` to Python `sum` over expressions. Avoid
forming a dense identity for a squared norm or a dense Gram matrix when the
residual/factor representation preserves useful structure. For reshape/vec,
specify `order="C"` or `order="F"` consistently with the intended indexing.
Choose a version-supported canonicalization backend only after measuring its
effect on the actual vectorized/parameterized workload. Measure construction,
compilation/update, and solve-call/solver time separately; faster compilation
alone is not a faster end-to-end solve.

Name original variables so a human can recover/interpret them. Store important
explicit constraints when duals are wanted. Parameter names and sign attributes
should express intended updates, not only the current example's values.

## Bounds and attributes

For lower/upper bounds with no requested bound duals, modern CVXPY supports:

```python
x = cp.Variable(n, bounds=[np.zeros(n), upper], name="x")
problem = cp.Problem(cp.Minimize(c @ x), [cp.sum(x) == mass])
```

The inspected 1.9.3 HiGHS interface can use column bounds from attributes rather
than expanding explicit lower/upper constraints into rows. Other solver paths
may still lower attributes into rows. Attributes provide useful sign/domain
information, but bounds and nonnegativity combinations are version-dependent;
choose compatible attributes and test the concrete problem.

When bound duals are requested, explicit constraints are often preferable:

```python
x = cp.Variable(n, name="x")
lower_bound = x >= 0
upper_bound = x <= upper
problem = cp.Problem(cp.Minimize(c @ x),
                     [lower_bound, upper_bound, cp.sum(x) == mass])
```

Do not claim the attribute form exposes separately named bound multipliers.

## Solve and inspect

Check `problem.is_dcp()` before solve and `problem.is_dcp(dpp=True)` when
repeated-solve caching is part of the requirement. Select an installed solver:
Clarabel is a useful small conic/QP baseline; OSQP targets QPs; SCS is a conic
fallback whose achieved accuracy needs particular attention. Default selection
and cone conversions are version-specific, not a universal recommendation.

Do not access `.value` as an optimum before checking status. Infeasible,
unbounded, inaccurate, and iteration-limited outcomes require different
handling. Check original variables, constraints, and objective after recovery.
`problem.value` is the modeled objective at the returned solution/status;
comparing it with an original expression is not an independent optimality proof.

Never rely on printing a rounded solution as verification. Preserve raw values
for residuals and apply scale-aware tolerances. Do not require one exact vector
when the optimum is nonunique.

Sources: [CVXPY constraints](https://www.cvxpy.org/tutorial/constraints/index.html),
[solver features](https://www.cvxpy.org/tutorial/solvers/index.html), and
[API](https://www.cvxpy.org/api_reference/cvxpy.problems.html).
