"""Tests for physics.winding.mass.

Formula: m = CU_DENSITY × L × A
  CU_DENSITY = 8960 kg/m³
  L = wire length (m)
  A = bare copper cross-section (m²)  — NOT insulatedD

Reference fixture (packing_check.json):
  wireLength = 6.2832 m, bare_area = 2.047e-7 m²
  mass_expected = 0.011524 kg, tol_rel = 0.005
"""
import math
import pytest

from physics.constants import CU_DENSITY
from physics.geometry.circular import circumference as circular_circumference
from physics.winding.packing import wire_length
from physics.winding.mass import compute_mass


# ---------------------------------------------------------------------------
# Reference fixture
# ---------------------------------------------------------------------------

def test_mass_reference_fixture(packing_check):
    coil = packing_check["coil"]
    r = coil["geometry"]["radius"]
    turns = coil["winding"]["turns"]
    bare_area = coil["winding"]["wire"]["area"]
    check = packing_check["checks"][6]

    length = wire_length(circular_circumference(r), turns)
    mass = compute_mass(length, bare_area)

    assert math.isclose(mass, check["mass_expected"], rel_tol=check["tol_rel"])


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_mass_formula():
    """m = ρ_Cu × L × A with known values."""
    L = 1.0      # 1 m of wire
    A = 1e-6     # 1 mm²
    expected = CU_DENSITY * L * A
    assert math.isclose(compute_mass(L, A), expected)


def test_mass_scales_linearly_with_length():
    A = 2.047e-7
    m1 = compute_mass(1.0, A)
    m2 = compute_mass(3.0, A)
    assert math.isclose(m2, 3 * m1)


def test_mass_scales_linearly_with_area():
    L = 5.0
    m1 = compute_mass(L, 1e-7)
    m2 = compute_mass(L, 3e-7)
    assert math.isclose(m2, 3 * m1)


def test_mass_uses_bare_area_not_insulated():
    """Smoke-test: bare area and insulated area give different mass values."""
    L = 6.2832
    bare_area = 2.047e-7
    insulated_area = math.pi * (5.41e-4 / 2) ** 2  # ≈ 2.298e-7 m²
    assert not math.isclose(
        compute_mass(L, bare_area),
        compute_mass(L, insulated_area),
        rel_tol=1e-3,
    )
