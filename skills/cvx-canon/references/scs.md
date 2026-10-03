# SCS native conic interface

Use for appropriate large convex workloads, modest accuracy targets, or a
specific cone supported by the installed build. ADMM/operator splitting does
not imply SCS is faster on every instance or incapable of high accuracy.

API basis: SCS 3.3.1 Python.
[Python API](https://www.cvxgrp.org/scs/api/python.html),
[cones](https://www.cvxgrp.org/scs/api/cones.html), and
[statuses](https://www.cvxgrp.org/scs/api/exit_flags.html).

`scs.SCS({"P":P,"A":A,"b":b,"c":c},cone,...)` solves the quadratic
conic form `min 0.5*x'Px+c'x`, `Ax+s=b`. Matrices are CSC and `P` stores its
**upper triangle**. Vectors are one-dimensional. Do not reuse Moreau's full-P
storage or PSD row order without conversion. Constants stay outside the solver.

Cone rows follow zero `z`, nonnegative `l`, box if used, SOC `q`, real PSD `s`,
complex PSD `cs`, primal exponential `ep`, dual exponential `ed`, and power `p`.
PSD dimensions are matrix sizes, SOC dimensions are vector sizes, and exponential
counts count triples. Positive `p` entries represent primal power cones, negative
entries dual power cones; check the dual scaling rather than merely flipping
an inequality. Consult cone docs for ordering any additional spectral blocks.

Real PSD packing is **lower triangle, column-major**, with `sqrt(2)` on
off-diagonals: `[X00,sqrt(2)*X10,sqrt(2)*X20,X11,sqrt(2)*X21,X22]` in dimension three.
Apply it to both affine matrix coefficients and constant terms. Use
[the helper](../scripts/cone_layout.py) with backend `scs`; invert this same
packing for matrix-valued primal or requested dual results. Complex PSD uses
a different real/imaginary packing, documented separately by SCS.

Variable bounds normally become nonnegative slack rows. A box cone constrains
`[t;s]` with `t*lower<=s<=t*upper`; fixed scalar bounds require fixing `t=1`.
Generalized power cones can be decomposed into ordinary power cones with exact
weight ratios. Do not round exponents to obtain an approximate SOC decomposition.

SCS's experimental spectral cones include log-determinant, nuclear norm,
l1 norm, and sums of largest eigenvalues. They require explicit spectral/LAPACK
build support. Confirm keys, packing, and availability for that build before
using them; otherwise use a justified exact standard-cone representation when
available or report the limitation. Do not silently substitute a different set.

`solver.update(b=new_b,c=new_c)` reuses the workspace for new RHS/cost vectors.
Changes to `A`, `P`, or cone structure require a new workspace. `solve(warm_start=True)`
can reuse an iterate; warm starts are not data updates. Set `eps_abs`, `eps_rel`,
and iteration/time limits according to the requested accuracy and scale.

Results contain `x,s,y,info`. Check `info["status_val"]`: 1 is solved, 2 is solved
inaccurate; neither an infeasibility certificate nor an iteration failure is an
optimal original-variable result. Evaluate original residuals before accepting
an inaccurate result. Expose requested duals through `y` with the original row
mapping and PSD unpacking. See [SOCP/update](../assets/native_socp.py) and
[SDP relaxation](../assets/binary_sdp.py).
