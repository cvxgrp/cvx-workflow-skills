# Requested dual multipliers

Expose multipliers only when requested. Keep named explicit constraint objects
available to callers; variable attributes do not expose separately named bound
duals. Preserve attributes needed for DCP sign information and use explicit
constraints for requested multipliers. Avoid adding a redundant attribute for
the same bound when its separate multiplier matters: duplicate restrictions can
split multipliers. Use a justified equivalent formulation when sign information
and explicit dual access both matter.

Adapt the return interface to the user. The default constructor returns
`(problem, named_variables)`; an additional constraint map is appropriate when
requested. The optional existing verification helper keeps its two-item contract
and reports explicit constraints by index with `--include-duals`.

```python
x = cp.Variable(n, name="x")
constraints = {"lower": x >= lower, "capacity": A @ x <= capacity}
problem = cp.Problem(cp.Minimize(cp.sum_squares(R @ x)),
                     list(constraints.values()))
# A constructor can return problem, {"x": x}, constraints.
# In a requested solve workflow, check status and original residuals first.
problem.solve(solver=solver)
if problem.status != cp.OPTIMAL:
    raise RuntimeError(f"No accepted optimum: {problem.status}")
duals = {name: constraint.dual_value
         for name, constraint in constraints.items()}
```

Check presence, shapes, and finite values before interpreting multipliers.
Do not expose missing/stale values as optimal multipliers after a failed solve.
An infeasible solve can expose dual rays or certificate data in some versions;
nonempty dual arrays do not override the status or become optimal multipliers.
An inaccurate or iteration-limited result can be returned with that qualification
if useful, but must not be labeled a verified optimum. Retain vector constraint
indexing and identify the original row each entry corresponds to.

For minimization, use L=f+sum(y_i g_i)+z^T h with g_i<=0, y_i>=0, h=0.
For a<=b write a-b<=0; for a>=b write b-a<=0. Equality multipliers are signed.
If an inequality row is multiplied by positive s, its original multiplier is
s times the scaled-row multiplier. Objective scaling changes multipliers too.
Sensitivity signs depend on this convention and the perturbed quantity; avoid
unconditional shadow-price interpretations when derivatives or multipliers are
nonunique. Derive the convention separately for maximization.

Returned multipliers alone do not establish optimality, a dual bound, or strong
duality. When verification is requested and applicable, check original primal
feasibility, multiplier domains, complementarity, and stationarity with appropriate
tolerances; use subgradients for nonsmooth terms. Symbolic dual derivation is
outside this feature.

Sources: [CVXPY dual variables](https://www.cvxpy.org/tutorial/advanced/index.html#dual-variables),
[attributes](https://www.cvxpy.org/tutorial/constraints/index.html).
