# HiGHS native rows, bounds, and integrality

Use HiGHS for MILP, LP, and supported continuous convex QP. Its MILP solver does
not directly support integer quadratic, nonlinear, or conic models. A linearized
or discretized replacement needs its own equivalence/relaxation justification.

API basis: highspy 1.15.1.
[Python examples](https://ergo-code.github.io/HiGHS/dev/interfaces/python/example-py/)
and [supported problem classes](https://ergo-code.github.io/HiGHS/dev/).

Prefer native matrix APIs for sparse generated applications: a `HighsLp` carries
`num_col_`, `num_row_`, `col_cost_`, column lower/upper bounds, row lower/upper
bounds, `offset_`, `sense_`, and `integrality_` when needed. Its `a_matrix_` has
`format_=highspy.MatrixFormat.kColwise`, CSC `start_` including its final pointer,
`index_` row indices, and `value_` coefficients. Do not confuse this with a
row-wise `addRows` call. `passModel(lp)` loads it. Check each API call's status.

An equality uses equal row bounds; `G*x<=h` uses row bounds `[-inf,h]`.
Two-sided rows and variable bounds stay native. Use `highspy.kHighsInf` for absent
bounds. Binary variables require **both** integer type and `[0,1]` bounds.
Continuous variables remain `HighsVarType.kContinuous`; preserve all original
integer/semi-continuous types if the selected API supports them. Do not round a
continuous solution and describe it as a MILP solve.

For continuous QP use a `HighsModel` with `lp_` and `hessian_`. The native Hessian
is triangular column-wise (`HessianFormat.kTriangular`, lower triangle); objective
is `0.5*x'Qx+c'x+offset`. Verify PSD, triangle conventions, and coefficients for
the installed version; conic constraints do not become linear rows automatically.

`changeColCost`, `changeColsCost`, `changeColBounds`, `changeRowBounds`, and
`changeCoeff` update selected data; objective constants and integrality changes
need their corresponding APIs or rebuilding. Check returned statuses and keep
application data synchronized. Model dimensions or structural changes can require
reassembly. LP basis reuse differs from a MIP incumbent warm start.

Call `run()`, then inspect `getModelStatus()`, `getSolution()`, and `getInfo()`.
`HighsStatus.kOk` is API success, not a proof of optimality. Require a valid primal
solution before reading `col_value`; `HighsModelStatus.kOptimal` supports an
optimality conclusion under tolerances. A time/node limit can still have a useful
incumbent. Report incumbent objective, `mip_dual_bound`, and `mip_gap` when
available, preserving original objective direction and offsets. Keep a bound
separate from an incumbent. Check original bounds, rows, and integer residuals.

Requested continuous duals use row marginals and reduced costs with HiGHS's
objective/row conventions; derive the original signs. A MILP result does not
provide continuous KKT duals for the original discrete problem.
See the [binary covering example](../assets/highs_milp.py).
