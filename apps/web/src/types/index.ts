export type {
  Vec3,
  CoilType,
  CoilGeometry,
  CircularGeometry,
  RacetrackGeometry,
  EllipticalGeometry,
  ToroidalGeometry,
  ElongatedToroidalGeometry,
  WindingSpec,
  CoilDef,
  WireSpec,
  GroupDef,
  ProjectFile,
  UnitSystem,
  CoilStats,
  PackingResult,
  ProjectStats,
  BFieldSliceRequest,
  BFieldSliceResult,
  DiscretiseResult,
  ApiRouteName,
} from '@coil/contracts'

export { API_ROUTES } from '@coil/contracts'

// WindingMode is not re-exported from contracts index; define locally.
export type WindingMode = 'poloidal' | 'toroidal'
