"""
Physical constants used throughout the physics package.

All values are in SI units.
Do not import this module from apps/web. These constants must not appear in the frontend.
"""

import math

# Permeability of free space, H/m
MU0: float = 4 * math.pi * 1e-7

# Electrical resistivity of copper at 20°C (DC), Ω·m
# Assumption: room temperature, annealed copper. No temperature dependence.
CU_RESISTIVITY: float = 1.68e-8

# Mass density of copper, kg/m³
CU_DENSITY: float = 8960.0
