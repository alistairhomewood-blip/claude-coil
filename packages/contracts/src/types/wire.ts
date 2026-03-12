/**
 * Wire conductor specification.
 *
 * Two diameters are always required and must never be conflated:
 * - bareD  → resistance (R = ρL/A) and mass
 * - insulatedD → packing geometry and U-channel fit
 *
 * Mirrors wire_spec.schema.json.
 */
export interface WireSpec {
  /** AWG gauge number, or null for a custom wire definition. */
  awg: number | null;
  /** Human-readable label, e.g. 'AWG24' or 'Custom 0.5mm'. */
  label: string;
  /** Bare copper outer diameter, metres. Use for resistance and mass only. */
  bareD: number;
  /** Insulated outer diameter, metres. Use for packing and U-channel fit only. */
  insulatedD: number;
  /** Bare copper cross-sectional area, m². = π*(bareD/2)². */
  area: number;
}
