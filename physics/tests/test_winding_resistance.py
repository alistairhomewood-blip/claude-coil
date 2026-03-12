"""Tests for physics.winding.resistance.

Formula: R = CU_RESISTIVITY × L / A
  CU_RESISTIVITY = 1.68e-8 Ω·m
  L = wire length (m)
  A = bare copper cross-section (m²)

Reference fixture (packing_check.json):
  wireLength = 6.2832 m, bare_area = 2.047e-7 m²
  resistance_expected = 0.5157 Ω, tol_rel = 0.005
"""
import math
import pytest

from physics.constants import CU_RESISTIVITY
from physics.geometry.circular import circumference as circular_circumference
from physics.winding.packing import wire_length
from physics.winding.resistance import compute_resistance


# ---------------------------------------------------------------------------
# Reference fixture
# ---------------------------------------------------------------------------

def test_resistance_reference_fixture(packing_check):
    coil = packing_check["coil"]
    r = coil["geometry"]["radius"]
    turns = coil["winding"]["turns"]
    bare_area = coil["winding"]["wire"]["area"]
    check = packing_check["checks"][5]

    length = wire_length(circular_circumference(r), turns)
    resistance = compute_resistance(length, bare_area)

    assert math.isclose(resistance, check["resistance_expected"], rel_tol=check["tol_rel"])


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_resistance_formula():
    """R = ρL/A with known values."""
    L = 1.0      # 1 m of wire
    A = 1e-6     # 1 mm²
    expected = CU_RESISTIVITY / A  # ρ / A per metre
    assert math.isclose(compute_resistance(L, A), expected)


def test_resistance_scales_linearly_with_length():
    A = 2.047e-7
    r1 = compute_resistance(1.0, A)
    r2 = compute_resistance(2.0, A)
    assert math.isclose(r2, 2 * r1)


def test_resistance_scales_inversely_with_area():
    L = 5.0
    r1 = compute_resistance(L, 1e-6)
    r2 = compute_resistance(L, 2e-6)
    assert math.isclose(r2, r1 / 2)


def test_resistance_uses_bare_area_not_insulated():
    """Smoke-test: bare area (2.047e-7) and insulated area (π(5.41e-4/2)²)
    give different results — confirms the caller must pass bare area."""
    L = 6.2832
    bare_area = 2.047e-7
    insulated_area = math.pi * (5.41e-4 / 2) ** 2  # ≈ 2.298e-7 m²
    assert not math.isclose(
        compute_resistance(L, bare_area),
        compute_resistance(L, insulated_area),
        rel_tol=1e-3,
    )
