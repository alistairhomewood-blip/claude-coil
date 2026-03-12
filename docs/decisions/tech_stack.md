# Tech Stack Decision

**Date:** 2026-03-11
**Status:** Decided

---

## Decision

- **Backend / Physics:** Python (FastAPI + uvicorn)
- **Frontend / UI:** TypeScript + React (Vite)
- **Shared contracts:** `/packages/contracts` — JSON Schema files (primary) + TypeScript mirror types
- **File I/O:** h5py (HDF5), pythonOCC (STEP) — both backend-only
- **Coordinate system:** Right-handed XYZ, Z-up (see `docs/notes/coordinate_system.md`)

---

## Architecture

```
/packages/contracts     JSON Schema + TypeScript types (shared boundary)
        ↑                         ↑
/physics (Python)        /apps/web (TypeScript/React)
FastAPI backend          Vite + React frontend
All physics formulas     3D viewport (Three.js)
HDF5, STEP I/O           No physics formulas
```

Communication: HTTP JSON API. Routes are defined in `packages/contracts/src/api/routes.ts`.

---

## Rationale

- Python chosen for physics: NumPy vectorisation for Biot–Savart, h5py for HDF5, pythonOCC for STEP.
- TypeScript chosen for frontend: strong typing, Three.js ecosystem.
- JSON Schema chosen as the boundary: language-agnostic, can be validated in both Python (Pydantic) and TypeScript.
- Contracts package prevents physics logic from leaking into the frontend.

---

## Constraints

- `/apps/web` must never import from `/physics` directly.
- `/apps/web` may only import from `/packages/contracts`.
- `/physics` validates inbound requests using its Pydantic models (which mirror the contracts schemas).
- Three.js uses Y-up internally; the adapter in `apps/web/src/adapters/` is the **only** place Y↔Z conversion occurs.
- All physics code uses SI units internally (metres, amperes, tesla).
- Display units (m or cm) are a frontend / project-file concern, not a physics concern.
