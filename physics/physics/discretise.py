"""Discretise a CoilDef into a list of filament paths in global coordinates.

Entry point: discretise_coil(coil, n_segments) -> DiscretiseResult

Output is TRANSIENT — DiscretiseResult is never stored in canonical project
data. It is computed on demand and discarded after use.

Supported geometry types: circular, racetrack, elliptical, toroidal, elongated_toroidal.

Coordinate convention:
    Flat-coil types (circular, racetrack, elliptical):
        base_path() returns a single path in local coil coordinates
        (XY plane, z=0, centred at origin, CCW from +Z).
        orient() applies ZYX Euler rotation then translation.
        All turns share the same nominal path.

    Toroidal-family types (toroidal, elongated_toroidal):
        filament_paths() returns N DISTINCT paths in local torus frame
        (centred at origin, Z-up). Each turn is geometrically different.
        orient() is applied individually to each path.
"""

from dataclasses import dataclass, field

import numpy as np

from physics.geometry import circular, elliptical, racetrack
from physics.geometry import toroidal as toroidal_geom
from physics.geometry import elongated_toroidal as elongated_toroidal_geom
from physics.geometry.common import orient
from physics.types import (
    CircularGeometry,
    CoilDef,
    EllipticalGeometry,
    ElongatedToroidalGeometry,
    RacetrackGeometry,
    ToroidalGeometry,
)


@dataclass
class DiscretiseResult:
    """Transient output of coil discretisation. Never stored in project data.

    Attributes
    ----------
    coil_id : str
        ID of the source coil.
    filament_paths : list of ndarray, each shape (N, 3)
        One path per turn, in global coordinates (metres, Z-up).
        All turns share the same nominal path (single-radius approximation).
    """
    coil_id: str
    filament_paths: list[np.ndarray] = field(default_factory=list)


def discretise_coil(coil: CoilDef, n_segments: int = 200) -> DiscretiseResult:
    """Discretise a coil into filament paths in global coordinates.

    Parameters
    ----------
    coil : CoilDef
        Validated coil definition.
    n_segments : int
        Number of points per turn (polygon segments per closed loop).
        Default 200, matching DiscretiseRequest.segmentsPerTurn default.

    Returns
    -------
    DiscretiseResult
        One filament path per turn. All turns share the nominal geometry
        (single-radius approximation — no radial offset between layers).

    Raises
    ------
    NotImplementedError
        If the geometry type is not yet supported.
    ValueError
        If n_segments < 3.
    """
    if n_segments < 3:
        raise ValueError(f"n_segments must be >= 3, got {n_segments}")

    geom = coil.geometry

    c = coil.center
    rot = coil.rotationEulerDeg
    center_xyz = (c.x, c.y, c.z)
    rotation_deg = (rot.x, rot.y, rot.z)

    # --- Flat-coil types: single base path replicated N times ---
    if isinstance(geom, CircularGeometry):
        local_path = circular.base_path(geom.radius, n_segments)
    elif isinstance(geom, RacetrackGeometry):
        local_path = racetrack.base_path(
            geom.straightLength, geom.arcRadius, n_segments
        )
    elif isinstance(geom, EllipticalGeometry):
        local_path = elliptical.base_path(geom.semiMajor, geom.semiMinor, n_segments)

    if isinstance(geom, (CircularGeometry, RacetrackGeometry, EllipticalGeometry)):
        global_path = orient(local_path, center_xyz, rotation_deg)
        return DiscretiseResult(
            coil_id=coil.id,
            filament_paths=[global_path] * coil.winding.turns,
        )

    # --- Toroidal family: N distinct paths ---
    if isinstance(geom, ToroidalGeometry):
        local_paths = toroidal_geom.filament_paths(
            geom.majorRadius, geom.minorRadius,
            coil.winding.windingMode,   # guaranteed non-None by CoilDef validator
            coil.winding.turns,
            n_segments,
        )
        return DiscretiseResult(
            coil_id=coil.id,
            filament_paths=[orient(p, center_xyz, rotation_deg) for p in local_paths],
        )

    if isinstance(geom, ElongatedToroidalGeometry):
        local_paths = elongated_toroidal_geom.filament_paths(
            geom.majorRadius, geom.minorRadius, geom.extension,
            coil.winding.windingMode,
            coil.winding.turns,
            n_segments,
        )
        return DiscretiseResult(
            coil_id=coil.id,
            filament_paths=[orient(p, center_xyz, rotation_deg) for p in local_paths],
        )

    raise NotImplementedError(
        f"discretise_coil: geometry type '{geom.type}' not yet supported."
    )
