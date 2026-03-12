"""Tests for physics.geometry.toroidal.

Reference geometry: R=0.15m, r=0.02m, N=100, n_segments=200.

Covers:
  - per_turn_length: poloidal (constant), toroidal (varies, exact values)
  - total_wire_length: poloidal and toroidal; toroidal cancellation check
  - filament_paths: shape, count, and geometric properties of specific turns
  - Loop normals computed from area vectors (right-hand rule)
"""

import math

import numpy as np
import pytest

from physics.geometry.toroidal import filament_paths, per_turn_length, total_wire_length

R = 0.15   # majorRadius, m
r = 0.02   # minorRadius, m
N = 100    # turns
SEG = 200  # n_segments


# ---------------------------------------------------------------------------
# per_turn_length
# ---------------------------------------------------------------------------

class TestPerTurnLength:
    def test_poloidal_constant_all_turns(self):
        expected = 2.0 * math.pi * r
        for k in [0, 1, 25, 50, 75, 99]:
            assert per_turn_length(R, r, "poloidal", k, N) == pytest.approx(expected, rel=1e-12)

    def test_poloidal_value(self):
        assert per_turn_length(R, r, "poloidal", 0, N) == pytest.approx(0.12566, abs=1e-4)

    def test_toroidal_turn0_outer(self):
        # psi_0=0 → rho_0 = R + r = 0.17 m
        assert per_turn_length(R, r, "toroidal", 0, N) == pytest.approx(
            2.0 * math.pi * (R + r), rel=1e-12
        )

    def test_toroidal_turn25_at_R(self):
        # psi_25 = pi/2 → cos(psi_25) = 0 → rho_25 = R
        assert per_turn_length(R, r, "toroidal", 25, N) == pytest.approx(
            2.0 * math.pi * R, rel=1e-10
        )

    def test_toroidal_turn50_inner(self):
        # psi_50 = pi → rho_50 = R - r = 0.13 m
        assert per_turn_length(R, r, "toroidal", 50, N) == pytest.approx(
            2.0 * math.pi * (R - r), rel=1e-10
        )

    def test_toroidal_varies_between_min_max(self):
        lengths = [per_turn_length(R, r, "toroidal", k, N) for k in range(N)]
        assert max(lengths) == pytest.approx(2.0 * math.pi * (R + r), rel=1e-10)
        assert min(lengths) == pytest.approx(2.0 * math.pi * (R - r), rel=1e-10)
        # turn 0 is the outermost, turn 50 innermost
        assert lengths[0] > lengths[25] > lengths[50 - 1]  # strictly decreasing 0→50


# ---------------------------------------------------------------------------
# total_wire_length
# ---------------------------------------------------------------------------

class TestTotalWireLength:
    def test_poloidal(self):
        assert total_wire_length(R, r, "poloidal", N) == pytest.approx(
            N * 2.0 * math.pi * r, rel=1e-12
        )

    def test_poloidal_fixture(self):
        # fixture: 100 * 2*pi*0.02 = 12.566 m
        assert total_wire_length(R, r, "poloidal", N) == pytest.approx(12.566, abs=1e-3)

    def test_toroidal_exact_formula(self):
        # N * 2*pi*R (exact due to cos cancellation)
        assert total_wire_length(R, r, "toroidal", N) == pytest.approx(
            N * 2.0 * math.pi * R, rel=1e-12
        )

    def test_toroidal_fixture(self):
        # fixture: 100 * 2*pi*0.15 = 94.248 m, tol_abs=0.01
        assert total_wire_length(R, r, "toroidal", N) == pytest.approx(94.248, abs=0.01)

    def test_toroidal_equals_sum_of_per_turn(self):
        # The formula N*2*pi*R must equal the exact per-turn sum
        total = total_wire_length(R, r, "toroidal", N)
        per_turn_sum = sum(per_turn_length(R, r, "toroidal", k, N) for k in range(N))
        assert total == pytest.approx(per_turn_sum, rel=1e-9)

    def test_toroidal_cos_cancellation_is_exact(self):
        # Direct verification: sum of cos(2*pi*k/N) over k=0..N-1 is 0
        psi = np.array([2.0 * math.pi * k / N for k in range(N)])
        assert np.sum(np.cos(psi)) == pytest.approx(0.0, abs=1e-12)


# ---------------------------------------------------------------------------
# filament_paths — shape and count
# ---------------------------------------------------------------------------

class TestFilamentPathsShape:
    def test_poloidal_count(self):
        assert len(filament_paths(R, r, "poloidal", N, SEG)) == N

    def test_poloidal_each_shape(self):
        for p in filament_paths(R, r, "poloidal", N, SEG):
            assert p.shape == (SEG, 3)

    def test_toroidal_count(self):
        assert len(filament_paths(R, r, "toroidal", N, SEG)) == N

    def test_toroidal_each_shape(self):
        for p in filament_paths(R, r, "toroidal", N, SEG):
            assert p.shape == (SEG, 3)


# ---------------------------------------------------------------------------
# filament_paths — poloidal: geometric checks
# ---------------------------------------------------------------------------

class TestFilamentPathsPoloidal:
    @pytest.fixture(autouse=True)
    def paths(self):
        self._paths = filament_paths(R, r, "poloidal", N, SEG)

    def test_turn0_centre(self):
        # phi_0=0: centre at (R, 0, 0)
        centre = self._paths[0].mean(axis=0)
        np.testing.assert_allclose(centre, [R, 0.0, 0.0], atol=1e-10)

    def test_turn0_lies_in_xz_plane(self):
        # All y-coords of turn 0 should be zero
        np.testing.assert_allclose(self._paths[0][:, 1], 0.0, atol=1e-12)

    def test_turn0_x_range(self):
        x = self._paths[0][:, 0]
        assert x.min() == pytest.approx(R - r, abs=1e-6)
        assert x.max() == pytest.approx(R + r, abs=1e-6)

    def test_turn0_z_range(self):
        z = self._paths[0][:, 2]
        assert z.min() == pytest.approx(-r, abs=1e-6)
        assert z.max() == pytest.approx(r, abs=1e-6)

    def test_turn25_centre(self):
        # phi_25 = pi/2: centre at (0, R, 0)
        centre = self._paths[25].mean(axis=0)
        np.testing.assert_allclose(centre, [0.0, R, 0.0], atol=1e-10)

    def test_turn25_lies_in_yz_plane(self):
        np.testing.assert_allclose(self._paths[25][:, 0], 0.0, atol=1e-12)

    def test_turn50_centre(self):
        # phi_50 = pi: centre at (-R, 0, 0)
        centre = self._paths[50].mean(axis=0)
        np.testing.assert_allclose(centre, [-R, 0.0, 0.0], atol=1e-10)

    def test_all_turns_same_minor_radius(self):
        for k, p in enumerate(self._paths):
            centre = p.mean(axis=0)
            # Distances from centre should all be ≈ r
            dists = np.linalg.norm(p - centre, axis=1)
            np.testing.assert_allclose(dists, r, rtol=1e-3,
                                       err_msg=f"turn {k}: distance from centre not ≈ r")

    def test_turn0_loop_normal(self):
        # Area vector for turn 0: integral gives (0, -pi*r^2, 0) → normal = (0, -1, 0)
        # See geometry_definitions.md for derivation.
        p = self._paths[0]
        area = np.sum(np.cross(p, np.roll(p, -1, axis=0)), axis=0) / 2.0
        normal = area / np.linalg.norm(area)
        np.testing.assert_allclose(normal, [0.0, -1.0, 0.0], atol=1e-6)

    def test_turn25_loop_normal(self):
        # phi_25=pi/2 → n_hat_25 = (sin(pi/2), -cos(pi/2), 0) = (1, 0, 0)
        p = self._paths[25]
        area = np.sum(np.cross(p, np.roll(p, -1, axis=0)), axis=0) / 2.0
        normal = area / np.linalg.norm(area)
        np.testing.assert_allclose(normal, [1.0, 0.0, 0.0], atol=1e-6)


# ---------------------------------------------------------------------------
# filament_paths — toroidal: geometric checks
# ---------------------------------------------------------------------------

class TestFilamentPathsToroidal:
    @pytest.fixture(autouse=True)
    def paths(self):
        self._paths = filament_paths(R, r, "toroidal", N, SEG)

    def test_turn0_is_horizontal(self):
        # z should be constant = z_0 = r*sin(0) = 0
        np.testing.assert_allclose(self._paths[0][:, 2], 0.0, atol=1e-12)

    def test_turn0_effective_radius(self):
        # rho_0 = R + r = 0.17 m
        p = self._paths[0]
        radii = np.sqrt(p[:, 0] ** 2 + p[:, 1] ** 2)
        np.testing.assert_allclose(radii, R + r, rtol=1e-10)

    def test_turn25_height(self):
        # psi_25=pi/2: z_25 = r*sin(pi/2) = r = 0.02 m
        np.testing.assert_allclose(self._paths[25][:, 2], r, atol=1e-12)

    def test_turn25_effective_radius(self):
        # rho_25 = R + r*cos(pi/2) = R = 0.15 m
        p = self._paths[25]
        radii = np.sqrt(p[:, 0] ** 2 + p[:, 1] ** 2)
        np.testing.assert_allclose(radii, R, rtol=1e-10)

    def test_turn50_is_horizontal(self):
        # z_50 = r*sin(pi) = 0
        np.testing.assert_allclose(self._paths[50][:, 2], 0.0, atol=1e-12)

    def test_turn50_effective_radius(self):
        # rho_50 = R - r = 0.13 m
        p = self._paths[50]
        radii = np.sqrt(p[:, 0] ** 2 + p[:, 1] ** 2)
        np.testing.assert_allclose(radii, R - r, rtol=1e-10)

    def test_all_turns_loop_normal_is_z(self):
        # All toroidal turns are horizontal → area vector in Z direction
        for k, p in enumerate(self._paths):
            area = np.sum(np.cross(p, np.roll(p, -1, axis=0)), axis=0) / 2.0
            normal = area / np.linalg.norm(area)
            assert abs(normal[2]) == pytest.approx(1.0, abs=1e-6), \
                f"turn {k}: loop normal z-component not ±1"

    def test_fixture_turn0_effective_radius(self, toroidal_toroidal_winding):
        check = next(c for c in toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_0_effective_radius")
        p = self._paths[0]
        rho = np.sqrt(p[:, 0] ** 2 + p[:, 1] ** 2).mean()
        assert rho == pytest.approx(check["rho_expected"], rel=1e-6)

    def test_fixture_turn25_effective_radius(self, toroidal_toroidal_winding):
        check = next(c for c in toroidal_toroidal_winding["checks"]
                     if c["check"] == "turn_25_effective_radius")
        p = self._paths[25]
        rho = np.sqrt(p[:, 0] ** 2 + p[:, 1] ** 2).mean()
        assert rho == pytest.approx(check["rho_expected"], abs=check.get("tol_abs", 1e-10))
