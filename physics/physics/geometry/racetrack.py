import math
import numpy as np


def circumference(straight_length: float, arc_radius: float) -> float:
    """Return circumference of a racetrack coil.

    A racetrack has two straight segments (each of length straight_length)
    and two semicircular ends (each of radius arc_radius).

    Parameters
    ----------
    straight_length : float
        Length of one straight segment (metres).
    arc_radius : float
        Radius of the semicircular ends (metres).

    Returns
    -------
    float
        Circumference = 2 * straight_length + 2 * pi * arc_radius (metres).
    """
    return 2.0 * straight_length + 2.0 * math.pi * arc_radius


def base_path(
    straight_length: float,
    arc_radius: float,
    n_segments: int = 200,
) -> np.ndarray:
    """Return N points on a racetrack coil in local coil coordinates.

    Geometry (local frame, XY plane, z=0):
    - Two straight segments parallel to the X axis, centred at origin.
    - Straight centres at y = ±arc_radius.
    - Right arc: centre at (+straight_length/2, 0, 0).
    - Left arc:  centre at (-straight_length/2, 0, 0).
    - Points are ordered CCW when viewed from +Z.

    The n_segments points are distributed proportionally around the perimeter:
    each of the four sections receives a number of points proportional to its
    arc-length fraction, so path_length(base_path(...)) ≈ circumference(...).

    Parameters
    ----------
    straight_length : float
        Length of one straight segment (metres).
    arc_radius : float
        Radius of the semicircular ends (metres).
    n_segments : int
        Total number of points. Must be >= 4.

    Returns
    -------
    ndarray, shape (n_segments, 3)
        N distinct points. No repeated endpoint; path[-1] → path[0] closes the loop.
    """
    total = circumference(straight_length, arc_radius)
    straight_frac = straight_length / total
    arc_frac = (math.pi * arc_radius) / total

    # Points per section (two straights, two arcs); keep total exact.
    n_top    = max(1, round(straight_frac * n_segments))  # top straight
    n_right  = max(1, round(arc_frac     * n_segments))   # right semicircle
    n_bot    = max(1, round(straight_frac * n_segments))  # bottom straight
    n_left   = n_segments - n_top - n_right - n_bot       # left semicircle (remainder)
    n_left   = max(1, n_left)

    # Rebalance if rounding pushed total away from n_segments
    # (adjust n_right by the deficit)
    total_pts = n_top + n_right + n_bot + n_left
    if total_pts != n_segments:
        n_right = max(1, n_right + (n_segments - total_pts))

    half = straight_length / 2.0
    points = []

    # CCW from +Z means: top edge goes right→left, bottom edge goes left→right.

    # Top straight: right to left, y = +arc_radius
    t = np.linspace(0.0, 1.0, n_top, endpoint=False)
    points.append(np.column_stack((
        half - t * straight_length,
        np.full(n_top, arc_radius),
        np.zeros(n_top),
    )))

    # Left arc: angles increasing π/2 → 3π/2 (CCW), centre at (-half, 0, 0).
    # Sweeps from (-half, +arc_radius) around the left end to (-half, -arc_radius).
    theta = np.linspace(math.pi / 2.0, 3.0 * math.pi / 2.0, n_left, endpoint=False)
    points.append(np.column_stack((
        -half + arc_radius * np.cos(theta),
        arc_radius * np.sin(theta),
        np.zeros(n_left),
    )))

    # Bottom straight: left to right, y = -arc_radius
    t = np.linspace(0.0, 1.0, n_bot, endpoint=False)
    points.append(np.column_stack((
        -half + t * straight_length,
        np.full(n_bot, -arc_radius),
        np.zeros(n_bot),
    )))

    # Right arc: angles increasing -π/2 → π/2 (CCW), centre at (+half, 0, 0).
    # Sweeps from (+half, -arc_radius) around the right end to (+half, +arc_radius).
    theta = np.linspace(-math.pi / 2.0, math.pi / 2.0, n_right, endpoint=False)
    points.append(np.column_stack((
        half + arc_radius * np.cos(theta),
        arc_radius * np.sin(theta),
        np.zeros(n_right),
    )))

    return np.vstack(points)
