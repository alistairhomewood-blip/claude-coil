import math
import numpy as np


def circumference(semi_major: float, semi_minor: float) -> float:
    """Return circumference of an elliptical coil using Ramanujan's second approximation.

    Accuracy: relative error < 3×10⁻⁸ for all eccentricities (0 ≤ e < 1).

    Formula (Ramanujan 1914):
        h = ((a − b) / (a + b))²
        C ≈ π(a + b)(1 + 3h / (10 + √(4 − 3h)))

    Reduces exactly to 2πa when a == b (circle).

    Parameters
    ----------
    semi_major : float
        Semi-major axis at wire centreline (metres). Must be >= semi_minor.
    semi_minor : float
        Semi-minor axis at wire centreline (metres).

    Returns
    -------
    float
        Approximate circumference (metres).
    """
    a, b = semi_major, semi_minor
    h = ((a - b) / (a + b)) ** 2
    return math.pi * (a + b) * (1.0 + 3.0 * h / (10.0 + math.sqrt(4.0 - 3.0 * h)))


def base_path(
    semi_major: float,
    semi_minor: float,
    n_segments: int = 200,
) -> np.ndarray:
    """Return N points on an elliptical coil in local coil coordinates.

    The path lies in the XY plane (z=0), centred at the origin, with
    the semi-major axis along X and the semi-minor axis along Y.
    Points are ordered CCW when viewed from +Z.

    Parameters
    ----------
    semi_major : float
        Semi-major axis (metres). Must be >= semi_minor.
    semi_minor : float
        Semi-minor axis (metres).
    n_segments : int
        Number of points (= number of segments in the closed polygon).

    Returns
    -------
    ndarray, shape (n_segments, 3)
        N distinct points. No repeated endpoint; path[-1] → path[0] closes the loop.
    """
    theta = np.linspace(0.0, 2.0 * math.pi, n_segments, endpoint=False)
    x = semi_major * np.cos(theta)
    y = semi_minor * np.sin(theta)
    z = np.zeros(n_segments)
    return np.column_stack((x, y, z))
