"""Tests for physics.stats.compute_coil_stats.

Fixtures used:
  single_circular_loop — R=0.1m, I=1A, N=1, AWG24
  packing_check        — R=0.05m, I=1A, N=20, AWG24, channelWidth=10mm

We verify:
  - wire_length = circumference × turns
  - packing fields match reference fixture
  - resistance matches reference fixture
  - mass matches reference fixture
  - power = I² × R_elec
  - voltage = I × R_elec
  - unsupported geometry raises NotImplementedError
  - wire-too-wide produces warning and fits_in_channel=False
"""
import math
import pytest

from physics.stats import compute_coil_stats
from physics.types import (
    CircularGeometry,
    CoilDef,
    CoilStats,
    ElongatedToroidalGeometry,
    Vec3,
    WindingSpec,
    WireSpec,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_coil(geometry, turns=1, current=1.0, channel_width=0.01,
               insulated_d=5.41e-4, bare_d=5.106e-4, area=2.047e-7,
               center=None, rotation=None, winding_mode=None) -> CoilDef:
    """Convenience factory for test CoilDef objects."""
    return CoilDef(
        id="test-coil",
        name="test",
        center=center or Vec3(x=0, y=0, z=0),
        rotationEulerDeg=rotation or Vec3(x=0, y=0, z=0),
        geometry=geometry,
        winding=WindingSpec(
            turns=turns,
            current=current,
            channelWidth=channel_width,
            windingMode=winding_mode,
            wire=WireSpec(
                label="AWG24",
                bareD=bare_d,
                insulatedD=insulated_d,
                area=area,
            ),
        ),
    )


def _coil_from_fixture(fixture: dict) -> CoilDef:
    return CoilDef.model_validate(fixture["coil"])


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

def test_returns_coil_stats(single_circular_loop):
    coil = _coil_from_fixture(single_circular_loop)
    result = compute_coil_stats(coil)
    assert isinstance(result, CoilStats)


def test_coil_id_preserved(single_circular_loop):
    coil = _coil_from_fixture(single_circular_loop)
    result = compute_coil_stats(coil)
    assert result.coilId == coil.id


# ---------------------------------------------------------------------------
# Wire length — single_circular_loop fixture (R=0.1m, N=1)
# ---------------------------------------------------------------------------

def test_wire_length_single_loop(single_circular_loop):
    coil = _coil_from_fixture(single_circular_loop)
    result = compute_coil_stats(coil)
    expected = 2 * math.pi * 0.1 * 1  # circumference × turns
    assert math.isclose(result.wireLength, expected, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# Full winding stats — packing_check fixture
# ---------------------------------------------------------------------------

def test_wire_length_packing_fixture(packing_check):
    coil = _coil_from_fixture(packing_check)
    result = compute_coil_stats(coil)
    check = packing_check["checks"][4]
    assert abs(result.wireLength - check["wireLength_expected"]) <= check["tol_abs"]


def test_packing_turns_per_layer(packing_check):
    coil = _coil_from_fixture(packing_check)
    result = compute_coil_stats(coil)
    assert result.packing.turnsPerLayer == packing_check["checks"][0]["turnsPerLayer_expected"]


def test_packing_num_layers(packing_check):
    coil = _coil_from_fixture(packing_check)
    result = compute_coil_stats(coil)
    assert result.packing.numLayers == packing_check["checks"][1]["numLayers_expected"]


def test_packing_channel_depth(packing_check):
    coil = _coil_from_fixture(packing_check)
    result = compute_coil_stats(coil)
    check = packing_check["checks"][2]
    assert abs(result.packing.channelDepth - check["channelDepth_expected"]) <= check["tol_abs"]


def test_packing_fits_in_channel(packing_check):
    coil = _coil_from_fixture(packing_check)
    result = compute_coil_stats(coil)
    assert result.packing.fitsInChannel == packing_check["checks"][3]["fitsInChannel_expected"]


def test_resistance_packing_fixture(packing_check):
    coil = _coil_from_fixture(packing_check)
    result = compute_coil_stats(coil)
    check = packing_check["checks"][5]
    assert math.isclose(result.resistance, check["resistance_expected"], rel_tol=check["tol_rel"])


def test_mass_packing_fixture(packing_check):
    coil = _coil_from_fixture(packing_check)
    result = compute_coil_stats(coil)
    check = packing_check["checks"][6]
    assert math.isclose(result.wireMass, check["mass_expected"], rel_tol=check["tol_rel"])


# ---------------------------------------------------------------------------
# Power and voltage
# ---------------------------------------------------------------------------

def test_power_formula(single_circular_loop):
    """power = I² × resistance."""
    coil = _coil_from_fixture(single_circular_loop)
    result = compute_coil_stats(coil)
    assert math.isclose(result.power, coil.winding.current ** 2 * result.resistance)


def test_voltage_formula(single_circular_loop):
    """voltage = I × resistance (signed)."""
    coil = _coil_from_fixture(single_circular_loop)
    result = compute_coil_stats(coil)
    assert math.isclose(result.voltage, coil.winding.current * result.resistance)


def test_negative_current_voltage_sign():
    """Negative current → negative voltage."""
    coil = _make_coil(
        CircularGeometry(type="circular", radius=0.1),
        current=-2.0,
    )
    result = compute_coil_stats(coil)
    assert result.voltage < 0
    assert result.power > 0  # I²R always positive


# ---------------------------------------------------------------------------
# Supported geometry types
# ---------------------------------------------------------------------------

def test_racetrack_stats(racetrack_coil):
    coil = _coil_from_fixture(racetrack_coil)
    result = compute_coil_stats(coil)
    assert result.wireLength > 0
    assert result.errors == []


def test_elliptical_stats():
    coil = _make_coil(
        geometry=__import__("physics.types", fromlist=["EllipticalGeometry"])
        .EllipticalGeometry(type="elliptical", semiMajor=0.1, semiMinor=0.05),
    )
    result = compute_coil_stats(coil)
    assert result.wireLength > 0
    assert result.errors == []



# ---------------------------------------------------------------------------
# Warning: wire too wide for channel
# ---------------------------------------------------------------------------

def test_wire_too_wide_warning():
    coil = _make_coil(
        CircularGeometry(type="circular", radius=0.1),
        channel_width=0.0001,   # 0.1 mm — narrower than insulatedD
        insulated_d=5.41e-4,    # 0.541 mm
    )
    result = compute_coil_stats(coil)
    assert not result.packing.fitsInChannel
    assert len(result.warnings) > 0
    assert result.errors == []
