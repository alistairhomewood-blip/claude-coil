"""Tests for physics/validation.py.

All CoilDef objects are built directly (no JSON fixtures) so tests remain
self-contained and don't depend on reference-case files.

Convention throughout:
- insulatedD is used for every fit / packing assertion.
- bareD < insulatedD always (WireSpec validator enforces this).
- Z-up, ZYX Euler, signed current — same as the rest of the physics package.
"""

from __future__ import annotations

import math

import pytest

from physics.types import (
    CircularGeometry,
    CoilDef,
    ElongatedToroidalGeometry,
    EllipticalGeometry,
    RacetrackGeometry,
    ToroidalGeometry,
    Vec3,
    WindingSpec,
    WireSpec,
)
from physics.validation import (
    INVALID_TRANSFORM,
    TURN_PITCH_TOO_SMALL,
    WIRE_DOES_NOT_FIT_CHANNEL,
    WOUND_DEPTH_EXCEEDS_COIL_RADIUS,
    WOUND_DEPTH_EXCEEDS_TUBE_RADIUS,
    ZERO_CURRENT,
    ValidationResult,
    validate_coil,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AWG24_BARE_D = 5.106e-4      # m  (bare copper OD)
AWG24_INSULATED_D = 5.41e-4  # m  (class-1 enamel insulated OD)
AWG24_AREA = 2.047e-7        # m² (bare copper cross-section)


def _wire(*, insulated_d: float = AWG24_INSULATED_D, bare_d: float = AWG24_BARE_D) -> WireSpec:
    return WireSpec(
        label="AWG24",
        bareD=bare_d,
        insulatedD=insulated_d,
        area=AWG24_AREA,
    )


def _origin() -> Vec3:
    return Vec3(x=0.0, y=0.0, z=0.0)


def _circular_coil(
    *,
    radius: float = 0.1,
    turns: int = 10,
    insulated_d: float = AWG24_INSULATED_D,
    channel_width: float = 0.01,
    current: float = 1.0,
    center: Vec3 | None = None,
    rotation: Vec3 | None = None,
) -> CoilDef:
    return CoilDef(
        id="test-circular",
        name="Test circular coil",
        center=center or _origin(),
        rotationEulerDeg=rotation or _origin(),
        geometry=CircularGeometry(type="circular", radius=radius),
        winding=WindingSpec(
            turns=turns,
            current=current,
            wire=_wire(insulated_d=insulated_d),
            channelWidth=channel_width,
        ),
    )


def _toroidal_coil(
    *,
    major_r: float = 0.10,
    minor_r: float = 0.03,
    turns: int = 10,
    insulated_d: float = AWG24_INSULATED_D,
    channel_width: float = 0.01,
    current: float = 1.0,
    mode: str = "poloidal",
) -> CoilDef:
    return CoilDef(
        id="test-toroidal",
        name="Test toroidal coil",
        center=_origin(),
        rotationEulerDeg=_origin(),
        geometry=ToroidalGeometry(
            type="toroidal", majorRadius=major_r, minorRadius=minor_r
        ),
        winding=WindingSpec(
            turns=turns,
            current=current,
            wire=_wire(insulated_d=insulated_d),
            channelWidth=channel_width,
            windingMode=mode,  # type: ignore[arg-type]
        ),
    )


def _elongated_toroidal_coil(
    *,
    major_r: float = 0.10,
    minor_r: float = 0.03,
    extension: float = 0.05,
    turns: int = 10,
    insulated_d: float = AWG24_INSULATED_D,
    channel_width: float = 0.01,
    current: float = 1.0,
    mode: str = "poloidal",
) -> CoilDef:
    return CoilDef(
        id="test-elongated",
        name="Test elongated toroidal coil",
        center=_origin(),
        rotationEulerDeg=_origin(),
        geometry=ElongatedToroidalGeometry(
            type="elongated_toroidal",
            majorRadius=major_r,
            minorRadius=minor_r,
            extension=extension,
        ),
        winding=WindingSpec(
            turns=turns,
            current=current,
            wire=_wire(insulated_d=insulated_d),
            channelWidth=channel_width,
            windingMode=mode,  # type: ignore[arg-type]
        ),
    )


def _codes(result: ValidationResult) -> set[str]:
    return {i.code for i in result.errors + result.warnings}


# ---------------------------------------------------------------------------
# 1. Valid coil — no issues
# ---------------------------------------------------------------------------

def test_valid_circular_coil_no_issues():
    coil = _circular_coil()
    result = validate_coil(coil)
    assert result.is_valid
    assert result.errors == []
    assert result.warnings == []


def test_valid_toroidal_coil_no_issues():
    # R=100mm, r=30mm, 10 turns, AWG24 → pitch >> insulatedD
    coil = _toroidal_coil()
    result = validate_coil(coil)
    assert result.is_valid
    assert result.errors == []
    assert result.warnings == []


def test_result_carries_coil_id():
    coil = _circular_coil()
    result = validate_coil(coil)
    assert result.coil_id == "test-circular"


# ---------------------------------------------------------------------------
# 2. WIRE_DOES_NOT_FIT_CHANNEL
# ---------------------------------------------------------------------------

def test_wire_does_not_fit_channel_error():
    # insulatedD (1 mm) > channelWidth (0.5 mm) → error
    coil = _circular_coil(insulated_d=1e-3, channel_width=5e-4)
    result = validate_coil(coil)
    assert not result.is_valid
    assert len(result.errors) == 1
    err = result.errors[0]
    assert err.code == WIRE_DOES_NOT_FIT_CHANNEL
    assert err.severity == "error"
    assert err.field == "winding.wire.insulatedD"


def test_wire_exactly_fits_channel_no_error():
    # insulatedD == channelWidth is the boundary — should NOT error
    d = AWG24_INSULATED_D
    coil = _circular_coil(insulated_d=d, channel_width=d)
    result = validate_coil(coil)
    assert WIRE_DOES_NOT_FIT_CHANNEL not in _codes(result)


def test_wire_fits_channel_no_error():
    # insulatedD well below channelWidth
    coil = _circular_coil(insulated_d=AWG24_INSULATED_D, channel_width=0.01)
    result = validate_coil(coil)
    assert WIRE_DOES_NOT_FIT_CHANNEL not in _codes(result)


# ---------------------------------------------------------------------------
# 3. INVALID_TRANSFORM
# ---------------------------------------------------------------------------

def test_invalid_transform_nan_center():
    coil = _circular_coil(center=Vec3(x=math.nan, y=0.0, z=0.0))
    result = validate_coil(coil)
    assert not result.is_valid
    codes = {e.code for e in result.errors}
    assert INVALID_TRANSFORM in codes
    fields = {e.field for e in result.errors if e.code == INVALID_TRANSFORM}
    assert "center.x" in fields


def test_invalid_transform_inf_rotation():
    coil = _circular_coil(rotation=Vec3(x=0.0, y=0.0, z=math.inf))
    result = validate_coil(coil)
    assert not result.is_valid
    fields = {e.field for e in result.errors if e.code == INVALID_TRANSFORM}
    assert "rotationEulerDeg.z" in fields


def test_invalid_transform_neg_inf():
    coil = _circular_coil(center=Vec3(x=0.0, y=-math.inf, z=0.0))
    result = validate_coil(coil)
    fields = {e.field for e in result.errors if e.code == INVALID_TRANSFORM}
    assert "center.y" in fields


def test_valid_transform_no_error():
    coil = _circular_coil(
        center=Vec3(x=0.5, y=-0.3, z=1.2),
        rotation=Vec3(x=45.0, y=0.0, z=90.0),
    )
    result = validate_coil(coil)
    assert INVALID_TRANSFORM not in _codes(result)


# ---------------------------------------------------------------------------
# 4. TURN_PITCH_TOO_SMALL — toroidal, poloidal mode
# ---------------------------------------------------------------------------

def test_turn_pitch_toroidal_poloidal_clean():
    # 2π·R = 2π·0.1 ≈ 628 mm; 10 turns → pitch 62.8 mm >> insulatedD 0.541 mm
    coil = _toroidal_coil(major_r=0.1, minor_r=0.03, turns=10, mode="poloidal")
    result = validate_coil(coil)
    assert TURN_PITCH_TOO_SMALL not in _codes(result)


def test_turn_pitch_toroidal_poloidal_violation():
    # 2π·R = 2π·0.1 ≈ 628.3 mm
    # pitch < insulatedD (0.541 mm) when N > 628.3 / 0.541 ≈ 1161
    coil = _toroidal_coil(major_r=0.1, minor_r=0.03, turns=1500, mode="poloidal")
    result = validate_coil(coil)
    assert TURN_PITCH_TOO_SMALL in _codes(result)
    w = next(w for w in result.warnings if w.code == TURN_PITCH_TOO_SMALL)
    assert w.severity == "warning"
    assert w.field == "winding.turns"


def test_turn_pitch_toroidal_poloidal_boundary():
    # N chosen so arc == insulatedD exactly: arc = 2πR/N = insulatedD → no warning
    R = 0.1
    insulated_d = AWG24_INSULATED_D
    N = int(2 * math.pi * R / insulated_d)  # floor → arc >= insulatedD
    coil = _toroidal_coil(major_r=R, minor_r=0.03, turns=N, mode="poloidal",
                          insulated_d=insulated_d)
    result = validate_coil(coil)
    assert TURN_PITCH_TOO_SMALL not in _codes(result)


# ---------------------------------------------------------------------------
# 5. TURN_PITCH_TOO_SMALL — toroidal, toroidal mode
# ---------------------------------------------------------------------------

def test_turn_pitch_toroidal_toroidal_mode_clean():
    # 2π·r = 2π·0.03 ≈ 188.5 mm; 10 turns → pitch 18.9 mm >> insulatedD
    coil = _toroidal_coil(major_r=0.1, minor_r=0.03, turns=10, mode="toroidal")
    result = validate_coil(coil)
    assert TURN_PITCH_TOO_SMALL not in _codes(result)


def test_turn_pitch_toroidal_toroidal_mode_violation():
    # 2π·r = 2π·0.03 ≈ 188.5 mm; pitch < 0.541 mm when N > 348
    coil = _toroidal_coil(major_r=0.1, minor_r=0.03, turns=500, mode="toroidal")
    result = validate_coil(coil)
    assert TURN_PITCH_TOO_SMALL in _codes(result)


# ---------------------------------------------------------------------------
# 6. TURN_PITCH_TOO_SMALL — elongated toroidal, poloidal mode
# ---------------------------------------------------------------------------

def test_turn_pitch_elongated_toroidal_poloidal_clean():
    # centreline = 2π·0.1 + 4·0.05 ≈ 828 mm; 10 turns → pitch 82.8 mm >> insulatedD
    coil = _elongated_toroidal_coil(
        major_r=0.1, minor_r=0.03, extension=0.05, turns=10, mode="poloidal"
    )
    result = validate_coil(coil)
    assert TURN_PITCH_TOO_SMALL not in _codes(result)


def test_turn_pitch_elongated_toroidal_poloidal_violation():
    # centreline ≈ 828 mm; pitch < 0.541 mm when N > 828/0.541 ≈ 1530
    coil = _elongated_toroidal_coil(
        major_r=0.1, minor_r=0.03, extension=0.05, turns=2000, mode="poloidal"
    )
    result = validate_coil(coil)
    assert TURN_PITCH_TOO_SMALL in _codes(result)


# ---------------------------------------------------------------------------
# 7. TURN_PITCH_TOO_SMALL — elongated toroidal, toroidal mode
# ---------------------------------------------------------------------------

def test_turn_pitch_elongated_toroidal_toroidal_mode_clean():
    # 2π·r = 2π·0.03 ≈ 188.5 mm; 10 turns → pitch 18.9 mm >> insulatedD
    coil = _elongated_toroidal_coil(
        major_r=0.1, minor_r=0.03, extension=0.05, turns=10, mode="toroidal"
    )
    result = validate_coil(coil)
    assert TURN_PITCH_TOO_SMALL not in _codes(result)


def test_turn_pitch_elongated_toroidal_toroidal_mode_violation():
    # 2π·r ≈ 188.5 mm; pitch < 0.541 mm when N > 348
    coil = _elongated_toroidal_coil(
        major_r=0.1, minor_r=0.03, extension=0.05, turns=500, mode="toroidal"
    )
    result = validate_coil(coil)
    assert TURN_PITCH_TOO_SMALL in _codes(result)


# ---------------------------------------------------------------------------
# 8. WOUND_DEPTH_EXCEEDS_TUBE_RADIUS — toroidal
# ---------------------------------------------------------------------------

def test_wound_depth_within_tube_radius_no_warning():
    # minor_r = 30 mm; 10 turns at AWG24 in 10 mm channel
    # turnsPerLayer = floor(10/0.541) = 18; numLayers = 1; depth = 0.541 mm << 30 mm
    coil = _toroidal_coil(minor_r=0.03, turns=10)
    result = validate_coil(coil)
    assert WOUND_DEPTH_EXCEEDS_TUBE_RADIUS not in _codes(result)


def test_wound_depth_exceeds_tube_radius_warning():
    # Use a tiny minor radius and many turns.
    # minor_r = 2 mm, insulatedD = 0.5 mm, channelWidth = 1 mm
    # turnsPerLayer = floor(1/0.5) = 2; for depth > 2 mm: numLayers > 4 → turns = 10
    # depth = 5 × 0.5 = 2.5 mm > 2 mm minor_r → warning
    coil = CoilDef(
        id="t",
        name="t",
        center=_origin(),
        rotationEulerDeg=_origin(),
        geometry=ToroidalGeometry(
            type="toroidal", majorRadius=0.05, minorRadius=0.002
        ),
        winding=WindingSpec(
            turns=10,
            current=1.0,
            wire=_wire(insulated_d=5e-4, bare_d=4.7e-4),
            channelWidth=1e-3,
            windingMode="poloidal",
        ),
    )
    result = validate_coil(coil)
    assert WOUND_DEPTH_EXCEEDS_TUBE_RADIUS in _codes(result)
    w = next(w for w in result.warnings if w.code == WOUND_DEPTH_EXCEEDS_TUBE_RADIUS)
    assert w.severity == "warning"
    assert w.field == "winding.turns"


def test_wound_depth_exceeds_tube_radius_elongated():
    # Same geometry but elongated_toroidal — same check applies
    coil = CoilDef(
        id="t",
        name="t",
        center=_origin(),
        rotationEulerDeg=_origin(),
        geometry=ElongatedToroidalGeometry(
            type="elongated_toroidal", majorRadius=0.05, minorRadius=0.002, extension=0.02
        ),
        winding=WindingSpec(
            turns=10,
            current=1.0,
            wire=_wire(insulated_d=5e-4, bare_d=4.7e-4),
            channelWidth=1e-3,
            windingMode="poloidal",
        ),
    )
    result = validate_coil(coil)
    assert WOUND_DEPTH_EXCEEDS_TUBE_RADIUS in _codes(result)


# ---------------------------------------------------------------------------
# 9. WOUND_DEPTH_EXCEEDS_COIL_RADIUS — circular
# ---------------------------------------------------------------------------

def test_wound_depth_within_coil_radius_no_warning():
    # radius = 100 mm; 10 turns AWG24 → depth 0.541 mm << 100 mm
    coil = _circular_coil(radius=0.1, turns=10)
    result = validate_coil(coil)
    assert WOUND_DEPTH_EXCEEDS_COIL_RADIUS not in _codes(result)


def test_wound_depth_exceeds_coil_radius_warning():
    # radius = 2 mm, insulatedD = 0.5 mm, channelWidth = 1 mm
    # turnsPerLayer = 2; 10 turns → numLayers = 5; depth = 2.5 mm > 2 mm → warning
    coil = CoilDef(
        id="c",
        name="c",
        center=_origin(),
        rotationEulerDeg=_origin(),
        geometry=CircularGeometry(type="circular", radius=0.002),
        winding=WindingSpec(
            turns=10,
            current=1.0,
            wire=_wire(insulated_d=5e-4, bare_d=4.7e-4),
            channelWidth=1e-3,
        ),
    )
    result = validate_coil(coil)
    assert WOUND_DEPTH_EXCEEDS_COIL_RADIUS in _codes(result)
    w = next(w for w in result.warnings if w.code == WOUND_DEPTH_EXCEEDS_COIL_RADIUS)
    assert w.severity == "warning"
    assert w.field == "winding.turns"


def test_wound_depth_not_checked_for_racetrack():
    # Racetrack and elliptical coils do not trigger WOUND_DEPTH_EXCEEDS_COIL_RADIUS
    coil = CoilDef(
        id="r",
        name="r",
        center=_origin(),
        rotationEulerDeg=_origin(),
        geometry=RacetrackGeometry(type="racetrack", straightLength=0.05, arcRadius=0.002),
        winding=WindingSpec(
            turns=10,
            current=1.0,
            wire=_wire(insulated_d=5e-4, bare_d=4.7e-4),
            channelWidth=1e-3,
        ),
    )
    result = validate_coil(coil)
    assert WOUND_DEPTH_EXCEEDS_COIL_RADIUS not in _codes(result)


# ---------------------------------------------------------------------------
# 10. ZERO_CURRENT
# ---------------------------------------------------------------------------

def test_zero_current_warning():
    coil = _circular_coil(current=0.0)
    result = validate_coil(coil)
    assert ZERO_CURRENT in _codes(result)
    w = next(w for w in result.warnings if w.code == ZERO_CURRENT)
    assert w.severity == "warning"
    assert w.field == "winding.current"


def test_negative_current_no_warning():
    coil = _circular_coil(current=-5.0)
    result = validate_coil(coil)
    assert ZERO_CURRENT not in _codes(result)


def test_positive_current_no_warning():
    coil = _circular_coil(current=1.0)
    result = validate_coil(coil)
    assert ZERO_CURRENT not in _codes(result)


# ---------------------------------------------------------------------------
# 11. Severity separation — errors and warnings in correct lists
# ---------------------------------------------------------------------------

def test_severity_separation_errors_and_warnings():
    # Wire doesn't fit (error) + zero current (warning) at the same time.
    coil = CoilDef(
        id="mixed",
        name="mixed",
        center=_origin(),
        rotationEulerDeg=_origin(),
        geometry=CircularGeometry(type="circular", radius=0.1),
        winding=WindingSpec(
            turns=10,
            current=0.0,          # warning: ZERO_CURRENT
            wire=_wire(insulated_d=1e-3, bare_d=9e-4),
            channelWidth=5e-4,    # error: WIRE_DOES_NOT_FIT_CHANNEL
        ),
    )
    result = validate_coil(coil)

    assert not result.is_valid
    error_codes = {e.code for e in result.errors}
    warning_codes = {w.code for w in result.warnings}

    assert WIRE_DOES_NOT_FIT_CHANNEL in error_codes
    assert ZERO_CURRENT in warning_codes

    # Nothing bleeds across the boundary
    assert ZERO_CURRENT not in error_codes
    assert WIRE_DOES_NOT_FIT_CHANNEL not in warning_codes


# ---------------------------------------------------------------------------
# 12. Wire-does-not-fit suppresses self-intersection check
# ---------------------------------------------------------------------------

def test_self_intersection_skipped_when_wire_does_not_fit():
    # Wire doesn't fit → packing undefined → no wound-depth warning should appear
    coil = CoilDef(
        id="skip",
        name="skip",
        center=_origin(),
        rotationEulerDeg=_origin(),
        geometry=CircularGeometry(type="circular", radius=0.002),
        winding=WindingSpec(
            turns=100,
            current=1.0,
            wire=_wire(insulated_d=2e-3, bare_d=1.9e-3),  # insulatedD > channelWidth
            channelWidth=1e-3,
        ),
    )
    result = validate_coil(coil)
    assert WIRE_DOES_NOT_FIT_CHANNEL in {e.code for e in result.errors}
    assert WOUND_DEPTH_EXCEEDS_COIL_RADIUS not in _codes(result)


# ---------------------------------------------------------------------------
# 13. ValidationResult serialises to JSON
# ---------------------------------------------------------------------------

def test_result_serialises_to_dict():
    coil = _circular_coil(current=0.0)
    result = validate_coil(coil)
    d = result.model_dump()
    assert d["coil_id"] == "test-circular"
    assert isinstance(d["errors"], list)
    assert isinstance(d["warnings"], list)
    assert any(w["code"] == ZERO_CURRENT for w in d["warnings"])
