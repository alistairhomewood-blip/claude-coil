import type React from 'react'
import type { CoilDef, CoilType } from '../types'

const COIL_TYPES: CoilType[] = [
  'circular',
  'racetrack',
  'elliptical',
  'toroidal',
  'elongated_toroidal',
]

interface Props {
  coils: CoilDef[]
  selectedId: string | null
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onAdd: (type: CoilType) => void
}

const s: Record<string, React.CSSProperties> = {
  root: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    background: '#16161a',
    borderRight: '1px solid #2a2a35',
  },
  header: {
    padding: '12px 16px',
    borderBottom: '1px solid #2a2a35',
    fontWeight: 600,
    fontSize: 13,
    color: '#a0a0b0',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
  },
  list: {
    flex: 1,
    overflowY: 'auto',
    padding: '4px 0',
  },
  name: {
    flex: 1,
    fontSize: 14,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  badge: {
    fontSize: 10,
    color: '#606080',
    fontFamily: 'monospace',
  },
  delBtn: {
    background: 'none',
    border: 'none',
    color: '#505060',
    cursor: 'pointer',
    fontSize: 16,
    lineHeight: 1,
    padding: '0 2px',
  },
  addSection: {
    padding: 12,
    borderTop: '1px solid #2a2a35',
  },
  select: {
    width: '100%',
    padding: '7px 10px',
    background: '#1e1e2e',
    border: '1px solid #2a2a35',
    borderRadius: 6,
    color: '#e0e0e0',
    fontSize: 13,
    cursor: 'pointer',
    marginBottom: 8,
  },
  addBtn: {
    width: '100%',
    padding: '7px 0',
    background: '#7c6af7',
    border: 'none',
    borderRadius: 6,
    color: '#fff',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
  },
}

function itemStyle(selected: boolean): React.CSSProperties {
  return {
    display: 'flex',
    alignItems: 'center',
    padding: '8px 16px',
    cursor: 'pointer',
    background: selected ? '#1e1e2e' : 'transparent',
    borderLeft: selected ? '3px solid #7c6af7' : '3px solid transparent',
    gap: 8,
  }
}

export function CoilList({ coils, selectedId, onSelect, onDelete, onAdd }: Props) {
  function handleAdd(e: React.ChangeEvent<HTMLSelectElement>) {
    const type = e.target.value as CoilType
    if (type) {
      onAdd(type)
      e.target.value = ''
    }
  }

  return (
    <div style={s.root}>
      <div style={s.header}>Coils ({coils.length})</div>
      <div style={s.list}>
        {coils.length === 0 && (
          <div style={{ padding: '16px', color: '#505060', fontSize: 13 }}>
            No coils yet. Add one below.
          </div>
        )}
        {coils.map((coil) => (
          <div
            key={coil.id}
            style={itemStyle(coil.id === selectedId)}
            onClick={() => onSelect(coil.id)}
          >
            <span style={s.name}>{coil.name}</span>
            <span style={s.badge}>{coil.geometry.type}</span>
            <button
              style={s.delBtn}
              title="Delete coil"
              onClick={(e) => {
                e.stopPropagation()
                onDelete(coil.id)
              }}
            >
              ×
            </button>
          </div>
        ))}
      </div>
      <div style={s.addSection}>
        <select style={s.select} onChange={handleAdd} defaultValue="">
          <option value="" disabled>
            Add coil…
          </option>
          {COIL_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
