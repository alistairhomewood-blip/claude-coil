"""Toroidal geometry: circular torus.

Support shape
-------------
The tube centreline is a circle of radius majorRadius (R) in the XY plane
(for identity rotation). The tube cross-section is a circle of radius
minorRadius (r). Constraint: r < R.

Winding mode
------------
winding.windingMode controls how turns are distributed (NOT a geometry field).

  'poloidal'
    N turns distributed evenly along the torus centreline by toroidal angle.
    Turn k at toroidal angle phi_k = 2*pi*k/N.
    Each turn is a circle of radius r in the plane containing Z and r_hat_k.
    Parametrisation: p_k(psi) = (R + r cos psi) r_hat_k + r sin psi z_hat
      where r_hat_k = (cos phi_k, sin phi_k, 0).
    Loop normal (right-hand rule):  n_hat_k = (sin phi_k, -cos phi_k, 0)
      = -phi_hat_k (opposite to toroidal tangent direction).
    Per-turn length: 2*pi*r (constant for all k).
    Total wire:      N * 2*pi*r.

  'toroidal'
    N turns distributed evenly around the tube cross-section by poloidal angle.
    Turn k at poloidal angle psi_k = 2*pi*k/N.
    Each turn is a horizontal circle:
      height z_k = r sin psi_k
      radius rho_k = R + r cos psi_k
    Parametrisation: p_k(phi) = rho_k (cos phi, sin phi, 0) + (0, 0, z_k)
    Loop normal: (0, 0, 1) for all turns (azimuthal loop, normal = torus axis).
    Per-turn length: 2*pi*rho_k = 2*pi*(R + r cos psi_k) — varies per turn.
    Total wire:      N * 2*pi*R  (exact: sum of cos(psi_k) over N equal steps = 0).

Coordinate convention
---------------------
Z-up, right-handed. Identity torus: centreline in XY plane, axis = +Z.
filament_paths() returns paths in local torus frame (centred at origin, Z-up).
Caller applies orient() for global position/orientation.
"""

import math

import numpy as np


def per_turn_length(
    major_radius: float,
    minor_radius: float,
    winding_mode: str,
    turn_index: int,
    n_turns: int,
) -> float:
    """Exact arc length of turn k.

    Parameters
    ----------
    major_radius : float
        R — torus axis to tube centreline, metres.
    minor_radius : float
        r — tube cross-section radius, metres.
    winding_mode : str
        'poloidal' or 'toroidal'.
    turn_index : int
        k in 0..n_turns-1.
    n_turns : int
        Total number of turns N.

    Returns
    -------
    float
        Arc length in metres.
        Poloidal: 2*pi*r (constant).
        Toroidal: 2*pi*(R + r*cos(2*pi*k/N)) — varies.
    """
    if winding_mode == "poloidal":
        return 2.0 * math.pi * minor_radius
    else:  # toroidal
        psi_k = 2.0 * math.pi * turn_index / n_turns
        rho_k = major_radius + minor_radius * math.cos(psi_k)
        return 2.0 * math.pi * rho_k


def total_wire_length(
    major_radius: float,
    minor_radius: float,
    winding_mode: str,
    n_turns: int,
) -> float:
    """Exact total conductor length.

    Parameters
    ----------
    major_radius : float
        R — torus axis to tube centreline, metres.
    minor_radius : float
        r — tube cross-section radius, metres.
    winding_mode : str
        'poloidal' or 'toroidal'.
    n_turns : int
        Total number of turns N.

    Returns
    -------
    float
        Total wire length in metres.

    Notes
    -----
    Poloidal: N * 2*pi*r.  Helix-pitch ignored; error < 0.3% for N >= 20.

    Toroidal: sum_k 2*pi*(R + r*cos(psi_k)) = N*2*pi*R + 2*pi*r*sum_k cos(psi_k).
    For psi_k = 2*pi*k/N (k=0..N-1), sum_k cos(psi_k) = 0 exactly (for N >= 2).
    Therefore total = N * 2*pi*R  — exact, not an approximation.
    """
    if winding_mode == "poloidal":
        return n_turns * 2.0 * math.pi * minor_radius
    else:  # toroidal
        return n_turns * 2.0 * math.pi * major_radius


def filament_paths(
    major_radius: float,
    minor_radius: float,
    winding_mode: str,
    n_turns: int,
    n_segments: int,
) -> list[np.ndarray]:
    """Return N filament paths in local torus frame (centred at origin, Z-up).

    Caller applies orient() for global position/orientation.

    Parameters
    ----------
    major_radius : float
        R — torus axis to tube centreline, metres.
    minor_radius : float
        r — tube cross-section radius, metres.
    winding_mode : str
        'poloidal' or 'toroidal'.
    n_turns : int
        Number of filament paths N (one per turn).
    n_segments : int
        Number of vertices per closed path (polygon approximation).

    Returns
    -------
    list of ndarray, each shape (n_segments, 3)
        Points in local torus frame, metres.
    """
    R = major_radius
    r = minor_radius
    angle = np.linspace(0.0, 2.0 * math.pi, n_segments, endpoint=False)
    paths: list[np.ndarray] = []

    if winding_mode == "poloidal":
        # Turn k: circle of radius r in the plane containing Z and r_hat_k.
        # p_k(psi) = (R + r cos psi) r_hat_k + r sin psi z_hat
        cos_psi = np.cos(angle)
        sin_psi = np.sin(angle)
        for k in range(n_turns):
            phi_k = 2.0 * math.pi * k / n_turns
            cos_phi = math.cos(phi_k)
            sin_phi = math.sin(phi_k)
            radial = R + r * cos_psi   # (n_segments,)
            x = radial * cos_phi
            y = radial * sin_phi
            z = r * sin_psi
            paths.append(np.column_stack([x, y, z]))

    else:  # toroidal
        # Turn k: horizontal circle at height z_k, radius rho_k.
        # p_k(phi) = rho_k (cos phi, sin phi, 0) + (0, 0, z_k)
        cos_phi = np.cos(angle)
        sin_phi = np.sin(angle)
        for k in range(n_turns):
            psi_k = 2.0 * math.pi * k / n_turns
            rho_k = R + r * math.cos(psi_k)
            z_k = r * math.sin(psi_k)
            x = rho_k * cos_phi
            y = rho_k * sin_phi
            z = np.full(n_segments, z_k)
            paths.append(np.column_stack([x, y, z]))

    return paths
