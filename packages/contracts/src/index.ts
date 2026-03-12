// Types
export type { Vec3, CoilType, CoilGeometry, CoilDef, WindingSpec } from './types/coil.js';
export type {
  CircularGeometry,
  RacetrackGeometry,
  EllipticalGeometry,
  ToroidalGeometry,
  ElongatedToroidalGeometry,
} from './types/coil.js';
export type { WireSpec } from './types/wire.js';
export type { UnitSystem, GroupDef, ProjectFile } from './types/project.js';
export type { PackingResult, CoilStats, ProjectStats } from './types/stats.js';
export type {
  BFieldSliceRequest,
  BFieldSliceResult,
  DiscretiseResult,
} from './types/field.js';

// API
export { API_ROUTES } from './api/routes.js';
export type { ApiRouteName } from './api/routes.js';
