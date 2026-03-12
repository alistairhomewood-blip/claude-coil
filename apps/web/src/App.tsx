import { useState, useEffect } from 'react'
import { useCoilsStore } from './store/coils'
import { CoilList } from './components/CoilList'
import { CoilForm } from './components/CoilForm'
import { StatsPanel } from './components/StatsPanel'
import { ViewportScaffold } from './components/ViewportScaffold'
import { checkHealth } from './api/client'

type Tab = 'form' | 'stats' | 'viewport'

import type React from 'react'

const css: Record<string, React.CSSProperties> = {
  shell: { display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' },
  topbar: {
    display: 'flex',
    alignItems: 'center',
    padding: '0 16px',
    height: 44,
    background: '#12121a',
    borderBottom: '1px solid #2a2a35',
    gap: 12,
    flexShrink: 0,
  },
  title: { fontWeight: 700, fontSize: 15, color: '#d0d0f0', letterSpacing: '0.02em' },
  body: { display: 'flex', flex: 1, overflow: 'hidden' },
  sidebar: { width: 220, flexShrink: 0, overflow: 'hidden' },
  main: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  tabs: {
    display: 'flex',
    background: '#12121a',
    borderBottom: '1px solid #2a2a35',
    flexShrink: 0,
  },
  pane: { flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' },
  empty: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#404055',
    fontSize: 13,
  },
}

function healthStyle(ok: boolean | null): React.CSSProperties {
  return {
    fontSize: 11,
    padding: '2px 8px',
    borderRadius: 10,
    background: ok === null ? '#2a2a35' : ok ? '#1a3a1a' : '#3a1a1a',
    color: ok === null ? '#606080' : ok ? '#60c060' : '#c06060',
    marginLeft: 'auto',
  }
}

function tabStyle(active: boolean): React.CSSProperties {
  return {
    padding: '10px 20px',
    fontSize: 13,
    cursor: 'pointer',
    background: 'none',
    border: 'none',
    borderBottom: active ? '2px solid #7c6af7' : '2px solid transparent',
    color: active ? '#c0b8ff' : '#606080',
    fontWeight: active ? 600 : 400,
  }
}

export default function App() {
  const store = useCoilsStore()
  const [tab, setTab] = useState<Tab>('form')
  const [health, setHealth] = useState<boolean | null>(null)

  useEffect(() => {
    checkHealth()
      .then(() => setHealth(true))
      .catch(() => setHealth(false))
  }, [])

  return (
    <div style={css.shell}>
      {/* Top bar */}
      <div style={css.topbar}>
        <span style={css.title}>Coil Geometry Tool</span>
        <span style={healthStyle(health)}>
          API {health === null ? '…' : health ? 'online' : 'offline'}
        </span>
      </div>

      <div style={css.body}>
        {/* Sidebar */}
        <div style={css.sidebar}>
          <CoilList
            coils={store.coils}
            selectedId={store.selectedId}
            onSelect={store.setSelectedId}
            onDelete={store.deleteCoil}
            onAdd={store.addCoil}
          />
        </div>

        {/* Main panel */}
        <div style={css.main}>
          <div style={css.tabs}>
            {(['form', 'stats', 'viewport'] as Tab[]).map((t) => (
              <button key={t} style={tabStyle(tab === t)} onClick={() => setTab(t)}>
                {t === 'form' ? 'Parameters' : t === 'stats' ? 'Stats' : '3D View'}
              </button>
            ))}
          </div>

          <div style={css.pane}>
            {tab === 'form' &&
              (store.selectedCoil ? (
                <CoilForm
                  coil={store.selectedCoil}
                  onChange={store.updateCoil}
                />
              ) : (
                <div style={css.empty}>Select or add a coil to edit</div>
              ))}

            {tab === 'stats' && <StatsPanel coils={store.coils} />}

            {tab === 'viewport' && (
              <ViewportScaffold
                coils={store.coils}
                selectedId={store.selectedId}
                onSelectCoil={store.setSelectedId}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
