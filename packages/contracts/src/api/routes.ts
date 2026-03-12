/**
 * Typed API route definitions.
 * All routes accept and return JSON unless noted.
 * Base URL is configured per environment (e.g. http://localhost:8000 in dev).
 *
 * Request/response types are defined in ../types/.
 * The frontend must use these constants and never hardcode route strings.
 */
export const API_ROUTES = {
  /** GET /api/health — liveness check. Returns { status: 'ok' }. */
  health: { method: 'GET', path: '/api/health' },

  /**
   * POST /api/stats
   * Request:  { coils: CoilDef[] }
   * Response: { perCoil: CoilStats[], totalWireLength, totalWireMass, totalPower }
   * Computes electrical and packing stats for the given coils.
   * Does not require filament paths.
   */
  computeStats: { method: 'POST', path: '/api/stats' },

  /**
   * POST /api/discretise
   * Request:  { coils: CoilDef[], segmentsPerTurn?: number }
   * Response: DiscretiseResult[]
   * Discretises each coil into per-turn filament paths.
   * Result is transient — not stored in the project file.
   */
  discretise: { method: 'POST', path: '/api/discretise' },

  /**
   * POST /api/bfield/slice
   * Request:  BFieldSliceRequest (coilIds must be discretised on the backend)
   * Response: BFieldSliceResult
   * Long-running. Computed from filament paths only (no approximations).
   */
  bFieldSlice: { method: 'POST', path: '/api/bfield/slice' },

  /**
   * POST /api/project/save
   * Request:  ProjectFile (JSON body)
   * Response: binary HDF5 blob (Content-Type: application/x-hdf5)
   * Serialises the project to HDF5 format for download.
   */
  saveProject: { method: 'POST', path: '/api/project/save' },

  /**
   * POST /api/project/load
   * Request:  multipart/form-data with field 'file' (HDF5 blob)
   * Response: ProjectFile (JSON)
   * Parses an HDF5 project file and returns the ProjectFile schema.
   * Validates schema version and emits warnings for outdated files.
   */
  loadProject: { method: 'POST', path: '/api/project/load' },

  /**
   * POST /api/export/step
   * Request:  ProjectFile (JSON body)
   * Response: binary STEP blob (Content-Type: application/step)
   * Generates a STEP file from the coil geometry.
   * STEP is export-only; it is never the source of truth.
   */
  exportStep: { method: 'POST', path: '/api/export/step' },
} as const;

export type ApiRouteName = keyof typeof API_ROUTES;
