import type { Vec3 } from './coil.js';

export type { Vec3 };

/**
 * Request for a 2D B-field slice computation.
 * The backend computes the field from discretised filament paths only.
 * No approximations (no dipole, no on-axis formulas).
 *
 * All coordinates in the global Z-up frame, metres.
 *
 * Mirrors b_field_slice_request.schema.json.
 */
export interface BFieldSliceRequest {
  /**
   * Coil IDs to include. Empty array = include all coils.
   * Coils must have been discretised (filamentPaths available on the backend).
   */
  coilIds: string[];
  /** Z height of the slice plane, metres. */
  sliceZ: number;
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
  /**
   * Number of grid points along each axis.
   * Total field evaluations = resolution × resolution.
   * Range: 2–2048.
   */
  resolution: number;
}

/**
 * Result of a 2D B-field slice computation.
 * All field values in tesla.
 * Array indexing: [xIndex][yIndex].
 *
 * Mirrors b_field_slice_result.schema.json.
 */
export interface BFieldSliceResult {
  /** The Z height at which the slice was computed, metres. */
  sliceZ: number;
  /** X coordinates of the grid, metres. Length = resolution. */
  xGrid: number[];
  /** Y coordinates of the grid, metres. Length = resolution. */
  yGrid: number[];
  /** B_x component, tesla. Shape: [resolution][resolution]. */
  Bx: number[][];
  /** B_y component, tesla. Shape: [resolution][resolution]. */
  By: number[][];
  /** B_z component, tesla. Shape: [resolution][resolution]. */
  Bz: number[][];
  /** |B| magnitude, tesla. Shape: [resolution][resolution]. = sqrt(Bx²+By²+Bz²). */
  Bmag: number[][];
}

/**
 * Transient response from POST /api/discretise.
 * Not stored in the project file. Used by the backend to compute Biot–Savart.
 */
export interface DiscretiseResult {
  coilId: string;
  /**
   * Per-turn wire paths in the global Z-up frame, metres.
   * Outer array: one entry per turn. Inner array: points along that turn's path.
   */
  filamentPaths: Vec3[][];
}
