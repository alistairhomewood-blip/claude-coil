import type { CoilDef } from './coil.js';

/**
 * Display unit system. Physics is always SI (metres, amperes, tesla) internally.
 * This is a UI preference stored once per project.
 */
export type UnitSystem = 'm' | 'cm';

/**
 * A flat group of coils. No nested groups.
 * A coil can belong to at most one group at a time.
 * Group transforms use the group centroid as the pivot.
 *
 * Mirrors group_def.schema.json.
 */
export interface GroupDef {
  id: string;
  name: string;
  /** Ordered list of coil IDs in this group. */
  coilIds: string[];
  /** When true, all coils in the group are locked. */
  locked: boolean;
}

/**
 * The canonical project master file.
 * Saved to HDF5. Re-imported with no data loss.
 * The source of truth is always this file, never the STEP export.
 *
 * Mirrors project_file.schema.json.
 */
export interface ProjectFile {
  /** Semver string for this schema version. */
  schemaVersion: string;
  /** Version of the application that wrote this file. */
  appVersion: string;
  /** ISO 8601 UTC timestamp of the last save. */
  exportTimestamp: string;
  projectName: string;
  creatorMetadata: Record<string, unknown> | null;
  /** UI display preference. Does not affect physics calculations. */
  displayUnits: UnitSystem;
  coils: CoilDef[];
  groups: GroupDef[];
}
