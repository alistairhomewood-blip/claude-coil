import type { CoilDef } from '../types'
import { useDiscretise } from '../hooks/useDiscretise'
import { CoilScene } from './viewport/CoilScene'

interface ViewportScaffoldProps {
  coils: CoilDef[]
  selectedId: string | null
  onSelectCoil: (id: string) => void
}

export function ViewportScaffold({ coils, selectedId, onSelectCoil }: ViewportScaffoldProps) {
  const { data, loading, isFallback } = useDiscretise(coils)

  return (
    <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
      {isFallback && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 10,
            textAlign: 'center',
            padding: '4px 12px',
            background: '#2a1a0a',
            color: '#c08040',
            fontSize: 11,
            fontFamily: 'monospace',
            borderBottom: '1px solid #4a2a0a',
          }}
        >
          Backend offline — showing coil positions only
        </div>
      )}

      {loading && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 5,
            background: 'rgba(13,13,18,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#606080',
            fontSize: 12,
            fontFamily: 'monospace',
            pointerEvents: 'none',
          }}
        >
          Loading…
        </div>
      )}

      <CoilScene
        coils={coils}
        selectedId={selectedId}
        onSelectCoil={onSelectCoil}
        discretiseData={data}
        isFallback={isFallback}
      />
    </div>
  )
}
