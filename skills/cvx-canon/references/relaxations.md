# Small relaxation corpus

Choose a relaxation to answer a requested bound/tractable-approximation task.
State original assumptions, enlarged set, objective relationship, and recovery.
For minimization an outer relaxation supplies a theoretical lower bound; for
maximization it supplies an upper bound. A numerically computed **primal** relaxed
objective is not automatically a certified bound on the original optimum: use a
valid solver dual bound/certificate when certification is required, or label it
an estimated relaxation optimum. A recovered original-feasible point gives the
opposite bound. Keep estimates, certified bounds, and candidates distinct.

## Integrality relaxation

Replace integer membership with its continuous domain, retaining original bounds,
rows, and objective. For binaries retain `[0,1]`; dropping the bounds too creates
an unnecessarily weak relaxation. Use HiGHS for the LP/continuous convex QP or a
conic solver for a supported convex relaxation. Rounding is a candidate heuristic;
check original constraints, and repair with an appropriate original model when
requested. Do not call a continuous NLP relaxation convex without checking it.

## Bounded bilinear McCormick envelopes

For `w=x*y`, with finite `lx<=x<=ux`, `ly<=y<=uy`, replace equality with:

```
w >= lx*y + ly*x - lx*ly
w >= ux*y + uy*x - ux*uy
w <= ux*y + ly*x - ux*ly
w <= lx*y + uy*x - lx*uy
```

These linear inequalities are the convex hull of a single product's graph over
the box. Multiple coupled products generally yield a relaxation, not an exact
model. Bound tightening can help; do not invent finite bounds for unbounded data.
They are exact for binary-times-bounded-continuous products when the binary
variable retains integrality. A changed bound changes every affected envelope
coefficient and constant. Recover `x,y`, then evaluate original products rather
than trusting relaxed `w` values.

## Shor SDP for quadratic problems

For quadratics `x.T@Qi@x + ai.T@x + bi`, introduce `X` for `x*x.T` and
`Y=[[1,x.T],[x,X]]`. Replace each quadratic with `trace(Qi@X)+ai.T@x+bi`,
retain original affine/bound restrictions, and impose `Y PSD`. Dropping the
rank-one condition yields an SDP relaxation even for indefinite `Qi`.
The PSD matrix is affine in the native coordinates; use the backend's svec
packing for every coefficient, including objective trace terms. Preserve
symmetry so off-diagonal coefficients are counted correctly. Add justified
bound/product inequalities when they materially improve tightness.

For `x in {0,1}^n`, add `diag(X)=x` and `[0,1]` bounds; for spins `z in {-1,1}^n`,
use `Z PSD, diag(Z)=1` and lift `z*z.T`. The [binary quadratic example](../assets/binary_sdp.py)
implements the latter minimization and deterministic hyperplane rounding. A
rounded spin vector is feasible for the unconstrained binary quadratic problem;
with additional combinatorial constraints it needs an independent feasibility
check/repair. Rank-one recovery can establish exactness within tolerances;
an optimum match on one instance cannot establish universal tightness.

For a general QCQP, the first-moment `x` or samples from `X-x*x.T` are candidates,
not guaranteed feasible solutions. Numerical symmetrization/PSD projection used
for sampling changes a recovery heuristic, not the relaxation's optimum certificate.

## SOCP weakening of a lifted PSD constraint

For an affine symmetric matrix `Y`, full PSD implies all diagonal entries are
nonnegative and each 2x2 principal minor is PSD. Replace full PSD by these SOCs:
`||(2*Yij, Yii-Yjj)||₂ <= Yii+Yjj` for every `i<j`, retaining diagonals.
This is an outer relaxation; pairwise conditions generally do not imply full PSD
in dimension three or above. It can reduce per-cone projection/factorization costs
but creates quadratically many blocks, so select it for a reason and measure.
When weakening a Shor lift keep `Y00=1`, affine restrictions, and trace objectives.
Use Moreau or SCS with ordinary SOCs. Do not claim that substituting a diagonally
dominant **inner** PSD approximation supplies the same outer bound direction.

The distinction from [CCP](ccp.md) matters: a relaxation targets bounds; CCP
targets local candidates through iterated convex subproblems. They can compose
(a relaxation can suggest an initialization) without transferring guarantees.
