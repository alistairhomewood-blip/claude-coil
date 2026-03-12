import math
import numpy as np


def circumference(radius: float) -> float:
    """Return circumference of a circular coil.

    Parameters
    ----------
    radius : float
        Distance from coil centre to wire centreline (metres).

    Returns
    -------
    float
        Circumference = 2 * pi * radius (metres).
    """
    return 2.0 * math.pi * radius


def base_path(radius: float, n_segments: int = 200) -> np.ndarray:
    """Return N points on a circular coil in local coil coordinates.

    The path lies in the XY plane (z=0), centred at the origin.
    Points are ordered CCW when viewed from +Z, consistent with
    the positive-current convention (CCW from +n̂).

    Parameters
    ----------
    radius : float
        Distance from coil centre to wire centreline (metres).
    n_segments : int
        Number of points (= number of segments in the closed polygon).

    Returns
    -------
    ndarray, shape (n_segments, 3)
        N distinct points. No repeated endpoint; path[-1] → path[0] closes the loop.
    """
    theta = np.linspace(0.0, 2.0 * math.pi, n_segments, endpoint=False)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    z = np.zeros(n_segments)
    return np.column_stack((x, y, z))
