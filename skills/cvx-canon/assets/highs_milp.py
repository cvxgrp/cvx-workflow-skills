"""Exact binary covering: min cost'x+offset, coverage'x>=demand."""

import numpy as np
from scipy import sparse


def solve_cover(cost, coverage, demand, offset=0.0, time_limit=None):
    import highspy

    cost, coverage = np.asarray(cost, dtype=float), np.asarray(coverage, dtype=float)
    if cost.ndim != 1 or not cost.size or coverage.shape != cost.shape:
        raise ValueError("cost and coverage must be same-length nonempty vectors")
    if not all(np.all(np.isfinite(v)) for v in (cost, coverage, demand, offset)):
        raise ValueError("Data must be finite")
    A = sparse.csc_matrix(coverage[None, :])
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = cost.size, 1
    lp.col_cost_, lp.col_lower_, lp.col_upper_ = cost, np.zeros(cost.size), np.ones(cost.size)
    lp.row_lower_, lp.row_upper_ = np.array([demand]), np.array([highspy.kHighsInf])
    lp.offset_ = float(offset)
    lp.integrality_ = [highspy.HighsVarType.kInteger] * cost.size
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = A.indptr, A.indices, A.data
    solver = highspy.Highs()

    def checked(status):
        if status != highspy.HighsStatus.kOk:
            raise RuntimeError(f"HiGHS API failed: {status}")

    checked(solver.setOptionValue("output_flag", False))
    if time_limit is not None:
        checked(solver.setOptionValue("time_limit", float(time_limit)))
    checked(solver.passModel(lp))
    run_status = solver.run()
    if run_status == highspy.HighsStatus.kError:
        raise RuntimeError("HiGHS run failed")
    status, solution, info = solver.getModelStatus(), solver.getSolution(), solver.getInfo()
    result = {"status":solver.modelStatusToString(status), "optimal":status == highspy.HighsModelStatus.kOptimal}
    if not solution.value_valid:
        return {**result, "x":None}
    x = np.asarray(solution.col_value)
    return {
        **result, "x":x, "objective":float(cost@x + offset),
        "dual_bound":float(info.mip_dual_bound), "gap":float(info.mip_gap),
        "violation":float(max(0.0, demand-coverage@x, -np.min(x), np.max(x)-1)),
        "integer_violation":float(np.max(np.abs(x-np.rint(x)))),
    }
