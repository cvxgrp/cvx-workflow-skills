---
name: cvx-model
description: Write reusable, efficient CVXPY code from natural-language descriptions of real continuous convex LP, QP, and SOCP problems. Use when the requested deliverable is a CVXPY implementation. Not for describing existing code, standalone proofs or dual analysis, solver-native code, or custom solver algorithms.
license: Apache-2.0
---

# Natural language to CVXPY code

The deliverable is runnable CVXPY code. Keep accompanying prose to necessary
assumptions, use instructions, and checks actually performed. Existing-code
descriptions belong to `cvx-explain`; neither skill requires the other installed.

## Translate the requirements

Identify decision variables and shapes, fixed data, changing parameters, units,
domains, objective direction and scaling, and every constraint. Preserve rows,
columns, inequality directions, quantifiers, and constants. Read
[formulation](references/formulation.md) when the description is ambiguous or
needs an exact reformulation, including a linear-fractional objective.

Ask a focused question if a missing choice changes the model, such as budget
equality versus cap or borrowing rules. Do not invent data or quietly choose a
different problem. Otherwise proceed with ordinary implementation choices.

## Construct the model

Read [CVXPY implementation](languages/cvxpy.md). Use a function accepting the
user's data and returning a `cp.Problem` and named original variables; expose
parameters when callers need updates. Adapt to a requested interface. Separate
construction from solving, unless the user explicitly wants a solve workflow.

- Default input checks to shapes and finite values. Add a domain check only if
  the request or representation requires it (such as PSD quadratic data).
  Do not reject loose bounds or screen feasibility unless requested. Preserve
  infeasible instances as models, and preserve sparse inputs.
- Vectorize expressions and reductions; use deliberate axes and reshape order.
- Use appropriate atoms: `sum_squares`, `norm`, `multiply`, `quad_form`, and
  `quad_over_lin` instead of opaque variable products or divisions.
- Retain original variables and objective factors. Use supported bound/sign
  attributes when appropriate; preserve explicit constraints when needed.
- For repeated solves, use named parameters and check DPP; read
  [parameters](references/parameters.md).

Read only the matching [worked recipe](references/recipes.md): sparse production,
mean-loss lasso, transportation, quadratic perspective, or repeated ridge.
Before using `geo_mean`, noninteger `power`, or `pnorm` with an exponent other
than 1, 2, or infinity, read [atoms](references/atoms.md). Weighted geometric
means must use its exactness pattern or [helper](scripts/exact_atoms.py) inside
the constructor, so every input is checked. Other compositions also use
[atoms](references/atoms.md) and [DCP rules](references/dcp.md).
Do not conceal indefinite data with `psd_wrap`,
clip values, drop requirements, or label a relaxation as exact.
If an atom can approximate coefficients/exponents, check its represented values
against the requested function before claiming equivalence; read
[atoms](references/atoms.md) for the applicable check. Disclose or reject an
unrequested approximation rather than silently changing the model.

If the requested problem is outside continuous convex LP/QP/SOCP support,
state the obstruction briefly. Do not replace it with a surrogate or turn the
answer into a solver implementation or a general mathematical analysis.

## Check and deliver the code

Audit code against the original objective, each constraint, domains, and shapes.
Check `problem.is_dcp()`; for promised parameter reuse also check
`problem.is_dcp(dpp=True)`. Include only justified input checks and useful comments
in the code. DCP acceptance alone does not verify the translation.

When execution is available and appropriate, first construct with supplied data.
The optional [construction checker](scripts/check_model.py) needs only `build`;
read its [usage and limits](references/verification.md). Correct reported errors
and rerun the check without weakening the original requirements. Report checks
not run when execution is unavailable. Check original residuals/objectives after
any solve. The optional
[verification helper](scripts/verify_model.py), [contract](references/verification.md),
and [ball example](assets/ball_projection.py) with [data](assets/ball_projection.json)
support this. They execute trusted Python and check supplied callbacks, not
semantic equivalence or independent optimality. Use an existing environment;
do not silently install dependencies.

Return Python source or code files, with a brief statement of any consequential
assumptions or unexecuted checks. Numerical examples are optional; do not invent
solutions, timings, or verified optima. Detailed LaTeX derivations and a JSON
envelope are not default deliverables.
