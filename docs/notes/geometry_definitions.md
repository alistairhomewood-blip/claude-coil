# Geometry Definitions

All parameters are defined at the **wire centerline**, not the outer surface of the wire.
All dimensions in **metres (m)** in physics code and project files.

---

## Universal Fields (all coil types)

| Field | Type | Definition | Unit |
|---|---|---|---|
| `center` | Vec3 | centroid of the coil in the global Z-up frame | m |
| `rotationEulerDeg` | Vec3 | ZYX Euler angles (degrees); identity = coil in XY plane, axis = +Z | deg |
| `turns` | int | total number of wire turns, summed across all layers | — |
| `current` | float | signed amperes; positive = CCW from +n̂ (right-hand rule) | A |
| `channelWidth` | float | internal width of U-channel; determines packing layout | m |

---

## Coil Type: `circular`

A planar loop. All turns lie in the plane perpendicular to n̂, centred at `center`.

| Parameter | Definition | Unit |
|---|---|---|
| `radius` | distance from `center` to the wire centerline | m |

Circumference of one turn: `C = 2 * π * radius`

---

## Coil Type: `racetrack`

Two parallel straight segments joined by two semicircular arcs. The long axis lies in the plane of the coil.

| Parameter | Definition | Unit |
|---|---|---|
| `straightLength` | length of one straight segment (total straight run = 2 × straightLength) | m |
| `arcRadius` | radius of each semicircular end | m |

Circumference of one turn: `C = 2 * π * arcRadius + 2 * straightLength`

Width of bounding box: `2 * arcRadius`
Length of bounding box: `2 * arcRadius + 2 * straightLength`

Note: `straightLength` is the half-length of each straight section as defined in the legacy code. Verify against the actual path generation when porting.

---

## Coil Type: `elliptical`

A planar elliptical loop.

| Parameter | Definition | Unit |
|---|---|---|
| `semiMajor` | semi-major axis length at wire centerline | m |
| `semiMinor` | semi-minor axis length at wire centerline | m |

Circumference of one turn: Ramanujan's approximation:
```
h = ((semiMajor - semiMinor) / (semiMajor + semiMinor))^2
C ≈ π * (semiMajor + semiMinor) * (1 + 3h / (10 + sqrt(4 - 3h)))
```
Error: < 0.04% for eccentricity e < 0.95. Degrades for e → 1. Must be tested against numeric quadrature in the regression suite.

---

## Coil Type: `toroidal`

A circular torus. The tube's centreline is a circle of radius `majorRadius` in the XY plane
(for identity rotation). The tube cross-section is a circle of radius `minorRadius`.

| Parameter | Definition | Unit |
|---|---|---|
| `majorRadius` R | distance from the torus axis (Z) to the tube centreline | m |
| `minorRadius` r | radius of the tube cross-section | m |

Constraint: `minorRadius < majorRadius`.

---

## Coil Type: `elongated_toroidal`

A racetrack-shaped torus. The tube **centreline** is a stadium (racetrack) in the XY plane
for identity rotation. The tube cross-section is a circle of radius `minorRadius`.

| Parameter | Definition | Unit |
|---|---|---|
| `majorRadius` R | radius of the semicircular ends of the racetrack centreline | m |
| `minorRadius` r | radius of the tube cross-section | m |
| `extension` E | half-length of each straight section of the racetrack centreline | m |

Racetrack centreline perimeter: `L_cl = 2π R + 4E`.

The straight sections run parallel to X, the semicircular ends are centred at (±E, 0, 0).

> **Note:** this is a racetrack-shaped centreline with a circular tube cross-section.
> This is distinct from the legacy prototype model, which used a stadium-shaped
> cross-section on a circular torus. The new interpretation is canonical.

---

## Winding mode (`winding.windingMode`) — applies to `toroidal` and `elongated_toroidal` only

`windingMode` is a field inside **`winding`** (not `geometry`).
Geometry describes the support shape; `windingMode` describes how the conductor is arranged on it.
It is required when `geometry.type` is `toroidal` or `elongated_toroidal`, and must be absent/null otherwise.

```
winding.windingMode: 'poloidal' | 'toroidal'
```

### `windingMode: 'poloidal'`

Each turn is a **small closed loop wound around the tube cross-section once**.
Turns are distributed evenly **along the torus centreline by arc length**.

For a circular torus with N turns:
- Turn k is at toroidal angle `φ_k = 2π k / N` around the torus axis.
- Turn k lies in the plane containing the torus axis (Z) and the radial
  direction `r̂_k = (cos φ_k, sin φ_k, 0)`.
- Turn k is a circle of radius `r` centred at `R r̂_k`.
- Points on turn k at poloidal angle ψ:
  ```
  p_k(ψ) = (R + r cos ψ)(cos φ_k, sin φ_k, 0) + r sin ψ (0, 0, 1)
  ```
- Loop normal for turn k (from right-hand rule applied to the parametrisation above):
  `n̂_k = (sin φ_k, −cos φ_k, 0) = −φ̂_k`
  where `φ̂_k = (−sin φ_k, cos φ_k, 0)` is the toroidal tangent direction.
  Derivation: area vector `A = (1/2)∮ r × dr = (0, −πr², 0)` for turn 0 (φ_k=0), so `n̂_0 = (0, −1, 0)`.
  Note: the outward radial `r̂_k = (cos φ_k, sin φ_k, 0)` is perpendicular to `n̂_k` and is NOT the loop normal.

For an elongated torus: turns are placed at equally-spaced arc-length positions
`s_k = k · L_cl / N` along the racetrack centreline. At each position the loop
lies in the plane perpendicular to the centreline tangent, using the Frenet frame
(see `docs/notes/toroidal_geometry.md` for the frame definition on each section).

### `windingMode: 'toroidal'`

Each turn is a **large closed loop wound once around the torus axis** (or once around
the racetrack centreline for elongated_toroidal). The N turns are distributed evenly
around the **tube cross-section** by poloidal angle.

For a circular torus with N turns:
- Turn k is at poloidal angle `ψ_k = 2π k / N` around the tube cross-section.
- Turn k is a circle in the **horizontal plane** at height `z_k = r sin ψ_k`,
  with effective radius `ρ_k = R + r cos ψ_k`.
- Points on turn k at toroidal angle φ:
  ```
  p_k(φ) = ρ_k (cos φ, sin φ, 0) + (0, 0, z_k)
  ```
- Loop normal for turn k: `n̂_k = (0, 0, 1)` (the torus axis Z — every turn
  is an azimuthal loop whose normal is the torus axis).

For an elongated torus: at each poloidal position ψ_k, the turn follows the closed
racetrack path offset by `r cos ψ_k · N_frame(s)` outward and `r sin ψ_k · Ẑ`
vertically at each arc-length position `s`.

---

## Wire length by geometry × winding mode

**Key distinction:**
- For flat-coil types (circular, racetrack, elliptical): all turns are identical; per-turn length = circumference of one turn.
- For toroidal-family with toroidal winding: per-turn length varies with poloidal angle. The total wire length must be computed as a sum over all turns, not as `circumference × N`.

### Per-turn wire length

| geometry | windingMode | Per-turn length `L_k` |
|---|---|---|
| toroidal | poloidal | `2π r` (constant for all k) |
| toroidal | toroidal | `2π (R + r cos ψ_k)` where `ψ_k = 2π k / N` |
| elongated_toroidal | poloidal | `2π r` (constant for all k) |
| elongated_toroidal | toroidal | `L_cl + 2π r cos ψ_k` where `L_cl = 2π R + 4E` |

The elongated_toroidal toroidal result follows from:
- Arcs: two arcs of π each at effective radius `R + r cos ψ_k` → contribution `2π(R + r cos ψ_k)`
- Straights: two straights of length `2E` each, offset is perpendicular to the straight direction → contribution `4E`
- Total: `2π(R + r cos ψ_k) + 4E = (2π R + 4E) + 2π r cos ψ_k = L_cl + 2π r cos ψ_k`

### Total wire length

For evenly distributed turns (`ψ_k = 2π k / N`, k = 0..N−1), the sum `Σ cos(ψ_k) = 0` exactly
(for any N ≥ 2). This cancellation makes the total exact, not just an approximation:

| geometry | windingMode | Total wire length `L_wire` | Exact? |
|---|---|---|---|
| toroidal | poloidal | `N · 2π r` | Yes (ignoring helix pitch, error < 0.3% for N ≥ 20) |
| toroidal | toroidal | `N · 2π R` | Yes (cos terms cancel exactly) |
| elongated_toroidal | poloidal | `N · 2π r` | Yes (same caveat) |
| elongated_toroidal | toroidal | `N · L_cl = N · (2π R + 4E)` | Yes (cos terms cancel exactly) |

**Proof for toroidal winding:**
`L_wire = Σ_{k=0}^{N-1} L_k = Σ [C_0 + 2π r cos(2π k/N)]`
`= N · C_0 + 2π r · Σ cos(2π k/N)`
`= N · C_0 + 2π r · 0 = N · C_0`

where `C_0 = 2π R` (circular torus) or `C_0 = L_cl` (elongated torus).

### Average per-turn length

Useful for characterising typical turn length, not for computing total:

| geometry | windingMode | Average per-turn |
|---|---|---|
| toroidal | poloidal | `2π r` |
| toroidal | toroidal | `2π R` |
| elongated_toroidal | poloidal | `2π r` |
| elongated_toroidal | toroidal | `L_cl = 2π R + 4E` |

### Implementation note

For stats computation (`compute_coil_stats`), use `total_wire_length(coil)` as a single dispatch
function. Do **not** use a single `circumference()` value multiplied by N for toroidal-winding
cases — the per-turn circumference varies and the correct total is derived from the cancellation
argument above, not from an average.

---

## Wire Parameters

Stored in `WireSpec`. Two diameters are always required and must never be conflated.

| Field | Definition | Used for |
|---|---|---|
| `bareD` | bare copper outer diameter (m) | resistance (`R = ρL/A`), mass (`m = ρ_Cu × L × A`) |
| `insulatedD` | insulated outer diameter (m) | packing geometry, U-channel fit check |
| `area` | bare copper cross-sectional area = `π * (bareD/2)^2` (m²) | resistance and mass (same as `bareD`) |

**Rule:** packing calculations use `insulatedD`. Electrical and mass calculations use `bareD` / `area`.

---

## Winding Packing Model

Turns fill the U-channel layer by layer, from the centerline outward.

- `turnsPerLayer = floor(channelWidth / insulatedD)`
- `numLayers = ceil(turns / turnsPerLayer)`
- `channelDepth = numLayers * insulatedD`
- `fitsInChannel = true` if the wire physically fits (i.e., `turnsPerLayer >= 1`)

The channel is filled from the centre of the cross-section outward, one layer at a time. The U-channel wall thickness (1 mm per the spec) does not affect the packing model but must be added to visualise the U-channel geometry.
