# Repeated solves and DPP

Use a single `cp.Problem` with named `cp.Parameter` objects when data changes
but structure/shapes remain fixed. A quantity the request sweeps or revisits
("plot cost versus capacity", "repeat for C = 1", "for each lambda") is data
to make a Parameter, not a variable; build the problem once, outside the loop,
and assign values inside it. Set parameter values before solving and
validate their domains on updates. Changing dimensions generally requires
rebuilding. Negative regularization is not repaired by silently clipping it.

```python
lam = cp.Parameter(nonneg=True, name="lam")
x = cp.Variable(A.shape[1], name="x")
problem = cp.Problem(cp.Minimize(
    0.5 * cp.sum_squares(A @ x-b) + lam * cp.sum_squares(x)))
assert problem.is_dcp(dpp=True)
for value in regularization_values:
    lam.value = value  # rejects negative values
    problem.solve(solver="CLARABEL", warm_start=True)
    # Check status and original quantities on every solve.
```

DCP treats parameters as constants with respect to variables. DPP additionally
restricts parameter dependence so canonicalized data can be updated efficiently.
A parameter-affine factor multiplied by a parameter-free expression is an
allowed DPP pattern when the DCP curvature/sign rules are also satisfied.
Products of parameters may be DCP but not DPP. Always check the actual problem;
copying a pattern is not evidence that every extension is compliant.

A parameterized `quad_form(x, Q)` may fail DPP even when Q is declared PSD.
A factor-based representation can help: compute Q=R^T R outside the DSL, assign
R to an appropriately shaped Parameter, and use `sum_squares(R @ x)`.
Factor changes, rank changes, memory cost, and floating-point PSD assumptions
must be considered. `is_dcp(dpp=True)` is the verdict on the concrete version/path.

DPP caching, solver warm starts, symbolic factorization reuse, and numerical
factorization reuse are distinct. Changing a linear-system matrix can require
new numerical factorization even when canonicalization is cached. Profile
first solve, subsequent updates/compilation, and solver work separately.
Do not promise a universal repeated-solve speedup or move immediately to native
code before establishing that modeling overhead is the consequential cost.

Source: [CVXPY DPP tutorial](https://www.cvxpy.org/tutorial/dpp/index.html).
