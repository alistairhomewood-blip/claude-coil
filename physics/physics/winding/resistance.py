"""DC resistance of a copper winding.

Formula: R = ρ × L / A

where:
    ρ = CU_RESISTIVITY = 1.68×10⁻⁸ Ω·m  (copper, 20 °C, DC)
    L = total wire length (metres)
    A = bare copper cross-section (m²)  — NOT the insulated OD

Assumptions:
    - Uniform copper conductor at 20 °C.
    - Bare copper area (wire.area = π(bareD/2)²) is used, never insulatedD.
    - Skin effect and proximity effect are neglected (DC model only).
"""

from physics.constants import CU_RESISTIVITY


def compute_resistance(wire_length: float, bare_area: float) -> float:
    """Return DC resistance in ohms.

    Parameters
    ----------
    wire_length : float
        Total wire length (metres).
    bare_area : float
        Bare copper cross-sectional area (m²). Use wire.area, not insulatedD.

    Returns
    -------
    float
        DC resistance (ohms).
    """
    return CU_RESISTIVITY * wire_length / bare_area
