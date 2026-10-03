# Moreau in PyTorch and JAX

Use for requested tensor-native convex layers, batched solves, and gradients.
Assembly conventions remain those in [Moreau core](moreau.md): full symmetric P,
CSR structure, native cone row order, and parameter-dependent recovery. API basis:
Moreau 0.4.1. Consult the installed build and official
[PyTorch guide](https://moreau.so/guide/pytorch-integration.html),
[JAX guide](https://moreau.so/guide/jax-integration.html), and
[device guide](https://moreau.so/guide/device-selection.html) when adapting.

## PyTorch

Construct `moreau.torch.Solver(n,m,P_row_offsets,P_col_indices,A_row_offsets,
A_col_indices,cones,settings=...)` outside the training loop. CSR indices are
integer tensors; numerical values are float64 tensors on the chosen device.
Choose `moreau.Settings(solver="ipm",device="cpu" or "cuda",batch_size=B)`
after checking availability. The framework wrapper enables differentiation.

Call `solver.solve(P_values,A_values,q,b)` on each forward pass. Unlike the core
compiled API, this PyTorch method takes all four data arguments; it caches matrix
setup internally. Values may be `(nnz,)` or `(B,nnz)`; q/b are `(n,)/(m,)` or
`(B,n)/(B,m)`. Check actual supported broadcasting and batch status behavior.
Backpropagate a scalar loss built from `solution.x` using normal autograd.
Construct P/A/q/b using tensor operations on the original parameters; converting
them to NumPy, creating fresh tensors from them, or detaching them breaks that
path. Diagnostic detaching after the solve is separate from returned primal data.

`solver.info.status` is a status or list of statuses. Check every member against
`moreau.SolverStatus.Solved` before accepting the layer output at full accuracy.
Check original residuals and reject invalid outputs before computing a training
loss. Solver instances are not thread-safe; use distinct instances for concurrent
workers. A warm start is initialization, with no gradient through its values.

## JAX

Enable x64 explicitly at application startup. Construct `moreau.jax.Solver` with
the same CSR metadata/cones/settings outside transformed functions. Use
`solver.solve(P_values,A_values,q,b)`. For genuinely fixed matrices the two-step
`setup(P_values,A_values); solve(q,b)` is available, but pass all four arguments
inside differentiated functions when matrix values depend on traced parameters.
Do not mutate cached setup with a tracer that will escape its transformation.

The solution is a pytree with `.x`; use `jax.grad` on a scalar loss and `jax.jit`
on the enclosing function. **CPU 0.4.1 has a shared-matrix backward shape issue**:
a direct batch with rank-one shared P/A can solve forward but fail in `grad`.
Explicitly `jnp.broadcast_to` P/A values to `(B,nnz)` within the differentiated
wrapper (and broadcast any shared q/b to batch shapes). JAX then reduces gradients
back to shared inputs. Keep this workaround version-specific and verify it.
Batch-shaped data can use the native batch path;
`jax.vmap` is also supported. Test the chosen composition, not just eager forward
execution. `solver.info` is mutable last-call metadata: **return its status from
inside the same wrapper that calls solve**, so JIT/vmap transform that metadata
along with the primal output. Inspect these returned statuses outside the trace;
do not use Python `int`, `bool`, or exceptions on traced statuses. Reading the
last `solver.info` outside a mapped function does not give per-member results.
Use the returned status plus original residuals to gate downstream use (or a
supported JAX check mechanism), not a fabricated primal on failure.

## Gradient contract

Gradients are with respect to numerical P/A/q/b entries. Include the chain rule
through original-data assembly, symmetric P entries, scaled PSD coordinates, and
original-variable recovery. For shared inputs in a batch, the loss's gradient
must accumulate contributions from all members. Check this explicitly rather
than assuming a broadcasting implementation does it correctly.

Check directional finite differences for P, A, q, b and original parameters at
points away from active-set changes; include both active and inactive constraints.
Check batched against separate solves/gradients, and sequential calls against
fresh instances. A successful forward solve alone does not qualify differentiation.

`IPMSettings(diff_method="exact")` requests the ordinary implicit derivative.
Moreau also offers experimental `diff_method="smoothed"` with
`diff_smoothing_mu`. This changes the backward rule via a nearby central-path
point; it does not make it the derivative of the exact forward optimizer. Label
that surrogate gradient and check the installed cone support (the guide lists
zero/nonnegative/SOC support, not all cones). Added forward regularization changes
the optimization problem separately. See
[smoothed differentiation](https://moreau.so/guide/smoothed-differentiation.html).

The [small layer examples](../assets/moreau_layers.py) cover a native batch and
shared matrix values. They provide a CPU starting point; CUDA throughput and all
cone derivatives require separate checks.
