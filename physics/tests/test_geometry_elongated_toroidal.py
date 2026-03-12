"""Tests for physics.geometry.elongated_toroidal.

Reference geometry: R=0.10m, r=0.02m, E=0.05m, N=100, n_segments=200.
Reference fixture values from elongated_toroidal_poloidal_winding.json and
elongated_toroidal_toroidal_winding.json.

Covers:
  - centreline_perimeter: L_cl = 2*pi*R + 4*E
  - per_turn_length: poloidal (constant 2*pi*r), toroidal (varies per turn)
  - total_wire_length: poloidal (N*2*pi*r), toroidal (N*L_cl, exact)
  - filament_paths poloidal: count, shape, centre, loop normal
  - filament_paths toroidal: count, shape, per-turn offsets from fixture
"""

import math

import numpy as np
import pytest

from physics.geometry.elongated_toroidal import (
    centreline_perimeter,
    filament_paths,
    per_turn_length,
    total_wire_length,
)

R = 0.10   # majorRadius, m
r = 0.02   # minorRadius, m
E = 0.05   # extension (half-length of straights), m
N = 100    # turns
SEG = 200  # n_segments

L_CL = 2.0 * math.pi * R + 4.0 * E   # ≈ 0.82832 m


# ---------------------------------------------------------------------------
# centreline_perimeter
# ---------------------------------------------------------------------------

class TestCentrelinePerimeter:
    def test_formula(self):
        assert centreline_perimeter(R, E) == pytest.approx(2.0 * math.pi * R + 4.0 * E, rel=1e-12)

    def test_fixture_value(self):
        assert centreline_perimeter(R, E) == pytest.approx(0.82832, abs=1e-4)


# ---------------------------------------------------------------------------
# per_turn_length
# ---------------------------------------------------------------------------

class TestPerTurnLength:
    def test_poloidal_constant_all_turns(self):
        expected = 2.0 * math.pi * r
        for k in [0, 1, 25, 50, 75, 99]:
            assert per_turn_length(R, r, E, "poloidal", k, N) == pytest.approx(expected, rel=1e-12)

    def test_poloidal_fixture_value(self):
        assert per_turn_length(R, r, E, "poloidal", 0, N) == pytest.approx(0.12566, abs=1e-4)

    def test_toroidal_turn0_max(self):
        # psi_0=0: length = L_cl + 2*pi*r*cos(0) = L_cl + 2*pi*r
        assert per_turn_length(R, r, E, "toroidal", 0, N) == pytest.approx(
            L_CL + 2.0 * math.pi * r, rel=1e-12
        )

    def test_toroidal_turn25_at_Lcl(self):
        # psi_25=pi/2: cos=0 → length = L_cl
        assert per_turn_length(R, r, E, "toroidal", 25, N) == pytest.approx(L_CL, rel=1e-10)

    def test_toroidal_turn50_min(self):
        # psi_50=pi: length = L_cl + 2*pi*r*cos(pi) = L_cl - 2*pi*r
        assert per_turn_length(R, r, E, "toroidal", 50, N) == pytest.approx(
            L_CL - 2.0 * math.pi * r, rel=1e-10
        )

    def test_toroidal_varies(self):
        lengths = [per_turn_length(R, r, E, "toroidal", k, N) for k in range(N)]
        assert max(lengths) == pytest.approx(L_CL + 2.0 * math.pi * r, rel=1e-10)
        assert min(lengths) == pytest.approx(L_CL - 2.0 * math.pi * r, rel=1e-10)


# ---------------------------------------------------------------------------
# total_wire_length
# ---------------------------------------------------------------------------

class TestTotalWireLength:
    def test_poloidal_formula(self):
        assert total_wire_length(R, r, E, "poloidal", N) == pytest.approx(
            N * 2.0 * math.pi * r, rel=1e-12
        )

    def test_poloidal_fixture(self):
        assert total_wire_length(R, r, E, "poloidal", N) == pytest.approx(12.566, abs=0.001)

    def test_toroidal_formula(self):
        # N * L_cl (exact via cos cancellation)
        assert total_wire_length(R, r, E, "toroidal", N) == pytest.approx(
            N * L_CL, rel=1e-12
        )

    def test_toroidal_fixture(self):
        assert total_wire_length(R, r, E, "toroidal", N) == pytest.approx(82.832, abs=0.01)

    def test_toroidal_equals_sum_of_per_turn(self):
        total = total_wire_length(R, r, E, "toroidal", N)
        per_turn_sum = sum(per_turn_length(R, r, E, "toroidal", k, N) for k in range(N))
        assert total == pytest.approx(per_turn_sum, rel=1e-9)

    def test_toroidal_cos_cancellation_exact(self):
        psi = np.array([2.0 * math.pi * k / N for k in range(N)])
        assert np.sum(np.cos(psi)) == pytest.approx(0.0, abs=1e-12)


# ---------------------------------------------------------------------------
# filament_paths — shape and count
# ---------------------------------------------------------------------------

class TestFilamentPathsShape:
    def test_poloidal_count(self):
        assert len(filament_paths(R, r, E, "poloidal", N, SEG)) == N

    def test_poloidal_each_shape(self):
        for p in filament_paths(R, r, E, "poloidal", N, SEG):
            assert p.shape == (SEG, 3)

    def test_toroidal_count(self):
        assert len(filament_paths(R, r, E, "toroidal", N, SEG)) == N

    def test_toroidal_each_shape(self):
        for p in filament_paths(R, r, E, "toroidal", N, SEG):
            assert p.shape == (SEG, 3)


# ---------------------------------------------------------------------------
# filament_paths — poloidal: geometric checks
# ---------------------------------------------------------------------------

class TestFilamentPathsPoloidal:
    @pytest.fixture(autouse=True)
    def paths(self):
        self._paths = filament_paths(R, r, E, "poloidal", N, SEG)

    def test_paths_are_distinct(self):
        assert not np.allclose(self._paths[0], self._paths[25])

    def test_turn0_centre_fixture(self, elongated_toroidal_poloidal_winding):
        # s_0=0: top-right corner (E, R, 0) = (0.05, 0.10, 0)
        check = next(c for c in elongated_toroidal_poloidal_winding["checks"]
                     if c["check"] == "turn_0_centre")
        exp = check["centre_expected"]
        centre = self._paths[0].mean(axis=0)
        np.testing.assert_allclose(centre, [exp["x"], exp["y"], exp["z"]], atol=1e-6)

    def test_turn0_loop_normal_fixture(self, elongated_toroidal_poloidal_winding):
        # T_hat on top straight = (-1, 0, 0); loop normal = T_hat
        check = next(c for c in elongated_toroidal_poloidal_winding["checks"]
                     if c["check"] == "turn_0_loop_normal")
        exp = check["normal_expected"]
        p = self._paths[0]
        area = np.sum(np.cross(p, np.roll(p, -1, axis=0)), axis=0) / 2.0
        normal = area / np.linalg.norm(area)
        np.testing.assert_allclose(normal, [exp["x"], exp["y"], exp["z"]], atol=1e-4)

    def test_turn0_z_range(self):
        z = self._paths[0][:, 2]
        assert z.min() == pytest.approx(-r, abs=1e-6)
        assert z.max() == pytest.approx(r, abs=1e-6)

    def test_all_turns_minor_radius(self):
        for k, p in enumerate(self._paths):
            centre = p.mean(axis=0)
            dists = np.linalg.norm(p - centre, axis=1)
            np.testing.assert_allclose(dists, r, rtol=1e-3,
                                       err_msg=f"turn {k}: distance from centre not ≈ r")


# ---------------------------------------------------------------------------
# filament_paths — toroidal: geometric checks
# ---------------------------------------------------------------------------

class TestFilamentPathsToroidal:
    @pytest.fixture(autouse=True)
    def paths(self):
        self._paths = filament_paths(R, r, E, "toroidal", N, SEG)

    def test_paths_are_distinct(self):
        assert not np.allclose(self._paths[0], self._paths[25])

    def test_turn0_top_straight_y(self, elongated_toroidal_toroidal_winding):
        # psi_0=0: top straight at y = R + r*cos(0) = R+r = 0.12
        check = next(c for c in elongated_toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_0_top_straight_y")
        p = self._paths[0]
        # Top straight: |x| <= E (between arc centres) and y > 0 (top half)
        top_mask = (np.abs(p[:, 0]) <= E + 1e-9) & (p[:, 1] > 0)
        assert top_mask.any(), "No points on top straight for turn 0"
        np.testing.assert_allclose(
            p[top_mask, 1], check["y_on_top_straight"], atol=1e-6
        )

    def test_turn0_right_arc_effective_radius(self, elongated_toroidal_toroidal_winding):
        # psi_0=0: effective radius on right arc = R+r = 0.12
        check = next(c for c in elongated_toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_0_right_arc_effective_radius")
        p = self._paths[0]
        # Right arc: x > E, so distance from (E, 0) ≈ R+r
        mask = p[:, 0] > E
        if mask.any():
            rho = np.sqrt((p[mask, 0] - E) ** 2 + p[mask, 1] ** 2)
            np.testing.assert_allclose(
                rho, check["effective_arc_radius_expected"], atol=1e-6
            )

    def test_turn25_top_straight_yz(self, elongated_toroidal_toroidal_winding):
        # psi_25=pi/2: y = R (no outward offset), z = r = 0.02 on top straight
        check = next(c for c in elongated_toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_25_top_straight_y")
        p = self._paths[25]
        # Top straight: |x| <= E and y > 0
        top_mask = (np.abs(p[:, 0]) <= E + 1e-9) & (p[:, 1] > 0)
        assert top_mask.any(), "No points on top straight for turn 25"
        np.testing.assert_allclose(p[top_mask, 1], check["y_on_top_straight"], atol=1e-6)
        np.testing.assert_allclose(p[top_mask, 2], check["z_on_top_straight"], atol=1e-6)

    def test_turn50_right_arc_effective_radius(self, elongated_toroidal_toroidal_winding):
        # psi_50=pi: effective radius = R-r = 0.08
        check = next(c for c in elongated_toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_50_right_arc_effective_radius")
        p = self._paths[50]
        mask = p[:, 0] > E
        if mask.any():
            rho = np.sqrt((p[mask, 0] - E) ** 2 + p[mask, 1] ** 2)
            np.testing.assert_allclose(
                rho, check["effective_arc_radius_expected"], atol=1e-6
            )
