import { useState, useCallback } from 'react'
import type { CoilDef, CoilGeometry, CoilType } from '../types'

const AWG24: CoilDef['winding']['wire'] = {
  awg: 24,
  label: 'AWG24',
  bareD: 0.000511,
  insulatedD: 0.000574,
  area: 2.05e-7,
}

const DEFAULT_WINDING: Omit<CoilDef['winding'], 'windingMode'> = {
  turns: 10,
  current: 1.0,
  wire: AWG24,
  channelWidth: 0.01,
}

function defaultGeometry(type: CoilType): CoilGeometry {
  switch (type) {
    case 'circular':
      return { type: 'circular', radius: 0.05 }
    case 'racetrack':
      return { type: 'racetrack', straightLength: 0.1, arcRadius: 0.05 }
    case 'elliptical':
      return { type: 'elliptical', semiMajor: 0.08, semiMinor: 0.05 }
    case 'toroidal':
      return { type: 'toroidal', majorRadius: 0.1, minorRadius: 0.02 }
    case 'elongated_toroidal':
      return {
        type: 'elongated_toroidal',
        majorRadius: 0.1,
        minorRadius: 0.02,
        extension: 0.05,
      }
  }
}

function newCoil(type: CoilType, index: number): CoilDef {
  const isToroidal = type === 'toroidal' || type === 'elongated_toroidal'
  return {
    id: crypto.randomUUID(),
    groupId: null,
    name: `Coil ${index}`,
    colour: null,
    notes: null,
    locked: false,
    center: { x: 0, y: 0, z: 0 },
    rotationEulerDeg: { x: 0, y: 0, z: 0 },
    geometry: defaultGeometry(type),
    winding: {
      ...DEFAULT_WINDING,
      windingMode: isToroidal ? 'poloidal' : null,
    },
  }
}

export function useCoilsStore() {
  const [coils, setCoils] = useState<CoilDef[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const addCoil = useCallback(
    (type: CoilType) => {
      const coil = newCoil(type, coils.length + 1)
      setCoils((prev) => [...prev, coil])
      setSelectedId(coil.id)
    },
    [coils.length],
  )

  const updateCoil = useCallback((updated: CoilDef) => {
    setCoils((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
  }, [])

  const deleteCoil = useCallback(
    (id: string) => {
      setCoils((prev) => prev.filter((c) => c.id !== id))
      setSelectedId((prev) => {
        if (prev !== id) return prev
        const remaining = coils.filter((c) => c.id !== id)
        return remaining.length > 0 ? remaining[remaining.length - 1].id : null
      })
    },
    [coils],
  )

  const selectedCoil = coils.find((c) => c.id === selectedId) ?? null

  return {
    coils,
    selectedId,
    selectedCoil,
    setSelectedId,
    addCoil,
    updateCoil,
    deleteCoil,
  }
}
