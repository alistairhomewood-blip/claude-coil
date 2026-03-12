import { Html, Line } from '@react-three/drei'
import * as THREE from 'three'

const SIZE = 0.06 // metres

/**
 * 3D axis arrows in the scene at the world origin.
 *
 * Axes are defined in Three.js Y-up space. The coordinate adapter is NOT used here
 * because these are hard-coded directions, not physics Vec3 values.
 *
 * Physics → Three.js mapping (documented for reference):
 *   Physics X  →  Three.js X  →  dir [1, 0, 0]  (red)
 *   Physics Y  →  Three.js Z  →  dir [0, 0, 1]  (green)
 *   Physics Z↑ →  Three.js Y  →  dir [0, 1, 0]  (blue)  ← labelled Z↑
 */
const AXES = [
  {
    dir: new THREE.Vector3(1, 0, 0),
    color: '#e05050',
    label: 'X',
  },
  {
    dir: new THREE.Vector3(0, 0, 1),
    color: '#50c050',
    label: 'Y',
  },
  {
    dir: new THREE.Vector3(0, 1, 0),
    color: '#5080e0',
    label: 'Z↑',
  },
]

export function AxesOverlay() {
  return (
    <group>
      {AXES.map(({ dir, color, label }) => {
        const end = dir.clone().multiplyScalar(SIZE)
        const points = [new THREE.Vector3(0, 0, 0), end]
        const labelPos = dir.clone().multiplyScalar(SIZE * 1.3)
        return (
          <group key={label}>
            <Line points={points} color={color} lineWidth={2} />
            <Html position={[labelPos.x, labelPos.y, labelPos.z]} center>
              <span
                style={{
                  color,
                  fontSize: 11,
                  fontFamily: 'monospace',
                  fontWeight: 600,
                  userSelect: 'none',
                  pointerEvents: 'none',
                }}
              >
                {label}
              </span>
            </Html>
          </group>
        )
      })}
    </group>
  )
}
