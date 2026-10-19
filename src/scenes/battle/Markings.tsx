import { useFrame } from '@react-three/fiber'
import { useMemo } from 'react'
import {
  BufferAttribute,
  BufferGeometry,
  CatmullRomCurve3,
  Color,
  DoubleSide,
  Mesh,
  MeshBasicMaterial,
  Vector3,
} from 'three'
import { approach } from '../../map/camera.ts'
import { useDeferredDispose } from './ground.ts'
import { heightAt, type HeightField } from './heightfield.ts'
import type { Arrow, Battle, Side } from './schema.ts'
import { useBattle } from './store.ts'
import { phaseIndexAt, placeFigure, stateAt, type Placement, type Slot, type UnitState, type UnitTrack } from './timeline.ts'

export const SIDE_COLORS: Record<Side, string> = { rome: '#c2462f', carthage: '#3c78b4' }

const ACROSS = 10
const DEEP = 2
const FOOTPRINT_LIFT = 3
const ARROW_LIFT = 9
const ARROW_WIDTH: Record<Arrow['kind'], number> = { move: 46, attack: 64, flee: 38 }
const ARROW_OPACITY: Record<Arrow['kind'], number> = { move: 0.78, attack: 0.92, flee: 0.6 }
const GROW_SHARE = 0.55
const FADE_TIME_CONSTANT = 0.35

function footprintSlots(): Slot[] {
  const slots: Slot[] = []
  for (let row = 0; row <= DEEP; row += 1) {
    for (let column = 0; column <= ACROSS; column += 1) slots.push({ u: column / ACROSS, v: row / DEEP, jitterX: 0, jitterY: 0, phase: 0 })
  }
  return slots
}

function footprintIndex(units: number): Uint32Array {
  const perUnit = (ACROSS + 1) * (DEEP + 1)
  const indices: number[] = []
  for (let unit = 0; unit < units; unit += 1) {
    const base = unit * perUnit
    for (let row = 0; row < DEEP; row += 1) {
      for (let column = 0; column < ACROSS; column += 1) {
        const a = base + row * (ACROSS + 1) + column
        const b = a + 1
        const c = a + ACROSS + 1
        const d = c + 1
        indices.push(a, c, b, b, c, d)
      }
    }
  }
  return new Uint32Array(indices)
}

function overlayMaterial(color: string, opacity: number): MeshBasicMaterial {
  return new MeshBasicMaterial({
    color: new Color(color),
    transparent: true,
    opacity,
    depthWrite: false,
    side: DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor: -4,
    fog: false,
  })
}

interface FootprintSide {
  units: number[]
  mesh: Mesh
  opacity: number
}

function updateFootprints(
  sides: FootprintSide[],
  slots: Slot[],
  tracks: UnitTrack[],
  field: HeightField,
  scratch: { state: UnitState; placement: Placement },
  delta: number,
) {
  const { time, view } = useBattle.getState()
  for (const side of sides) {
    const material = side.mesh.material as MeshBasicMaterial
    material.opacity = approach(material.opacity, view === 'tactical' ? side.opacity : 0, delta, FADE_TIME_CONSTANT)
    side.mesh.visible = material.opacity > 0.01
    if (!side.mesh.visible) continue
    const positions = side.mesh.geometry.getAttribute('position') as BufferAttribute
    side.units.forEach((unit, order) => {
      const state = stateAt(tracks[unit]!, time, scratch.state)
      const survivors = 1 - state.losses * 0.6
      const thinned = { ...state, depth: Math.max(8, state.depth * survivors) }
      slots.forEach((slot, index) => {
        const placed = placeFigure(thinned, slot, scratch.placement)
        const z = -placed.y
        positions.setXYZ(order * slots.length + index, placed.x, heightAt(field, placed.x, z) + FOOTPRINT_LIFT, z)
      })
    })
    positions.needsUpdate = true
  }
}

export function Footprints({ battle, tracks, field }: { battle: Battle; tracks: UnitTrack[]; field: HeightField }) {
  const slots = useMemo(() => footprintSlots(), [])
  const sides = useMemo(
    () =>
      (['rome', 'carthage'] as const).map((side) => {
        const units = battle.units.flatMap((unit, index) => (unit.side === side ? [index] : []))
        const geometry = new BufferGeometry()
        geometry.setAttribute('position', new BufferAttribute(new Float32Array(units.length * slots.length * 3), 3))
        geometry.setIndex(new BufferAttribute(footprintIndex(units.length), 1))
        const mesh = new Mesh(geometry, overlayMaterial(SIDE_COLORS[side], 0.34))
        mesh.frustumCulled = false
        mesh.renderOrder = 5
        return { units, mesh, opacity: 0.34 }
      }),
    [battle, slots],
  )
  const scratch = useMemo(() => ({ state: {} as UnitState, placement: {} as Placement }), [])

  const dispose = useMemo(
    () => () => {
      for (const side of sides) {
        side.mesh.geometry.dispose()
        ;(side.mesh.material as MeshBasicMaterial).dispose()
      }
    },
    [sides],
  )
  useDeferredDispose(dispose)

  useFrame((_, delta) => updateFootprints(sides, slots, tracks, field, scratch, delta))

  return (
    <>
      {sides.map((side) => (
        <primitive key={side.mesh.uuid} object={side.mesh} />
      ))}
    </>
  )
}

function arrowGeometry(arrow: Arrow, field: HeightField): BufferGeometry {
  const curve = new CatmullRomCurve3(
    arrow.path.map(([x, y]) => new Vector3(x, 0, -y)),
    false,
    'centripetal',
  )
  const length = curve.getLength()
  const width = ARROW_WIDTH[arrow.kind]
  const headLength = Math.min(length * 0.4, width * 2.6)
  const steps = Math.max(8, Math.round(length / 40))
  const shaftEnd = 1 - headLength / length
  const positions: number[] = []
  const indices: number[] = []
  const point = new Vector3()
  const tangent = new Vector3()
  const lift = (x: number, z: number) => heightAt(field, x, z) + ARROW_LIFT
  for (let step = 0; step <= steps; step += 1) {
    const t = (step / steps) * shaftEnd
    curve.getPointAt(t, point)
    curve.getTangentAt(t, tangent)
    const nx = -tangent.z * (width / 2)
    const nz = tangent.x * (width / 2)
    positions.push(point.x + nx, lift(point.x + nx, point.z + nz), point.z + nz)
    positions.push(point.x - nx, lift(point.x - nx, point.z - nz), point.z - nz)
    if (step > 0) {
      const base = (step - 1) * 2
      indices.push(base, base + 1, base + 2, base + 1, base + 3, base + 2)
    }
  }
  curve.getPointAt(shaftEnd, point)
  curve.getTangentAt(shaftEnd, tangent)
  const tip = curve.getPointAt(1, new Vector3())
  const spread = width * 1.25
  const nx = -tangent.z * spread
  const nz = tangent.x * spread
  const head = positions.length / 3
  positions.push(point.x + nx, lift(point.x + nx, point.z + nz), point.z + nz)
  positions.push(point.x - nx, lift(point.x - nx, point.z - nz), point.z - nz)
  positions.push(tip.x, lift(tip.x, tip.z), tip.z)
  indices.push(head, head + 1, head + 2)
  const geometry = new BufferGeometry()
  geometry.setAttribute('position', new BufferAttribute(new Float32Array(positions), 3))
  geometry.setIndex(indices)
  return geometry
}

interface ArrowMesh {
  phase: number
  kind: Arrow['kind']
  mesh: Mesh
  total: number
}

function updateArrows(arrows: ArrowMesh[], phases: number, delta: number) {
  const { time, view } = useBattle.getState()
  const current = phaseIndexAt(time, phases)
  const progress = time - current
  for (const arrow of arrows) {
    const material = arrow.mesh.material as MeshBasicMaterial
    const shown = view === 'tactical' && arrow.phase === current && time > 0
    material.opacity = approach(material.opacity, shown ? ARROW_OPACITY[arrow.kind] : 0, delta, FADE_TIME_CONSTANT)
    arrow.mesh.visible = material.opacity > 0.01
    const grown = shown ? Math.min(1, progress / GROW_SHARE) : 1
    const shaftTriangles = (arrow.total - 3) / 3
    const visibleTriangles = grown >= 1 ? arrow.total / 3 : Math.max(1, Math.floor(shaftTriangles * grown))
    arrow.mesh.geometry.setDrawRange(0, visibleTriangles * 3)
  }
}

export function Arrows({ battle, field }: { battle: Battle; field: HeightField }) {
  const arrows = useMemo<ArrowMesh[]>(
    () =>
      battle.phases.flatMap((phase, index) =>
        phase.arrows.map((arrow) => {
          const geometry = arrowGeometry(arrow, field)
          const mesh = new Mesh(geometry, overlayMaterial(SIDE_COLORS[arrow.side], 0))
          mesh.frustumCulled = false
          mesh.renderOrder = 6
          mesh.visible = false
          return { phase: index, kind: arrow.kind, mesh, total: geometry.index!.count }
        }),
      ),
    [battle, field],
  )

  const dispose = useMemo(
    () => () => {
      for (const arrow of arrows) {
        arrow.mesh.geometry.dispose()
        ;(arrow.mesh.material as MeshBasicMaterial).dispose()
      }
    },
    [arrows],
  )
  useDeferredDispose(dispose)

  useFrame((_, delta) => updateArrows(arrows, battle.phases.length, delta))

  return (
    <>
      {arrows.map((arrow) => (
        <primitive key={arrow.mesh.uuid} object={arrow.mesh} />
      ))}
    </>
  )
}
