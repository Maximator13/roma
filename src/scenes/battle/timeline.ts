import type { Action, Point, Unit } from './schema.ts'

export interface UnitState {
  x: number
  y: number
  facing: number
  width: number
  depth: number
  bulge: number
  action: Action
  losses: number
}

interface Segment {
  from: number
  to: number
  start: UnitState
  end: UnitState
  path: Point[] | null
}

export interface UnitTrack {
  initial: UnitState
  segments: Segment[]
}

export interface Slot {
  u: number
  v: number
  jitterX: number
  jitterY: number
  phase: number
}

export interface Placement {
  x: number
  y: number
  heading: number
}

const DEGREES = Math.PI / 180
const LOSS_SAMPLES_PER_PHASE = 200
const POSITION_JITTER = 1.2
const SLOT_JITTER = 0.22

export function seeded(index: number): number {
  const value = Math.sin(index * 127.1 + 311.7) * 43758.5453
  return value - Math.floor(value)
}

export function ease(t: number): number {
  const clamped = Math.min(1, Math.max(0, t))
  return clamped * clamped * (3 - 2 * clamped)
}

export function lerpAngle(from: number, to: number, t: number): number {
  const delta = ((((to - from) % 360) + 540) % 360) - 180
  return from + delta * t
}

export function headingOf(dx: number, dy: number): number {
  return Math.atan2(dx, dy) / DEGREES
}

function initialState(unit: Unit): UnitState {
  const start = unit.start
  return {
    x: start.at[0],
    y: start.at[1],
    facing: start.facing,
    width: start.width,
    depth: start.depth,
    bulge: start.bulge ?? 0,
    action: start.action ?? 'stand',
    losses: start.losses ?? 0,
  }
}

export function trackOf(unit: Unit): UnitTrack {
  const initial = initialState(unit)
  const segments: Segment[] = []
  let current = initial
  let time = 0
  for (const frame of unit.moves) {
    const end: UnitState = {
      x: frame.at?.[0] ?? current.x,
      y: frame.at?.[1] ?? current.y,
      facing: frame.facing ?? current.facing,
      width: frame.width ?? current.width,
      depth: frame.depth ?? current.depth,
      bulge: frame.bulge ?? current.bulge,
      action: frame.action ?? holdAction(current.action),
      losses: frame.losses ?? current.losses,
    }
    const path: Point[] | null = frame.via ? [[current.x, current.y], ...frame.via, [end.x, end.y]] : null
    segments.push({ from: time, to: frame.phase, start: current, end, path })
    current = end
    time = frame.phase
  }
  return { initial, segments }
}

function pointAlong(path: Point[], t: number): { x: number; y: number; heading: number } {
  const lengths = path.slice(1).map((point, index) => Math.hypot(point[0] - path[index]![0], point[1] - path[index]![1]))
  const total = lengths.reduce((sum, length) => sum + length, 0)
  let remaining = Math.min(1, Math.max(0, t)) * total
  for (let index = 0; index < lengths.length; index += 1) {
    const length = lengths[index]!
    const a = path[index]!
    const b = path[index + 1]!
    if (remaining <= length || index === lengths.length - 1) {
      const local = length > 0 ? Math.min(1, remaining / length) : 1
      return { x: a[0] + (b[0] - a[0]) * local, y: a[1] + (b[1] - a[1]) * local, heading: headingOf(b[0] - a[0], b[1] - a[1]) }
    }
    remaining -= length
  }
  const last = path[path.length - 1]!
  return { x: last[0], y: last[1], heading: 0 }
}

function copyInto(out: UnitState, source: UnitState): UnitState {
  out.x = source.x
  out.y = source.y
  out.facing = source.facing
  out.width = source.width
  out.depth = source.depth
  out.bulge = source.bulge
  out.action = source.action
  out.losses = source.losses
  return out
}

function holdAction(action: Action): Action {
  return action === 'march' || action === 'charge' ? 'stand' : action
}

export function stateAt(track: UnitTrack, time: number, out: UnitState): UnitState {
  let previous = track.initial
  for (const segment of track.segments) {
    if (time < segment.from) break
    if (time <= segment.to) {
      const linear = (time - segment.from) / Math.max(1e-6, segment.to - segment.from)
      const t = ease(linear)
      const { start, end } = segment
      if (segment.path) {
        const along = pointAlong(segment.path, t)
        out.x = along.x
        out.y = along.y
        const turn = Math.min(1, Math.min(t, 1 - t) / 0.12)
        out.facing = lerpAngle(lerpAngle(start.facing, end.facing, t), along.heading, turn)
      } else {
        out.x = start.x + (end.x - start.x) * t
        out.y = start.y + (end.y - start.y) * t
        out.facing = lerpAngle(start.facing, end.facing, t)
      }
      out.width = start.width + (end.width - start.width) * t
      out.depth = start.depth + (end.depth - start.depth) * t
      out.bulge = start.bulge + (end.bulge - start.bulge) * t
      out.losses = start.losses + (end.losses - start.losses) * linear
      out.action = linear >= 1 ? holdAction(end.action) : end.action
      return out
    }
    previous = segment.end
  }
  copyInto(out, previous)
  out.action = previous === track.initial ? previous.action : holdAction(previous.action)
  return out
}

export function figureCount(unit: Unit, scale: number): number {
  return Math.max(1, Math.round(unit.soldiers / scale))
}

export function slotsFor(count: number, width: number, depth: number, seed: number): Slot[] {
  const columns = Math.max(1, Math.min(count, Math.round(Math.sqrt((count * width) / depth))))
  const rows = Math.ceil(count / columns)
  return Array.from({ length: count }, (_, index) => {
    const column = index % columns
    const row = Math.floor(index / columns)
    const key = seed * 7919 + index * 13
    return {
      u: (column + 0.5 + (seeded(key) - 0.5) * SLOT_JITTER) / columns,
      v: (row + 0.5 + (seeded(key + 1) - 0.5) * SLOT_JITTER) / rows,
      jitterX: (seeded(key + 2) - 0.5) * POSITION_JITTER,
      jitterY: (seeded(key + 3) - 0.5) * POSITION_JITTER,
      phase: seeded(key + 4) * Math.PI * 2,
    }
  })
}

export function placeFigure(state: UnitState, slot: Slot, out: Placement): Placement {
  const angle = state.facing * DEGREES
  const forwardX = Math.sin(angle)
  const forwardY = Math.cos(angle)
  const across = slot.u - 0.5
  const along = across * state.width
  const ahead = state.depth * (0.5 - slot.v) + state.bulge * (1 - 4 * across * across)
  out.x = state.x + forwardY * along + forwardX * ahead + slot.jitterX
  out.y = state.y - forwardX * along + forwardY * ahead + slot.jitterY
  out.heading = state.facing
  return out
}

export function deathTimes(track: UnitTrack, count: number, phases: number, seed: number): Float32Array {
  const samples = phases * LOSS_SAMPLES_PER_PHASE
  const scratch = copyInto({} as UnitState, track.initial)
  const curve = new Float32Array(samples + 1)
  for (let step = 0; step <= samples; step += 1) curve[step] = stateAt(track, (step / samples) * phases, scratch).losses
  const order = Array.from({ length: count }, (_, index) => index).sort((a, b) => seeded(seed * 31 + a) - seeded(seed * 31 + b))
  const times = new Float32Array(count).fill(Number.POSITIVE_INFINITY)
  order.forEach((figure, rank) => {
    const threshold = (rank + 0.5) / count
    for (let step = 0; step <= samples; step += 1) {
      if (curve[step]! >= threshold) {
        times[figure] = (step / samples) * phases
        break
      }
    }
  })
  return times
}

export function pointForTime(time: number, phases: number): number {
  if (time <= 0) return 0
  return Math.min(phases, Math.floor(time) + 1)
}

export function phaseIndexAt(time: number, phases: number): number {
  return Math.max(0, Math.min(phases - 1, Math.floor(time)))
}

export function timeForPoint(point: number, settledAtEnd: boolean): number {
  if (point <= 0) return 0
  return settledAtEnd ? point : point - 1
}

export function sunAt(hour: number, latitude: number, declination: number): { azimuth: number; elevation: number } {
  const hourAngle = (hour - 12) * 15 * DEGREES
  const phi = latitude * DEGREES
  const delta = declination * DEGREES
  const elevation = Math.asin(Math.sin(phi) * Math.sin(delta) + Math.cos(phi) * Math.cos(delta) * Math.cos(hourAngle))
  const azimuth = Math.atan2(Math.sin(hourAngle), Math.cos(hourAngle) * Math.sin(phi) - Math.tan(delta) * Math.cos(phi))
  return { azimuth: (azimuth / DEGREES + 180 + 360) % 360, elevation: elevation / DEGREES }
}

export function counterValue(from: number, to: number, progress: number): number {
  return Math.round(from + (to - from) * Math.min(1, Math.max(0, progress)))
}
