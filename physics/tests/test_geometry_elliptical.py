"""Tests for physics.geometry.elliptical.

Verification targets:
- circumference() reduces to 2πa when a == b (circle, exact for Ramanujan)
- circumference() is symmetric: circumference(a, b) == circumference(b, a)
  (Ramanujan formula is symmetric in a and b via h)
- base_path() returns (N, 3) array, z=0, centred at origin
- Semi-axis extents: max|x| == semi_major, max|y| == semi_minor  (to float precision)
- Points are ordered CCW when viewed from +Z (positive shoelace signed area)
- path_length(base_path()) ≈ circumference() within 0.5% for N=200
"""
import math
import numpy as np
import pytest

from physics.geometry.elliptical import circumference, base_path
from physics.geometry.common import path_length


# ---------------------------------------------------------------------------
# circumference() — analytic checks
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("r", [0.01, 0.1, 1.0])
def test_circumference_circle(r):
    """a == b → exact circle; Ramanujan gives exactly 2πa."""
    assert math.isclose(circumference(r, r), 2 * math.pi * r, rel_tol=1e-12)


def test_circumference_symmetry():
    """h depends only on (a-b)²/(a+b)², so circumference(a,b)==circumference(b,a)."""
    assert math.isclose(circumference(0.2, 0.05), circumference(0.05, 0.2), rel_tol=1e-15)


def test_circumference_larger_than_minor_axis_circle():
    """Ellipse circumference must be > 2π×semi_minor and < 2π×semi_major."""
    a, b = 0.2, 0.05
    c = circumference(a, b)
    assert c > 2 * math.pi * b
    assert c < 2 * math.pi * a


def test_circumference_known_value():
    """a=0.2, b=0.1 — cross-check against independent numerical estimate.

    The Ramanujan approximation is accurate to < 3e-8 relative error.
    We compare against a high-resolution numerical integral via polygon (N=100000)
    to verify the formula is implemented correctly.
    """
    a, b = 0.2, 0.1
    c_ram = circumference(a, b)
    # High-N polygon as reference (relative error ~ (π/N)²/6 ≈ 5e-11 for N=100000)
    theta = np.linspace(0.0, 2 * math.pi, 100_000, endpoint=False)
    pts = np.column_stack((a * np.cos(theta), b * np.sin(theta), np.zeros(100_000)))
    c_ref = path_length(pts)
    assert math.isclose(c_ram, c_ref, rel_tol=1e-5)


# ---------------------------------------------------------------------------
# base_path() — shape and geometry
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [4, 50, 200])
def test_base_path_shape(n):
    path = base_path(0.2, 0.1, n_segments=n)
    assert path.shape == (n, 3)


def test_base_path_z_is_zero():
    path = base_path(0.2, 0.1)
    np.testing.assert_array_equal(path[:, 2], 0.0)


def test_base_path_centred_at_origin():
    path = base_path(0.2, 0.1)
    centre = path.mean(axis=0)
    np.testing.assert_allclose(centre, [0.0, 0.0, 0.0], atol=1e-12)


def test_base_path_x_extent():
    """Max |x| should equal semi_major (achieved at θ=0 and θ=π)."""
    a, b = 0.2, 0.1
    path = base_path(a, b, n_segments=1000)
    np.testing.assert_allclose(np.max(np.abs(path[:, 0])), a, rtol=1e-3)


def test_base_path_y_extent():
    """Max |y| should equal semi_minor (achieved at θ=π/2 and θ=3π/2)."""
    a, b = 0.2, 0.1
    path = base_path(a, b, n_segments=1000)
    np.testing.assert_allclose(np.max(np.abs(path[:, 1])), b, rtol=1e-3)


def test_base_path_no_repeated_endpoint():
    path = base_path(0.2, 0.1)
    assert not np.allclose(path[-1], path[0])


# ---------------------------------------------------------------------------
# CCW orientation from +Z
# ---------------------------------------------------------------------------

def test_base_path_ccw():
    """Shoelace signed area must be positive → CCW when viewed from +Z."""
    path = base_path(0.2, 0.1, n_segments=200)
    x, y = path[:, 0], path[:, 1]
    signed_area = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
    assert signed_area > 0.0


def test_base_path_shoelace_area():
    """Shoelace area of ellipse polygon ≈ π×a×b."""
    a, b = 0.15, 0.08
    path = base_path(a, b, n_segments=500)
    x, y = path[:, 0], path[:, 1]
    signed_area = 0.5 * abs(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
    np.testing.assert_allclose(signed_area, math.pi * a * b, rtol=1e-4)


# ---------------------------------------------------------------------------
# path_length ≈ circumference
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("a,b", [(0.1, 0.1), (0.2, 0.1), (0.15, 0.05)])
def test_path_length_matches_circumference(a, b):
    path = base_path(a, b, n_segments=200)
    np.testing.assert_allclose(path_length(path), circumference(a, b), rtol=5e-3)
