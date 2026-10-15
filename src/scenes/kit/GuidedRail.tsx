import { useFrame, useThree } from '@react-three/fiber'
import gsap from 'gsap'
import { useEffect, useMemo, useRef } from 'react'
import { Vector3, type CatmullRomCurve3, type PerspectiveCamera } from 'three'
import { EASE, prefersReducedMotion } from '../../core/motion.ts'
import type { UiInsets } from '../../map/MapStage.tsx'
import { approach } from '../../map/camera.ts'
import { clampLook, lookDirection, travelCurve, travelSeconds, type CameraStop } from './rail.ts'

const LOOK_SPEED = 0.004
const LOOK_TIME_CONSTANT = 0.25
const SWAY_METERS = 0.35
const NEAR = 0.5
const FAR = 60000
const MAP_NEAR = 0.05
const MAP_FAR = 400

interface Travel {
  curve: CatmullRomCurve3 | null
  end: Vector3
  fromTarget: Vector3
  toTarget: Vector3
  progress: number
}

function settled(stop: CameraStop): Travel {
  return { curve: null, end: stop.position.clone(), fromTarget: stop.target.clone(), toTarget: stop.target.clone(), progress: 1 }
}

export function GuidedRail({ stops, index, insets }: { stops: CameraStop[]; index: number; insets: UiInsets }) {
  const element = useThree((state) => state.gl.domElement)
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])
  const first = stops[0]
  const travel = useRef<Travel | null>(first ? settled(first) : null)
  const pose = useRef({ position: first?.position.clone() ?? new Vector3(), target: first?.target.clone() ?? new Vector3() })
  const look = useRef({ yaw: 0, pitch: 0, goalYaw: 0, goalPitch: 0 })
  const scratchRef = useRef({ position: new Vector3(), target: new Vector3(), direction: new Vector3() })

  useEffect(() => {
    const destination = stops[Math.min(index, stops.length - 1)]
    if (!destination) return
    look.current.goalYaw = 0
    look.current.goalPitch = 0
    const from = { position: pose.current.position.clone(), target: pose.current.target.clone() }
    if (reducedMotion || from.position.distanceTo(destination.position) < 0.01) {
      travel.current = settled(destination)
      return
    }
    const next: Travel = {
      curve: travelCurve(from, destination),
      end: destination.position.clone(),
      fromTarget: from.target,
      toTarget: destination.target.clone(),
      progress: 0,
    }
    travel.current = next
    const tween = gsap.to(next, { progress: 1, duration: travelSeconds(from, destination), ease: EASE })
    return () => {
      tween.kill()
    }
  }, [index, stops, reducedMotion])

  useEffect(() => {
    let last: { x: number; y: number } | null = null
    const onDown = (event: PointerEvent) => {
      if (event.button === 0) last = { x: event.clientX, y: event.clientY }
    }
    const onMove = (event: PointerEvent) => {
      if (!last) return
      const state = look.current
      const limited = clampLook(state.goalYaw + (event.clientX - last.x) * LOOK_SPEED, state.goalPitch + (event.clientY - last.y) * LOOK_SPEED)
      state.goalYaw = limited.yaw
      state.goalPitch = limited.pitch
      last = { x: event.clientX, y: event.clientY }
    }
    const onUp = () => {
      last = null
    }
    element.addEventListener('pointerdown', onDown)
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    return () => {
      element.removeEventListener('pointerdown', onDown)
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
  }, [element])

  useFrame(({ camera: frameCamera, clock, size }, delta) => {
    const camera = frameCamera as PerspectiveCamera
    const scratch = scratchRef.current
    const current = travel.current
    if (!current) return
    if (current.curve) current.curve.getPoint(current.progress, scratch.position)
    else scratch.position.copy(current.end)
    scratch.target.lerpVectors(current.fromTarget, current.toTarget, current.progress)
    pose.current.position.copy(scratch.position)
    pose.current.target.copy(scratch.target)

    const state = look.current
    const timeConstant = reducedMotion ? 0 : LOOK_TIME_CONSTANT
    state.yaw = approach(state.yaw, state.goalYaw, delta, timeConstant)
    state.pitch = approach(state.pitch, state.goalPitch, delta, timeConstant)
    if (!reducedMotion) {
      const time = clock.elapsedTime
      scratch.position.x += Math.sin(time * 0.37) * SWAY_METERS
      scratch.position.y += Math.sin(time * 0.23) * SWAY_METERS * 0.5
    }
    lookDirection(scratch.position, scratch.target, state.yaw, state.pitch, scratch.direction)
    camera.position.copy(scratch.position)
    camera.lookAt(scratch.target.copy(scratch.position).add(scratch.direction))
    if (camera.near !== NEAR || camera.far !== FAR) {
      camera.near = NEAR
      camera.far = FAR
    }
    camera.setViewOffset(size.width, size.height, (insets.right - insets.left) / 2, (insets.bottom - insets.top) / 2, size.width, size.height)
    camera.updateProjectionMatrix()
  })

  useEffect(
    () => () => {
      travel.current = null
    },
    [],
  )

  return <CameraRestore near={MAP_NEAR} far={MAP_FAR} />
}

function CameraRestore({ near, far }: { near: number; far: number }) {
  const camera = useThree((state) => state.camera)
  useEffect(
    () => () => {
      const perspective = camera as PerspectiveCamera
      perspective.near = near
      perspective.far = far
      perspective.updateProjectionMatrix()
    },
    [camera, near, far],
  )
  return null
}
