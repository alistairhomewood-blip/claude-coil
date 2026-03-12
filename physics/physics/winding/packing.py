"""Winding packing geometry.

Model: turns are wound in layers inside a U-channel of fixed axial width
(channelWidth). Each layer fits floor(channelWidth / insulatedD) turns side
by side. Layers stack radially; the total radial depth of the winding is
numLayers × insulatedD.

All calculations use the insulated wire OD (insulatedD) for geometry.
Resistance and mass use the bare copper area — see resistance.py and mass.py.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PackingResult:
    turns_per_layer: int  # turns fitting in one layer; 0 if wire too wide
    num_layers: int        # layers needed for all turns; 0 if wire too wide
    channel_depth: float   # radial winding depth = num_layers × insulatedD (m)
    fits_in_channel: bool  # True iff insulatedD <= channelWidth (turns_per_layer >= 1)


def compute_packing(
    turns: int,
    channel_width: float,
    insulated_d: float,
) -> PackingResult:
    """Compute winding packing geometry.

    Parameters
    ----------
    turns : int
        Total number of turns.
    channel_width : float
        Internal axial width of the U-channel (metres).
        Uses insulatedD for fit; does NOT set radial depth.
    insulated_d : float
        Insulated wire OD (metres). Used for both packing and fit.

    Returns
    -------
    PackingResult
    """
    turns_per_layer = math.floor(channel_width / insulated_d)
    if turns_per_layer == 0:
        return PackingResult(
            turns_per_layer=0,
            num_layers=0,
            channel_depth=0.0,
            fits_in_channel=False,
        )
    num_layers = math.ceil(turns / turns_per_layer)
    channel_depth = num_layers * insulated_d
    return PackingResult(
        turns_per_layer=turns_per_layer,
        num_layers=num_layers,
        channel_depth=channel_depth,
        fits_in_channel=True,
    )


def wire_length(circumference: float, turns: int) -> float:
    """Total wire length in metres.

    Uses the nominal coil circumference for all turns (single-radius
    approximation — does not account for the slight radius increase in
    outer layers of a multi-layer winding).

    Parameters
    ----------
    circumference : float
        Coil circumference at the wire centreline (metres).
    turns : int
        Total number of turns.

    Returns
    -------
    float
        Wire length = circumference × turns (metres).
    """
    return circumference * turns
