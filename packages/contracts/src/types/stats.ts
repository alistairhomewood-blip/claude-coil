/**
 * Packing geometry result for a single coil winding.
 * Uses wire.insulatedD for all packing calculations.
 */
export interface PackingResult {
  /** floor(channelWidth / wire.insulatedD). */
  turnsPerLayer: number;
  /** ceil(turns / turnsPerLayer). 0 if wire does not fit. */
  numLayers: number;
  /** Total channel depth needed, metres. = numLayers × wire.insulatedD. */
  channelDepth: number;
  /** True if turnsPerLayer >= 1 (wire physically fits in the channel at all). */
  fitsInChannel: boolean;
}

/**
 * Computed electrical and geometric statistics for a single coil.
 * Returned by POST /api/stats. Not stored in the project file.
 *
 * All quantities use:
 * - wire.bareD / wire.area for resistance and mass
 * - wire.insulatedD for packing (via PackingResult)
 *
 * Mirrors coil_stats.schema.json.
 */
export interface CoilStats {
  coilId: string;
  /** Total wire length, metres. = circumference × turns. */
  wireLength: number;
  /** Total wire mass, kg. = CU_DENSITY × wireLength × wire.area. */
  wireMass: number;
  /** DC resistance, ohms. = CU_RESISTIVITY × wireLength / wire.area. */
  resistance: number;
  /** Power dissipated, watts. = current² × resistance. */
  power: number;
  /** Required voltage, volts. = |current| × resistance. */
  voltage: number;
  packing: PackingResult;
  /** Non-blocking unusual conditions. */
  warnings: string[];
  /** Physically invalid conditions. Block export. */
  errors: string[];
}

/** Aggregate stats across all coils in the project. */
export interface ProjectStats {
  perCoil: CoilStats[];
  totalWireLength: number;  // m
  totalWireMass: number;    // kg
  totalPower: number;       // W
}
