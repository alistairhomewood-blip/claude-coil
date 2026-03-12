import * as THREE from 'three'
import type { Vec3 } from '../types'

/**
 * Convert a physics Z-up Vec3 to a Three.js Y-up Vector3.
 *
 * Mapping: physics(x, y, z) → THREE.Vector3(x, z, y)
 *
 * Physics frame: X=right, Y=forward, Z=up (right-handed)
 * Three.js frame: X=right, Y=up,     Z=toward viewer
 *
 * THIS IS THE ONLY PLACE THE Z↔Y SWAP OCCURS IN THE UI LAYER.
 * Do not replicate this swap anywhere else.
 */
export function toThreeVec3(v: Vec3): THREE.Vector3 {
  return new THREE.Vector3(v.x, v.z, v.y)
}

/**
 * Convert a Three.js Y-up Vector3 back to a physics Z-up Vec3.
 * Inverse of toThreeVec3. Use when reading back transformed object positions.
 */
export function toPhysicsVec3(v: THREE.Vector3): Vec3 {
  return { x: v.x, y: v.z, z: v.y }
}

/**
 * Convert an array of physics Z-up points to Three.js Vector3[].
 * For use with <Line points={...}> and similar drei primitives.
 */
export function toThreePath(points: Vec3[]): THREE.Vector3[] {
  return points.map(toThreeVec3)
}
