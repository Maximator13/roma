import { Environment, Sky } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { Color, Vector3, type DirectionalLight, type HemisphereLight } from 'three'
import { approach } from '../../map/camera.ts'

export interface SunSettings {
  azimuth: number
  elevation: number
  color: string
  intensity: number
}

export interface HazeSettings {
  color: string
  density: number
}

const MIN_SHADOW_EXTENT = 140
const MAX_SHADOW_EXTENT = 1400
const SUN_DISTANCE = 3000
const SKY_DISTANCE = 50000

export function sunDirection(sun: SunSettings): Vector3 {
  const azimuth = (sun.azimuth * Math.PI) / 180
  const elevation = (sun.elevation * Math.PI) / 180
  return new Vector3(Math.sin(azimuth) * Math.cos(elevation), Math.sin(elevation), -Math.cos(azimuth) * Math.cos(elevation))
}

export interface InteriorSettings {
  center: [number, number, number]
  radius: number
  height: number
  ambientScale: number
}

const AMBIENT = 0.55

export interface SkySettings {
  turbidity: number
  rayleigh: number
}

const CLEAR_SKY: SkySettings = { turbidity: 7, rayleigh: 1.6 }
const ENVIRONMENT = 0.75

export function interiorFactor(position: Vector3, interior: InteriorSettings | undefined): number {
  if (!interior) return 0
  const [x, y, z] = interior.center
  const horizontal = Math.hypot(position.x - x, position.z - z)
  return horizontal < interior.radius && position.y > y && position.y < y + interior.height ? 1 : 0
}

export function Atmosphere({
  sun,
  haze,
  shadows,
  shadowMapSize = 2048,
  interior,
  sky = CLEAR_SKY,
}: {
  sun: SunSettings
  haze: HazeSettings
  shadows: boolean
  shadowMapSize?: number
  interior?: InteriorSettings
  sky?: SkySettings
}) {
  const ambient = useRef<HemisphereLight>(null)
  const inside = useRef(0)
  const light = useRef<DirectionalLight>(null)
  const direction = useMemo(() => sunDirection(sun), [sun])
  const skyPosition = useMemo(() => direction.clone().multiplyScalar(SUN_DISTANCE).toArray(), [direction])
  const hazeColor = useMemo(() => new Color(haze.color), [haze.color])
  const focusRef = useRef(new Vector3())

  useFrame(({ camera, scene: frameScene }, delta) => {
    frameScene.background = null
    inside.current = approach(inside.current, interiorFactor(camera.position, interior), delta, 0.4)
    const scale = 1 - inside.current * (1 - (interior?.ambientScale ?? 1))
    frameScene.environmentIntensity = ENVIRONMENT * scale
    if (ambient.current) ambient.current.intensity = AMBIENT * scale
    const current = light.current
    if (!current) return
    const focus = focusRef.current
    camera.getWorldDirection(focus)
    const reach = Math.min(600, Math.max(40, camera.position.y * 1.5))
    focus.multiplyScalar(reach).add(camera.position)
    focus.y = 0
    current.position.copy(focus).addScaledVector(direction, SUN_DISTANCE)
    current.target.position.copy(focus)
    current.target.updateMatrixWorld()
    const extent = Math.min(MAX_SHADOW_EXTENT, Math.max(MIN_SHADOW_EXTENT, camera.position.y * 1.2))
    const shadowCamera = current.shadow.camera
    if (shadowCamera.right !== extent) {
      shadowCamera.left = -extent
      shadowCamera.right = extent
      shadowCamera.top = extent
      shadowCamera.bottom = -extent
      shadowCamera.updateProjectionMatrix()
    }
  })

  return (
    <>
      <Sky distance={SKY_DISTANCE} sunPosition={skyPosition} turbidity={sky.turbidity} rayleigh={sky.rayleigh} mieCoefficient={0.006} mieDirectionalG={0.86} />
      <Environment frames={1} resolution={256} environmentIntensity={ENVIRONMENT}>
        <Sky sunPosition={skyPosition} turbidity={sky.turbidity} rayleigh={sky.rayleigh} mieCoefficient={0.006} mieDirectionalG={0.86} />
      </Environment>
      <fogExp2 attach="fog" args={[hazeColor, haze.density]} />
      <hemisphereLight ref={ambient} args={['#cfdcef', '#8a6a48', AMBIENT]} />
      <directionalLight
        ref={light}
        color={sun.color}
        intensity={sun.intensity}
        castShadow={shadows}
        shadow-mapSize={[shadowMapSize, shadowMapSize]}
        shadow-bias={-0.0004}
        shadow-normalBias={0.6}
        shadow-camera-near={10}
        shadow-camera-far={SUN_DISTANCE * 2}
      />
    </>
  )
}
