import { CatmullRomCurve3, Vector3, type Box3 } from 'three'

export interface CameraStop {
  position: Vector3
  target: Vector3
}

export const LOOK_LIMITS = { yaw: 0.45, pitch: 0.22 } as const

const MIN_TRAVEL_SECONDS = 2.4
const MAX_TRAVEL_SECONDS = 6.5
const TRAVEL_METERS_PER_SECOND = 280
const CRANE_LIFT = 0.18
const MARKER_FOCUS_METERS = 60

export function travelSeconds(from: CameraStop, to: CameraStop): number {
  const distance = from.position.distanceTo(to.position)
  return Math.min(MAX_TRAVEL_SECONDS, Math.max(MIN_TRAVEL_SECONDS, 1.6 + distance / TRAVEL_METERS_PER_SECOND))
}

export function travelCurve(from: CameraStop, to: CameraStop): CatmullRomCurve3 {
  const distance = from.position.distanceTo(to.position)
  const middle = from.position.clone().lerp(to.position, 0.5)
  middle.y = (from.position.y + to.position.y) / 2 + distance * CRANE_LIFT
  return new CatmullRomCurve3([from.position.clone(), middle, to.position.clone()], false, 'centripetal')
}

export function clampLook(yaw: number, pitch: number): { yaw: number; pitch: number } {
  return {
    yaw: Math.max(-LOOK_LIMITS.yaw, Math.min(LOOK_LIMITS.yaw, yaw)),
    pitch: Math.max(-LOOK_LIMITS.pitch, Math.min(LOOK_LIMITS.pitch, pitch)),
  }
}

export function stopFromMarker(position: Vector3, forward: Vector3, focus = MARKER_FOCUS_METERS): CameraStop {
  return { position: position.clone(), target: position.clone().addScaledVector(forward.clone().normalize(), focus) }
}

export function overviewStop(bounds: Box3, azimuthDegrees: number, elevationDegrees: number): CameraStop {
  const center = bounds.getCenter(new Vector3())
  const size = bounds.getSize(new Vector3())
  const radius = Math.max(size.x, size.z) * 0.55
  const azimuth = (azimuthDegrees * Math.PI) / 180
  const elevation = (elevationDegrees * Math.PI) / 180
  const horizontal = Math.cos(elevation) * radius
  const position = new Vector3(
    center.x + Math.sin(azimuth) * horizontal,
    bounds.min.y + Math.sin(elevation) * radius,
    center.z - Math.cos(azimuth) * horizontal,
  )
  return { position, target: new Vector3(center.x, bounds.min.y, center.z) }
}

export function lookDirection(position: Vector3, target: Vector3, yaw: number, pitch: number, result = new Vector3()): Vector3 {
  result.subVectors(target, position)
  const length = result.length()
  if (length === 0) return result.set(0, 0, -1)
  const heading = Math.atan2(result.x, result.z) + yaw
  const tilt = Math.max(-1.5, Math.min(1.5, Math.asin(result.y / length) + pitch))
  return result.set(Math.sin(heading) * Math.cos(tilt), Math.sin(tilt), Math.cos(heading) * Math.cos(tilt))
}
