# Coordinate System Convention

## Global Frame

**Right-handed XYZ, Z-up.**

```
        Z (up)
        |
        |
        +------Y
       /
      X
```

- X: right
- Y: forward (into screen / depth axis)
- Z: up

Origin: `(0, 0, 0)` — global. All coil positions are relative to this origin.

---

## Identity Coil Orientation

A coil with `rotationEulerDeg = {x: 0, y: 0, z: 0}`:
- lies in the **XY plane**
- its axis (the direction of the magnetic field at its center for positive current) points along **+Z**

---

## Euler Angle Convention

Orientation is stored as `rotationEulerDeg: Vec3` — ZYX intrinsic Euler angles in **degrees**.

ZYX order means: first rotate around Z, then around the new Y, then around the new X.

The coil normal is derived in physics code only:
```
n̂ = R_ZYX(rotZ, rotY, rotX) · [0, 0, 1]
```

`n̂` is **never stored** in project data. It is computed at runtime in `/physics` as needed.

---

## Units

- All positions: **metres (m)** in physics code and project files
- All angles: **degrees** in project files and UI; **radians** in all Python physics code (convert at the API boundary)

---

## Three.js Rendering

Three.js uses Y-up by default. The adapter in `apps/web/src/adapters/physics_to_threejs.ts` is the **only** place the Y↔Z swap occurs.

When passing a physics Vec3 `{x, y, z}` to Three.js, the adapter produces `new THREE.Vector3(x, z, y)`.

**No other file in `apps/web` may perform this conversion.**

---

## Assumptions Stated Explicitly

- There is no per-coil local coordinate frame stored separately. The global frame is the only frame.
- Rotation is applied to the coil geometry at the global origin, not about the coil center. The coil center is specified separately via `center: Vec3`.
- Sign convention for rotations: positive angle = counter-clockwise when viewed from the positive axis end (standard right-hand rule for rotations).
