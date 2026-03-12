# Current Direction Convention

## Convention

`current` is a **signed scalar in amperes (A)**.

**Positive current** flows counter-clockwise (CCW) when viewed from the **+n̂ direction**, where n̂ is the coil axis derived from `rotationEulerDeg`.

This is the standard right-hand rule: curl the right hand in the direction of current flow; the thumb points along the direction of the magnetic field at the coil center.

For a coil with identity rotation (`rotationEulerDeg = {0,0,0}`):
- n̂ = +Z
- Positive current flows CCW when viewed from above (+Z looking down)
- The B field at the coil center points in the +Z direction

---

## What `current` Controls

| `current` | Effect |
|---|---|
| `+5.0` | Current CCW from +n̂; B field along +n̂ at center |
| `-5.0` | Current CW from +n̂; B field along -n̂ at center |

To reverse the field direction of a coil: **negate `current`**.

Do **not** flip `rotationEulerDeg` to reverse the field. `rotationEulerDeg` is a geometric property describing how the coil is oriented in space, not a field-direction control.

---

## Storage

`current` is stored directly in `winding.current` in the `CoilDef` schema.

`n̂` is **never stored** in project data. It is a derived quantity computed in `/physics` from `rotationEulerDeg`.

---

## Biot–Savart Integration Direction

The Biot–Savart kernel integrates along the wire path in the direction of current flow.

For positive `current`, the integration proceeds in the CCW direction when the coil is viewed from +n̂.

The sign of `current` directly multiplies the magnetic field contribution: `dB ∝ current · (dl × r̂) / |r|²`.

---

## Multi-Coil Configurations

For Helmholtz coils (field addition): both coils have `current > 0` and normals pointing in the same direction.

For anti-Helmholtz coils (gradient coils): one coil has `current > 0`, the other has `current < 0` (with normals pointing in the same direction).

Never achieve this by flipping normals — always achieve it by negating `current`.

---

## Toroidal Windings

Each individual turn of a toroidal winding has its own local axis direction, derived from its position on the toroidal path. The same sign convention applies: positive current = CCW when viewed from the local loop's +n̂.

The global `current` in `WindingSpec` applies uniformly to all turns. Its sign determines whether the toroidal field is clockwise or counter-clockwise when viewed from the top (+Z for identity rotation).
