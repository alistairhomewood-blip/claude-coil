import type { CoilDef, CoilGeometry, CoilType, WindingMode } from '../types'

interface Props {
  coil: CoilDef
  onChange: (updated: CoilDef) => void
}

// ---------------------------------------------------------------------------
// Style primitives
// ---------------------------------------------------------------------------
const css: Record<string, React.CSSProperties> = {
  root: { padding: '16px', overflowY: 'auto', height: '100%', color: '#e0e0e0' },
  section: { marginBottom: 20 },
  sectionTitle: {
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    color: '#7c6af7',
    marginBottom: 10,
    paddingBottom: 4,
    borderBottom: '1px solid #2a2a35',
  },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 12px' },
  grid3: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px 12px' },
  field: { display: 'flex', flexDirection: 'column', gap: 4 },
  label: { fontSize: 11, color: '#808090' },
  input: {
    padding: '6px 8px',
    background: '#1e1e2e',
    border: '1px solid #2a2a35',
    borderRadius: 5,
    color: '#e0e0e0',
    fontSize: 13,
    width: '100%',
  },
  select: {
    padding: '6px 8px',
    background: '#1e1e2e',
    border: '1px solid #2a2a35',
    borderRadius: 5,
    color: '#e0e0e0',
    fontSize: 13,
    width: '100%',
    cursor: 'pointer',
  },
  checkRow: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 },
  lockedBanner: {
    background: '#2a1a1a',
    border: '1px solid #5a3030',
    borderRadius: 6,
    padding: '8px 12px',
    fontSize: 13,
    color: '#c06060',
    marginBottom: 12,
  },
}

// ---------------------------------------------------------------------------
// Field helpers
// ---------------------------------------------------------------------------
function NumField({
  label,
  value,
  unit,
  onChange,
  disabled,
}: {
  label: string
  value: number
  unit?: string
  onChange: (v: number) => void
  disabled?: boolean
}) {
  return (
    <div style={css.field}>
      <label style={css.label}>
        {label}
        {unit ? <span style={{ color: '#505060' }}> ({unit})</span> : null}
      </label>
      <input
        type="number"
        step="any"
        style={css.input}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
      />
    </div>
  )
}

function TextField({
  label,
  value,
  onChange,
  disabled,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  disabled?: boolean
}) {
  return (
    <div style={css.field}>
      <label style={css.label}>{label}</label>
      <input
        type="text"
        style={css.input}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Geometry fields — one sub-form per type
// ---------------------------------------------------------------------------
const GEOMETRY_TYPES: CoilType[] = [
  'circular',
  'racetrack',
  'elliptical',
  'toroidal',
  'elongated_toroidal',
]

function GeometryFields({
  geometry,
  windingMode,
  onChange,
  onWindingModeChange,
  disabled,
}: {
  geometry: CoilGeometry
  windingMode: WindingMode | null | undefined
  onChange: (g: CoilGeometry) => void
  onWindingModeChange: (m: WindingMode) => void
  disabled?: boolean
}) {
  const isToroidal =
    geometry.type === 'toroidal' || geometry.type === 'elongated_toroidal'

  return (
    <>
      <div style={css.grid}>
        {geometry.type === 'circular' && (
          <NumField
            label="Radius"
            unit="m"
            value={geometry.radius}
            disabled={disabled}
            onChange={(v) => onChange({ ...geometry, radius: v })}
          />
        )}

        {geometry.type === 'racetrack' && (
          <>
            <NumField
              label="Straight Length"
              unit="m"
              value={geometry.straightLength}
              disabled={disabled}
              onChange={(v) => onChange({ ...geometry, straightLength: v })}
            />
            <NumField
              label="Arc Radius"
              unit="m"
              value={geometry.arcRadius}
              disabled={disabled}
              onChange={(v) => onChange({ ...geometry, arcRadius: v })}
            />
          </>
        )}

        {geometry.type === 'elliptical' && (
          <>
            <NumField
              label="Semi-major"
              unit="m"
              value={geometry.semiMajor}
              disabled={disabled}
              onChange={(v) => onChange({ ...geometry, semiMajor: v })}
            />
            <NumField
              label="Semi-minor"
              unit="m"
              value={geometry.semiMinor}
              disabled={disabled}
              onChange={(v) => onChange({ ...geometry, semiMinor: v })}
            />
          </>
        )}

        {(geometry.type === 'toroidal' ||
          geometry.type === 'elongated_toroidal') && (
          <>
            <NumField
              label="Major Radius"
              unit="m"
              value={geometry.majorRadius}
              disabled={disabled}
              onChange={(v) => onChange({ ...geometry, majorRadius: v })}
            />
            <NumField
              label="Minor Radius"
              unit="m"
              value={geometry.minorRadius}
              disabled={disabled}
              onChange={(v) => onChange({ ...geometry, minorRadius: v })}
            />
            {geometry.type === 'elongated_toroidal' && (
              <NumField
                label="Extension"
                unit="m"
                value={geometry.extension}
                disabled={disabled}
                onChange={(v) => onChange({ ...geometry, extension: v })}
              />
            )}
          </>
        )}
      </div>

      {isToroidal && (
        <div style={{ marginTop: 8, ...css.field }}>
          <label style={css.label}>Winding Mode</label>
          <select
            style={css.select}
            value={windingMode ?? 'poloidal'}
            disabled={disabled}
            onChange={(e) => onWindingModeChange(e.target.value as WindingMode)}
          >
            <option value="poloidal">poloidal</option>
            <option value="toroidal">toroidal</option>
          </select>
        </div>
      )}
    </>
  )
}

// ---------------------------------------------------------------------------
// Main form
// ---------------------------------------------------------------------------
export function CoilForm({ coil, onChange }: Props) {
  const disabled = coil.locked

  function patch(partial: Partial<CoilDef>) {
    onChange({ ...coil, ...partial })
  }

  function handleGeometryTypeChange(newType: CoilType) {
    const isToroidal = newType === 'toroidal' || newType === 'elongated_toroidal'
    let geometry: CoilGeometry
    switch (newType) {
      case 'circular':
        geometry = { type: 'circular', radius: 0.05 }
        break
      case 'racetrack':
        geometry = { type: 'racetrack', straightLength: 0.1, arcRadius: 0.05 }
        break
      case 'elliptical':
        geometry = { type: 'elliptical', semiMajor: 0.08, semiMinor: 0.05 }
        break
      case 'toroidal':
        geometry = { type: 'toroidal', majorRadius: 0.1, minorRadius: 0.02 }
        break
      case 'elongated_toroidal':
        geometry = {
          type: 'elongated_toroidal',
          majorRadius: 0.1,
          minorRadius: 0.02,
          extension: 0.05,
        }
        break
    }
    patch({
      geometry,
      winding: {
        ...coil.winding,
        windingMode: isToroidal ? 'poloidal' : null,
      },
    })
  }

  return (
    <div style={css.root}>
      {disabled && (
        <div style={css.lockedBanner}>
          Coil is locked — unlock to edit
        </div>
      )}

      {/* Identity */}
      <div style={css.section}>
        <div style={css.sectionTitle}>Identity</div>
        <div style={css.grid}>
          <TextField
            label="Name"
            value={coil.name}
            disabled={disabled}
            onChange={(v) => patch({ name: v })}
          />
          <div style={css.field}>
            <label style={css.label}>Colour (CSS hex)</label>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input
                type="color"
                style={{ ...css.input, width: 40, padding: 2, cursor: 'pointer' }}
                value={coil.colour ?? '#7c6af7'}
                disabled={disabled}
                onChange={(e) => patch({ colour: e.target.value })}
              />
              <input
                type="text"
                style={css.input}
                value={coil.colour ?? ''}
                placeholder="null"
                disabled={disabled}
                onChange={(e) =>
                  patch({ colour: e.target.value || null })
                }
              />
            </div>
          </div>
        </div>
        <div style={{ marginTop: 8, ...css.field }}>
          <label style={css.label}>Notes</label>
          <input
            type="text"
            style={css.input}
            value={coil.notes ?? ''}
            disabled={disabled}
            onChange={(e) => patch({ notes: e.target.value || null })}
          />
        </div>
        <div style={{ marginTop: 8, ...css.checkRow }}>
          <input
            type="checkbox"
            id="locked"
            checked={coil.locked}
            onChange={(e) => patch({ locked: e.target.checked })}
          />
          <label htmlFor="locked" style={{ cursor: 'pointer' }}>
            Locked
          </label>
        </div>
      </div>

      {/* Position */}
      <div style={css.section}>
        <div style={css.sectionTitle}>Position (Z-up frame)</div>
        <div style={{ marginBottom: 8, fontSize: 11, color: '#505060' }}>
          Center (m)
        </div>
        <div style={css.grid3}>
          <NumField
            label="X"
            unit="m"
            value={coil.center.x}
            disabled={disabled}
            onChange={(v) => patch({ center: { ...coil.center, x: v } })}
          />
          <NumField
            label="Y"
            unit="m"
            value={coil.center.y}
            disabled={disabled}
            onChange={(v) => patch({ center: { ...coil.center, y: v } })}
          />
          <NumField
            label="Z"
            unit="m"
            value={coil.center.z}
            disabled={disabled}
            onChange={(v) => patch({ center: { ...coil.center, z: v } })}
          />
        </div>
        <div style={{ marginTop: 8, marginBottom: 8, fontSize: 11, color: '#505060' }}>
          Rotation ZYX Euler (deg) — identity = XY plane, axis = +Z
        </div>
        <div style={css.grid3}>
          <NumField
            label="rot X"
            unit="°"
            value={coil.rotationEulerDeg.x}
            disabled={disabled}
            onChange={(v) =>
              patch({ rotationEulerDeg: { ...coil.rotationEulerDeg, x: v } })
            }
          />
          <NumField
            label="rot Y"
            unit="°"
            value={coil.rotationEulerDeg.y}
            disabled={disabled}
            onChange={(v) =>
              patch({ rotationEulerDeg: { ...coil.rotationEulerDeg, y: v } })
            }
          />
          <NumField
            label="rot Z"
            unit="°"
            value={coil.rotationEulerDeg.z}
            disabled={disabled}
            onChange={(v) =>
              patch({ rotationEulerDeg: { ...coil.rotationEulerDeg, z: v } })
            }
          />
        </div>
      </div>

      {/* Geometry */}
      <div style={css.section}>
        <div style={css.sectionTitle}>Geometry</div>
        <div style={{ ...css.field, marginBottom: 10 }}>
          <label style={css.label}>Shape</label>
          <select
            style={css.select}
            value={coil.geometry.type}
            disabled={disabled}
            onChange={(e) =>
              handleGeometryTypeChange(e.target.value as CoilType)
            }
          >
            {GEOMETRY_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <GeometryFields
          geometry={coil.geometry}
          windingMode={coil.winding.windingMode}
          disabled={disabled}
          onChange={(g) => patch({ geometry: g })}
          onWindingModeChange={(m) =>
            patch({ winding: { ...coil.winding, windingMode: m } })
          }
        />
      </div>

      {/* Winding */}
      <div style={css.section}>
        <div style={css.sectionTitle}>Winding</div>
        <div style={css.grid}>
          <NumField
            label="Turns"
            value={coil.winding.turns}
            disabled={disabled}
            onChange={(v) =>
              patch({ winding: { ...coil.winding, turns: Math.max(1, Math.round(v)) } })
            }
          />
          <NumField
            label="Current"
            unit="A"
            value={coil.winding.current}
            disabled={disabled}
            onChange={(v) =>
              patch({ winding: { ...coil.winding, current: v } })
            }
          />
          <NumField
            label="Channel Width"
            unit="m"
            value={coil.winding.channelWidth}
            disabled={disabled}
            onChange={(v) =>
              patch({ winding: { ...coil.winding, channelWidth: v } })
            }
          />
        </div>

        <div style={{ marginTop: 12, marginBottom: 6, fontSize: 11, color: '#505060' }}>
          Wire
        </div>
        <div style={css.grid}>
          <TextField
            label="Label"
            value={coil.winding.wire.label}
            disabled={disabled}
            onChange={(v) =>
              patch({
                winding: {
                  ...coil.winding,
                  wire: { ...coil.winding.wire, label: v },
                },
              })
            }
          />
          <NumField
            label="Bare diameter"
            unit="m"
            value={coil.winding.wire.bareD}
            disabled={disabled}
            onChange={(v) =>
              patch({
                winding: {
                  ...coil.winding,
                  wire: { ...coil.winding.wire, bareD: v },
                },
              })
            }
          />
          <NumField
            label="Insulated diameter"
            unit="m"
            value={coil.winding.wire.insulatedD}
            disabled={disabled}
            onChange={(v) =>
              patch({
                winding: {
                  ...coil.winding,
                  wire: { ...coil.winding.wire, insulatedD: v },
                },
              })
            }
          />
          <NumField
            label="Cross-section area"
            unit="m²"
            value={coil.winding.wire.area}
            disabled={disabled}
            onChange={(v) =>
              patch({
                winding: {
                  ...coil.winding,
                  wire: { ...coil.winding.wire, area: v },
                },
              })
            }
          />
        </div>
      </div>
    </div>
  )
}
