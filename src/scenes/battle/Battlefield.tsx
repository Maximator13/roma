import { useFrame } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import { Mesh, Vector3, type BufferGeometry, type Object3D } from 'three'
import { prefersReducedMotion } from '../../core/motion.ts'
import { QUALITY } from '../../stage/quality.ts'
import { useApp } from '../../store.ts'
import { Atmosphere, type HazeSettings } from '../kit/Atmosphere.tsx'
import { standingGeometry } from '../kit/Life.tsx'
import { useSceneModel } from '../kit/model.ts'
import type { SceneProps } from '../registry.ts'
import { CameraRig } from './CameraRig.tsx'
import { Controls } from './Controls.tsx'
import { addGroundDetail } from './ground.ts'
import { rasterize, type HeightField } from './heightfield.ts'
import { Labels } from './Labels.tsx'
import { Arrows, Footprints } from './Markings.tsx'
import type { Battle } from './schema.ts'
import { useBattle } from './store.ts'
import { phaseIndexAt, pointForTime, sunAt, timeForPoint } from './timeline.ts'
import { Troops, useTracks, type TroopTemplate } from './Troops.tsx'

export interface BattleConfig {
  model: string
  battle: Battle
  haze: HazeSettings
  sunColor: string
  sunIntensity: number
}

const TROOP_PREFIX = 'troop_'
const FAR_SUFFIX = '_far'
const GROUND = 'ground'
const HEIGHT_CELL = 10
const AUTOPLAY_DELAY_MS = 1800
const END_EPSILON = 1e-4

function worldPositions(mesh: Mesh): Float32Array {
  mesh.updateWorldMatrix(true, false)
  const source = mesh.geometry.getAttribute('position')
  const result = new Float32Array(source.count * 3)
  const point = new Vector3()
  for (let index = 0; index < source.count; index += 1) {
    point.fromBufferAttribute(source, index).applyMatrix4(mesh.matrixWorld)
    result.set([point.x, point.y, point.z], index * 3)
  }
  return result
}

export function readBattlefield(root: Object3D): { templates: Map<string, TroopTemplate>; field: HeightField } {
  const near = new Map<string, Mesh>()
  const far = new Map<string, BufferGeometry>()
  let ground: Mesh | null = null
  root.updateMatrixWorld(true)
  root.traverse((child) => {
    if (!(child instanceof Mesh)) return
    if (child.name === GROUND) ground = child
    if (!child.name.startsWith(TROOP_PREFIX)) return
    child.visible = false
    const kind = child.name.slice(TROOP_PREFIX.length)
    if (kind.endsWith(FAR_SUFFIX)) far.set(kind.slice(0, -FAR_SUFFIX.length), standingGeometry(child))
    else near.set(kind, child)
  })
  if (!ground) throw new Error('battlefield model without ground mesh')
  const terrain: Mesh = ground
  for (const material of Array.isArray(terrain.material) ? terrain.material : [terrain.material]) addGroundDetail(material)
  const field = rasterize(worldPositions(terrain), terrain.geometry.index?.array ?? null, HEIGHT_CELL)
  const templates = new Map<string, TroopTemplate>()
  for (const [kind, mesh] of near) {
    templates.set(kind, { near: standingGeometry(mesh), far: far.get(kind) ?? standingGeometry(mesh), material: mesh.material })
  }
  return { templates, field }
}

function usePlayback(battle: Battle, reducedMotion: boolean) {
  const ownPoint = useRef(0)
  const total = battle.phases.length

  useEffect(() => {
    useBattle.getState().reset()
    ownPoint.current = 0
    useApp.getState().setScenePoint(0)
    if (reducedMotion) return
    const timer = setTimeout(() => {
      const state = useBattle.getState()
      if (state.time === 0 && !state.playing) state.setPlaying(true)
    }, AUTOPLAY_DELAY_MS)
    return () => clearTimeout(timer)
  }, [battle, reducedMotion])

  useEffect(
    () =>
      useBattle.subscribe((state, previous) => {
        if (state.time === previous.time) return
        const point = pointForTime(state.time, total)
        if (point === useApp.getState().scenePoint) return
        ownPoint.current = point
        useApp.getState().setScenePoint(point)
      }),
    [total],
  )

  useEffect(
    () =>
      useApp.subscribe((state, previous) => {
        if (state.scenePoint === previous.scenePoint || state.scenePoint === ownPoint.current) return
        const battleState = useBattle.getState()
        if (pointForTime(battleState.time, total) === state.scenePoint) return
        ownPoint.current = state.scenePoint
        const time = timeForPoint(state.scenePoint, reducedMotion)
        battleState.setTime(reducedMotion && state.scenePoint > 0 ? time - END_EPSILON : time)
        battleState.setPlaying(!reducedMotion && state.scenePoint > 0)
      }),
    [total, reducedMotion],
  )

  useFrame((_, delta) => {
    const state = useBattle.getState()
    if (!state.playing) return
    const phase = battle.phases[phaseIndexAt(state.time, total)]!
    const next = Math.min(total, state.time + Math.min(delta, 0.1) / phase.seconds)
    state.setTime(next)
    if (next >= total) state.setPlaying(false)
  })
}

export function Battlefield({ config, scene, insets, quality }: SceneProps & { config: BattleConfig }) {
  const { battle } = config
  const shadows = QUALITY[quality].shadows
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])
  const model = useSceneModel(config.model, shadows)
  const { templates, field } = useMemo(() => readBattlefield(model.root), [model])
  const tracks = useTracks(battle)
  const phaseIndex = useBattle((state) => phaseIndexAt(state.time, battle.phases.length))
  const sun = useMemo(() => {
    const phase = battle.phases[phaseIndex]!
    const position = sunAt(phase.hour, battle.latitude, battle.declination)
    return { ...position, color: config.sunColor, intensity: config.sunIntensity }
  }, [battle, phaseIndex, config])
  usePlayback(battle, reducedMotion)

  return (
    <>
      <Atmosphere sun={sun} haze={config.haze} shadows={shadows} />
      <primitive object={model.root} />
      <Troops battle={battle} tracks={tracks} templates={templates} field={field} shadows={shadows} reducedMotion={reducedMotion} />
      <Footprints battle={battle} tracks={tracks} field={field} />
      <Arrows battle={battle} field={field} />
      <Labels battle={battle} tracks={tracks} field={field} insets={insets} />
      <CameraRig battle={battle} tracks={tracks} field={field} insets={insets} reducedMotion={reducedMotion} />
      <Controls battle={battle} scene={scene} insets={insets} />
    </>
  )
}
