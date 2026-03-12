"""Tests for physics.discretise.discretise_coil.

Key behaviours:
  - Returns DiscretiseResult with coil_id and one path per turn
  - Each path is (N, 3) in global coordinates
  - Identity rotation + zero center: path z-values all ≈ 0 (local XY plane)
  - Non-zero center: all points shifted by center
  - 90° rotation around Y: former X-axis points now on +Z (axis rotated to +X)
  - Unsupported geometry raises NotImplementedError
  - n_segments < 3 raises ValueError
"""
import math
import numpy as np
import pytest

from physics.discretise import DiscretiseResult, discretise_coil
from physics.types import (
    CircularGeometry,
    CoilDef,
    ElongatedToroidalGeometry,
    EllipticalGeometry,
    RacetrackGeometry,
    Vec3,
    WindingSpec,
    WireSpec,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_WIRE = WireSpec(label="AWG24", bareD=5.106e-4, insulatedD=5.41e-4, area=2.047e-7)


def _coil(geometry, turns=1, center=(0, 0, 0), rotation=(0, 0, 0), winding_mode=None) -> CoilDef:
    cx, cy, cz = center
    rx, ry, rz = rotation
    return CoilDef(
        id="test",
        name="test",
        center=Vec3(x=cx, y=cy, z=cz),
        rotationEulerDeg=Vec3(x=rx, y=ry, z=rz),
        geometry=geometry,
        winding=WindingSpec(turns=turns, current=1.0, channelWidth=0.01, wire=_WIRE,
                            windingMode=winding_mode),
    )


def _circular(r=0.1, **kwargs) -> CoilDef:
    return _coil(CircularGeometry(type="circular", radius=r), **kwargs)


# ---------------------------------------------------------------------------
# Return type and structure
# ---------------------------------------------------------------------------

def test_returns_discretise_result():
    result = discretise_coil(_circular())
    assert isinstance(result, DiscretiseResult)


def test_coil_id_preserved():
    coil = _circular()
    result = discretise_coil(coil)
    assert result.coil_id == coil.id


def test_one_path_per_turn_single():
    result = discretise_coil(_circular(turns=1))
    assert len(result.filament_paths) == 1


def test_one_path_per_turn_multi():
    result = discretise_coil(_circular(turns=5))
    assert len(result.filament_paths) == 5


# ---------------------------------------------------------------------------
# Path shape
# ---------------------------------------------------------------------------

def test_path_shape_default_n():
    result = discretise_coil(_circular())
    assert result.filament_paths[0].shape == (200, 3)


@pytest.mark.parametrize("n", [10, 50, 300])
def test_path_shape_custom_n(n):
    result = discretise_coil(_circular(), n_segments=n)
    assert result.filament_paths[0].shape == (n, 3)


def test_n_segments_too_small():
    with pytest.raises(ValueError):
        discretise_coil(_circular(), n_segments=2)


# ---------------------------------------------------------------------------
# Identity rotation, zero center → path in global XY plane
# ---------------------------------------------------------------------------

def test_identity_rotation_z_values():
    """Zero rotation + zero center: all z ≈ 0."""
    result = discretise_coil(_circular(r=0.1))
    z = result.filament_paths[0][:, 2]
    np.testing.assert_allclose(z, 0.0, atol=1e-12)


def test_identity_radius_preserved():
    """Points should lie at the correct radius from origin."""
    r = 0.1
    result = discretise_coil(_circular(r=r))
    path = result.filament_paths[0]
    radii = np.linalg.norm(path[:, :2], axis=1)
    np.testing.assert_allclose(radii, r, rtol=1e-12)


# ---------------------------------------------------------------------------
# Non-zero center translation
# ---------------------------------------------------------------------------

def test_center_offset_applied():
    """All points should be shifted by the center."""
    cx, cy, cz = 1.0, 2.0, 3.0
    coil = _circular(r=0.1, center=(cx, cy, cz))
    result = discretise_coil(coil)
    path = result.filament_paths[0]
    np.testing.assert_allclose(path[:, 2], cz, atol=1e-12)
    # XY centroid ≈ (cx, cy)
    np.testing.assert_allclose(path[:, :2].mean(axis=0), [cx, cy], atol=1e-12)


# ---------------------------------------------------------------------------
# Rotation
# ---------------------------------------------------------------------------

def test_90_deg_rotation_y():
    """90° around Y: coil axis flips from +Z to +X.
    A point initially at (r, 0, 0) in local frame maps to (0, 0, r) globally
    — because Ry(90°) sends +X → +Z and +Z → -X.
    Wait: Ry(90°) acts as:
      x' =  cos(90)*x + sin(90)*z =  z
      y' =  y
      z' = -sin(90)*x + cos(90)*z = -x
    So local (r, 0, 0) → global (0, 0, -r).
    The first point of base_path is (r, 0, 0) (θ=0).
    """
    r = 0.1
    coil = _circular(r=r, rotation=(0, 90, 0))  # ry=90°
    result = discretise_coil(coil)
    first_point = result.filament_paths[0][0]
    np.testing.assert_allclose(first_point, [0.0, 0.0, -r], atol=1e-12)


def test_90_deg_rotation_x():
    """90° around X: coil axis flips from +Z to -Y.
    Rx(90°): y' = -z, z' = y. Local (r,0,0) → global (r, 0, 0) unchanged in XZ.
    Local (0,r,0) → global (0, 0, r).
    The coil (circle in XY plane) now lies in XZ plane.
    """
    r = 0.1
    coil = _circular(r=r, rotation=(90, 0, 0))  # rx=90°
    result = discretise_coil(coil)
    path = result.filament_paths[0]
    # All points should have y ≈ 0 (coil now in XZ plane)
    np.testing.assert_allclose(path[:, 1], 0.0, atol=1e-12)


# ---------------------------------------------------------------------------
# Supported geometry types
# ---------------------------------------------------------------------------

def test_racetrack_discretise(racetrack_coil):
    coil = CoilDef.model_validate(racetrack_coil["coil"])
    result = discretise_coil(coil)
    assert result.filament_paths[0].shape == (200, 3)


def test_elliptical_discretise():
    coil = _coil(EllipticalGeometry(type="elliptical", semiMajor=0.2, semiMinor=0.1))
    result = discretise_coil(coil)
    path = result.filament_paths[0]
    assert path.shape == (200, 3)
    # X extent ≈ semi_major, Y extent ≈ semi_minor
    np.testing.assert_allclose(np.max(np.abs(path[:, 0])), 0.2, rtol=1e-3)
    np.testing.assert_allclose(np.max(np.abs(path[:, 1])), 0.1, rtol=1e-3)

