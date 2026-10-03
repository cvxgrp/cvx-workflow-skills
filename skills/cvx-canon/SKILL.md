---
name: cvx-canon
description: Generate solver-native optimization code from natural-language requirements, mathematical formulations, or CVXPY models. Use for direct Moreau, SCS, HiGHS, or IPOPT assembly, parameter updates, and original-variable recovery, including PyTorch/JAX batching and differentiation, CasADi/Pyomo NLPs, and requested convex relaxations or convex-concave procedures. Not for a CVXPY implementation or custom solver kernels.
license: Apache-2.0
---

# Problems to solver-native code

Deliver runnable code against an existing solver's public API, including data
assembly, updates when needed, status handling, and original-variable recovery.
Default to Python; preserve a requested framework. CasADi and Pyomo are supported
IPOPT frontends alongside native callbacks. Adapt to another language/interface after
checking that target's API. Installed resources are self-contained; another
skill or a repository checkout is not required.

## Interpret and choose the path

Identify original variables and shapes, fixed data, changing parameters, domains,
integrality, objective direction and constants, and every constraint. Inspect a
supplied CVXPY model as mathematical input, including variable attributes and
data-dependent branches. Resolve missing choices that change the problem; do not
invent data. Read [formulation](references/formulation.md) for the assembly and
recovery contract.

Identify the software framework, CPU/accelerator and available solver build,
precision, batch shapes/shared structure, and whether gradients through the solution
are required. Read [deployment](references/deployment.md) for these workloads.

Honor a requested backend when it supports the formulation. Otherwise route by
the actual problem and accuracy/deployment requirements:

| Path | Read |
|---|---|
| Continuous convex quadratic/conic; default high-accuracy IPM | [Moreau](references/moreau.md) |
| Large convex models, modest accuracy, or a specific supported specialized cone | [SCS](references/scs.md) |
| MILP; also LP or continuous convex QP when appropriate | [HiGHS](references/highs.md) |
| Smooth continuous nonlinear model, including nonconvex local optimization | [IPOPT](references/ipopt.md) |

Moreau is the default, explicitly selecting IPM. These roles do not promise a
speed ranking. Check the installed version, device, precision, and cone/build
capabilities rather than inferring them from a solver name. HiGHS does not cover
general integer nonlinear, mixed-integer quadratic, or mixed-integer conic models.
For PyTorch/JAX layers, read [Moreau frameworks](references/moreau-frameworks.md);
for CasADi/Pyomo, read [IPOPT frameworks](references/ipopt-frameworks.md).
IPOPT does not enforce integrality. Explain an unsupported combination and offer
a supported exact reformulation or a clearly identified alternative.

Distinguish **formulation** (exact, relaxation, or surrogate, with assumptions)
from **solution guarantee** (convex optimum to tolerances, integer incumbent/gap,
local nonlinear result, or heuristic candidate). An exact nonconvex formulation
does not imply a global solution. Do not silently replace the original problem
with a relaxation or local procedure; follow the user's requested guarantee and
disclose a consequential method choice.

## Derive and implement

For conic paths, read only the relevant [exact patterns](references/conic-patterns.md)
and the selected backend's conventions. Use separate representations for conic
programs, HiGHS rows/bounds/integrality, and IPOPT functions/derivatives. No universal
cone IR is required.

- Assemble from the user's original data and derived identities. Do not call
  CVXPY `get_problem_data`, export its solver data, or use reduction-chain
  inversion. CVXPY may be an independent development reference, never a runtime
  dependency of the native application.
- Preserve sparse structure. Allocate variable slices and row blocks in code;
  retain a map back to original names/shapes. Check objective factors, offsets,
  cone order, PSD packing, and affine signs explicitly.
- Separate reusable structure from numeric values. State which parameters can
  change in place and which require setup or reconstruction. Recheck assumptions
  after updates; warm starts do not replace updating problem data.
- Prefer supported native quadratic objectives, bounds, and direct cones when
  they improve the requested workload. Do not assume smaller cone dimensions
  establish better performance.
- Recover primal variables on every supported solve path. Retrieve/map duals
  only when requested; then verify signs, scales, and original constraint meaning.
  Solver-internal multipliers needed by a Hessian callback remain necessary.

Before constructing an IPOPT model, read [nonlinear formulations](references/nonlinear-formulations.md)
for smooth exact lifts, domains, scaling, and initialization. Preserve original
semantics when improving the numerical formulation.

For an appropriate difference-of-convex local method, read
[CCP](references/ccp.md). For a requested bound or relaxation, read
[relaxations](references/relaxations.md): integrality, bounded bilinear envelopes,
Shor/binary quadratic SDP, and selected SOCP relaxations. Both paths still emit
native solver code. They orchestrate existing solvers, not custom solver kernels.

## Verify and deliver

Read [verification](references/verification.md) for the selected path. Audit
semantics, transformation identities, and numerical behavior separately. When
execution is available, check original-expression objectives/residuals after
recovery, parameter changes, and relevant failure cases. For IPOPT check
derivatives and original feasibility; for differentiable layers check gradients
and each batch member; for CCP check original nonconvex constraints; for relaxations keep
bounds separate from recovered feasible candidates. A solve or matching optimum
alone does not prove equivalence.

Use an existing environment; do not silently install packages. Examples are
adaptable starting points, not a universal API or a performance qualification.
The optional [PSD packing helper](scripts/cone_layout.py) prevents triangle/order
mistakes. Report checks that were actually run and material checks unavailable.

Return source/code files and concise usage notes, the formulation/method labels,
parameter update limits, and any consequential assumptions. Return solver status
and original-variable values only when meaningful; distinguish a feasible
candidate from a certified optimum. Do not fabricate timings, solutions, or
guarantees. JSON wrappers and extensive mathematical exposition are not default
deliverables.
