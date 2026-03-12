"""
AWG enamelled copper wire data.

Two diameters per gauge — never conflate them:
  bare_d      → electrical (resistance, mass): R = ρL/A, m = ρ_Cu × L × A
  insulated_d → mechanical (packing, U-channel fit)

WARNING: insulated_d values are approximate class-1 enamel estimates.
They must be verified against IEC 60317-0-1 or manufacturer datasheets
before being used in fit/packing calculations.

Source for bare_d: IEC 60317 / NEMA MW1000 nominal AWG diameters.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class WireData:
    awg: int
    bare_d: float        # m — bare copper OD
    insulated_d: float   # m — insulated OD (class-1 enamel, approx) ⚠️ verify
    area: float          # m² — bare copper cross-section = π*(bare_d/2)²

    @staticmethod
    def from_bare_d(awg: int, bare_d_mm: float, insulated_d_mm: float) -> "WireData":
        bare_d = bare_d_mm * 1e-3
        insulated_d = insulated_d_mm * 1e-3
        area = math.pi * (bare_d / 2) ** 2
        return WireData(awg=awg, bare_d=bare_d, insulated_d=insulated_d, area=area)


# fmt: off
# AWG table. insulated_d marked ⚠️ as approximate — must be verified.
_TABLE_RAW: list[tuple[int, float, float]] = [
    # (awg, bare_d_mm, insulated_d_mm)
    (4,  5.189, 5.31),   # ⚠️ insulated approx
    (6,  4.115, 4.22),   # ⚠️
    (8,  3.264, 3.35),   # ⚠️
    (10, 2.588, 2.66),   # ⚠️
    (12, 2.053, 2.11),   # ⚠️
    (14, 1.628, 1.68),   # ⚠️
    (16, 1.291, 1.34),   # ⚠️
    (18, 1.024, 1.07),   # ⚠️
    (20, 0.8128, 0.853), # ⚠️
    (22, 0.6438, 0.678), # ⚠️
    (24, 0.5106, 0.541), # ⚠️
    (26, 0.4049, 0.432), # ⚠️
    (28, 0.3211, 0.343), # ⚠️
    (30, 0.2546, 0.274), # ⚠️
    (32, 0.2019, 0.218), # ⚠️
]
# fmt: on

AWG_TABLE: dict[int, WireData] = {
    awg: WireData.from_bare_d(awg, bare_mm, ins_mm)
    for awg, bare_mm, ins_mm in _TABLE_RAW
}


def get_wire(awg: int) -> WireData:
    """Return wire data for a standard AWG gauge. Raises KeyError if not found."""
    if awg not in AWG_TABLE:
        supported = sorted(AWG_TABLE.keys())
        raise KeyError(f"AWG {awg} not in wire table. Supported: {supported}")
    return AWG_TABLE[awg]
