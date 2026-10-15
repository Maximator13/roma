import { useFrame, useLoader } from '@react-three/fiber'
import { use, useEffect, useMemo, useRef } from 'react'
import { Color, PlaneGeometry, TextureLoader, type Mesh, type PerspectiveCamera, type ShaderMaterial } from 'three'
import { prefersReducedMotion } from '../core/motion.ts'
import { eras } from '../data/eras.ts'
import { events } from '../data/events.ts'
import { places } from '../data/places.ts'
import { gradingAt, readableAccent } from '../stage/grading.ts'
import { useApp } from '../store.ts'
import { approach, approachGoal, goalForBounds, goalForPlace, MAX_DISTANCE, type CameraGoal } from './camera.ts'
import { MAP_SIZE } from './geo.ts'
import { MapOverlays } from './MapOverlays.tsx'
import { createHeightSampler } from './reliefSampler.ts'
import { createTerrainMaterial, LAND_SCALE } from './terrainMaterial.ts'
import { TerritoryMasks } from './TerritoryMasks.ts'
import { activeSlices, isMainTrack, sliceKey, unionBounds, type TerritoryData } from './territories.ts'

const TRANSITION_SECONDS = 1.6
const REDRAW_INTERVAL = 0.12
const OVERVIEW_PITCH = 0.95
const CLOSE_PITCH = 0.78
const INTRO_PITCH = 1.45
const CAMERA_TIME_CONSTANT = 0.9

let territoriesPromise: Promise<TerritoryData> | null = null

function loadTerritories(): Promise<TerritoryData> {
  territoriesPromise ??= fetch(`${import.meta.env.BASE_URL}geo/territories.json`)
    .then((response) => (response.ok ? (response.json() as Promise<TerritoryData>) : { attribution: '', slices: [] }))
    .catch(() => ({ attribution: '', slices: [] }))
  return territoriesPromise
}

export interface UiInsets {
  left: number
  right: number
  top: number
  bottom: number
}

function selectedPlace(): { lon: number; lat: number } | null {
  const { route } = useApp.getState()
  if (route.name !== 'event') return null
  const event = events.find((candidate) => candidate.id === route.id)
  const place = places.find((candidate) => candidate.id === event?.placeId)
  return place ? { lon: place.lon, lat: place.lat } : null
}

export function MapStage({ segments, insets, detail }: { segments: number; insets: UiInsets; detail: number }) {
  const territories = use(loadTerritories())
  const relief = useLoader(TextureLoader, `${import.meta.env.BASE_URL}geo/relief.webp`)
  const masks = useMemo(() => new TerritoryMasks(), [])
  const material = useMemo(() => createTerrainMaterial({ relief, ...masks.textures }), [relief, masks])
  const heightAt = useMemo(() => createHeightSampler(relief, LAND_SCALE), [relief])
  const geometry = useMemo(() => {
    const plane = new PlaneGeometry(MAP_SIZE.width, MAP_SIZE.depth, segments, Math.round((segments * MAP_SIZE.depth) / MAP_SIZE.width))
    plane.rotateX(-Math.PI / 2)
    return plane
  }, [segments])
  const background = useMemo(() => new Color(), [])
  const horizon = useMemo(() => new Color(), [])
  const terrain = useRef<Mesh>(null)
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])
  const state = useRef({
    goal: { x: 0, z: 0, distance: MAX_DISTANCE } as CameraGoal,
    pitch: reducedMotion ? OVERVIEW_PITCH : INTRO_PITCH,
    transitionStart: -Infinity,
    lastRedraw: -Infinity,
  })

  useEffect(() => () => {
    masks.dispose()
    material.dispose()
    geometry.dispose()
  }, [masks, material, geometry])

  useFrame(({ clock, scene, size, camera: frameCamera }, delta) => {
    const mesh = terrain.current
    if (!mesh) return
    const camera = frameCamera as PerspectiveCamera
    const now = clock.elapsedTime
    const year = useApp.getState().view.center
    const slices = activeSlices(territories.slices, year)
    const frame = state.current
    if (now - frame.lastRedraw >= REDRAW_INTERVAL && masks.show(slices, sliceKey(slices))) {
      frame.transitionStart = reducedMotion ? -Infinity : now
      frame.lastRedraw = now
    }
    const uniforms = (mesh.material as ShaderMaterial).uniforms
    uniforms.transition!.value = Math.min(1, (now - frame.transitionStart) / TRANSITION_SECONDS)
    uniforms.time!.value = now
    uniforms.detail!.value = detail

    const grading = gradingAt(year, eras)
    uniforms.sunDirection!.value.set(-0.6, 0.35 + grading.sunElevation * 0.6, -0.45).normalize()
    uniforms.sunColor!.value.fromArray(grading.sun)
    uniforms.ambientColor!.value.fromArray(grading.skyTop).lerp(horizon.fromArray(grading.skyHorizon), 0.5).multiplyScalar(0.75)
    uniforms.fogColor!.value.fromArray(grading.skyHorizon).multiplyScalar(0.8)
    uniforms.territoryColor!.value.fromArray(readableAccent(grading.accent))
    background.copy(uniforms.fogColor!.value)
    scene.background = background

    const freeWidth = Math.max(1, size.width - insets.left - insets.right)
    const freeHeight = Math.max(1, size.height - insets.top - insets.bottom)
    const visibleFov = (2 * Math.atan(Math.tan((camera.fov * Math.PI) / 360) * (freeHeight / size.height)) * 180) / Math.PI
    const place = selectedPlace()
    const bounds = unionBounds(slices.filter((slice) => isMainTrack(slice.track)))
    const target = place
      ? goalForPlace(place.lon, place.lat)
      : bounds
        ? goalForBounds(bounds, visibleFov, freeWidth / freeHeight, Math.sin(OVERVIEW_PITCH))
        : frame.goal
    const timeConstant = reducedMotion ? 0 : CAMERA_TIME_CONSTANT
    frame.goal = approachGoal(frame.goal, target, delta, timeConstant)
    frame.pitch = approach(frame.pitch, place ? CLOSE_PITCH : OVERVIEW_PITCH, delta, reducedMotion ? 0 : 1.6)

    const yaw = reducedMotion ? 0 : Math.sin(now * 0.05) * 0.06
    const horizontal = Math.cos(frame.pitch) * frame.goal.distance
    camera.position.set(
      frame.goal.x + Math.sin(yaw) * horizontal,
      Math.sin(frame.pitch) * frame.goal.distance,
      frame.goal.z + Math.cos(yaw) * horizontal,
    )
    camera.lookAt(frame.goal.x, 0, frame.goal.z)
    uniforms.fogNear!.value = frame.goal.distance * 1.1
    uniforms.fogFar!.value = frame.goal.distance * 3.2 + 12
    camera.setViewOffset(size.width, size.height, (insets.right - insets.left) / 2, (insets.bottom - insets.top) / 2, size.width, size.height)
    camera.updateProjectionMatrix()
  })

  return (
    <>
      <mesh ref={terrain} geometry={geometry} material={material} frustumCulled={false} />
      <MapOverlays height={heightAt} />
    </>
  )
}
