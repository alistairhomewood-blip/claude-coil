"""Tests for physics.geometry.circular.

Verification targets:
- circumference() matches analytic formula 2*pi*R
- base_path() returns (N, 3) array, z=0, centred at origin
- path_length(base_path()) ≈ circumference() within 0.1% for N=200
- Radius of every point matches the given radius
- Points are ordered CCW when viewed from +Z (cross-product z > 0)
- Reference fixture single_circular_loop: R=0.1m, circumference=2*pi*0.1
"""
import math
import numpy as np
import pytest

from physics.geometry.circular import circumference, base_path
from physics.geometry.common import path_length


# ---------------------------------------------------------------------------
# circumference()
# ---------------------------------------------------------------------------

def test_circumference_unit_circle():
    assert math.isclose(circumference(1.0), 2 * math.pi)


def test_circumference_small_radius():
    r = 0.1
    assert math.isclose(circumference(r), 2 * math.pi * r)


def test_circumference_reference_fixture(single_circular_loop):
    """R=0.1m from reference fixture."""
    r = single_circular_loop["coil"]["geometry"]["radius"]
    assert math.isclose(circumference(r), 2 * math.pi * r)


# ---------------------------------------------------------------------------
# base_path() — shape and geometry
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [4, 50, 200])
def test_base_path_shape(n):
    path = base_path(0.1, n_segments=n)
    assert path.shape == (n, 3)


def test_base_path_z_is_zero():
    path = base_path(0.1)
    np.testing.assert_array_equal(path[:, 2], 0.0)


def test_base_path_centred_at_origin():
    path = base_path(0.1)
    centre = path.mean(axis=0)
    np.testing.assert_allclose(centre[:2], [0.0, 0.0], atol=1e-12)


def test_base_path_radius():
    r = 0.07
    path = base_path(r)
    radii = np.linalg.norm(path[:, :2], axis=1)
    np.testing.assert_allclose(radii, r, rtol=1e-12)


def test_base_path_no_repeated_endpoint():
    """Last point must differ from first (closed loop is implicit)."""
    path = base_path(0.1)
    assert not np.allclose(path[-1], path[0])


# ---------------------------------------------------------------------------
# CCW orientation from +Z
# ---------------------------------------------------------------------------

def test_base_path_ccw():
    """Cross product of consecutive edge vectors should have z > 0 (CCW from +Z)."""
    path = base_path(0.1, n_segments=8)
    v1 = path[1] - path[0]
    v2 = path[2] - path[1]
    cross_z = v1[0] * v2[1] - v1[1] * v2[0]
    assert cross_z > 0.0


# ---------------------------------------------------------------------------
# path_length ≈ circumference
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("r", [0.05, 0.1, 0.5])
def test_path_length_matches_circumference(r):
    path = base_path(r, n_segments=200)
    assert math.isclose(path_length(path), circumference(r), rel_tol=1e-3)


def test_path_length_reference_fixture(single_circular_loop):
    """Path length must match circumference within 0.1% for N=200."""
    r = single_circular_loop["coil"]["geometry"]["radius"]
    path = base_path(r, n_segments=200)
    np.testing.assert_allclose(path_length(path), circumference(r), rtol=1e-3)
