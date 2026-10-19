import { useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import { Vector3, type PerspectiveCamera } from 'three'
import type { UiInsets } from '../../map/MapStage.tsx'
import { approach } from '../../map/camera.ts'
import { heightAt, type HeightField } from './heightfield.ts'
import type { Battle } from './schema.ts'
import { useBattle } from './store.ts'
import { phaseIndexAt, stateAt, type UnitState, type UnitTrack } from './timeline.ts'

const DEGREES = Math.PI / 180
const TACTICAL_TILT = 52
const TILT_LIMITS = [28, 80] as const
const YAW_LIMIT = 70
const ZOOM_LIMITS = [0.35, 1.8] as const
const EYE_HEIGHT = 1.7
const TARGET_HEIGHT = 1.4
const TIME_CONSTANT = 0.9
const DRAG_SPEED = 0.25
const MAX_ASPECT = 1.6
const NEAR = { tactical: 2, ground: 0.25 }
const FAR = 60000
const MAP_NEAR = 0.05
const MAP_FAR = 400

interface Look {
  yaw: number
  tilt: number
  zoom: number
}

function useLookControls(element: HTMLElement, look: React.RefObject<Look>) {
  useEffect(() => {
    let last: { x: number; y: number } | null = null
    const pointers = new Map<number, { x: number; y: number }>()
    let pinch = 0
    const onDown = (event: PointerEvent) => {
      pointers.set(event.pointerId, { x: event.clientX, y: event.clientY })
      if (event.button === 0) last = { x: event.clientX, y: event.clientY }
    }
    const onMove = (event: PointerEvent) => {
      if (pointers.has(event.pointerId)) pointers.set(event.pointerId, { x: event.clientX, y: event.clientY })
      const state = look.current
      if (pointers.size === 2) {
        const [a, b] = [...pointers.values()]
        const distance = Math.hypot(a!.x - b!.x, a!.y - b!.y)
        if (pinch > 0) state.zoom = Math.min(ZOOM_LIMITS[1], Math.max(ZOOM_LIMITS[0], state.zoom * (pinch / distance)))
        pinch = distance
        return
      }
      if (!last) return
      state.yaw = Math.max(-YAW_LIMIT, Math.min(YAW_LIMIT, state.yaw + (event.clientX - last.x) * DRAG_SPEED))
      state.tilt = Math.max(TILT_LIMITS[0], Math.min(TILT_LIMITS[1], state.tilt + (event.clientY - last.y) * DRAG_SPEED * 0.6))
      last = { x: event.clientX, y: event.clientY }
    }
    const onUp = (event: PointerEvent) => {
      pointers.delete(event.pointerId)
      pinch = 0
      last = null
    }
    const onWheel = (event: WheelEvent) => {
      event.preventDefault()
      const state = look.current
      state.zoom = Math.min(ZOOM_LIMITS[1], Math.max(ZOOM_LIMITS[0], state.zoom * Math.exp(event.deltaY * 0.0012)))
    }
    element.addEventListener('pointerdown', onDown)
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    window.addEventListener('pointercancel', onUp)
    element.addEventListener('wheel', onWheel, { passive: false })
    return () => {
      element.removeEventListener('pointerdown', onDown)
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
      window.removeEventListener('pointercancel', onUp)
      element.removeEventListener('wheel', onWheel)
    }
  }, [element, look])
}

export function CameraRig({
  battle,
  tracks,
  field,
  insets,
  reducedMotion,
}: {
  battle: Battle
  tracks: UnitTrack[]
  field: HeightField
  insets: UiInsets
  reducedMotion: boolean
}) {
  const element = useThree((state) => state.gl.domElement)
  const view = useBattle((state) => state.view)
  const look = useRef<Look>({ yaw: 0, tilt: TACTICAL_TILT, zoom: 1 })
  const pose = useRef<{ position: Vector3; target: Vector3 } | null>(null)
  const goal = useMemo(() => ({ position: new Vector3(), target: new Vector3() }), [])
  const unitIndex = useMemo(() => new Map(battle.units.map((unit, index) => [unit.id, index])), [battle])
  const scratch = useMemo(() => ({}) as UnitState, [])
  useLookControls(element, look)

  useEffect(() => {
    look.current.yaw = 0
    look.current.tilt = TACTICAL_TILT
    look.current.zoom = 1
  }, [view])

  useFrame(({ camera: frameCamera, size }, delta) => {
    const camera = frameCamera as PerspectiveCamera
    const { time, view: current, controlsHeight } = useBattle.getState()
    const phase = battle.phases[phaseIndexAt(time, battle.phases.length)]!
    const state = look.current
    if (current === 'tactical') {
      const [fx, fy] = phase.focus
      goal.target.set(fx, heightAt(field, fx, -fy), -fy)
      const aspect = Math.min(MAX_ASPECT, size.width / Math.max(1, size.height))
      const distance = (phase.span / (2 * Math.tan((camera.fov * DEGREES) / 2) * aspect)) * state.zoom
      const heading = state.yaw * DEGREES
      const tilt = state.tilt * DEGREES
      goal.position.set(
        fx - Math.sin(heading) * Math.cos(tilt) * distance,
        goal.target.y + Math.sin(tilt) * distance,
        -fy + Math.cos(heading) * Math.cos(tilt) * distance,
      )
    } else {
      const view = phase.ground
      const unit = stateAt(tracks[unitIndex.get(view.unit)!]!, time, scratch)
      const facing = unit.facing * DEGREES
      const forwardX = Math.sin(facing)
      const forwardY = Math.cos(facing)
      const ex = unit.x + forwardX * view.along + forwardY * view.across
      const ey = unit.y + forwardY * view.along - forwardX * view.across
      const heading = facing + ((view.turn ?? 0) + state.yaw * 0.6) * DEGREES
      const tx = ex + Math.sin(heading) * view.look
      const ty = ey + Math.cos(heading) * view.look
      goal.position.set(ex, heightAt(field, ex, -ey) + EYE_HEIGHT, -ey)
      goal.target.set(tx, heightAt(field, tx, -ty) + TARGET_HEIGHT - (state.tilt - TACTICAL_TILT) * 0.5, -ty)
    }
    if (!pose.current || reducedMotion) pose.current = { position: goal.position.clone(), target: goal.target.clone() }
    const current3 = pose.current
    for (const axis of ['x', 'y', 'z'] as const) {
      current3.position[axis] = approach(current3.position[axis], goal.position[axis], delta, TIME_CONSTANT)
      current3.target[axis] = approach(current3.target[axis], goal.target[axis], delta, TIME_CONSTANT)
    }
    const floor = heightAt(field, current3.position.x, current3.position.z) + 1.2
    camera.position.set(current3.position.x, Math.max(floor, current3.position.y), current3.position.z)
    camera.lookAt(current3.target)
    const near = NEAR[current]
    if (camera.near !== near || camera.far !== FAR) {
      camera.near = near
      camera.far = FAR
    }
    camera.setViewOffset(size.width, size.height, (insets.right - insets.left) / 2, (insets.bottom + controlsHeight - insets.top) / 2, size.width, size.height)
    camera.updateProjectionMatrix()
  })

  return <CameraRestore />
}

function CameraRestore() {
  const camera = useThree((state) => state.camera)
  useEffect(
    () => () => {
      const perspective = camera as PerspectiveCamera
      perspective.near = MAP_NEAR
      perspective.far = MAP_FAR
      perspective.updateProjectionMatrix()
    },
    [camera],
  )
  return null
}
