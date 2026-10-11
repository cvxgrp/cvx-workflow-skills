---
name: cvx-debug
description: Diagnose and repair supplied CVXPY code or formulations with modeling errors, DCP/DPP failures, incorrect results, infeasibility, or poor performance. Recommend suitable solvers using problem structure and evidence. Use for debugging existing models, not literal documentation, fresh code generation, symbolic dual derivation, or native/custom solver implementation.
license: Apache-2.0
---

# Diagnose an existing optimization model

Return evidence-backed findings and focused corrections, with checks performed
and remaining uncertainty. Keep this proportional to the reported symptom;
correct code may need no change. Literal descriptions belong to `cvx-explain`
and fresh CVXPY implementations to `cvx-model`; neither must be installed.

## Establish the issue

Read supplied source, formulation, data, and error/status evidence. Distinguish
the intended problem from what the code actually implements. Ask for missing
requirements only when they affect the diagnosis; code alone cannot establish
application intent. A runtime Problem may have lost original names and context.
Use the existing environment and supplied instance where practical. Report
unavailable evidence rather than inventing an error or timing.

Read only the references matching the symptom:

- Wrong formulation, unexpected results, infeasibility, or unboundedness:
  [modeling and statuses](references/modeling.md).
- Shape, atom, DCP, DPP, or quadratic-expression failure:
  [implementation](references/implementation.md); for quadratic terms read
  [quadratic representations](references/quadratics.md).
- Slow construction, compilation, repeated solves, or numerical convergence:
  [performance](references/performance.md).
- Solver choice or polyhedral feasibility structure:
  [solver routing](references/solver-routing.md).

Separate a demonstrated bug, a suspected issue needing evidence, and an optional
improvement. Cite the relevant expression, data, exception, or measurement and
explain its consequence. Do not turn every diagnosis into a full model rewrite
or an automatic benchmark across solvers.

## Correct and verify

Give or apply a minimal repair within the requested scope. Preserve the original
objective, domains, constraints, and interface unless a change is explicitly
requested. Label a proposed modeling change as such. An indefinite quadratic,
nonconvex equality, or unsupported cone is not repaired by dropping requirements,
asserting PSD, adding arbitrary bounds, or silently introducing a relaxation.

Verify three questions separately: does the code match the stated requirements;
is the replacement equivalent under its assumptions; and do numerical results
meet original-domain checks? DCP acceptance or solver success proves neither
of the first two. Reproduce the reported failure and check the repair when
execution is available, using meaningful original-expression/residual checks.
For a performance claim, compare at matched accuracy and state timing boundaries.

Diagnosis can cover expressions beyond continuous LP/QP/SOCP, including an affine
operator on a matrix variable, without promising a general implementation of
unsupported problem classes. Explain any scope obstruction. Solver-native code,
custom algorithms, and symbolic dual derivation are separate deliverables.

Return the issue and consequence first, then the correction and actual validation.
If the model is correct or evidence is insufficient, say so and identify a useful
next check. Do not claim certification, speedups, or solved problems without
the corresponding evidence.
