"""Tests for discretise_coil with elongated_toroidal geometry.

Checks:
  - Returns DiscretiseResult with correct coil_id
  - N distinct paths (not N copies of one path)
  - Each path shape (n_segments, 3)
  - Poloidal: turn 0 centre and loop normal match fixture
  - Toroidal: turn 0/25/50 offsets match fixture checks
  - Identity rotation + zero center: output in local frame
  - Non-zero center: orient() shifts all paths correctly
"""

import math

import numpy as np
import pytest

from physics.discretise import DiscretiseResult, discretise_coil
from physics.types import CoilDef

R = 0.10
r = 0.02
E = 0.05
N = 100
SEG = 200


@pytest.fixture
def coil_poloidal(elongated_toroidal_poloidal_winding) -> CoilDef:
    return CoilDef.model_validate(elongated_toroidal_poloidal_winding["coil"])


@pytest.fixture
def coil_toroidal(elongated_toroidal_toroidal_winding) -> CoilDef:
    return CoilDef.model_validate(elongated_toroidal_toroidal_winding["coil"])


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

    def test_path_count_equals_n_turns(self, elongated_toroidal_poloidal_winding):
        check = next(c for c in elongated_toroidal_poloidal_winding["checks"]
                     if c["check"] == "discretisation_count")
        assert len(self._result.filament_paths) == check["filament_paths_expected"]

    def test_each_path_shape(self):
        for p in self._result.filament_paths:
            assert p.shape == (SEG, 3)

    def test_paths_are_distinct(self):
        p0 = self._result.filament_paths[0]
        p25 = self._result.filament_paths[25]
        assert not np.allclose(p0, p25)

    def test_turn0_centre_fixture(self, elongated_toroidal_poloidal_winding):
        check = next(c for c in elongated_toroidal_poloidal_winding["checks"]
                     if c["check"] == "turn_0_centre")
        exp = check["centre_expected"]
        centre = self._result.filament_paths[0].mean(axis=0)
        np.testing.assert_allclose(centre, [exp["x"], exp["y"], exp["z"]], atol=1e-6)

    def test_turn0_loop_normal_fixture(self, elongated_toroidal_poloidal_winding):
        check = next(c for c in elongated_toroidal_poloidal_winding["checks"]
                     if c["check"] == "turn_0_loop_normal")
        exp = check["normal_expected"]
        p = self._result.filament_paths[0]
        area = np.sum(np.cross(p, np.roll(p, -1, axis=0)), axis=0) / 2.0
        normal = area / np.linalg.norm(area)
        np.testing.assert_allclose(normal, [exp["x"], exp["y"], exp["z"]], atol=1e-4)


# ---------------------------------------------------------------------------
# Toroidal winding
# ---------------------------------------------------------------------------

class TestDiscretiseToroidal:
    @pytest.fixture(autouse=True)
    def result(self, coil_toroidal):
        self._result = discretise_coil(coil_toroidal, SEG)

    def test_path_count_equals_n_turns(self, elongated_toroidal_toroidal_winding):
        check = next(c for c in elongated_toroidal_toroidal_winding["checks"]
                     if c["check"] == "discretisation_count")
        assert len(self._result.filament_paths) == check["filament_paths_expected"]

    def test_each_path_shape(self):
        for p in self._result.filament_paths:
            assert p.shape == (SEG, 3)

    def test_paths_are_distinct(self):
        p0 = self._result.filament_paths[0]
        p25 = self._result.filament_paths[25]
        assert not np.allclose(p0, p25)

    def test_turn0_top_straight_y(self, elongated_toroidal_toroidal_winding):
        check = next(c for c in elongated_toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_0_top_straight_y")
        p = self._result.filament_paths[0]
        # Top straight: |x| <= E (between arc centres) and y > 0
        top_mask = (np.abs(p[:, 0]) <= E + 1e-9) & (p[:, 1] > 0)
        assert top_mask.any(), "No points on top straight for turn 0"
        np.testing.assert_allclose(p[top_mask, 1], check["y_on_top_straight"], atol=1e-6)

    def test_turn0_right_arc_effective_radius(self, elongated_toroidal_toroidal_winding):
        check = next(c for c in elongated_toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_0_right_arc_effective_radius")
        p = self._result.filament_paths[0]
        mask = p[:, 0] > E
        assert mask.any()
        rho = np.sqrt((p[mask, 0] - E) ** 2 + p[mask, 1] ** 2)
        np.testing.assert_allclose(rho, check["effective_arc_radius_expected"], atol=1e-6)

    def test_turn25_top_straight_yz(self, elongated_toroidal_toroidal_winding):
        check = next(c for c in elongated_toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_25_top_straight_y")
        p = self._result.filament_paths[25]
        # Top straight: |x| <= E and y > 0
        top_mask = (np.abs(p[:, 0]) <= E + 1e-9) & (p[:, 1] > 0)
        assert top_mask.any(), "No points on top straight for turn 25"
        np.testing.assert_allclose(p[top_mask, 1], check["y_on_top_straight"], atol=1e-6)
        np.testing.assert_allclose(p[top_mask, 2], check["z_on_top_straight"], atol=1e-6)

    def test_turn50_right_arc_effective_radius(self, elongated_toroidal_toroidal_winding):
        check = next(c for c in elongated_toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_50_right_arc_effective_radius")
        p = self._result.filament_paths[50]
        mask = p[:, 0] > E
        assert mask.any()
        rho = np.sqrt((p[mask, 0] - E) ** 2 + p[mask, 1] ** 2)
        np.testing.assert_allclose(rho, check["effective_arc_radius_expected"], atol=1e-6)


# ---------------------------------------------------------------------------
# Orientation: non-zero center
# ---------------------------------------------------------------------------

def test_center_offset_applied(coil_poloidal):
    from physics.types import Vec3

    coil2 = coil_poloidal.model_copy(update={"center": Vec3(x=1.0, y=0.0, z=0.0)})
    result_origin = discretise_coil(coil_poloidal, n_segments=50)
    result_shifted = discretise_coil(coil2, n_segments=50)

    for p_orig, p_shift in zip(result_origin.filament_paths, result_shifted.filament_paths):
        diff = p_shift - p_orig
        np.testing.assert_allclose(diff[:, 0], 1.0, atol=1e-12)
        np.testing.assert_allclose(diff[:, 1], 0.0, atol=1e-12)
        np.testing.assert_allclose(diff[:, 2], 0.0, atol=1e-12)
