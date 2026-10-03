# IPOPT through the user's framework

Use this path when the user works in CasADi or Pyomo. Express the derived smooth
NLP in that framework and call its IPOPT interface. Do not translate an existing
framework application into handwritten callbacks without a reason. This explicit
frontend support does not permit CVXPY solver-data export or inversion. Read
[nonlinear formulations](nonlinear-formulations.md) before constructing expressions.

## CasADi

Create SX or MX decision variables and a separate symbolic parameter vector p.
Use CasADi operations (`vertcat`, `sumsqr`, `log`, etc.), not NumPy evaluation or
Python conditionals on symbolic decisions. SX suits simple scalar expressions;
MX can retain larger matrix/function structure. Specify
`nlp={"x":w,"p":p,"f":f,"g":g}` and build
`ca.nlpsol("name","ipopt",nlp,options)` once. CasADi supplies sparse automatic
first and second derivatives. Prefer this direct NLP plugin for a thin layer;
keep Opti when already used by the application and its interface is appropriate.

Pass `x0,p,lbx,ubx,lbg,ubg` on each call. Equality rows have identical lbg/ubg.
Numeric bounds and p can change without reconstructing an unchanged expression
graph; graph/dimension/sparsity changes require reconstruction. Warm starts use
`x0` and optionally `lam_x0/lam_g0`, with appropriate IPOPT warm-start options;
previous inputs are not parameter updates. Keep a named slice map for lifted w.
CasADi matrix vectorization/reshape is column-major; use matching NumPy `order="F"`
when recovering matrices.

Read `solver.stats()` immediately: `success` and `return_status` distinguish
termination, including acceptable-level success versus full tolerances. Check
original-domain, bound, and constraint residuals before accepting `result["x"]`.
Return a local candidate and original objective, not a global optimum claim.
Requested duals use `lam_g/lam_x` with documented row/bound signs and scaling.
A differentiable symbolic objective is not automatically a differentiable NLP
solution layer; do not promise differentiation through `nlpsol` without a separate
verified sensitivity method.

[Official NLP interface](https://web.casadi.org/docs/#nonlinear-programming).
The [CasADi example](../assets/casadi_nlp.py) reuses parameters and native bounds,
with an exact absolute-value epigraph inside a nonconvex objective.

## Pyomo

Use `ConcreteModel`, explicitly indexed `Var`, mutable `Param` for changing data,
and symbolic `Objective`/`Constraint` expressions. Use Pyomo mathematical functions.
Calling `value(param)` while building an expression freezes that value; retain the
mutable Param symbol when the expression must update. Python branches during
construction select a structure and do not model decision-dependent logic.
Use native variable bounds and preserve an index/name map for recovery.

The standard `pyo.SolverFactory("ipopt")` path writes NL, invokes an IPOPT
executable, and reads its result. Installing Pyomo alone does not install that
executable. Check `available(exception_flag=False)`; report a missing backend
instead of claiming a solve. Pyomo's cyipopt/PyNumero paths have different native
requirements (including ASL), so do not assume they work because CasADi bundles an
IPOPT library. Choose one installed interface and follow its actual result API.

For the standard interface call `solve(model,load_solutions=False)`, inspect solver
status, termination, and existence of a returned solution, then
`model.solutions.load_from(results)` only on an accepted path. Pyomo's
`optimal`/`locallyOptimal` labels for IPOPT do not establish global optimality.
Limit or infeasible outcomes must not leave stale initial/previous variable values
presented as a new solution. Check original expressions after loading.

Mutable Params and bounds may be updated before another solve. The standard NL
interface rewrites the model; do not advertise persistent matrix updates. Provide
domain-safe initial values for all lifts. Optional multipliers/warm-start suffixes
are interface-specific; add only when required. Keep solver-generated files in
the user's artifact directory; use framework-supported temporary-file settings.

[Solver recipes](https://pyomo.readthedocs.io/en/stable/howto/solver_recipes.html).
The [Pyomo example](../assets/pyomo_nlp.py) mirrors the CasADi formulation and
explicitly checks backend availability and solution loading.
