import { Environment, Sky } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { Color, Vector3, type DirectionalLight } from 'three'

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

const SHADOW_MAP_SIZE = 2048
const MIN_SHADOW_EXTENT = 140
const MAX_SHADOW_EXTENT = 1400
const SUN_DISTANCE = 3000
const SKY_DISTANCE = 50000

export function sunDirection(sun: SunSettings): Vector3 {
  const azimuth = (sun.azimuth * Math.PI) / 180
  const elevation = (sun.elevation * Math.PI) / 180
  return new Vector3(Math.sin(azimuth) * Math.cos(elevation), Math.sin(elevation), -Math.cos(azimuth) * Math.cos(elevation))
}

export function Atmosphere({ sun, haze, shadows }: { sun: SunSettings; haze: HazeSettings; shadows: boolean }) {
  const light = useRef<DirectionalLight>(null)
  const direction = useMemo(() => sunDirection(sun), [sun])
  const skyPosition = useMemo(() => direction.clone().multiplyScalar(SUN_DISTANCE).toArray(), [direction])
  const hazeColor = useMemo(() => new Color(haze.color), [haze.color])
  const focusRef = useRef(new Vector3())

  useFrame(({ camera, scene: frameScene }) => {
    frameScene.background = null
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
      <Sky distance={SKY_DISTANCE} sunPosition={skyPosition} turbidity={7} rayleigh={1.6} mieCoefficient={0.006} mieDirectionalG={0.86} />
      <Environment frames={1} resolution={128}>
        <Sky sunPosition={skyPosition} turbidity={7} rayleigh={1.6} mieCoefficient={0.006} mieDirectionalG={0.86} />
      </Environment>
      <fogExp2 attach="fog" args={[hazeColor, haze.density]} />
      <hemisphereLight args={['#c9d6e8', '#6b5440', 0.55]} />
      <directionalLight
        ref={light}
        color={sun.color}
        intensity={sun.intensity}
        castShadow={shadows}
        shadow-mapSize={[SHADOW_MAP_SIZE, SHADOW_MAP_SIZE]}
        shadow-bias={-0.0004}
        shadow-normalBias={0.6}
        shadow-camera-near={10}
        shadow-camera-far={SUN_DISTANCE * 2}
      />
    </>
  )
}
