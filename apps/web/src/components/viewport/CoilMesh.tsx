import { Html, Line } from '@react-three/drei'
import * as THREE from 'three'
import type { ThreeEvent } from '@react-three/fiber'
import type { CoilDef } from '../../types'
import type { DiscretiseResult } from '../../types'
import { toThreeVec3, toThreePath } from '../../adapters/coordAdapter'

// Default colour palette (one per coil, cycling)
const PALETTE = [
  '#7c6af7', // purple
  '#f7916a', // orange
  '#6af7c4', // teal
  '#f7e06a', // yellow
  '#6ab8f7', // sky blue
  '#f76ab8', // pink
]

function resolveColor(coil: CoilDef, index: number, isSelected: boolean): string {
  const base = coil.colour ?? PALETTE[index % PALETTE.length]
  if (!isSelected) return base
  const c = new THREE.Color(base)
  c.lerp(new THREE.Color('#ffffff'), 0.4)
  return `#${c.getHexString()}`
}

/**
 * Bounding radius for the hit-box mesh.
 * UI geometry estimate only — no physics formulas.
 */
function hitRadius(coil: CoilDef): number {
  const g = coil.geometry
  switch (g.type) {
    case 'circular':
      return g.radius
    case 'racetrack':
      return g.arcRadius + g.straightLength / 2
    case 'elliptical':
      return g.semiMajor
    case 'toroidal':
      return g.majorRadius + g.minorRadius
    case 'elongated_toroidal':
      return g.majorRadius + g.minorRadius + g.extension
  }
}

interface CoilMeshProps {
  coil: CoilDef
  paths: DiscretiseResult['filamentPaths'] | null
  isSelected: boolean
  index: number
  onSelect: (id: string) => void
}

export function CoilMesh({ coil, paths, isSelected, index, onSelect }: CoilMeshProps) {
  const color = resolveColor(coil, index, isSelected)
  const center = toThreeVec3(coil.center)
  const radius = hitRadius(coil)
  const lineWidth = isSelected ? 2.5 : 1.5
  const hasPaths = paths !== null && paths.length > 0

  function handleClick(e: ThreeEvent<MouseEvent>) {
    e.stopPropagation()
    onSelect(coil.id)
  }

  return (
    <group>
      {/* Real wire geometry — shown only when filament paths are available */}
      {hasPaths &&
        paths!.map((turn, i) => (
          <Line
            key={i}
            points={toThreePath(turn)}
            color={color}
            lineWidth={lineWidth}
          />
        ))}

      {/* Fallback: solid sphere + name label when no paths are available.
          Disappears as soon as hasPaths becomes true. */}
      {!hasPaths && (
        <>
          <mesh position={[center.x, center.y, center.z]} onClick={handleClick}>
            <sphereGeometry args={[0.006, 12, 12]} />
            <meshBasicMaterial color={color} />
          </mesh>
          <Html position={[center.x, center.y + 0.012, center.z]} center>
            <span
              style={{
                color: '#a0a0c0',
                fontSize: 10,
                fontFamily: 'monospace',
                userSelect: 'none',
                pointerEvents: 'none',
                whiteSpace: 'nowrap',
              }}
            >
              {coil.name}
            </span>
          </Html>
        </>
      )}

      {/* Hit-box for click selection — always present, visually transparent.
          Uses opacity=0 + transparent rather than visible=false so that
          Three.js raycasting still works. depthWrite=false prevents it from
          occluding other geometry in the depth buffer.
          userData.coilId is the attachment point for future TransformControls. */}
      <mesh
        position={[center.x, center.y, center.z]}
        onClick={handleClick}
        userData={{ coilId: coil.id }}
      >
        <sphereGeometry args={[Math.max(radius, 0.005), 8, 8]} />
        <meshBasicMaterial transparent opacity={0} depthWrite={false} />
      </mesh>
    </group>
  )
}
