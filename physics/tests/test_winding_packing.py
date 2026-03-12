"""Tests for physics.winding.packing.

Reference fixture: packing_check.json
  AWG24, channelWidth=10mm, insulatedD=5.41e-4m, turns=20, radius=0.05m.

Expected results from the fixture:
  turnsPerLayer = 18  (floor(0.010 / 5.41e-4) = floor(18.484))
  numLayers     = 2   (ceil(20 / 18))
  channelDepth  = 1.082e-3 m  (2 × 5.41e-4)
  fitsInChannel = True
  wireLength    = 6.2832 m  (2π×0.05 × 20)
"""
import math
import pytest

from physics.geometry.circular import circumference as circular_circumference
from physics.winding.packing import compute_packing, wire_length


# ---------------------------------------------------------------------------
# Reference fixture — packing geometry
# ---------------------------------------------------------------------------

def test_turns_per_layer(packing_check):
    winding = packing_check["coil"]["winding"]
    result = compute_packing(
        turns=winding["turns"],
        channel_width=winding["channelWidth"],
        insulated_d=winding["wire"]["insulatedD"],
    )
    expected = packing_check["checks"][0]["turnsPerLayer_expected"]
    assert result.turns_per_layer == expected


def test_num_layers(packing_check):
    winding = packing_check["coil"]["winding"]
    result = compute_packing(
        turns=winding["turns"],
        channel_width=winding["channelWidth"],
        insulated_d=winding["wire"]["insulatedD"],
    )
    expected = packing_check["checks"][1]["numLayers_expected"]
    assert result.num_layers == expected


def test_channel_depth(packing_check):
    winding = packing_check["coil"]["winding"]
    result = compute_packing(
        turns=winding["turns"],
        channel_width=winding["channelWidth"],
        insulated_d=winding["wire"]["insulatedD"],
    )
    check = packing_check["checks"][2]
    assert abs(result.channel_depth - check["channelDepth_expected"]) <= check["tol_abs"]


def test_fits_in_channel(packing_check):
    winding = packing_check["coil"]["winding"]
    result = compute_packing(
        turns=winding["turns"],
        channel_width=winding["channelWidth"],
        insulated_d=winding["wire"]["insulatedD"],
    )
    expected = packing_check["checks"][3]["fitsInChannel_expected"]
    assert result.fits_in_channel == expected


def test_wire_length_reference_fixture(packing_check):
    """wire_length = circumference × turns."""
    coil = packing_check["coil"]
    r = coil["geometry"]["radius"]
    turns = coil["winding"]["turns"]
    check = packing_check["checks"][4]
    length = wire_length(circular_circumference(r), turns)
    assert abs(length - check["wireLength_expected"]) <= check["tol_abs"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_wire_too_wide_for_channel():
    """insulatedD > channelWidth → fits_in_channel=False, layers=0."""
    result = compute_packing(turns=10, channel_width=0.001, insulated_d=0.002)
    assert result.fits_in_channel is False
    assert result.turns_per_layer == 0
    assert result.num_layers == 0
    assert result.channel_depth == 0.0


def test_single_turn():
    result = compute_packing(turns=1, channel_width=0.01, insulated_d=5.41e-4)
    assert result.turns_per_layer == 18
    assert result.num_layers == 1


def test_exact_fit():
    """turns = turnsPerLayer → exactly one layer."""
    result = compute_packing(turns=18, channel_width=0.01, insulated_d=5.41e-4)
    assert result.num_layers == 1


def test_one_over_fit():
    """turns = turnsPerLayer + 1 → two layers."""
    result = compute_packing(turns=19, channel_width=0.01, insulated_d=5.41e-4)
    assert result.num_layers == 2


def test_wire_length_proportional_to_turns():
    c = 2 * math.pi * 0.1
    assert math.isclose(wire_length(c, 5), 5 * c)
    assert math.isclose(wire_length(c, 1), c)
