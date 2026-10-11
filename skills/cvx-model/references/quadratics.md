# Quadratic expressions: identify what varies

These patterns cover real-valued expressions. Preserve objective factors,
constants, dimensions, and domains. An equivalent expression can have different
compilation and solve costs; measure before claiming an improvement.

## Variable vector, fixed or parameterized PSD matrix

For x^T Q x with symmetric PSD data Q, prefer an available factor Q=R^T R:

```python
term = cp.sum_squares(R @ x)
```

Keep residuals such as `cp.sum_squares(A @ x - b)` in residual form; do not form
A^T A merely to use a quadratic-form atom. Sparse or rectangular factors can
preserve structure. A factor can also be a `cp.Parameter`; compute the factor
outside CVXPY and check `problem.is_dcp(dpp=True)` on the concrete problem.
Changing factors does not guarantee solver factorization reuse.

NumPy's Cholesky returns L with Q=L L^T: use R=L^T, not L. Cholesky requires
positive definiteness and can fail for valid singular PSD data. A known
rectangular factor handles that case. If deriving a factor spectrally, justify
the PSD tolerance, quantify reconstruction error, and preserve zero eigenvalues.
Do not silently clip genuinely negative eigenvalues or add a ridge term.
Include factorization cost and memory in any performance comparison.

`cp.quad_form(x, Q)` remains a valid option for suitable PSD data when a factor
would destroy useful structure or be disproportionately expensive. Distinguish
a numerical PSD-certification failure from an indefinite matrix using the data's
construction, factor, or appropriate numerical evidence. `psd_wrap` and
`assume_PSD=True` assert an assumption; they do not establish it. Never use them
to conceal indefinite or unverified data.

## Fixed vector, variable matrix

For fixed a and variable X, a^T X a is affine, regardless of whether X is PSD:

```python
# a has shape (n,), X has shape (n, n)
C = np.outer(a, a)
term = cp.trace(X @ C)
# Equivalent Frobenius contraction:
term = cp.sum(cp.multiply(C, X))
```

Here C is symmetric, so the elementwise contraction equals the trace expression.
For general fixed B, trace(B X) instead uses the contraction with B^T. Preserve
that transpose; not every coefficient matrix is symmetric. For many fixed
vectors, a sparse coefficient operator or contractions can avoid dense outer
products. Check dimensions and original expression values on supplied data.

Retain any requested symmetry/PSD domain of X. These affine expressions do not
require adding a PSD constraint. A model with a PSD matrix variable is outside
`cvx-model`'s LP/QP/SOCP scope unless an exact in-scope representation is justified;
`cvx-debug` can still diagnose its expression without expanding modeling scope.

If both x and Q are variables, neither replacement makes x^T Q x affine or
generally convex. Do not replace it with trace(Q X) and drop X=x x^T; that is a
different model, often a relaxation.

Sources: [CVXPY DPP](https://www.cvxpy.org/tutorial/dpp/index.html),
[atoms](https://www.cvxpy.org/tutorial/functions/index.html).
