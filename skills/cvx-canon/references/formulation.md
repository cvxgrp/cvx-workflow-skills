# Assembly and recovery contract

Use the user's objective, quantifiers, units, and domains as the specification.
For supplied CVXPY code, include implicit bounds, symmetry, PSD, boolean/integer
attributes, indexing, reshape order, and all construction branches that apply.
Do not infer the intended model from a successful solve.

## Common bookkeeping

Keep a compact trace from original expressions to implemented rows, bounds,
cones, or callbacks. A few comments and named slices suffice for small models.
Record auxiliary variable meanings and their elimination/recovery identities.
Use a declared flattening order; a reshape must invert that same order.

For minimization of `0.5*x.T@H@x + a.T@x + d`, native quadratic solvers need
`P=H`, linear cost `a`, and separate offset `d` unless the API stores it.
For `||F*x-g||²`, use `P=2*F.T@F`, `q=-2*F.T@g`, `d=g.T@g`.
For maximization negate the entire objective, including its constant; undo the
sign on recovered objective values and bound directions. Avoid forming `F.T@F`
when it destroys useful sparsity or worsens conditioning; an epigraph or residual
variable formulation may be preferable. Do not clip negative eigenvalues to turn
an indefinite input into a convex one.

For `Ax+s=b`, an intended slack expression `s=F*x+g` requires `A=-F, b=g`.
Thus `G*x<=h` uses `A=G,b=h` and a nonnegative cone; `E*x=f` uses a zero cone.
Check this identity before assigning any cone. Conic row ordering and symmetric
matrix packing belong to the backend, not this common contract.

Conic original variables may be slices of the native vector or affine functions
of it. SDP variables must be unpacked using the same scaling/order used for
assembly. HiGHS columns map to original variables, including original integer
values. IPOPT callbacks must use a fixed original/auxiliary variable layout.
Do not return auxiliaries under an original variable's name.

## Updates and results

Document each changing datum's effects on matrices, vectors, offsets, bounds,
callbacks, and recovery. Updating only a linear cost is wrong if the same datum
also affects an objective constant or constraint. Structural changes include new
dimensions, sparsity positions, integrality, or cone types/parameters; honor the
backend's reconstruction requirements. Recheck PSD, finite bounds, or DC-domain
assumptions when parameter values change.

Keep formulation and solve conclusions independent:

| Formulation | Meaning |
|---|---|
| Exact, under named assumptions | Feasible original points lift and native feasible points recover appropriately; objective preserved |
| Relaxation | Feasible set enlarged or objective weakened in a justified bound direction; native feasibility need not imply original feasibility |
| Surrogate | A changed objective/constraint without a demonstrated bound or equivalence |

A CCP iteration uses an inner approximation to DC constraints, while the overall
method is a local heuristic for the original problem. Penalty slacks remove that
iteration's original-feasibility guarantee. An exact NLP sent to IPOPT remains a
local solve. MILP time limits can yield an incumbent without an optimality proof.

For requested duals derive a Lagrangian in the original conventions. Track row
negations, rescaling, objective sign flips, cone adjoints, and eliminated variables.
HiGHS row marginals and IPOPT bound multipliers are not interchangeable with
nonnegative cone multipliers. MILP generally has no original-problem dual vector
with the continuous KKT interpretation. State unsupported dual recovery rather
than returning unrelated native values.
