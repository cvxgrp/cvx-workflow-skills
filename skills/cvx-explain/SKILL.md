---
name: cvx-explain
description: Describe a supplied CVXPY model in Markdown or LaTeX, identifying decision variables, changing parameters, fixed data, the objective, and every constraint. Use to document what existing CVXPY code or a Problem represents. Not for generating or repairing code, solving the problem, or deriving duals.
license: Apache-2.0
---

# CVXPY code to a mathematical description

Describe the supplied model as written. Default to Markdown with mathematical
notation; use standalone LaTeX when requested. Keep the description proportional
to the code. This task does not require solving or changing the model. Read
[notation](references/notation.md) before writing math: standard-form layout,
preamble-free macros, and marimo notebook specifics.

1. Identify each decision variable's name, shape, and domain, including implicit
   attributes such as nonnegativity, bounds, symmetry, or integrality. Distinguish
   original variables from auxiliary variables when the source identifies them.
2. Identify `cp.Parameter` objects separately from fixed input arrays/scalars.
   Give shapes, sign/domain attributes, supplied values when relevant, and which
   quantities callers can update. Fixed data passed into a builder does not
   become a CVXPY Parameter merely because callers could rebuild with new data.
3. Write the objective with its actual minimize/maximize direction, coefficients,
   normalization, and constants. Translate atoms into their mathematical meaning.
4. List every explicit constraint and variable-domain restriction. Expand vector
   constraints using clear indices; preserve reduction axes, broadcasting, matrix
   products versus elementwise products, and boundary conventions.
5. State only meanings supported by source names, comments, or supplied context.
   Mark unknown dimensions or missing data definitions instead of inventing them.
   If only a runtime Problem is supplied, original data names and application
   meanings may be unavailable; use neutral labels or request the source.

Describe auxiliary/epigraph constraints literally unless an elimination is
requested and justified. Do not silently replace the code with an intended or
"corrected" formulation. Flag apparent inconsistencies briefly and separately.
For data-dependent construction branches, state the applicable conditions; ask
for missing inputs when they determine which model is built.
Do not claim convexity, DCP acceptance, feasibility, or optimality without the
corresponding evidence. Read the source before considering execution; describing
a model usually needs no execution. The optional [math checker](scripts/check_latex.py)
scans the written description, not the model. Return prose/math, without a JSON
wrapper unless the user explicitly requests one.
