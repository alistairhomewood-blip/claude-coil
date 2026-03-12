"""Coil statistics: wire length, packing, resistance, mass, power, voltage.

Entry point: compute_coil_stats(coil) -> CoilStats

Supported geometry types: circular, racetrack, elliptical, toroidal, elongated_toroidal.

Physical model for flat-coil types (circular, racetrack, elliptical):
    wire_length  = circumference(nominal geometry) × turns
    (single-radius approximation — no per-layer radial offset)

Physical model for toroidal-family types:
    wire_length is computed by total_wire_length() which accounts for
    winding mode. For toroidal winding the per-turn length varies with
    poloidal angle; the total is computed exactly (cos terms cancel).
    See geometry/toroidal.py for derivation.

Shared:
    turnsPerLayer = floor(channelWidth / insulatedD)     — insulated OD only
    numLayers    = ceil(turns / turnsPerLayer)
    channelDepth = numLayers × insulatedD
    resistance   = CU_RESISTIVITY × wire_length / wire.area  — bare area only
    mass         = CU_DENSITY     × wire_length × wire.area  — bare area only
    power        = current² × resistance
    voltage      = current  × resistance                      — signed
"""

from physics.geometry import circular, elliptical, racetrack
from physics.geometry import toroidal as toroidal_geom
from physics.geometry import elongated_toroidal as elongated_toroidal_geom
from physics.types import (
    CircularGeometry,
    CoilDef,
    CoilStats,
    EllipticalGeometry,
    ElongatedToroidalGeometry,
    PackingStats,
    RacetrackGeometry,
    ToroidalGeometry,
)
from physics.winding.mass import compute_mass
from physics.winding.packing import compute_packing, wire_length
from physics.winding.resistance import compute_resistance


def compute_coil_stats(coil: CoilDef) -> CoilStats:
    """Compute all winding statistics for a single coil.

    Parameters
    ----------
    coil : CoilDef
        Validated coil definition.

    Returns
    -------
    CoilStats
        Wire length, packing geometry, resistance, mass, power, voltage.

    Raises
    ------
    NotImplementedError
        If the coil geometry type is not yet supported (toroidal,
        elongated_toroidal).
    """
    geom = coil.geometry
    winding = coil.winding
    wire = winding.wire

    # 1. Wire length — geometry-type dispatch
    if isinstance(geom, CircularGeometry):
        length = wire_length(circular.circumference(geom.radius), winding.turns)
    elif isinstance(geom, RacetrackGeometry):
        length = wire_length(
            racetrack.circumference(geom.straightLength, geom.arcRadius), winding.turns
        )
    elif isinstance(geom, EllipticalGeometry):
        length = wire_length(
            elliptical.circumference(geom.semiMajor, geom.semiMinor), winding.turns
        )
    elif isinstance(geom, ToroidalGeometry):
        # Per-turn length varies for toroidal winding; use total_wire_length()
        # which computes the exact sum (see geometry/toroidal.py for derivation).
        length = toroidal_geom.total_wire_length(
            geom.majorRadius, geom.minorRadius,
            winding.windingMode,    # guaranteed non-None by CoilDef validator
            winding.turns,
        )
    elif isinstance(geom, ElongatedToroidalGeometry):
        # Same exact-sum approach; see geometry/elongated_toroidal.py for derivation.
        length = elongated_toroidal_geom.total_wire_length(
            geom.majorRadius, geom.minorRadius, geom.extension,
            winding.windingMode,
            winding.turns,
        )
    else:
        raise NotImplementedError(
            f"compute_coil_stats: geometry type '{geom.type}' not yet supported. "
            "Implement the geometry module first."
        )

    # 3. Packing — uses insulatedD
    packing = compute_packing(winding.turns, winding.channelWidth, wire.insulatedD)

    warnings: list[str] = []
    if not packing.fits_in_channel:
        warnings.append(
            f"Wire does not fit in channel: insulatedD={wire.insulatedD*1e3:.3f} mm "
            f"> channelWidth={winding.channelWidth*1e3:.3f} mm"
        )

    # 4. Electrical and mass — use bare copper area
    resistance = compute_resistance(length, wire.area)
    mass = compute_mass(length, wire.area)
    power = winding.current ** 2 * resistance
    voltage = winding.current * resistance

    return CoilStats(
        coilId=coil.id,
        wireLength=length,
        wireMass=mass,
        resistance=resistance,
        power=power,
        voltage=voltage,
        packing=PackingStats(
            turnsPerLayer=packing.turns_per_layer,
            numLayers=packing.num_layers,
            channelDepth=packing.channel_depth,
            fitsInChannel=packing.fits_in_channel,
        ),
        warnings=warnings,
        errors=[],
    )
