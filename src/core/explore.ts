import type { Route } from './route.ts'

export const EXPLORE_KEY = 'roma.explore'

export interface ExploreLog {
  scenes: string[]
  events: string[]
}

function list(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : []
}

export function parseExplore(raw: string | null): ExploreLog {
  try {
    const value: unknown = raw === null ? null : JSON.parse(raw)
    if (typeof value !== 'object' || value === null) return { scenes: [], events: [] }
    const record = value as Record<string, unknown>
    return { scenes: list(record.scenes), events: list(record.events) }
  } catch {
    return { scenes: [], events: [] }
  }
}

export function withVisit(log: ExploreLog, route: Route): ExploreLog {
  if (route.name === 'scene' && !log.scenes.includes(route.id)) return { ...log, scenes: [...log.scenes, route.id] }
  if (route.name === 'event' && !log.events.includes(route.id)) return { ...log, events: [...log.events, route.id] }
  return log
}

export function readExplore(): ExploreLog {
  try {
    return parseExplore(localStorage.getItem(EXPLORE_KEY))
  } catch {
    return { scenes: [], events: [] }
  }
}

export function recordVisit(route: Route) {
  if (route.name !== 'scene' && route.name !== 'event') return
  const log = readExplore()
  const next = withVisit(log, route)
  if (next === log) return
  try {
    localStorage.setItem(EXPLORE_KEY, JSON.stringify(next))
  } catch {
    return
  }
}
