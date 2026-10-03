"""Moreau 0.4.1 tensor layers; import only the selected framework.

min .5*sum(weight*(x-target)**2), coefficient*x <= upper.
weight/coefficient are positive shared vectors; target/upper may be batched.
The constant .5*sum(weight*target**2) stays in the original loss, not native q.
CPU examples; explicitly verify an installed CUDA build before choosing CUDA.
"""


def torch_box(n, batch_size=1, device="cpu"):
    import moreau
    import torch
    from moreau.torch import Solver

    rows = torch.arange(n + 1, dtype=torch.int64)
    cols = torch.arange(n, dtype=torch.int64)
    return Solver(
        n=n, m=n, P_row_offsets=rows, P_col_indices=cols,
        A_row_offsets=rows, A_col_indices=cols,
        cones=moreau.Cones(num_nonneg_cones=n),
        settings=moreau.Settings(solver="ipm", device=device, batch_size=batch_size,
                                ipm_settings=moreau.IPMSettings(diff_method="exact")),
    )


def solve_torch_box(solver, target, weight, coefficient, upper):
    """Keep returned primal connected to autograd; reject invalid batch members."""
    import moreau
    import torch

    inputs = (target, weight, coefficient, upper)
    if any(t.dtype != torch.float64 for t in inputs):
        raise ValueError("Moreau inputs must be float64")
    if not all(bool(torch.isfinite(t).all()) for t in inputs):
        raise ValueError("Inputs must be finite")
    if not bool((weight > 0).all() & (coefficient > 0).all()):
        raise ValueError("weight and coefficient must be positive")
    solution = solver.solve(weight, coefficient, -weight * target, upper)
    statuses = solver.info.status
    if not isinstance(statuses, list):
        statuses = [statuses]
    if any(status != moreau.SolverStatus.Solved for status in statuses):
        raise RuntimeError(f"Unaccepted batch statuses: {statuses}")
    x = solution.x
    scale = 1 + torch.abs(upper)
    if not bool(torch.isfinite(x).all()) or bool(((coefficient*x-upper)/scale > 1e-7).any()):
        raise RuntimeError("Original bound check failed")
    return x


def jax_box(n, batch_size=1, device="cpu"):
    """Return solver and transformable solve function yielding (x, statuses).

    Configure jax_enable_x64 at application startup. Inputs must be finite float64,
    with positive shared weight/coefficient. Check returned statuses and original
    residuals before using the primal or its gradients; no Python guards in traces.
    """
    import moreau
    import jax
    import jax.numpy as jnp
    from moreau.jax import Solver

    if not jax.config.x64_enabled:
        raise ValueError("Enable jax_enable_x64 before constructing the layer")
    rows = jnp.arange(n + 1, dtype=jnp.int64)
    cols = jnp.arange(n, dtype=jnp.int64)
    solver = Solver(
        n=n, m=n, P_row_offsets=rows, P_col_indices=cols,
        A_row_offsets=rows, A_col_indices=cols,
        cones=moreau.Cones(num_nonneg_cones=n),
        settings=moreau.Settings(solver="ipm", device=device, batch_size=batch_size,
                                ipm_settings=moreau.IPMSettings(diff_method="exact")),
    )

    def solve(target, weight, coefficient, upper):
        # CPU 0.4.1 backward requires matrix-data shapes to match the native batch.
        # Explicit JAX broadcasting also sums gradients back to shared inputs.
        P_values = jnp.broadcast_to(weight, target.shape)
        A_values = jnp.broadcast_to(coefficient, target.shape)
        q = -weight * target
        b = jnp.broadcast_to(upper, target.shape)
        solution = solver.solve(P_values, A_values, q, b)
        # Capture metadata in the same trace so jit/vmap return each call's status.
        return solution.x, solver.info.status

    return solver, solve
