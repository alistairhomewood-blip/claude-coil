import { useState, useEffect, useMemo, useRef } from 'react'
import type { CoilDef, DiscretiseResult } from '../types'
import { discretise } from '../api/client'

export interface UseDiscretiseResult {
  data: DiscretiseResult[]
  loading: boolean
  isFallback: boolean
}

/**
 * Calls /api/discretise and caches results by geometry fingerprint.
 *
 * Only re-fetches when fields that affect discretisation change
 * (id, geometry, winding.turns, center, rotationEulerDeg).
 * Cosmetic fields (name, colour, notes, locked) do not trigger a re-fetch.
 *
 * isFallback is true when the backend returned an empty result for non-empty coils
 * (endpoint missing, network error, etc.).
 */
export function useDiscretise(coils: CoilDef[]): UseDiscretiseResult {
  const [data, setData] = useState<DiscretiseResult[]>([])
  const [loading, setLoading] = useState(false)
  const [isFallback, setIsFallback] = useState(false)

  // Always hold the latest coils so the effect closure never goes stale.
  const coilsRef = useRef(coils)
  coilsRef.current = coils

  // Cache: fingerprint → DiscretiseResult[]
  const cache = useRef<Map<string, DiscretiseResult[]>>(new Map())

  // Fingerprint: only fields that affect discretisation output.
  // String comparison lets useEffect skip re-fetches on cosmetic-only edits.
  const fingerprint = useMemo(
    () =>
      JSON.stringify(
        coils.map((c) => ({
          id: c.id,
          geometry: c.geometry,
          turns: c.winding.turns,
          center: c.center,
          rotationEulerDeg: c.rotationEulerDeg,
        })),
      ),
    [coils],
  )

  useEffect(() => {
    const currentCoils = coilsRef.current

    if (currentCoils.length === 0) {
      setData([])
      setLoading(false)
      setIsFallback(false)
      return
    }

    // Cache hit — skip network round-trip.
    const cached = cache.current.get(fingerprint)
    if (cached) {
      setData(cached)
      setLoading(false)
      setIsFallback(false)
      return
    }

    let cancelled = false
    setLoading(true)

    discretise(currentCoils, 64).then((result) => {
      if (cancelled) return

      const fallback = result.length === 0 && currentCoils.length > 0
      if (!fallback) {
        cache.current.set(fingerprint, result)
      }
      setData(result)
      setIsFallback(fallback)
      setLoading(false)
    })

    // Cleanup: if fingerprint changes before the response lands, ignore it.
    return () => {
      cancelled = true
    }
  }, [fingerprint]) // fingerprint encodes all geometry-relevant coil fields

  return { data, loading, isFallback }
}
