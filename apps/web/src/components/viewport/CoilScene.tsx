import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import type { CoilDef } from '../../types'
import type { DiscretiseResult } from '../../types'
import { AxesOverlay } from './AxesOverlay'
import { CoilMesh } from './CoilMesh'

interface CoilSceneProps {
  coils: CoilDef[]
  selectedId: string | null
  onSelectCoil: (id: string) => void
  discretiseData: DiscretiseResult[]
  isFallback: boolean
}

export function CoilScene({
  coils,
  selectedId,
  onSelectCoil,
  discretiseData,
}: CoilSceneProps) {
  return (
    <Canvas
      camera={{
        // Position in Three.js Y-up space. Looking at origin from above-right-front.
        position: [0.2, 0.25, 0.4],
        fov: 45,
        up: [0, 1, 0],
        near: 0.001,
        far: 100,
      }}
      style={{ background: '#0d0d12', width: '100%', height: '100%' }}
      gl={{ antialias: true }}
    >
      <ambientLight intensity={0.4} />
      <pointLight position={[1, 2, 1]} intensity={0.6} />

      {/* makeDefault registers these controls in r3f state so future
          TransformControls can automatically disable orbit while dragging. */}
      <OrbitControls
        makeDefault
        enableDamping
        dampingFactor={0.1}
      />

      <AxesOverlay />

      {coils.map((coil, index) => {
        const result = discretiseData.find((d) => d.coilId === coil.id)
        return (
          <CoilMesh
            key={coil.id}
            coil={coil}
            paths={result?.filamentPaths ?? null}
            isSelected={coil.id === selectedId}
            index={index}
            onSelect={onSelectCoil}
          />
        )
      })}
    </Canvas>
  )
}
