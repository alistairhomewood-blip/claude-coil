import math

import numpy as np


def path_length(path: np.ndarray) -> float:
    """Return total length of a closed polygonal path.

    Parameters
    ----------
    path : ndarray, shape (N, 3)
        N distinct points. The path is treated as a closed loop:
        the segment from path[-1] back to path[0] is included.

    Returns
    -------
    float
        Total perimeter length (metres, or whatever units path is in).
    """
    segments = np.roll(path, -1, axis=0) - path  # shape (N, 3)
    return float(np.sum(np.linalg.norm(segments, axis=1)))


def orient(
    path: np.ndarray,
    center_xyz: tuple[float, float, float],
    rotation_deg: tuple[float, float, float],
) -> np.ndarray:
    """Transform a local coil path into global coordinates.

    Applies ZYX intrinsic Euler rotation followed by translation.

    Convention (matches types.py::coil_normal and docs/notes/coordinate_system.md):
        R = Rz(rz) @ Ry(ry) @ Rx(rx)   (ZYX intrinsic = extrinsic XYZ)
        global_point = R @ local_point + center

    Identity rotation (all angles = 0) leaves the path unchanged before
    adding the center offset, so a coil at (0,0,0) with zero rotation maps
    its XY-plane base_path directly to global XY.

    Parameters
    ----------
    path : ndarray, shape (N, 3)
        Points in local coil coordinates (XY plane, z=0, centred at origin).
    center_xyz : (cx, cy, cz)
        Global position of the coil centre (metres).
    rotation_deg : (rx_deg, ry_deg, rz_deg)
        ZYX Euler angles in degrees (X rotation applied first).

    Returns
    -------
    ndarray, shape (N, 3)
        Points in global coordinates (metres).
    """
    rx = math.radians(rotation_deg[0])
    ry = math.radians(rotation_deg[1])
    rz = math.radians(rotation_deg[2])

    cx, cy, cz = math.cos(rx), math.cos(ry), math.cos(rz)
    sx, sy, sz = math.sin(rx), math.sin(ry), math.sin(rz)

    # Rotation matrices
    Rx = np.array([[1, 0,   0  ],
                   [0, cx, -sx ],
                   [0, sx,  cx ]], dtype=float)
    Ry = np.array([[ cy, 0, sy ],
                   [  0, 1,  0 ],
                   [-sy, 0, cy ]], dtype=float)
    Rz = np.array([[cz, -sz, 0],
                   [sz,  cz, 0],
                   [ 0,   0, 1]], dtype=float)

    R = Rz @ Ry @ Rx  # ZYX intrinsic

    # Apply rotation then translation:  global = (R @ local.T).T + center
    rotated = path @ R.T
    center = np.array(center_xyz, dtype=float)
    return rotated + center
