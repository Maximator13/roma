import { Vector3 } from 'three'

export interface Route {
  points: Vector3[]
  lengths: number[]
  total: number
}

export function routeFrom(points: Vector3[]): Route {
  const lengths = [0]
  for (let index = 1; index < points.length; index += 1) {
    lengths.push(lengths[index - 1]! + points[index]!.distanceTo(points[index - 1]!))
  }
  return { points, lengths, total: lengths.at(-1) ?? 0 }
}

export function pingPong(distance: number, total: number): { distance: number; forward: boolean } {
  if (total <= 0) return { distance: 0, forward: true }
  const cycle = ((distance % (2 * total)) + 2 * total) % (2 * total)
  return cycle <= total ? { distance: cycle, forward: true } : { distance: 2 * total - cycle, forward: false }
}

export function pointAlong(route: Route, distance: number, result = new Vector3()): { point: Vector3; segment: number } {
  const { points, lengths, total } = route
  if (points.length === 0) return { point: result.set(0, 0, 0), segment: 0 }
  const clamped = Math.max(0, Math.min(total, distance))
  let segment = 1
  while (segment < lengths.length - 1 && lengths[segment]! < clamped) segment += 1
  const start = points[segment - 1] ?? points[0]!
  const end = points[segment] ?? start
  const span = lengths[segment]! - lengths[segment - 1]!
  const t = span > 0 ? (clamped - lengths[segment - 1]!) / span : 0
  return { point: result.lerpVectors(start, end, t), segment }
}

export function groupRoutes(named: { name: string; position: Vector3 }[], prefix: string): Map<string, Vector3[]> {
  const pattern = new RegExp(`^${prefix}(.+)_([0-9]+)$`)
  const groups = new Map<string, { order: number; position: Vector3 }[]>()
  for (const { name, position } of named) {
    const match = pattern.exec(name)
    if (!match) continue
    const list = groups.get(match[1]!) ?? []
    list.push({ order: Number(match[2]), position })
    groups.set(match[1]!, list)
  }
  return new Map([...groups].map(([id, list]) => [id, list.sort((a, b) => a.order - b.order).map((entry) => entry.position)]))
}

export function walkerCount(total: number, spacing: number, maximum: number): number {
  return Math.max(1, Math.min(maximum, Math.round(total / spacing)))
}
