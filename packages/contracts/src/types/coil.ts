import type { WireSpec } from './wire.js';

/**
 * 3-component vector. All physics coordinates are Z-up.
 * When passing to Three.js (Y-up), use the adapter in apps/web/src/adapters/.
 */
export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

// ---------------------------------------------------------------------------
// Geometry — geometry.type is the sole coil-type discriminator.
// No top-level type field on CoilDef.
// ---------------------------------------------------------------------------

export interface CircularGeometry {
  type: 'circular';
  /** Distance from center to wire centerline, metres. Circumference = 2πr. */
  radius: number;
}

export interface RacetrackGeometry {
  type: 'racetrack';
  /** Length of one straight segment, metres. Circumference = 2πr + 2L. */
  straightLength: number;
  /** Radius of the semicircular ends, metres. */
  arcRadius: number;
}

export interface EllipticalGeometry {
  type: 'elliptical';
  /** Semi-major axis at wire centerline, metres. */
  semiMajor: number;
  /** Semi-minor axis at wire centerline, metres. Must be ≤ semiMajor. */
  semiMinor: number;
}

/**
 * How turns are arranged on the torus surface. Only applies to toroidal-family geometries.
 *
 * 'poloidal' — each turn is a small loop around the tube cross-section;
 *   turns distributed evenly along the torus centreline by arc length.
 *   Per-turn wire length ≈ 2π × minorRadius.
 *
 * 'toroidal' — each turn is a large loop around the torus axis / centreline;
 *   turns distributed evenly around the tube cross-section by poloidal angle.
 *   Per-turn wire length ≈ 2π × majorRadius (circular) or 2π×R + 4E (elongated).
 */
export type WindingMode = 'poloidal' | 'toroidal';

export interface ToroidalGeometry {
  type: 'toroidal';
  /** Distance from the torus axis (Z) to the tube centreline, metres. Must be > minorRadius. */
  majorRadius: number;
  /** Radius of the tube cross-section, metres. Must be < majorRadius. */
  minorRadius: number;
}

export interface ElongatedToroidalGeometry {
  type: 'elongated_toroidal';
  /** Radius of the semicircular ends of the racetrack centreline, metres. */
  majorRadius: number;
  /** Radius of the tube cross-section, metres. */
  minorRadius: number;
  /** Half-length of each straight section of the racetrack centreline, metres. */
  extension: number;
}

export type CoilGeometry =
  | CircularGeometry
  | RacetrackGeometry
  | EllipticalGeometry
  | ToroidalGeometry
  | ElongatedToroidalGeometry;

export type CoilType = CoilGeometry['type'];

// ---------------------------------------------------------------------------
// Winding
// ---------------------------------------------------------------------------

export interface WindingSpec {
  /** Total number of wire turns, summed across all layers. */
  turns: number;
  /**
   * Signed amperes. Positive = CCW from +n̂ (right-hand rule).
   * To reverse field direction: negate current. Do not flip rotationEulerDeg.
   * n̂ is derived from rotationEulerDeg in physics code — it is never stored.
   */
  current: number;
  wire: WireSpec;
  /** Internal width of the U-channel, metres. Packing uses wire.insulatedD against this. */
  channelWidth: number;
  /**
   * Required when geometry.type is 'toroidal' or 'elongated_toroidal'.
   * Must be null or absent for all other geometry types.
   * See WindingMode for definition.
   */
  windingMode?: WindingMode | null;
}

// ---------------------------------------------------------------------------
// CoilDef — the canonical coil representation
// ---------------------------------------------------------------------------

export interface CoilDef {
  /** Unique coil identifier (UUID). */
  id: string;
  /** Group ID, or null if not in a group. */
  groupId: string | null;
  /** User-editable display name. */
  name: string;
  /** CSS hex colour (e.g. '#ff6600'), or null to use the default. */
  colour: string | null;
  /** Optional user notes. */
  notes: string | null;
  /** When true, the coil cannot be edited until explicitly unlocked. */
  locked: boolean;

  /**
   * Centroid of the coil in the global Z-up frame, metres.
   * The coil geometry is centred here after rotation is applied.
   */
  center: Vec3;

  /**
   * ZYX intrinsic Euler angles in degrees.
   * Identity (0,0,0) = coil lies in XY plane, axis = +Z.
   * The coil normal n̂ = R_ZYX(rotZ, rotY, rotX) · [0,0,1].
   * n̂ is computed only in physics code. It is never stored in project data.
   */
  rotationEulerDeg: Vec3;

  /**
   * Type-discriminated geometry parameters.
   * geometry.type is the sole discriminator for the coil shape.
   */
  geometry: CoilGeometry;

  winding: WindingSpec;
}
