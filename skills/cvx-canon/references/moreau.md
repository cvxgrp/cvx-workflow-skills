# Moreau native conic interface

Default convex backend. Select `moreau.Settings(solver="ipm")` explicitly:
`solver="auto"` can choose an active-set method for small QPs. Select device
deliberately; the examples use CPU so that correctness does not depend on CUDA.

API basis: Moreau 0.4.1 Python core; consult the installed version before adapting.
[Core API](https://moreau.so/api/core.html),
[PSD conventions](https://moreau.so/guide/psd-cones.html), and
[batching](https://moreau.so/guide/batching.html) are authoritative for changes.

## Assembly

`moreau.Solver(P,q,A,b,cones,settings=...)` solves `min 0.5*x'Px+q'x`
with `Ax+s=b`, slack cone constraints, and optional direct cones on `x`.
Supply **full symmetric P**, not just an upper triangle. Retain the objective
constant separately. Sparse matrices are supported; compiled structure uses CSR.

Verified **CPU 0.4.1** slack rows follow this order:

1. `num_zero_cones`: scalar equality rows.
2. `num_nonneg_cones`: scalar inequality rows.
3. `so_cone_dims`: SOC block lengths, including the leading scalar.
4. `psd_dims`: symmetric matrix dimensions, consuming `k*(k+1)//2` rows each.
5. `num_exp_cones`: triples `(u,v,w)` with `v*exp(u/v)<=w` and closed boundary.
6. `power_alphas`: primal power-cone triples.
7. `gen_power_cone_params`: `(alphas,dim2)` blocks with positive normalized weights.

The published guide places PSD last, but CPU 0.4.1's `cones_to_cpu` conversion
places it before exponential/power cones. An analytic mixed-cone probe confirms
the CPU order above. Using the guide's order can silently encode another problem.
For another release/device, check its backend conversion and a small mixed-cone
case with known affine slacks before using a fixed row order. GPU order is not
established by these CPU checks.

Real PSD packing is **upper triangle, column-major**, multiplying off-diagonals
by `sqrt(2)`: for dimension three `[X00,sqrt(2)*X01,X11,sqrt(2)*X02,sqrt(2)*X12,X22]`.
Use [the packing helper](../scripts/cone_layout.py) with backend `moreau` for
assembly and recovery. SCS's order is different beyond dimension two.

`Cones(dir_cones=[moreau.DirectConeSpec(kind="nonneg",indices=[...]), ...])`
can constrain ordered subvectors of `x` without slack rows. Direct index sets
must be disjoint. Direct PSD coordinates are already scaled svec values; use
the corresponding matrix recovery. Use slack rows for overlapping sets or general
affine cone expressions. Direct cones are an optimization, not a license to drop
affine offsets or forget a variable's other restrictions.

## Reuse, batches, and results

Use `CompiledSolver(n,m,P_row_offsets,P_col_indices,A_row_offsets,A_col_indices,
cones,settings)` for repeated/batched problems with shared sparsity and cone
structure. Sort/canonicalize CSR once, retaining deliberate structural zeros
where later updates need them. `setup(P_values,A_values)` sets numeric matrix
entries; `solve(qs,bs)` takes arrays of shape `(batch,n)` and `(batch,m)`.
With fixed matrices, repeat `solve` for new cost/RHS values. With changed matrix
values, repeat `setup`; changed structure requires reconstruction. A single
repeated problem can use batch size one. Do not invent a `Solver.update` method.

Read `solution.x` and `solver.info.status` for a single solve; compiled output
has batched arrays and `solver.info.status` per member. Compare against
`moreau.SolverStatus.Solved`, not an assumed string. `AlmostSolved` uses reduced
tolerances; it is not equivalent to requested high accuracy. Infeasibility and
limit/error statuses must not produce an unconditional optimal solution result.
Use `solution.to_warm_start()` only as initialization for correctly updated data.

Requested duals are slack `solution.z` and, for direct constraints, `solution.z_x`.
Keep their row/index maps distinct. Map back through signs/scales explicitly.
For GPU/batches validate each member and measure transfer/setup costs; CPU
checks do not establish GPU accuracy, throughput, or differentiation correctness.
For PyTorch/JAX use the [framework APIs](moreau-frameworks.md), preserving
the assembly and recovery maps. Differentiation is a separate contract requiring
checked derivatives; a forward solve does not establish it.

See [native SOCP and compiled reuse](../assets/native_socp.py) and
[binary quadratic SDP](../assets/binary_sdp.py).
