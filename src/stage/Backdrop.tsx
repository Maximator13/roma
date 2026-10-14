import { useFrame } from '@react-three/fiber'
import { useLayoutEffect, useMemo, useRef } from 'react'
import { BackSide, Color, DirectionalLight, Fog, HemisphereLight, InstancedMesh, Object3D, ShaderMaterial, Vector3 } from 'three'
import { prefersReducedMotion } from '../core/motion.ts'
import { eras } from '../data/eras.ts'
import { useApp } from '../store.ts'
import { gradingAt, type Grading } from './grading.ts'

const COLUMNS_PER_ROW = 8
const COLUMN_SPACING = 3.4
const ROW_DEPTHS = [-9, -13]
const SHAFT_HEIGHT = 5.6
const BASE_HEIGHT = 0.4
const CAPITAL_HEIGHT = 0.4
const SUN_DISTANCE = 60
const COLUMN_COUNT = COLUMNS_PER_ROW * ROW_DEPTHS.length
const ROW_WIDTH = (COLUMNS_PER_ROW - 1) * COLUMN_SPACING + 2

const skyVertexShader = `
varying vec3 vDirection;
void main() {
  vDirection = normalize(position);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`

const skyFragmentShader = `
uniform vec3 topColor;
uniform vec3 horizonColor;
uniform vec3 sunColor;
uniform vec3 sunDirection;
varying vec3 vDirection;
void main() {
  float height = clamp(vDirection.y, 0.0, 1.0);
  vec3 color = mix(horizonColor, topColor, pow(height, 0.5));
  float glow = pow(max(dot(normalize(vDirection), sunDirection), 0.0), 18.0);
  gl_FragColor = vec4(color + sunColor * glow * 0.8, 1.0);
}
`

function columnPositions(): Vector3[] {
  return ROW_DEPTHS.flatMap((z) =>
    Array.from({ length: COLUMNS_PER_ROW }, (_, index) => new Vector3((index - (COLUMNS_PER_ROW - 1) / 2) * COLUMN_SPACING, 0, z)),
  )
}

function fillInstances(mesh: InstancedMesh | null, height: number) {
  if (!mesh) return
  const placement = new Object3D()
  columnPositions().forEach((position, index) => {
    placement.position.set(position.x, height, position.z)
    placement.updateMatrix()
    mesh.setMatrixAt(index, placement.matrix)
  })
  mesh.instanceMatrix.needsUpdate = true
}

function sunDirection(grading: Grading, target: Vector3): Vector3 {
  return target.set(-0.85, Math.max(0.03, grading.sunElevation), 0.25).normalize()
}

function Portico({ shadows }: { shadows: boolean }) {
  const bases = useRef<InstancedMesh>(null)
  const shafts = useRef<InstancedMesh>(null)
  const capitals = useRef<InstancedMesh>(null)

  useLayoutEffect(() => {
    fillInstances(bases.current, BASE_HEIGHT / 2)
    fillInstances(shafts.current, BASE_HEIGHT + SHAFT_HEIGHT / 2)
    fillInstances(capitals.current, BASE_HEIGHT + SHAFT_HEIGHT + CAPITAL_HEIGHT / 2)
  }, [])

  const entablatureHeight = BASE_HEIGHT + SHAFT_HEIGHT + CAPITAL_HEIGHT + 0.5
  return (
    <group>
      <instancedMesh ref={bases} args={[undefined, undefined, COLUMN_COUNT]} castShadow={shadows} receiveShadow={shadows}>
        <boxGeometry args={[1.3, BASE_HEIGHT, 1.3]} />
        <meshStandardMaterial color="#ddd5c6" roughness={0.7} />
      </instancedMesh>
      <instancedMesh ref={shafts} args={[undefined, undefined, COLUMN_COUNT]} castShadow={shadows} receiveShadow={shadows}>
        <cylinderGeometry args={[0.44, 0.52, SHAFT_HEIGHT, 24]} />
        <meshStandardMaterial color="#ece6da" roughness={0.55} />
      </instancedMesh>
      <instancedMesh ref={capitals} args={[undefined, undefined, COLUMN_COUNT]} castShadow={shadows} receiveShadow={shadows}>
        <boxGeometry args={[1.25, CAPITAL_HEIGHT, 1.25]} />
        <meshStandardMaterial color="#e2dacb" roughness={0.6} />
      </instancedMesh>
      {ROW_DEPTHS.map((z) => (
        <mesh key={z} position={[0, entablatureHeight, z]} castShadow={shadows} receiveShadow={shadows}>
          <boxGeometry args={[ROW_WIDTH, 1, 1.4]} />
          <meshStandardMaterial color="#e6dfd1" roughness={0.65} />
        </mesh>
      ))}
      <mesh position={[0, -0.15, (ROW_DEPTHS[0]! + ROW_DEPTHS[1]!) / 2]} receiveShadow={shadows}>
        <boxGeometry args={[ROW_WIDTH + 2, 0.3, 7]} />
        <meshStandardMaterial color="#cfc5b3" roughness={0.8} />
      </mesh>
    </group>
  )
}

export function Backdrop({ shadows }: { shadows: boolean }) {
  const fog = useRef<Fog>(null)
  const sun = useRef<DirectionalLight>(null)
  const hemisphere = useRef<HemisphereLight>(null)
  const direction = useMemo(() => new Vector3(), [])
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])
  const sky = useMemo(
    () =>
      new ShaderMaterial({
        vertexShader: skyVertexShader,
        fragmentShader: skyFragmentShader,
        side: BackSide,
        depthWrite: false,
        fog: false,
        uniforms: {
          topColor: { value: new Color() },
          horizonColor: { value: new Color() },
          sunColor: { value: new Color() },
          sunDirection: { value: new Vector3(0, 1, 0) },
        },
      }),
    [],
  )

  useFrame(({ camera, clock }) => {
    const grading = gradingAt(useApp.getState().view.center, eras)
    sunDirection(grading, direction)
    sky.uniforms.topColor!.value.fromArray(grading.skyTop)
    sky.uniforms.horizonColor!.value.fromArray(grading.skyHorizon)
    sky.uniforms.sunColor!.value.fromArray(grading.sun)
    sky.uniforms.sunDirection!.value.copy(direction)
    fog.current?.color.fromArray(grading.skyHorizon)
    sun.current?.color.fromArray(grading.sun)
    sun.current?.position.copy(direction).multiplyScalar(SUN_DISTANCE)
    hemisphere.current?.color.fromArray(grading.skyTop)
    hemisphere.current?.groundColor.fromArray(grading.fog)
    if (!reducedMotion) {
      const t = clock.elapsedTime * 0.05
      camera.position.set(Math.sin(t) * 2.5, 2.4 + Math.sin(t * 0.7) * 0.2, 8)
      camera.lookAt(0, 3.6, -11)
    }
  })

  return (
    <>
      <fog ref={fog} attach="fog" args={[0x000000, 20, 110]} />
      <mesh material={sky} renderOrder={-1}>
        <sphereGeometry args={[150, 32, 16]} />
      </mesh>
      <hemisphereLight ref={hemisphere} args={[0xffffff, 0x3a2c20, 0.7]} />
      <directionalLight
        ref={sun}
        intensity={2.6}
        castShadow={shadows}
        shadow-mapSize={[1024, 1024]}
        shadow-camera-left={-20}
        shadow-camera-right={20}
        shadow-camera-top={16}
        shadow-camera-bottom={-6}
      />
      <mesh rotation-x={-Math.PI / 2} receiveShadow={shadows}>
        <planeGeometry args={[300, 300]} />
        <meshStandardMaterial color="#a8957a" roughness={0.95} />
      </mesh>
      <Portico shadows={shadows} />
    </>
  )
}
