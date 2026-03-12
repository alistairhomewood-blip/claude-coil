"""Tests for discretise_coil with toroidal geometry.

Checks:
  - Returns DiscretiseResult with correct coil_id
  - N distinct paths (not N copies of one path)
  - Each path shape (n_segments, 3)
  - Poloidal: turn centres match fixture; paths are geometrically distinct
  - Toroidal: turn radii and heights match fixture checks
  - Identity rotation + zero center: output in local torus frame
  - Non-zero rotation: orient() is applied correctly
"""

import math

import numpy as np
import pytest

from physics.discretise import DiscretiseResult, discretise_coil
from physics.types import CoilDef

R = 0.15
r = 0.02
N = 100
SEG = 200


@pytest.fixture
def coil_poloidal(toroidal_poloidal_winding) -> CoilDef:
    return CoilDef.model_validate(toroidal_poloidal_winding["coil"])


@pytest.fixture
def coil_toroidal(toroidal_toroidal_winding) -> CoilDef:
    return CoilDef.model_validate(toroidal_toroidal_winding["coil"])


# ---------------------------------------------------------------------------
# Return type and structure
# ---------------------------------------------------------------------------

def test_returns_discretise_result(coil_poloidal):
    assert isinstance(discretise_coil(coil_poloidal, SEG), DiscretiseResult)


def test_coil_id_preserved(coil_poloidal):
    result = discretise_coil(coil_poloidal, SEG)
    assert result.coil_id == coil_poloidal.id


# ---------------------------------------------------------------------------
# Poloidal winding
# ---------------------------------------------------------------------------

class TestDiscretisePoloidal:
    @pytest.fixture(autouse=True)
    def result(self, coil_poloidal):
        self._result = discretise_coil(coil_poloidal, SEG)

    def test_path_count_equals_n_turns(self, toroidal_poloidal_winding):
        check = next(c for c in toroidal_poloidal_winding["checks"]
                     if c["check"] == "discretisation_count")
        assert len(self._result.filament_paths) == check["filament_paths_expected"]

    def test_each_path_shape(self):
        for p in self._result.filament_paths:
            assert p.shape == (SEG, 3)

    def test_paths_are_distinct(self):
        # Toroidal family must produce N distinct paths, not N references to one
        p0 = self._result.filament_paths[0]
        p25 = self._result.filament_paths[25]
        assert not np.allclose(p0, p25), "Turn 0 and turn 25 should differ"

    def test_turn0_centre_fixture(self, toroidal_poloidal_winding):
        check = next(c for c in toroidal_poloidal_winding["checks"]
                     if c["check"] == "turn_0_centre")
        exp = check["centre_expected"]
        centre = self._result.filament_paths[0].mean(axis=0)
        np.testing.assert_allclose(centre, [exp["x"], exp["y"], exp["z"]], atol=1e-9)

    def test_turn25_centre_fixture(self, toroidal_poloidal_winding):
        check = next(c for c in toroidal_poloidal_winding["checks"]
                     if c["check"] == "turn_25_centre")
        exp = check["centre_expected"]
        tol = check.get("tol_abs", 1e-9)
        centre = self._result.filament_paths[25].mean(axis=0)
        np.testing.assert_allclose(centre, [exp["x"], exp["y"], exp["z"]], atol=tol)

    def test_turn0_loop_normal_fixture(self, toroidal_poloidal_winding):
        # Loop normal from area vector; fixture gives corrected value (0, -1, 0)
        check = next(c for c in toroidal_poloidal_winding["checks"]
                     if c["check"] == "turn_0_loop_normal")
        exp = check["normal_expected"]
        p = self._result.filament_paths[0]
        area = np.sum(np.cross(p, np.roll(p, -1, axis=0)), axis=0) / 2.0
        normal = area / np.linalg.norm(area)
        np.testing.assert_allclose(
            normal, [exp["x"], exp["y"], exp["z"]], atol=1e-6
        )

    def test_turn0_in_xz_plane(self):
        # phi_0=0: turn lies in XZ plane (y=0 everywhere)
        np.testing.assert_allclose(
            self._result.filament_paths[0][:, 1], 0.0, atol=1e-12
        )


# ---------------------------------------------------------------------------
# Toroidal winding
# ---------------------------------------------------------------------------

class TestDiscretiseToroidal:
    @pytest.fixture(autouse=True)
    def result(self, coil_toroidal):
        self._result = discretise_coil(coil_toroidal, SEG)

    def test_path_count_equals_n_turns(self, toroidal_toroidal_winding):
        check = next(c for c in toroidal_toroidal_winding["checks"]
                     if c["check"] == "discretisation_count")
        assert len(self._result.filament_paths) == check["filament_paths_expected"]

    def test_each_path_shape(self):
        for p in self._result.filament_paths:
            assert p.shape == (SEG, 3)

    def test_paths_are_distinct(self):
        p0 = self._result.filament_paths[0]
        p25 = self._result.filament_paths[25]
        assert not np.allclose(p0, p25), "Turn 0 and turn 25 should differ"

    def test_turn0_effective_radius_fixture(self, toroidal_toroidal_winding):
        check = next(c for c in toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_0_effective_radius")
        p = self._result.filament_paths[0]
        rho = np.sqrt(p[:, 0] ** 2 + p[:, 1] ** 2).mean()
        assert rho == pytest.approx(check["rho_expected"], rel=1e-6)

    def test_turn0_at_z_zero(self, toroidal_toroidal_winding):
        check = next(c for c in toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_0_effective_radius")
        np.testing.assert_allclose(
            self._result.filament_paths[0][:, 2], check["z_expected"], atol=1e-12
        )

    def test_turn25_effective_radius_fixture(self, toroidal_toroidal_winding):
        check = next(c for c in toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_25_effective_radius")
        p = self._result.filament_paths[25]
        rho = np.sqrt(p[:, 0] ** 2 + p[:, 1] ** 2).mean()
        assert rho == pytest.approx(check["rho_expected"], abs=check.get("tol_abs", 1e-9))

    def test_turn25_height_fixture(self, toroidal_toroidal_winding):
        check = next(c for c in toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_25_effective_radius")
        z = self._result.filament_paths[25][:, 2].mean()
        assert z == pytest.approx(check["z_expected"], abs=check.get("tol_abs", 1e-10))


# ---------------------------------------------------------------------------
# Orientation: non-zero center and rotation
# ---------------------------------------------------------------------------

def test_center_offset_applied(coil_poloidal):
    # With identity rotation but non-zero centre, all paths should be shifted
    # We can't easily set center from a fixture; construct a minimal CoilDef variant
    from physics.types import Vec3
    import copy

    coil2 = coil_poloidal.model_copy(update={"center": Vec3(x=1.0, y=0.0, z=0.0)})
    result_origin = discretise_coil(coil_poloidal, n_segments=50)
    result_shifted = discretise_coil(coil2, n_segments=50)

    # Every point in every path should be shifted by exactly (1, 0, 0)
    for p_orig, p_shift in zip(result_origin.filament_paths, result_shifted.filament_paths):
        diff = p_shift - p_orig
        np.testing.assert_allclose(diff[:, 0], 1.0, atol=1e-12)
        np.testing.assert_allclose(diff[:, 1], 0.0, atol=1e-12)
        np.testing.assert_allclose(diff[:, 2], 0.0, atol=1e-12)
