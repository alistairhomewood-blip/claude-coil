# Toroidal and Elongated-Toroidal Geometry

## Scope

This note records the design decisions for `physics/geometry/toroidal.py` and
`physics/geometry/elongated_toroidal.py`. It supersedes the legacy prototype model.

---

## Geometry definitions

### Toroidal (`type: "toroidal"`)

| Parameter | Meaning |
|---|---|
| `majorRadius` R | Distance from the torus axis (Z) to the centre of each winding loop |
| `minorRadius` r | Radius of each individual winding loop (tube cross-section) |

The torus axis is **Z** for identity rotation (`rotationEulerDeg = (0,0,0)`).

### Elongated toroidal (`type: "elongated_toroidal"`)

| Parameter | Meaning |
|---|---|
| `majorRadius` R | Arc radius of the two **semicircular ends** of the racetrack centreline |
| `minorRadius` r | Radius of each winding loop (tube cross-section) |
| `extension` E | Half-length of each straight section of the racetrack centreline |

The racetrack **centreline** lies in the **XY plane** for identity rotation.
The straight sections are parallel to the X axis, the semicircular ends are
centred at (±E, 0, 0). Total centreline perimeter = 2πR + 4E.

> **This differs from the legacy prototype.**
> The legacy code used a horizontal-ring model where each turn is a full
> azimuthal circle at a (radius, height) position derived from a stadium-shaped
> *tube cross-section*. The new model treats the *centreline* as a racetrack and
> the tube cross-section as circular.

---

## Physical model: poloidal loops

Each turn of the winding is a **poloidal loop** — a small circle of radius
`minorRadius` wound around the torus tube once. The turns are equally spaced
around the torus centreline (by arc length).

**Why not horizontal rings (legacy model)?**
The legacy model generates each turn as a horizontal azimuthal ring. This gives:
- Wire length ≈ N × 2πR (wrong — uses major circumference)
- Physically incorrect current path for close-range B-field computation

The poloidal loop model gives:
- Wire length = N × 2πr (correct physical wire length)
- Correct current path for Biot-Savart integration

---

## Circumference convention

`circumference()` returns the **per-turn wire length** (one poloidal loop):

```
circumference = 2π × minorRadius
```

**Approximation**: this ignores the helical pitch — the small advance in the
toroidal direction per turn. The true per-turn length is:

```
L_turn = 2πr × √(1 + (R_eff / (r × N))²)
```

where R_eff is the local centreline radius. The helix-pitch correction is
< 0.3 % for N ≥ 20 and r/R ≤ 0.5, so it is neglected.

---

## `base_path()` — contract deviation

For all other geometry types, `base_path()` returns points in the **XY plane,
z = 0, centred at the origin**. Toroidal and elongated-toroidal break this
contract because each turn is at a different position in 3D space.

Instead, `base_path()` returns the **canonical poloidal loop** — the single turn
at the "zero" angular position:

| Type | Loop position | Loop plane |
|---|---|---|
| toroidal | φ = 0 (rightmost, along +X) | XZ plane (y = 0) |
| elongated_toroidal | arc-length s = 0 (right end of top straight) | YZ plane at x = +E |

`path_length(base_path(...))` ≈ `circumference(...)` for both types.

For the full N-turn discretisation, `discretise_coil()` generates N separate
poloidal loops:
- **Toroidal**: loop k is rotated by 2πk/N around Z from the canonical loop.
- **Elongated toroidal**: loop k is placed at arc-length position s_k = k × L/N
  along the racetrack centreline, using the Frenet frame at that point.

---

## Elongated-toroidal Frenet frame

The centreline is a **planar** racetrack in XY. The Frenet-Serret frame is:

- **T** (tangent): tangent to the centreline, in XY plane
- **N** (principal normal): centripetal direction for arc sections; resolved by
  **parallel transport** for straight sections (N is constant along a straight,
  equal to its value at the adjacent arc junction)
- **B** = T × N = **(0, 0, 1)** everywhere (planar curve, CCW traversal)

For a CCW-traversed racetrack:

| Section | T | N (centripetal) | B |
|---|---|---|---|
| Top straight (right→left) | (-1, 0, 0) | (0, -1, 0) | (0, 0, 1) |
| Left arc | (-sin α, cos α, 0) | (-cos α, -sin α, 0) | (0, 0, 1) |
| Bottom straight (left→right) | (1, 0, 0) | (0, 1, 0) | (0, 0, 1) |
| Right arc | (-sin α, cos α, 0) | (-cos α, -sin α, 0) | (0, 0, 1) |

Poloidal loop at centreline point (x_c, y_c, 0) with frame (N_x, N_y):

```
p(ψ) = (x_c + r cos(ψ) N_x,  y_c + r cos(ψ) N_y,  r sin(ψ))
```

This is fully analytical; no numerical integration required.

---

## Sign convention for poloidal loops

Positive current (CCW from +n̂ by right-hand rule) in each poloidal loop
should produce a B field in the **+φ direction** (azimuthal, CCW from +Z) inside
the torus. The canonical loop at φ=0 traverses CCW when viewed from +Y
(= the +φ direction at φ=0). Confirmed by: signed area in the XZ plane > 0
for increasing ψ ∈ [0, 2π).
