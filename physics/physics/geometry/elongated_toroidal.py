"""Elongated toroidal geometry: racetrack (stadium) torus.

Support shape
-------------
The tube centreline is a racetrack (stadium) in the XY plane: two semicircles of
radius majorRadius (R) connected by two straight sections of half-length extension (E).
The tube cross-section is a circle of radius minorRadius (r). Constraint: r < R.

Racetrack centreline (CCW, Z-up):
  Start at (E, R, 0). Sections in order:
    0: top straight  (E, R, 0) → (−E, R, 0),         length 2E
    1: left arc      centre (−E, 0, 0), π/2 → 3π/2,   length π·R
    2: bottom straight (−E, −R, 0) → (E, −R, 0),      length 2E
    3: right arc     centre (E, 0, 0), −π/2 → π/2,    length π·R

Centreline perimeter: L_cl = 2·π·R + 4·E

Frenet frame at arc-length s:
  T_hat = CCW tangent
  N_frame = outward radial from local arc centre (arcs) or outward perpendicular (straights)
  B_hat = Z_hat (always, since centreline is planar)

Winding mode
------------
winding.windingMode controls how turns are wound (NOT a geometry field).

  'poloidal'
    N turns distributed evenly along the racetrack centreline by arc length.
    Turn k at arc-length position s_k = k·L_cl/N.
    Each turn is a circle of radius r perpendicular to the centreline tangent T_hat:
      p_k(ψ) = centreline(s_k) + r·cos(ψ)·N_frame(s_k) + r·sin(ψ)·Z_hat
    Loop normal = T_hat at s_k (centreline tangent).
    Per-turn length: 2·π·r (constant). Helix pitch ignored; error < 0.3% for N ≥ 20.
    Total wire: N·2·π·r.

  'toroidal'
    N turns distributed evenly around the tube cross-section by poloidal angle.
    Turn k at poloidal angle ψ_k = 2·π·k/N.
    Each turn traces the full racetrack path at fixed poloidal offset:
      p_k(s) = centreline(s) + r·cos(ψ_k)·N_frame(s) + r·sin(ψ_k)·Z_hat
    On arcs: effective arc radius = R + r·cos(ψ_k).
    On straights: radial offset = r·cos(ψ_k), vertical offset = r·sin(ψ_k).
    Per-turn length: L_cl + 2·π·r·cos(ψ_k) — varies per turn.
    Total wire: N·L_cl (exact: sum of cos(ψ_k) over N equal steps = 0).

Coordinate convention
---------------------
Z-up, right-handed. Identity torus: centreline in XY plane, tube axis = +Z.
filament_paths() returns paths in local frame (centred at origin, Z-up).
Caller applies orient() for global position/orientation.
"""

import math
import numpy as np


# ---------------------------------------------------------------------------
# Centreline helpers
# ---------------------------------------------------------------------------

def centreline_perimeter(major_radius: float, extension: float) -> float:
    """L_cl = 2·π·R + 4·E."""
    return 2.0 * math.pi * major_radius + 4.0 * extension


def _eval_centreline(
    R: float, E: float, s: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate centreline at arc-length s (scalar).

    Returns
    -------
    pos : ndarray shape (3,)
    T_hat : ndarray shape (3,)  — CCW tangent
    N_frame : ndarray shape (3,) — outward normal (from local arc centre / straight)
    """
    L_cl = centreline_perimeter(R, E)
    s = s % L_cl

    s1 = 2.0 * E
    s2 = s1 + math.pi * R
    s3 = s2 + 2.0 * E

    if s < s1:
        # Top straight
        pos = np.array([E - s, R, 0.0])
        T = np.array([-1.0, 0.0, 0.0])
        N = np.array([0.0, 1.0, 0.0])

    elif s < s2:
        # Left arc: centre (−E, 0), angle π/2 → 3π/2
        theta = math.pi / 2.0 + (s - s1) / R
        c, si = math.cos(theta), math.sin(theta)
        pos = np.array([-E + R * c, R * si, 0.0])
        T = np.array([-si, c, 0.0])
        N = np.array([c, si, 0.0])

    elif s < s3:
        # Bottom straight
        t = s - s2
        pos = np.array([-E + t, -R, 0.0])
        T = np.array([1.0, 0.0, 0.0])
        N = np.array([0.0, -1.0, 0.0])

    else:
        # Right arc: centre (E, 0), angle −π/2 → π/2
        theta = -math.pi / 2.0 + (s - s3) / R
        c, si = math.cos(theta), math.sin(theta)
        pos = np.array([E + R * c, R * si, 0.0])
        T = np.array([-si, c, 0.0])
        N = np.array([c, si, 0.0])

    return pos, T, N


def _centreline_vectorized(
    R: float, E: float, s_vals: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized centreline evaluation for an array of arc-length values.

    Parameters
    ----------
    s_vals : ndarray shape (M,)
        Arc-length positions in [0, L_cl). Must be sorted; will be wrapped.

    Returns
    -------
    pos : ndarray shape (M, 3)
    N_frame : ndarray shape (M, 3)
    """
    M = len(s_vals)
    pos = np.empty((M, 3))
    N_frame = np.empty((M, 3))

    s1 = 2.0 * E
    s2 = s1 + math.pi * R
    s3 = s2 + 2.0 * E

    # Section 0: top straight
    mask = s_vals < s1
    if mask.any():
        t = s_vals[mask]
        pos[mask, 0] = E - t
        pos[mask, 1] = R
        pos[mask, 2] = 0.0
        N_frame[mask] = [0.0, 1.0, 0.0]

    # Section 1: left arc
    mask = (s_vals >= s1) & (s_vals < s2)
    if mask.any():
        theta = math.pi / 2.0 + (s_vals[mask] - s1) / R
        c = np.cos(theta)
        si = np.sin(theta)
        pos[mask, 0] = -E + R * c
        pos[mask, 1] = R * si
        pos[mask, 2] = 0.0
        N_frame[mask, 0] = c
        N_frame[mask, 1] = si
        N_frame[mask, 2] = 0.0

    # Section 2: bottom straight
    mask = (s_vals >= s2) & (s_vals < s3)
    if mask.any():
        t = s_vals[mask] - s2
        pos[mask, 0] = -E + t
        pos[mask, 1] = -R
        pos[mask, 2] = 0.0
        N_frame[mask] = [0.0, -1.0, 0.0]

    # Section 3: right arc
    mask = s_vals >= s3
    if mask.any():
        theta = -math.pi / 2.0 + (s_vals[mask] - s3) / R
        c = np.cos(theta)
        si = np.sin(theta)
        pos[mask, 0] = E + R * c
        pos[mask, 1] = R * si
        pos[mask, 2] = 0.0
        N_frame[mask, 0] = c
        N_frame[mask, 1] = si
        N_frame[mask, 2] = 0.0

    return pos, N_frame


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def per_turn_length(
    major_radius: float,
    minor_radius: float,
    extension: float,
    winding_mode: str,
    turn_index: int,
    n_turns: int,
) -> float:
    """Exact arc length of turn k.

    Parameters
    ----------
    major_radius : float  R — racetrack arc radius, metres.
    minor_radius : float  r — tube cross-section radius, metres.
    extension : float     E — half-length of straight sections, metres.
    winding_mode : str    'poloidal' or 'toroidal'.
    turn_index : int      k in 0..n_turns-1.
    n_turns : int         Total number of turns N.

    Returns
    -------
    float
        Poloidal: 2·π·r (constant).
        Toroidal: L_cl + 2·π·r·cos(2·π·k/N) — varies per turn.
    """
    if winding_mode == "poloidal":
        return 2.0 * math.pi * minor_radius
    else:  # toroidal
        L_cl = centreline_perimeter(major_radius, extension)
        psi_k = 2.0 * math.pi * turn_index / n_turns
        return L_cl + 2.0 * math.pi * minor_radius * math.cos(psi_k)


def total_wire_length(
    major_radius: float,
    minor_radius: float,
    extension: float,
    winding_mode: str,
    n_turns: int,
) -> float:
    """Exact total conductor length.

    Parameters
    ----------
    major_radius : float  R — racetrack arc radius, metres.
    minor_radius : float  r — tube cross-section radius, metres.
    extension : float     E — half-length of straight sections, metres.
    winding_mode : str    'poloidal' or 'toroidal'.
    n_turns : int         Total number of turns N.

    Returns
    -------
    float
        Total wire length in metres.

    Notes
    -----
    Poloidal: N·2·π·r.  Helix pitch ignored; error < 0.3% for N >= 20.

    Toroidal: sum_k (L_cl + 2·π·r·cos(ψ_k)) = N·L_cl + 2·π·r·sum_k cos(ψ_k).
    For ψ_k = 2·π·k/N (k=0..N-1), sum_k cos(ψ_k) = 0 exactly (for N >= 2).
    Therefore total = N·L_cl — exact, not an approximation.
    """
    if winding_mode == "poloidal":
        return n_turns * 2.0 * math.pi * minor_radius
    else:  # toroidal
        return n_turns * centreline_perimeter(major_radius, extension)


def filament_paths(
    major_radius: float,
    minor_radius: float,
    extension: float,
    winding_mode: str,
    n_turns: int,
    n_segments: int,
) -> list[np.ndarray]:
    """Return N filament paths in local elongated-torus frame (centred at origin, Z-up).

    Caller applies orient() for global position/orientation.

    Parameters
    ----------
    major_radius : float  R — racetrack arc radius, metres.
    minor_radius : float  r — tube cross-section radius, metres.
    extension : float     E — half-length of straight sections, metres.
    winding_mode : str    'poloidal' or 'toroidal'.
    n_turns : int         Number of filament paths N (one per turn).
    n_segments : int      Number of vertices per closed path.

    Returns
    -------
    list of ndarray, each shape (n_segments, 3)
        Points in local frame, metres.
    """
    R = major_radius
    r = minor_radius
    E = extension
    L_cl = centreline_perimeter(R, E)
    paths: list[np.ndarray] = []

    if winding_mode == "poloidal":
        # Turn k: small circle of radius r at arc-length position s_k.
        # p_k(ψ) = centreline(s_k) + r·cos(ψ)·N_frame + r·sin(ψ)·Z_hat
        psi = np.linspace(0.0, 2.0 * math.pi, n_segments, endpoint=False)
        cos_psi = np.cos(psi)
        sin_psi = np.sin(psi)
        for k in range(n_turns):
            s_k = k * L_cl / n_turns
            pos, _T, N = _eval_centreline(R, E, s_k)
            x = pos[0] + r * cos_psi * N[0]
            y = pos[1] + r * cos_psi * N[1]
            z = pos[2] + r * sin_psi          # Z_hat = (0, 0, 1)
            paths.append(np.column_stack([x, y, z]))

    else:  # toroidal
        # Turn k: full racetrack loop at fixed poloidal offset ψ_k.
        # p_k(s) = centreline(s) + r·cos(ψ_k)·N_frame(s) + r·sin(ψ_k)·Z_hat
        s_vals = np.linspace(0.0, L_cl, n_segments, endpoint=False)
        cl_pos, cl_N = _centreline_vectorized(R, E, s_vals)
        for k in range(n_turns):
            psi_k = 2.0 * math.pi * k / n_turns
            cos_k = math.cos(psi_k)
            sin_k = math.sin(psi_k)
            path = cl_pos + r * cos_k * cl_N
            path = path.copy()
            path[:, 2] += r * sin_k
            paths.append(path)

    return paths
