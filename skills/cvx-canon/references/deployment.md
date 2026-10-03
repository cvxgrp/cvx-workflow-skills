# Framework, hardware, and workload routing

Resolve only choices that affect the implementation: framework/language, available
CPU/CUDA backend, precision and accuracy, single/repeated/batched problems,
shared shapes/cones/sparsity, and gradients needed with respect to which inputs.
Keep the existing framework when its supported solver path meets the problem.

| Workload | Starting path and check |
|---|---|
| NumPy/SciPy convex conic, high accuracy | Moreau core CPU or an explicitly available CUDA build |
| PyTorch/JAX convex layer, batching or solution gradients | Moreau framework API; read [framework details](moreau-frameworks.md) |
| Modest accuracy or specialized convex cones | SCS; check its installed cone/linear-system build and transfers |
| Integer linear constraints/objective | HiGHS; CPU solve and incumbent/gap handling, no solution-autograd promise |
| CasADi/Pyomo continuous smooth NLP | IPOPT through that framework; read [IPOPT frontends](ipopt-frameworks.md) |
| Bare continuous smooth NLP callbacks | cyipopt; sparse derivatives and domain-safe initialization |

Framework and solver devices are separate facts. PyTorch CUDA availability alone
does not establish an installed Moreau CUDA extension. JAX on TPU or PyTorch on
MPS does not establish a native solver for that accelerator. Check Moreau's
`available_devices()` and framework devices. If host fallback is necessary,
expose the transfer and its cost; do not silently detach differentiable data.
IPOPT's CasADi/Pyomo paths are ordinarily CPU paths; GPU input tensors do not make
IPOPT GPU-native or give its solution map an autograd rule.

For Moreau 0.4.1 use float64 data. Enable JAX x64 at application initialization
before constructing arrays, explicitly in the delivered application. Confirm the
actual tensor dtype. Do not promise float32/low-precision support from framework
support alone. Ask about an incompatible precision requirement or identify a
supported alternative.

Batch only problems sharing dimensions, cone definitions, and declared sparsity;
partition other structures or construct separate solvers. State which matrices
are shared and which values vary per member. Budget batch memory, setup, transfer,
forward solve, and backward solve separately. Batching improves throughput only
when measured on the user's workload; it may not improve single-instance latency.
Recover and validate every member, including failures within an otherwise valid
batch. Conic packing must match the installed device backend, especially for
mixed PSD/exponential/power cones.

Preserve framework operations in parameter-to-data assembly and primal recovery
when gradients are requested. Sparse indices, cone sizes, integer decisions, and
branching on structure are not differentiable numeric parameters. Rebuilding after
a structure change is a separate operation. Preserve objective offsets for losses
and parameter gradients even though offsets do not change the optimizer.

Exact canonicalization does not establish differentiability. Active-set changes,
nonunique solutions, and ill-conditioned KKT systems can invalidate ordinary
solution derivatives. Check gradients at smooth, well-conditioned points first;
handle failed solves before using gradients. Do not invent straight-through rules
or add regularization without labeling the changed forward problem or gradient.
