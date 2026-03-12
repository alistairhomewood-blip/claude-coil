"""Copper wire mass of a winding.

Formula: m = ρ_Cu × L × A

where:
    ρ_Cu = CU_DENSITY = 8960 kg/m³  (copper)
    L    = total wire length (metres)
    A    = bare copper cross-section (m²)  — NOT the insulated OD

Assumptions:
    - Insulation mass is neglected (bare copper only).
    - Bare copper area (wire.area = π(bareD/2)²) is used, never insulatedD.
"""

from physics.constants import CU_DENSITY


def compute_mass(wire_length: float, bare_area: float) -> float:
    """Return copper wire mass in kg.

    Parameters
    ----------
    wire_length : float
        Total wire length (metres).
    bare_area : float
        Bare copper cross-sectional area (m²). Use wire.area, not insulatedD.

    Returns
    -------
    float
        Wire mass (kg).
    """
    return CU_DENSITY * wire_length * bare_area
