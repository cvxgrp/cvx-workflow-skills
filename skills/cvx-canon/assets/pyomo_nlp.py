"""Pyomo/IPOPT version of the CasADi double well with exact abs epigraph.

Pyomo itself does not install the ipopt executable. Params remain symbolic so
later updates change the written NLP. Solver files use the artifact directory.
"""
from pathlib import Path
import math


def build_model(tilt=0.1, lam=0.2, offset=0.0, x0=1.0):
    import pyomo.environ as pyo

    if not all(math.isfinite(v) for v in (tilt, lam, offset, x0)) or lam < 0 or abs(x0) > 2:
        raise ValueError("Finite data, lam >= 0, and -2 <= x0 <= 2 required")
    m = pyo.ConcreteModel()
    m.tilt = pyo.Param(initialize=tilt, mutable=True)
    m.lam = pyo.Param(initialize=lam, mutable=True, within=pyo.NonNegativeReals)
    m.offset = pyo.Param(initialize=offset, mutable=True)
    m.x = pyo.Var(bounds=(-2, 2), initialize=x0)
    m.t = pyo.Var(bounds=(0, None), initialize=abs(x0-.25)+.1)
    m.plus = pyo.Constraint(expr=m.t >= m.x-.25)
    m.minus = pyo.Constraint(expr=m.t >= -(m.x-.25))
    m.objective = pyo.Objective(expr=(m.x*m.x-1)**2 + m.tilt*m.x + m.lam*m.t + m.offset)
    return m


def solve_local(model, artifact_directory):
    import pyomo.environ as pyo
    from pyomo.common.tempfiles import TempfileManager
    from pyomo.opt import SolverStatus, TerminationCondition

    directory = Path(artifact_directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    if not all(math.isfinite(pyo.value(v)) for v in (model.tilt, model.lam, model.offset)):
        raise ValueError("Parameters must be finite")
    if pyo.value(model.lam) < 0:
        raise ValueError("Negative lam invalidates the exact epigraph")
    solver = pyo.SolverFactory("ipopt")
    if not solver.available(exception_flag=False):
        raise RuntimeError("Pyomo IPOPT executable is unavailable")
    solver.options.update(tol=1e-9, bound_relax_factor=0.0, print_level=0)
    # The solver pushes its own context; set the thread-local manager directory
    # for the call, then restore it even on failure.
    previous_directory = TempfileManager.tempdir
    TempfileManager.tempdir = str(directory)
    try:
        with TempfileManager:
            results = solver.solve(model, load_solutions=False)
    finally:
        TempfileManager.tempdir = previous_directory
    termination = results.solver.termination_condition
    accepted = termination in (TerminationCondition.optimal, TerminationCondition.locallyOptimal)
    if results.solver.status != SolverStatus.ok or not accepted or len(results.solution) == 0:
        return {"status": str(termination), "x": None, "guarantee": "no accepted local result"}
    model.solutions.load_from(results)
    x, t = pyo.value(model.x), pyo.value(model.t)
    if not all(math.isfinite(v) for v in (x, t)) or abs(x) > 2+1e-7 or t < abs(x-.25)-1e-7:
        raise RuntimeError("Original bounds or lifted constraints failed")
    objective = ((x*x-1)**2 + pyo.value(model.tilt)*x
                 + pyo.value(model.lam)*abs(x-.25) + pyo.value(model.offset))
    if abs(pyo.value(model.objective)-objective) > 1e-7*(1+abs(objective)):
        raise RuntimeError("Original and lifted objectives disagree")
    return {"status": str(termination), "x": x, "objective": objective,
            "guarantee": "local NLP candidate"}
