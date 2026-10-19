import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { Color, Euler, InstancedMesh, Matrix4, Quaternion, Vector3, type BufferGeometry, type Material } from 'three'
import { approach } from '../../map/camera.ts'
import { useDeferredDispose } from './ground.ts'
import { heightAt, type HeightField } from './heightfield.ts'
import type { Battle } from './schema.ts'
import { useBattle } from './store.ts'
import {
  deathTimes,
  figureCount,
  placeFigure,
  seeded,
  slotsFor,
  stateAt,
  trackOf,
  type Placement,
  type Slot,
  type UnitState,
  type UnitTrack,
} from './timeline.ts'

export interface TroopTemplate {
  near: BufferGeometry
  far: BufferGeometry
  material: Material | Material[]
}

interface Figure {
  unit: number
  slot: Slot
  death: number
  tint: number
}

interface Group {
  near: InstancedMesh
  far: InstancedMesh
  figures: Figure[]
}

const NEAR_DISTANCE = 240
const DEGREES = Math.PI / 180
const SCALE_TIME_CONSTANT = 0.6
const BOB: Record<UnitState['action'], { rate: number; height: number; lunge: number; sway: number }> = {
  stand: { rate: 0.4, height: 0, lunge: 0, sway: 0.02 },
  march: { rate: 1.7, height: 0.05, lunge: 0, sway: 0.03 },
  charge: { rate: 2.6, height: 0.09, lunge: 0, sway: 0.05 },
  fight: { rate: 1.3, height: 0.02, lunge: 0.35, sway: 0.18 },
  skirmish: { rate: 0.9, height: 0.02, lunge: 0.25, sway: 0.12 },
  flee: { rate: 2.8, height: 0.09, lunge: 0, sway: 0.08 },
}

export function useTracks(battle: Battle): UnitTrack[] {
  return useMemo(() => battle.units.map((unit) => trackOf(unit)), [battle])
}

function buildGroups(battle: Battle, tracks: UnitTrack[], templates: Map<string, TroopTemplate>, shadows: boolean) {
  const byKind = new Map<string, Figure[]>()
  battle.units.forEach((unit, index) => {
    const count = figureCount(unit, battle.scale)
    const start = tracks[index]!.initial
    const slots = slotsFor(count, start.width, start.depth, index + 1)
    const deaths = deathTimes(tracks[index]!, count, battle.phases.length, index + 1)
    const list = byKind.get(unit.troop) ?? []
    slots.forEach((slot, figure) => list.push({ unit: index, slot, death: deaths[figure]!, tint: 0.86 + seeded(index * 977 + figure) * 0.26 }))
    byKind.set(unit.troop, list)
  })
  const groups: Group[] = []
  for (const [kind, figures] of byKind) {
    const template = templates.get(kind)
    if (!template) throw new Error(`missing troop template: ${kind}`)
    const make = (geometry: BufferGeometry) => {
      const mesh = new InstancedMesh(geometry, template.material, figures.length)
      mesh.frustumCulled = false
      mesh.castShadow = shadows
      mesh.receiveShadow = shadows
      mesh.count = 0
      mesh.setColorAt(0, new Color(1, 1, 1))
      return mesh
    }
    groups.push({ near: make(template.near), far: make(template.far), figures })
  }
  return groups
}

export function Troops({
  battle,
  tracks,
  templates,
  field,
  shadows,
  reducedMotion,
}: {
  battle: Battle
  tracks: UnitTrack[]
  templates: Map<string, TroopTemplate>
  field: HeightField
  shadows: boolean
  reducedMotion: boolean
}) {
  const groups = useMemo(() => buildGroups(battle, tracks, templates, shadows), [battle, tracks, templates, shadows])
  const scale = useRef(battle.tacticalScale)
  const scratch = useMemo(
    () => ({
      states: battle.units.map(() => ({}) as UnitState),
      fallen: {} as UnitState,
      placement: {} as Placement,
      matrix: new Matrix4(),
      quaternion: new Quaternion(),
      euler: new Euler(0, 0, 0, 'YXZ'),
      position: new Vector3(),
      size: new Vector3(),
      color: new Color(),
    }),
    [battle],
  )

  const dispose = useMemo(
    () => () => {
      for (const group of groups) {
        group.near.dispose()
        group.far.dispose()
      }
    },
    [groups],
  )
  useDeferredDispose(dispose)

  useFrame(({ camera, clock }, delta) => {
    const { time, view } = useBattle.getState()
    const goal = view === 'tactical' ? battle.tacticalScale : 1
    scale.current = reducedMotion ? goal : approach(scale.current, goal, delta, SCALE_TIME_CONSTANT)
    const s = scale.current
    const seconds = reducedMotion ? 0 : clock.elapsedTime
    tracks.forEach((track, index) => stateAt(track, time, scratch.states[index]!))
    const near2 = NEAR_DISTANCE * NEAR_DISTANCE
    for (const group of groups) {
      let nearCount = 0
      let farCount = 0
      for (const figure of group.figures) {
        const dead = figure.death <= time
        const state = dead ? stateAt(tracks[figure.unit]!, figure.death, scratch.fallen) : scratch.states[figure.unit]!
        const placed = placeFigure(state, figure.slot, scratch.placement)
        const x = placed.x
        const z = -placed.y
        const ground = heightAt(field, x, z)
        const yaw = -placed.heading * DEGREES
        const motion = BOB[state.action]
        const beat = seconds * motion.rate * Math.PI * 2 + figure.slot.phase
        let pitch = 0
        let roll = 0
        let lift: number
        let lunge = 0
        let turn = 0
        if (dead) {
          roll = figure.slot.phase > Math.PI ? Math.PI / 2 : -Math.PI / 2
          lift = 0.25
        } else {
          lift = Math.abs(Math.sin(beat)) * motion.height
          lunge = Math.sin(beat) * motion.lunge
          turn = Math.sin(beat * 0.5) * motion.sway
          if (state.action === 'charge' || state.action === 'flee') pitch = -0.12
        }
        scratch.position.set(x - Math.sin(yaw) * lunge * s, ground + lift * s, z - Math.cos(yaw) * lunge * s)
        scratch.euler.set(pitch, yaw + turn, roll)
        scratch.quaternion.setFromEuler(scratch.euler)
        scratch.size.setScalar(s)
        scratch.matrix.compose(scratch.position, scratch.quaternion, scratch.size)
        const dx = camera.position.x - x
        const dz = camera.position.z - z
        const near = dx * dx + dz * dz < near2
        const mesh = near ? group.near : group.far
        const slot = near ? nearCount++ : farCount++
        mesh.setMatrixAt(slot, scratch.matrix)
        const shade = dead ? figure.tint * 0.7 : figure.tint
        mesh.setColorAt(slot, scratch.color.setRGB(shade, shade, shade))
      }
      for (const [mesh, count] of [
        [group.near, nearCount],
        [group.far, farCount],
      ] as const) {
        mesh.count = count
        mesh.instanceMatrix.needsUpdate = true
        if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true
      }
    }
  })

  return (
    <>
      {groups.map((group, index) => (
        <group key={index}>
          <primitive object={group.near} />
          <primitive object={group.far} />
        </group>
      ))}
    </>
  )
}
