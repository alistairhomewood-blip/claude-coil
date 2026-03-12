"""
FastAPI application entry point.

Phase 0: health endpoint.
Phase 1: /api/stats, /api/discretise.

Run in development:
    uvicorn api.main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from physics.discretise import discretise_coil
from physics.types import DiscretiseRequest

app = FastAPI(
    title="coil-physics",
    description="Physics and compute backend for the coil geometry tool.",
    version="0.1.0",
)

# CORS — in production, restrict origins to the hosted frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default dev port
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict:
    """Liveness check. Returns immediately with no dependencies."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Response models for /api/discretise
# ---------------------------------------------------------------------------

class Vec3Out(BaseModel):
    x: float
    y: float
    z: float


class DiscretiseResultOut(BaseModel):
    coilId: str
    filamentPaths: list[list[Vec3Out]]


@app.post("/api/discretise", response_model=list[DiscretiseResultOut])
def discretise_coils(req: DiscretiseRequest) -> list[DiscretiseResultOut]:
    """
    Discretise each coil into per-turn filament paths in global Z-up coordinates.

    Request:  { coils: CoilDef[], segmentsPerTurn?: int }
    Response: [{ coilId, filamentPaths: Vec3[][] }]

    filamentPaths is transient — not stored in project data.
    Coils with unsupported geometry (elongated_toroidal) are silently skipped.
    """
    results: list[DiscretiseResultOut] = []

    for coil in req.coils:
        try:
            res = discretise_coil(coil, req.segmentsPerTurn)
        except NotImplementedError:
            # elongated_toroidal not yet supported — skip this coil
            continue
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to discretise coil '{coil.id}': {exc}",
            ) from exc

        paths = [
            [Vec3Out(x=float(pt[0]), y=float(pt[1]), z=float(pt[2])) for pt in path]
            for path in res.filament_paths
        ]
        results.append(DiscretiseResultOut(coilId=res.coil_id, filamentPaths=paths))

    return results
