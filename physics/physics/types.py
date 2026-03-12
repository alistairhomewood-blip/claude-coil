"""
Pydantic models mirroring the contracts schemas in /packages/contracts/schema/.

These are the validated Python representations of inbound API data.
No physics logic lives here — only data shapes and validation.

Convention notes (see docs/notes/ for full details):
- rotationEulerDeg: ZYX Euler angles in degrees. Identity = coil in XY plane, axis = +Z.
- current: signed float (A). Positive = CCW from +n̂ (right-hand rule).
- n̂ is derived from rotationEulerDeg in physics code. It is never stored.
- filamentPaths: NOT part of CoilDef. Transient output of the discretise step only.
- All coordinates are in the Z-up global frame, metres.
"""

from __future__ import annotations

import math
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field, model_validator


class Vec3(BaseModel):
    x: float
    y: float
    z: float


# ---------------------------------------------------------------------------
# Wire
# ---------------------------------------------------------------------------

class WireSpec(BaseModel):
    """
    Wire conductor specification.
    Two diameters required — never conflate them:
      bareD      → resistance and mass (bare copper area)
      insulatedD → packing geometry and U-channel fit
    """
    awg: int | None = None
    label: str
    bareD: Annotated[float, Field(gt=0, description="Bare copper OD, metres")]
    insulatedD: Annotated[float, Field(gt=0, description="Insulated OD, metres")]
    area: Annotated[float, Field(gt=0, description="Bare copper cross-section, m²")]

    @model_validator(mode="after")
    def insulated_must_exceed_bare(self) -> WireSpec:
        if self.insulatedD < self.bareD:
            raise ValueError(
                f"insulatedD ({self.insulatedD}) must be >= bareD ({self.bareD})"
            )
        return self


# ---------------------------------------------------------------------------
# Geometry variants — geometry.type is the sole coil-type discriminator
# ---------------------------------------------------------------------------

class CircularGeometry(BaseModel):
    type: Literal["circular"]
    radius: Annotated[float, Field(gt=0, description="Distance center → wire centerline, m")]


class RacetrackGeometry(BaseModel):
    type: Literal["racetrack"]
    straightLength: Annotated[float, Field(gt=0, description="Length of one straight segment, m")]
    arcRadius: Annotated[float, Field(gt=0, description="Radius of semicircular ends, m")]


class EllipticalGeometry(BaseModel):
    type: Literal["elliptical"]
    semiMajor: Annotated[float, Field(gt=0, description="Semi-major axis at wire centreline, m")]
    semiMinor: Annotated[float, Field(gt=0, description="Semi-minor axis at wire centreline, m")]

    @model_validator(mode="after")
    def minor_le_major(self) -> EllipticalGeometry:
        if self.semiMinor > self.semiMajor:
            raise ValueError(
                f"semiMinor ({self.semiMinor}) must be <= semiMajor ({self.semiMajor})"
            )
        return self


class ToroidalGeometry(BaseModel):
    type: Literal["toroidal"]
    majorRadius: Annotated[float, Field(gt=0, description="Torus axis → tube centreline, m")]
    minorRadius: Annotated[float, Field(gt=0, description="Tube cross-section radius, m")]

    @model_validator(mode="after")
    def minor_lt_major(self) -> ToroidalGeometry:
        if self.minorRadius >= self.majorRadius:
            raise ValueError(
                f"minorRadius ({self.minorRadius}) must be < majorRadius ({self.majorRadius})"
            )
        return self


class ElongatedToroidalGeometry(BaseModel):
    type: Literal["elongated_toroidal"]
    majorRadius: Annotated[float, Field(gt=0, description="Radius of racetrack centreline ends, m")]
    minorRadius: Annotated[float, Field(gt=0, description="Tube cross-section radius, m")]
    extension: Annotated[float, Field(gt=0, description="Half-length of straight section, m")]


CoilGeometry = Annotated[
    Union[
        CircularGeometry,
        RacetrackGeometry,
        EllipticalGeometry,
        ToroidalGeometry,
        ElongatedToroidalGeometry,
    ],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Winding
# ---------------------------------------------------------------------------

class WindingSpec(BaseModel):
    turns: Annotated[int, Field(ge=1, description="Total turns across all layers")]
    current: float  # A, signed — positive = CCW from +n̂
    wire: WireSpec
    channelWidth: Annotated[float, Field(gt=0, description="U-channel internal width, m")]
    # Required when geometry.type is 'toroidal' or 'elongated_toroidal'.
    # Must be None for all other geometry types.
    # Validated at the CoilDef level (cross-field), not here.
    windingMode: Literal["poloidal", "toroidal"] | None = None


# ---------------------------------------------------------------------------
# CoilDef — canonical coil representation
# ---------------------------------------------------------------------------

_TOROIDAL_TYPES = {"toroidal", "elongated_toroidal"}


class CoilDef(BaseModel):
    """
    Canonical coil definition. Mirrors packages/contracts/schema/coil_def.schema.json.

    Orientation is stored as rotationEulerDeg (ZYX, degrees) only.
    The coil axis n̂ is derived in physics functions — call coil_normal(coil) to get it.
    filamentPaths is NOT part of this model; it is transient output from discretisation.
    """
    id: str
    groupId: str | None = None
    name: str
    colour: str | None = None
    notes: str | None = None
    locked: bool = False
    center: Vec3
    rotationEulerDeg: Vec3  # ZYX degrees; n̂ derived in physics, never stored
    geometry: CoilGeometry
    winding: WindingSpec

    @model_validator(mode="after")
    def winding_mode_required_for_toroidal(self) -> CoilDef:
        is_toroidal = self.geometry.type in _TOROIDAL_TYPES
        has_mode = self.winding.windingMode is not None
        if is_toroidal and not has_mode:
            raise ValueError(
                f"winding.windingMode is required when geometry.type is '{self.geometry.type}'"
            )
        if not is_toroidal and has_mode:
            raise ValueError(
                f"winding.windingMode must be null for geometry.type '{self.geometry.type}'"
            )
        return self


# ---------------------------------------------------------------------------
# Group
# ---------------------------------------------------------------------------

class GroupDef(BaseModel):
    id: str
    name: str
    coilIds: list[str]
    locked: bool = False


# ---------------------------------------------------------------------------
# Project file
# ---------------------------------------------------------------------------

class ProjectFile(BaseModel):
    schemaVersion: str
    appVersion: str
    exportTimestamp: str  # ISO 8601
    projectName: str
    creatorMetadata: dict | None = None
    displayUnits: Literal["m", "cm"]
    coils: list[CoilDef]
    groups: list[GroupDef]


# ---------------------------------------------------------------------------
# API request/response models
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Stats response types — mirror coil_stats.schema.json
# ---------------------------------------------------------------------------

class PackingStats(BaseModel):
    turnsPerLayer: int
    numLayers: int
    channelDepth: float   # m — radial depth of winding
    fitsInChannel: bool


class CoilStats(BaseModel):
    """
    Computed properties of a single coil.
    All values are in SI units.
    warnings/errors are non-empty only when something is unusual or unsupported.
    """
    coilId: str
    wireLength: float   # m
    wireMass: float     # kg
    resistance: float   # Ω (DC, bare copper area, 20 °C)
    power: float        # W = I² × R
    voltage: float      # V = I × R  (signed: follows current sign)
    packing: PackingStats
    warnings: list[str] = []
    errors: list[str] = []


# ---------------------------------------------------------------------------
# API request/response models
# ---------------------------------------------------------------------------

class StatsRequest(BaseModel):
    coils: list[CoilDef]


class DiscretiseRequest(BaseModel):
    coils: list[CoilDef]
    segmentsPerTurn: Annotated[int, Field(ge=8, le=1000)] = 200


class BFieldSliceRequest(BaseModel):
    coilIds: list[str] = Field(default_factory=list)
    sliceZ: float
    xMin: float
    xMax: float
    yMin: float
    yMax: float
    resolution: Annotated[int, Field(ge=2, le=2048)]


# ---------------------------------------------------------------------------
# Utility: derive coil normal from rotationEulerDeg
# ---------------------------------------------------------------------------

def coil_normal(coil: CoilDef) -> tuple[float, float, float]:
    """
    Derive the coil axis unit vector n̂ from rotationEulerDeg (ZYX, degrees).

    n̂ = R_ZYX(rotZ, rotY, rotX) · [0, 0, 1]

    ZYX intrinsic Euler = R = Rz @ Ry @ Rx (extrinsic XYZ).
    n̂ is the third column of R:

        nx =  cos(rz)*sin(ry)*cos(rx) + sin(rz)*sin(rx)
        ny =  sin(rz)*sin(ry)*cos(rx) - cos(rz)*sin(rx)
        nz =  cos(ry)*cos(rx)

    Verification of special cases:
      (0,0,0)   → (0, 0, 1)   identity, axis = +Z  ✓
      (0,90,0)  → (1, 0, 0)   90° around Y, axis = +X ✓
      (90,0,0)  → (0,-1, 0)   90° around X, axis = -Y ✓

    This is the only authoritative place n̂ is computed in the physics package.
    It must not be computed anywhere in apps/web.
    """
    rx = math.radians(coil.rotationEulerDeg.x)
    ry = math.radians(coil.rotationEulerDeg.y)
    rz = math.radians(coil.rotationEulerDeg.z)

    nx = math.cos(rz) * math.sin(ry) * math.cos(rx) + math.sin(rz) * math.sin(rx)
    ny = math.sin(rz) * math.sin(ry) * math.cos(rx) - math.cos(rz) * math.sin(rx)
    nz = math.cos(ry) * math.cos(rx)

    # Normalise to guard against float drift
    mag = math.sqrt(nx * nx + ny * ny + nz * nz)
    return (nx / mag, ny / mag, nz / mag)
