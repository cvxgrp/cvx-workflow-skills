# Worked CVXPY recipes

Match the mathematical structure and preserve the user's domains, coefficients,
and axes. Examples do not choose missing business requirements. `build(data)`
is a convenient example interface, not a required user artifact. Check solver
status before reading values and validate finite data at the input boundary.

## Production with sparse requirements

Choose output at minimum cost, meeting every requirement while respecting
product capacities: min c@x, A@x >= demand, 0 <= x <= capacity. Rows of A are
requirements, columns are products. Requirements are floors; capacities are
caps. Preserve sparse A and construct vector constraints.

```python
import cvxpy as cp
import numpy as np
from scipy import sparse

def build(data):
    A = data["A"]
    A = A.astype(float) if sparse.issparse(A) else np.asarray(A, dtype=float)
    c = np.asarray(data["c"], dtype=float)
    demand = np.asarray(data["demand"], dtype=float)
    capacity = np.asarray(data["capacity"], dtype=float)
    if A.shape != (demand.size, c.size) or capacity.shape != c.shape:
        raise ValueError("Requirement/product shapes do not agree")
    x = cp.Variable(c.size, bounds=[np.zeros(c.size), capacity], name="x")
    return cp.Problem(cp.Minimize(c @ x), [A @ x >= demand]), {"x": x}
```

Original checks: x>=0, x-capacity <= 0, demand-A@x <= 0, and cost c@x. Use
explicit bounds if their individual duals are requested. Lowering demand or
enlarging capacity changes an infeasible problem instead of repairing its code.

## Mean-loss lasso

Fit observations with mean squared loss divided by two plus lam times the L1
coefficient penalty. With m observations, the sum_squares coefficient is 1/(2*m).
Changing this coefficient while retaining lam changes the tradeoff.

```python
import cvxpy as cp
import numpy as np
from scipy import sparse

def build(data):
    A = data["A"]
    A = A.astype(float) if sparse.issparse(A) else np.asarray(A, dtype=float)
    b = np.asarray(data["b"], dtype=float)
    lam = float(data["lam"])
    if A.ndim != 2 or A.shape[0] == 0 or b.shape != (A.shape[0],):
        raise ValueError("Rows of A must match the observation vector")
    if not np.isfinite(lam) or lam < 0:
        raise ValueError("lam must be finite and nonnegative")
    x = cp.Variable(A.shape[1], name="x")
    objective = cp.sum_squares(A @ x - b) / (2 * A.shape[0]) + lam * cp.norm1(x)
    return cp.Problem(cp.Minimize(objective)), {"x": x}
```

Original check: sum((A@x-b)**2)/(2*m) + lam*sum(abs(x)). Include lam=0 and
changes in the observation count. A matching optimizer alone does not verify
the loss units or coefficient. Retain sparse residual structure when useful.

## Transportation axes

Ship all supply and meet all demand exactly at minimum cost. Rows are suppliers,
columns are customers. If unused supply is allowed, that requires an inequality
and differs from this exact-conservation model.

```python
import cvxpy as cp
import numpy as np

def build(data):
    cost = np.asarray(data["cost"], dtype=float)
    supply = np.asarray(data["supply"], dtype=float)
    demand = np.asarray(data["demand"], dtype=float)
    if cost.shape != (supply.size, demand.size):
        raise ValueError("Cost rows/columns must match supply/demand")
    x = cp.Variable(cost.shape, nonneg=True, name="x")
    constraints = [cp.sum(x, axis=1) == supply, cp.sum(x, axis=0) == demand]
    return cp.Problem(cp.Minimize(cp.sum(cp.multiply(cost, x))), constraints), {"x": x}
```

Original checks: nonnegative supplier-by-customer x, row sums equal supply,
column sums equal demand, and sum(cost*x) equals the objective. Test rectangular
instances to expose axis swaps. Unequal total supply/demand is infeasible here.

## A quadratic perspective

Choose nonnegative mixture weights summing to one and a positive scale t;
penalize squared fitting error divided by t plus weight*t. Use quad_over_lin
and retain the user's positive t_min. Elementwise ratios or a fixed t change it.

```python
import cvxpy as cp
import numpy as np

def build(data):
    A = np.asarray(data["A"], dtype=float)
    b = np.asarray(data["b"], dtype=float)
    t_min, weight = float(data["t_min"]), float(data["weight"])
    if not np.isfinite(t_min) or not np.isfinite(weight) or min(t_min, weight) <= 0:
        raise ValueError("This recipe requires positive t_min and weight")
    x = cp.Variable(A.shape[1], nonneg=True, name="x")
    t = cp.Variable(name="t")
    constraints = [cp.sum(x) == 1, t >= t_min]
    objective = cp.quad_over_lin(A @ x - b, t) + weight * t
    return cp.Problem(cp.Minimize(objective), constraints), {"x": x, "t": t}
```

Original checks: x>=0, sum(x)=1, t>=t_min, and sum((A@x-b)**2)/t + weight*t.
The identity holds for t>0. Allowing t=0 requires a closure argument; do not add
an arbitrary epsilon merely to reuse this recipe. Sparse A can be retained as
in the production/lasso recipes.

## Repeated ridge solves

The design matrix and observations stay fixed while the caller varies a
nonnegative regularization coefficient. Construct the problem once; change
the named Parameter instead of reconstructing the expressions.

```python
import cvxpy as cp
import numpy as np
from scipy import sparse

def build(data):
    A = data["A"]
    A = A.astype(float) if sparse.issparse(A) else np.asarray(A, dtype=float)
    b = np.asarray(data["b"], dtype=float)
    x = cp.Variable(A.shape[1], name="x")
    lam = cp.Parameter(nonneg=True, name="lam", value=data["lam"])
    objective = 0.5 * cp.sum_squares(A @ x - b) + lam * cp.sum_squares(x)
    problem = cp.Problem(cp.Minimize(objective))
    assert problem.is_dcp(dpp=True)
    return problem, {"x": x, "lam": lam}
```

Build once, assign `values["lam"].value` for each update, solve, and check the
original objective using the current coefficient. Negative assignments are
rejected by the Parameter. Include zero in checks. DPP caching does not promise
factorization reuse or a universal speedup; profile the actual solver path.
