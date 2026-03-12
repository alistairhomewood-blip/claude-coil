import { useState } from 'react'
import { computeStats } from '../api/client'
import type { CoilDef, CoilStats, ProjectStats } from '../types'

interface Props {
  coils: CoilDef[]
}

const css: Record<string, React.CSSProperties> = {
  root: { padding: 16, overflowY: 'auto', height: '100%' },
  btn: {
    padding: '8px 18px',
    background: '#7c6af7',
    border: 'none',
    borderRadius: 6,
    color: '#fff',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    marginBottom: 16,
  },
  btnDisabled: {
    padding: '8px 18px',
    background: '#333',
    border: 'none',
    borderRadius: 6,
    color: '#777',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'not-allowed',
    marginBottom: 16,
  },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 12 },
  th: {
    textAlign: 'left',
    padding: '5px 8px',
    color: '#808090',
    borderBottom: '1px solid #2a2a35',
    fontWeight: 600,
    fontSize: 11,
  },
  td: { padding: '5px 8px', borderBottom: '1px solid #1e1e2e', color: '#d0d0e0' },
  tdBold: {
    padding: '5px 8px',
    borderBottom: '1px solid #1e1e2e',
    color: '#e0e0f0',
    fontWeight: 700,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: '0.1em',
    textTransform: 'uppercase' as const,
    color: '#7c6af7',
    marginBottom: 10,
    paddingBottom: 4,
    borderBottom: '1px solid #2a2a35',
  },
  warn: { color: '#e0a050', fontSize: 12, marginBottom: 2 },
  err: { color: '#e05050', fontSize: 12, marginBottom: 2 },
  mock: {
    fontSize: 11,
    color: '#505060',
    padding: '6px 10px',
    background: '#1a1a22',
    borderRadius: 4,
    marginBottom: 12,
  },
}

function fmt(n: number, decimals = 3) {
  return n.toFixed(decimals)
}

function CoilRow({ stat }: { stat: CoilStats }) {
  return (
    <tr>
      <td style={css.td}>{stat.coilId.slice(0, 8)}…</td>
      <td style={css.td}>{fmt(stat.wireLength)} m</td>
      <td style={css.td}>{fmt(stat.wireMass * 1000, 1)} g</td>
      <td style={css.td}>{fmt(stat.resistance, 4)} Ω</td>
      <td style={css.td}>{fmt(stat.power, 2)} W</td>
      <td style={css.td}>{fmt(stat.voltage, 3)} V</td>
      <td style={css.td}>
        {stat.packing.fitsInChannel ? '✓' : '✗'}{' '}
        {stat.packing.turnsPerLayer}×{stat.packing.numLayers}L
      </td>
    </tr>
  )
}

export function StatsPanel({ coils }: Props) {
  const [stats, setStats] = useState<ProjectStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [isMock, setIsMock] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleCompute() {
    if (coils.length === 0) return
    setLoading(true)
    setError(null)
    try {
      const result = await computeStats(coils)
      setStats(result)
      setIsMock(result.perCoil.length === 0 && coils.length > 0)
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={css.root}>
      <button
        style={coils.length === 0 ? css.btnDisabled : css.btn}
        disabled={coils.length === 0 || loading}
        onClick={handleCompute}
      >
        {loading ? 'Computing…' : 'Compute Stats'}
      </button>

      {coils.length === 0 && (
        <div style={{ color: '#505060', fontSize: 13 }}>
          Add coils to compute stats.
        </div>
      )}

      {error && <div style={css.err}>{error}</div>}

      {isMock && (
        <div style={css.mock}>
          Backend /api/stats not available — showing mock data. Start the
          physics server to get real results.
        </div>
      )}

      {stats && (
        <>
          <div style={{ ...css.sectionTitle, marginTop: 0 }}>Per-coil</div>

          {stats.perCoil.length === 0 ? (
            <div style={{ color: '#505060', fontSize: 12 }}>
              No stats returned (backend not ready).
            </div>
          ) : (
            <table style={css.table}>
              <thead>
                <tr>
                  <th style={css.th}>ID</th>
                  <th style={css.th}>Wire length</th>
                  <th style={css.th}>Mass</th>
                  <th style={css.th}>Resistance</th>
                  <th style={css.th}>Power</th>
                  <th style={css.th}>Voltage</th>
                  <th style={css.th}>Packing</th>
                </tr>
              </thead>
              <tbody>
                {stats.perCoil.map((s) => (
                  <CoilRow key={s.coilId} stat={s} />
                ))}
                <tr>
                  <td style={css.tdBold}>TOTAL</td>
                  <td style={css.tdBold}>{fmt(stats.totalWireLength)} m</td>
                  <td style={css.tdBold}>—</td>
                  <td style={css.tdBold}>—</td>
                  <td style={css.tdBold}>{fmt(stats.totalPower, 2)} W</td>
                  <td style={css.tdBold}>—</td>
                  <td style={css.tdBold}>—</td>
                </tr>
              </tbody>
            </table>
          )}

          {/* Warnings & errors */}
          {stats.perCoil.some((s) => s.warnings.length > 0) && (
            <div style={{ marginTop: 16 }}>
              <div style={css.sectionTitle}>Warnings</div>
              {stats.perCoil.flatMap((s) =>
                s.warnings.map((w, i) => (
                  <div key={`${s.coilId}-w${i}`} style={css.warn}>
                    ⚠ {s.coilId.slice(0, 8)}: {w}
                  </div>
                )),
              )}
            </div>
          )}

          {stats.perCoil.some((s) => s.errors.length > 0) && (
            <div style={{ marginTop: 12 }}>
              <div style={css.sectionTitle}>Errors</div>
              {stats.perCoil.flatMap((s) =>
                s.errors.map((e, i) => (
                  <div key={`${s.coilId}-e${i}`} style={css.err}>
                    ✗ {s.coilId.slice(0, 8)}: {e}
                  </div>
                )),
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
