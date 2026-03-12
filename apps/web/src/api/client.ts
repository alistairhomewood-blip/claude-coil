import { API_ROUTES } from '../types'
import type { CoilDef, CoilStats, DiscretiseResult } from '../types'

export interface HealthResponse {
  status: string
}

export interface StatsResponse {
  perCoil: CoilStats[]
  totalWireLength: number
  totalWireMass: number
  totalPower: number
}

async function apiFetch<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    throw new Error(`${method} ${path} → ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export async function checkHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>(
    API_ROUTES.health.method,
    API_ROUTES.health.path,
  )
}

const MOCK_STATS: StatsResponse = {
  perCoil: [],
  totalWireLength: 0,
  totalWireMass: 0,
  totalPower: 0,
}

export async function computeStats(coils: CoilDef[]): Promise<StatsResponse> {
  try {
    return await apiFetch<StatsResponse>(
      API_ROUTES.computeStats.method,
      API_ROUTES.computeStats.path,
      { coils },
    )
  } catch (err) {
    console.warn('[api] computeStats not available, using mock data:', err)
    return MOCK_STATS
  }
}

export async function discretise(
  coils: CoilDef[],
  segmentsPerTurn?: number,
): Promise<DiscretiseResult[]> {
  try {
    return await apiFetch<DiscretiseResult[]>(
      API_ROUTES.discretise.method,
      API_ROUTES.discretise.path,
      { coils, segmentsPerTurn },
    )
  } catch (err) {
    console.warn('[api] discretise not available, using mock data:', err)
    return []
  }
}
