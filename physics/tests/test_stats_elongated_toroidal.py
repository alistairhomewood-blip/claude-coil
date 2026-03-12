"""Tests for compute_coil_stats with elongated_toroidal geometry.

Loads the two reference fixtures (poloidal and toroidal winding) and checks
wireLength, packing, resistance, mass, power, voltage.

Key distinction from flat-coil stats:
  - Poloidal winding: wireLength = N * 2*pi*r  (constant per-turn length)
  - Toroidal winding: wireLength = N * L_cl    (exact via cos cancellation)
    where L_cl = 2*pi*R + 4*E
  - Packing, resistance, mass, power, voltage use the same formulas as flat coils.
"""

import math

import pytest

from physics.geometry.elongated_toroidal import centreline_perimeter
from physics.stats import compute_coil_stats
from physics.types import CoilDef


@pytest.fixture
def coil_poloidal(elongated_toroidal_poloidal_winding) -> CoilDef:
    return CoilDef.model_validate(elongated_toroidal_poloidal_winding["coil"])


@pytest.fixture
def coil_toroidal(elongated_toroidal_toroidal_winding) -> CoilDef:
    return CoilDef.model_validate(elongated_toroidal_toroidal_winding["coil"])


# ---------------------------------------------------------------------------
# Poloidal winding stats
# ---------------------------------------------------------------------------

class TestStatsPoloidal:
    def test_wire_length_fixture(self, coil_poloidal, elongated_toroidal_poloidal_winding):
        check = next(c for c in elongated_toroidal_poloidal_winding["checks"]
                     if c["check"] == "wire_length")
        result = compute_coil_stats(coil_poloidal)
        assert result.wireLength == pytest.approx(
            check["wireLength_expected"], abs=check["tol_abs"]
        )

    def test_wire_length_formula(self, coil_poloidal):
        g = coil_poloidal.geometry
        result = compute_coil_stats(coil_poloidal)
        expected = coil_poloidal.winding.turns * 2.0 * math.pi * g.minorRadius
        assert result.wireLength == pytest.approx(expected, rel=1e-12)

    def test_packing_fits(self, coil_poloidal):
        result = compute_coil_stats(coil_poloidal)
        assert result.packing.fitsInChannel

    def test_resistance_positive(self, coil_poloidal):
        result = compute_coil_stats(coil_poloidal)
        assert result.resistance > 0

    def test_power_equals_i_squared_r(self, coil_poloidal):
        result = compute_coil_stats(coil_poloidal)
        I = coil_poloidal.winding.current
        assert result.power == pytest.approx(I ** 2 * result.resistance, rel=1e-12)

    def test_voltage_equals_i_times_r(self, coil_poloidal):
        result = compute_coil_stats(coil_poloidal)
        I = coil_poloidal.winding.current
        assert result.voltage == pytest.approx(I * result.resistance, rel=1e-12)

    def test_no_errors(self, coil_poloidal):
        result = compute_coil_stats(coil_poloidal)
        assert result.errors == []

    def test_coil_id_preserved(self, coil_poloidal):
        result = compute_coil_stats(coil_poloidal)
        assert result.coilId == coil_poloidal.id


# ---------------------------------------------------------------------------
# Toroidal winding stats
# ---------------------------------------------------------------------------

class TestStatsToroidal:
    def test_wire_length_fixture(self, coil_toroidal, elongated_toroidal_toroidal_winding):
        check = next(c for c in elongated_toroidal_toroidal_winding["checks"]
                     if c["check"] == "wire_length")
        result = compute_coil_stats(coil_toroidal)
        assert result.wireLength == pytest.approx(
            check["wireLength_expected"], abs=check["tol_abs"]
        )

    def test_wire_length_formula(self, coil_toroidal):
        g = coil_toroidal.geometry
        result = compute_coil_stats(coil_toroidal)
        L_cl = centreline_perimeter(g.majorRadius, g.extension)
        expected = coil_toroidal.winding.turns * L_cl
        assert result.wireLength == pytest.approx(expected, rel=1e-12)

    def test_toroidal_wire_longer_than_poloidal(self, coil_poloidal, coil_toroidal):
        # L_cl >> 2*pi*r, so toroidal total >> poloidal total
        pol = compute_coil_stats(coil_poloidal).wireLength
        tor = compute_coil_stats(coil_toroidal).wireLength
        assert tor > pol

    def test_packing_fits(self, coil_toroidal):
        result = compute_coil_stats(coil_toroidal)
        assert result.packing.fitsInChannel

    def test_power_equals_i_squared_r(self, coil_toroidal):
        result = compute_coil_stats(coil_toroidal)
        I = coil_toroidal.winding.current
        assert result.power == pytest.approx(I ** 2 * result.resistance, rel=1e-12)

    def test_no_errors(self, coil_toroidal):
        result = compute_coil_stats(coil_toroidal)
        assert result.errors == []

    def test_coil_id_preserved(self, coil_toroidal):
        result = compute_coil_stats(coil_toroidal)
        assert result.coilId == coil_toroidal.id
