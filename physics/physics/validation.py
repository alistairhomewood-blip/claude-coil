"""Coil geometry and winding validation.

Produces structured ValidationResult objects that can be serialised to JSON
and consumed by the frontend.

Conventions (see docs/notes/ for full details):
- All units SI (metres, amperes).
- Coordinate system: Z-up, right-handed XYZ.
- insulatedD is the sole dimension for all fit / packing checks.
- bareD is NOT used in this module.
- Pydantic enforces structural constraints (positive dims, minor < major, etc.).
  This module only adds runtime checks that Pydantic cannot enforce.

Assumptions:
- Packing layers stack radially outward from the geometry centreline radius.
- Turns are evenly spaced by arc length along the winding path (toroidal family).
- Arc-length per turn = total winding-path length / N.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel

from .types import (
    CircularGeometry,
    CoilDef,
    ElongatedToroidalGeometry,
    ToroidalGeometry,
)
from .winding.packing import compute_packing


# ---------------------------------------------------------------------------
# Issue codes — machine-readable identifiers for the frontend
# ---------------------------------------------------------------------------

INVALID_TRANSFORM = "INVALID_TRANSFORM"
WIRE_DOES_NOT_FIT_CHANNEL = "WIRE_DOES_NOT_FIT_CHANNEL"
TURN_PITCH_TOO_SMALL = "TURN_PITCH_TOO_SMALL"
WOUND_DEPTH_EXCEEDS_TUBE_RADIUS = "WOUND_DEPTH_EXCEEDS_TUBE_RADIUS"
WOUND_DEPTH_EXCEEDS_COIL_RADIUS = "WOUND_DEPTH_EXCEEDS_COIL_RADIUS"
ZERO_CURRENT = "ZERO_CURRENT"


# ---------------------------------------------------------------------------
# Output types
# ---------------------------------------------------------------------------

class ValidationIssue(BaseModel):
    """A single validation finding.

    code     — machine-readable SCREAMING_SNAKE_CASE identifier
    severity — "error" (fatal) or "warning" (non-fatal but problematic)
    message  — human-readable description; dimensions shown in mm
    field    — dot-path to the offending field, e.g. "winding.wire.insulatedD"
    """

    code: str
    severity: Literal["error", "warning"]
    message: str
    field: str | None = None


class ValidationResult(BaseModel):
    """Structured validation output for a single coil.

    Serialises to JSON via .model_dump().
    is_valid is True iff there are no errors (warnings are non-fatal).
    """

    coil_id: str
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _err(code: str, message: str, field: str | None = None) -> ValidationIssue:
    return ValidationIssue(code=code, severity="error", message=message, field=field)


def _warn(code: str, message: str, field: str | None = None) -> ValidationIssue:
    return ValidationIssue(code=code, severity="warning", message=message, field=field)


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def _check_transform(coil: CoilDef) -> list[ValidationIssue]:
    """Error if any component of center or rotationEulerDeg is NaN or Inf.

    Pydantic v2 allows non-finite floats in plain float fields by default,
    so this check is the only guard against degenerate transforms.
    """
    issues: list[ValidationIssue] = []
    candidates = [
        ("center.x", coil.center.x),
        ("center.y", coil.center.y),
        ("center.z", coil.center.z),
        ("rotationEulerDeg.x", coil.rotationEulerDeg.x),
        ("rotationEulerDeg.y", coil.rotationEulerDeg.y),
        ("rotationEulerDeg.z", coil.rotationEulerDeg.z),
    ]
    for field_path, value in candidates:
        if not math.isfinite(value):
            issues.append(
                _err(
                    INVALID_TRANSFORM,
                    f"{field_path} is not finite ({value!r}): "
                    "coil cannot be placed in world space",
                    field=field_path,
                )
            )
    return issues


def _check_wire_channel_fit(coil: CoilDef) -> list[ValidationIssue]:
    """Error if the insulated wire OD exceeds the U-channel width.

    Uses insulatedD exclusively — the physical dimension that determines fit.
    A single turn cannot be wound if insulatedD > channelWidth.
    """
    w = coil.winding
    if w.wire.insulatedD > w.channelWidth:
        d_mm = w.wire.insulatedD * 1e3
        cw_mm = w.channelWidth * 1e3
        return [
            _err(
                WIRE_DOES_NOT_FIT_CHANNEL,
                f"Insulated wire diameter {d_mm:.3f} mm exceeds channel width "
                f"{cw_mm:.3f} mm: no turn can fit",
                field="winding.wire.insulatedD",
            )
        ]
    return []


def _check_turn_pitch(coil: CoilDef) -> list[ValidationIssue]:
    """Warn if arc-length per turn is less than insulatedD (turns overlap).

    Only applies to the toroidal family; flat coils (circular, racetrack,
    elliptical) are governed by the channel packing model instead.

    Winding-path lengths used:
      Toroidal, poloidal mode  : centreline = 2π·R
      Toroidal, toroidal mode  : tube circumference = 2π·r
      Elongated toroidal, poloidal: centreline = 2π·R + 4·E
      Elongated toroidal, toroidal: tube circumference = 2π·r
    """
    g = coil.geometry
    w = coil.winding
    insulated_d = w.wire.insulatedD
    N = w.turns

    if isinstance(g, ToroidalGeometry):
        if w.windingMode == "poloidal":
            path = 2.0 * math.pi * g.majorRadius
            arc = path / N
            if arc < insulated_d:
                return [
                    _warn(
                        TURN_PITCH_TOO_SMALL,
                        f"Poloidal turn pitch {arc * 1e3:.3f} mm < insulated wire "
                        f"diameter {insulated_d * 1e3:.3f} mm: turns overlap along "
                        f"torus centreline (2π·R = {path * 1e3:.1f} mm, N = {N})",
                        field="winding.turns",
                    )
                ]
        elif w.windingMode == "toroidal":
            path = 2.0 * math.pi * g.minorRadius
            arc = path / N
            if arc < insulated_d:
                return [
                    _warn(
                        TURN_PITCH_TOO_SMALL,
                        f"Toroidal turn pitch {arc * 1e3:.3f} mm < insulated wire "
                        f"diameter {insulated_d * 1e3:.3f} mm: turns overlap around "
                        f"tube cross-section (2π·r = {path * 1e3:.1f} mm, N = {N})",
                        field="winding.turns",
                    )
                ]

    elif isinstance(g, ElongatedToroidalGeometry):
        if w.windingMode == "poloidal":
            path = 2.0 * math.pi * g.majorRadius + 4.0 * g.extension
            arc = path / N
            if arc < insulated_d:
                return [
                    _warn(
                        TURN_PITCH_TOO_SMALL,
                        f"Poloidal turn pitch {arc * 1e3:.3f} mm < insulated wire "
                        f"diameter {insulated_d * 1e3:.3f} mm: turns overlap along "
                        f"elongated-torus centreline "
                        f"(centreline = {path * 1e3:.1f} mm, N = {N})",
                        field="winding.turns",
                    )
                ]
        elif w.windingMode == "toroidal":
            path = 2.0 * math.pi * g.minorRadius
            arc = path / N
            if arc < insulated_d:
                return [
                    _warn(
                        TURN_PITCH_TOO_SMALL,
                        f"Toroidal turn pitch {arc * 1e3:.3f} mm < insulated wire "
                        f"diameter {insulated_d * 1e3:.3f} mm: turns overlap around "
                        f"tube cross-section (2π·r = {path * 1e3:.1f} mm, N = {N})",
                        field="winding.turns",
                    )
                ]

    return []


def _check_self_intersection(coil: CoilDef) -> list[ValidationIssue]:
    """Warn when wound depth exceeds a geometric bound.

    Two cases checked:

    1. Any toroidal geometry — channel_depth > minorRadius.
       The winding would extend past the tube centreline, so turns on
       opposite sides of the tube occupy the same physical volume.

    2. Circular coil — channel_depth > coil radius.
       The winding depth is as large as (or larger than) the coil itself,
       likely indicating a configuration error.

    Skipped if the wire already does not fit (packing undefined).
    channel_depth = numLayers × insulatedD via compute_packing().
    """
    issues: list[ValidationIssue] = []
    g = coil.geometry
    w = coil.winding

    # Packing is undefined when wire doesn't fit; skip to avoid noise.
    if w.wire.insulatedD > w.channelWidth:
        return []

    packing = compute_packing(w.turns, w.channelWidth, w.wire.insulatedD)

    if isinstance(g, (ToroidalGeometry, ElongatedToroidalGeometry)):
        if packing.channel_depth > g.minorRadius:
            issues.append(
                _warn(
                    WOUND_DEPTH_EXCEEDS_TUBE_RADIUS,
                    f"Wound depth {packing.channel_depth * 1e3:.2f} mm exceeds tube "
                    f"minor radius {g.minorRadius * 1e3:.2f} mm "
                    f"({packing.num_layers} layer(s) × "
                    f"{w.wire.insulatedD * 1e3:.3f} mm): "
                    "windings may self-intersect through the tube centreline",
                    field="winding.turns",
                )
            )

    elif isinstance(g, CircularGeometry):
        if packing.channel_depth > g.radius:
            issues.append(
                _warn(
                    WOUND_DEPTH_EXCEEDS_COIL_RADIUS,
                    f"Wound depth {packing.channel_depth * 1e3:.2f} mm exceeds coil "
                    f"radius {g.radius * 1e3:.2f} mm "
                    f"({packing.num_layers} layer(s) × "
                    f"{w.wire.insulatedD * 1e3:.3f} mm): "
                    "winding depth dominates coil geometry",
                    field="winding.turns",
                )
            )

    return issues


def _check_current(coil: CoilDef) -> list[ValidationIssue]:
    """Warn if current is exactly zero (coil produces no magnetic field)."""
    if coil.winding.current == 0.0:
        return [
            _warn(
                ZERO_CURRENT,
                "Current is zero: coil produces no magnetic field",
                field="winding.current",
            )
        ]
    return []


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def validate_coil(coil: CoilDef) -> ValidationResult:
    """Validate a single coil definition.

    Returns a ValidationResult with separate errors and warnings lists.

    Errors are fatal — the coil is physically impossible or statistics cannot
    be meaningfully computed.

    Warnings are non-fatal — the coil is computable but likely has a
    configuration problem.

    All fit and packing checks use insulatedD.
    bareD is not used here.

    Convention: Z-up, ZYX Euler rotation, signed current, SI units.
    """
    issues: list[ValidationIssue] = []
    issues.extend(_check_transform(coil))
    issues.extend(_check_wire_channel_fit(coil))
    issues.extend(_check_turn_pitch(coil))
    issues.extend(_check_self_intersection(coil))
    issues.extend(_check_current(coil))

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    return ValidationResult(coil_id=coil.id, errors=errors, warnings=warnings)
