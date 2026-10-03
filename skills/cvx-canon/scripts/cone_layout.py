"""Real symmetric PSD packing for Moreau and SCS; no solver dependency."""

import numpy as np


def _layout(n, backend):
    if backend == "moreau":
        pairs = [(i, j) for j in range(n) for i in range(j + 1)]
    elif backend == "scs":
        pairs = [(i, j) for j in range(n) for i in range(j, n)]
    else:
        raise ValueError("backend must be 'moreau' or 'scs'")
    rows = np.array([i for i, _ in pairs], dtype=int)
    cols = np.array([j for _, j in pairs], dtype=int)
    scales = np.where(rows == cols, 1.0, np.sqrt(2.0))
    return rows, cols, scales


def svec(matrix, backend):
    """Pack a real symmetric matrix in the backend's column-major cone order."""
    if np.iscomplexobj(matrix):
        raise ValueError("Use a documented complex cone representation")
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or not matrix.shape[0]:
        raise ValueError("Expected a nonempty square matrix")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("Matrix must be finite")
    if not np.allclose(matrix, matrix.T, rtol=1e-12, atol=1e-12):
        raise ValueError("Matrix must be symmetric")
    rows, cols, scales = _layout(matrix.shape[0], backend)
    return matrix[rows, cols] * scales


def smat(vector, n, backend):
    """Invert svec; n is the matrix dimension, not the cone-vector length."""
    if not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError("n must be a positive integer")
    if np.iscomplexobj(vector):
        raise ValueError("Expected a real cone vector")
    vector = np.asarray(vector, dtype=float)
    if vector.shape != (n * (n + 1) // 2,) or not np.all(np.isfinite(vector)):
        raise ValueError("Expected a finite vector of length n*(n+1)//2")
    rows, cols, scales = _layout(n, backend)
    matrix = np.zeros((n, n))
    matrix[rows, cols] = vector / scales
    matrix[cols, rows] = vector / scales
    return matrix
