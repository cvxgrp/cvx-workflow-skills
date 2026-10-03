# IPOPT nonlinear interfaces

Use for smooth continuous NLP, including nonconvex problems. IPOPT seeks a local
solution; an exact formulation does not establish global optimality. Nonsmooth
terms need a justified smooth exact reformulation or another solver. Smoothing
changes the problem and must be labeled when used. IPOPT does not enforce integers.

Preserve the user's framework: use CasADi's `nlpsol(..., "ipopt", ...)`,
Pyomo's IPOPT interface, or `cyipopt.Problem` for native callbacks. Read
[framework paths](ipopt-frameworks.md) for symbolic assembly and updates and
[formulation guidance](nonlinear-formulations.md) before choosing the expressions.
The callback details below apply to cyipopt, not to CasADi/Pyomo automatic
derivatives. API basis: cyipopt 1.7.0 documentation; verify the installed version
and native IPOPT build.
[Callback reference](https://cyipopt.readthedocs.io/stable/reference.html),
[IPOPT problem assumptions](https://coin-or.github.io/Ipopt/), and
[termination meanings](https://coin-or.github.io/Ipopt/OUTPUT.html).

Represent `min f(x)` subject to `cl<=g(x)<=cu`, `lb<=x<=ub`. Equality constraints
have equal lower/upper bounds. Keep domains explicit; logs, reciprocals, and square
roots must be well defined at starting/trial points. IPOPT can relax bounds
internally; configure domain-safe bound handling when necessary. Do not fix
callback domain errors by clipping the objective or constraints.

Implement `objective(x)`, `gradient(x)`, `constraints(x)`, and `jacobian(x)`.
For sparse Jacobians also provide `jacobianstructure()` with zero-based row/column
indices. Return values in exactly that fixed structure's order, including entries
that happen to be zero at the current iterate. A dense default Jacobian is
flattened row-major. Do not infer structural nonzeros from a single evaluation.

For exact Hessians, `hessian(x,lagrange,obj_factor)` returns the **lower triangle
of the Lagrangian Hessian** in the declared `hessianstructure()` order:
`obj_factor*Hf(x) + sum(lagrange[i]*Hg_i(x))`. Supplying only `Hf` is incorrect
with nonlinear constraints. Alternatively select
`hessian_approximation="limited-memory"` explicitly and provide correct first
derivatives. Analytic or automatic derivatives are appropriate; verify AD dtype,
shape, sparsity ordering, and framework-to-NumPy conversion.

Construct `cyipopt.Problem(n,m,problem_obj=callbacks,lb=lb,ub=ub,cl=cl,cu=cu)`,
set options with `add_option`, and call `solve(x0)`. Changing callback-owned data
can support new instances when structure stays fixed; changed constructor bounds
or dimensions normally require rebuilding. Warm-start primal/dual inputs are
initialization only; do not assume modifying a Python bound array updates native
bounds. Re-evaluate every parameter-dependent derivative after a change.

Inspect `info["status"]` and `status_msg`. Status 0 indicates success to configured
criteria; 1 indicates acceptable-level termination. Other terminations, including
small steps or detected local infeasibility, do not establish an optimum or global
infeasibility. Recheck original feasibility and, when needed, stationarity. Report
the starting point and a local result; multistart can help find candidates but
does not turn the method into a global solver. Requested multipliers require
mapping `mult_g`, `mult_x_L`, and `mult_x_U` to original rows/bounds and scaling.

The [small nonlinear example](../assets/ipopt_nlp.py) exposes exact first/second
derivatives without requiring cyipopt merely to import/check the callbacks.
