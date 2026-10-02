"""Copyable exact SOC geometric-mean constructor; requires existing CVXPY."""

from fractions import Fraction

import cvxpy as cp


def exact_geo_mean(x, weights, *, max_denom=1024):
    """Preserve normalized rational exponents, or raise rather than approximate.

    Weights may be Fractions, integers, exact fraction/decimal strings, or
    floats interpreted as their exact binary values. No rational is guessed
    from a rounded float. Copy this function/module into the application.
    max_denom bounds the attempted SOC representation; no solve is performed.
    """
    expected = tuple(Fraction(w) for w in weights)
    if not expected or any(w < 0 for w in expected) or sum(expected) != 1:
        raise ValueError("Expected nonnegative exact exponents summing to one; "
                         "use Fraction values or exact strings for rational inputs")
    try:
        atom = cp.geo_mean(x, p=expected, max_denom=max_denom)
    except ValueError as exc:
        raise ValueError(f"Exact SOC geometric mean could not be constructed at "
                         f"max_denom={max_denom}: {exc}") from exc
    # Some CVXPY versions omit zero-weight entries from the represented tuple.
    nonzero = tuple(w for w in expected if w > 0)
    if tuple(atom.w) not in (expected, nonzero) or atom.approx_error != 0:
        raise ValueError("Geometric-mean representation changed the requested exponents")
    return atom
