"""Tests for physics.geometry.racetrack.

Verification targets:
- circumference() matches analytic formula 2*L + 2*pi*R
- base_path() returns (N, 3) array, z=0, centred at origin
- path_length(base_path()) ≈ circumference() within 0.5% for N=200
- All points lie at correct y-extent (±arc_radius) on straights
- Points are ordered CCW when viewed from +Z
- Reference fixture racetrack_coil: L=0.1m, R=0.05m, circumference=0.51416m
"""
import math
import numpy as np
import pytest

from physics.geometry.racetrack import circumference, base_path
from physics.geometry.common import path_length


# ---------------------------------------------------------------------------
# circumference()
# ---------------------------------------------------------------------------

def test_circumference_formula():
    L, R = 0.1, 0.05
    expected = 2 * L + 2 * math.pi * R
    assert math.isclose(circumference(L, R), expected)


def test_circumference_reference_fixture(racetrack_coil):
    """Reference fixture: L=0.1m, R=0.05m → 0.51416m."""
    geom = racetrack_coil["coil"]["geometry"]
    L = geom["straightLength"]
    R = geom["arcRadius"]
    expected = racetrack_coil["checks"][0]["circumference_expected"]
    tol = racetrack_coil["checks"][0]["tol_abs"]
    assert abs(circumference(L, R) - expected) <= tol


def test_circumference_zero_straight():
    """Zero straight length → pure circle of circumference 2*pi*R."""
    R = 0.1
    assert math.isclose(circumference(0.0, R), 2 * math.pi * R)


# ---------------------------------------------------------------------------
# base_path() — shape and geometry
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [4, 50, 200])
def test_base_path_shape(n):
    path = base_path(0.1, 0.05, n_segments=n)
    assert path.shape == (n, 3)


def test_base_path_z_is_zero():
    path = base_path(0.1, 0.05)
    np.testing.assert_array_equal(path[:, 2], 0.0)


def test_base_path_centred_at_origin():
    """Centroid should be at origin (symmetric geometry)."""
    path = base_path(0.1, 0.05)
    centre = path.mean(axis=0)
    np.testing.assert_allclose(centre, [0.0, 0.0, 0.0], atol=1e-10)


def test_base_path_y_extent():
    """All points should satisfy |y| <= arc_radius."""
    R = 0.05
    path = base_path(0.1, R)
    assert np.all(np.abs(path[:, 1]) <= R + 1e-12)


def test_base_path_x_extent():
    """All points should satisfy |x| <= straight_length/2 + arc_radius."""
    L, R = 0.1, 0.05
    path = base_path(L, R)
    assert np.all(np.abs(path[:, 0]) <= L / 2 + R + 1e-12)


def test_base_path_no_repeated_endpoint():
    path = base_path(0.1, 0.05)
    assert not np.allclose(path[-1], path[0])


# ---------------------------------------------------------------------------
# CCW orientation from +Z
# ---------------------------------------------------------------------------

def test_base_path_ccw():
    """Signed area (shoelace) should be positive → CCW when viewed from +Z."""
    path = base_path(0.1, 0.05, n_segments=200)
    x, y = path[:, 0], path[:, 1]
    # Shoelace formula for signed area
    signed_area = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
    assert signed_area > 0.0


# ---------------------------------------------------------------------------
# path_length ≈ circumference
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("L,R", [(0.1, 0.05), (0.2, 0.03), (0.0, 0.1)])
def test_path_length_matches_circumference(L, R):
    path = base_path(L, R, n_segments=200)
    np.testing.assert_allclose(path_length(path), circumference(L, R), rtol=5e-3)


def test_path_length_reference_fixture(racetrack_coil):
    """path_length of the N=200 polygon must be within 0.5% of circumference().

    The fixture tol_abs applies to the analytic formula only, not to polygon
    approximation error, so we use rtol=5e-3 here.
    """
    geom = racetrack_coil["coil"]["geometry"]
    L = geom["straightLength"]
    R = geom["arcRadius"]
    path = base_path(L, R, n_segments=200)
    np.testing.assert_allclose(path_length(path), circumference(L, R), rtol=5e-3)
