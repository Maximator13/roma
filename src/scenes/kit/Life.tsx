import { useFrame } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import {
  BufferAttribute,
  BufferGeometry,
  AdditiveBlending,
  CanvasTexture,
  DoubleSide,
  Euler,
  InstancedBufferAttribute,
  InstancedMesh,
  Matrix4,
  MeshBasicMaterial,
  MeshLambertMaterial,
  PlaneGeometry,
  PointLight,
  Quaternion,
  Sprite,
  SpriteMaterial,
  Vector3,
  type Mesh,
} from 'three'
import { prefersReducedMotion } from '../../core/motion.ts'
import type { QualityTier } from '../../stage/quality.ts'
import type { SceneModel } from './model.ts'
import { pingPong, pointAlong, routeFrom, walkerCount, type Route } from './paths.ts'

const WALKER_SPACING = 22
const WALKERS_PER_ROUTE = 12
export interface PuffSettings {
  particles: number
  life: number
  rise: number
  drift: [number, number]
  sway: number
  scatter: number
  size: [number, number]
  opacity: number
  color: string
}

const SMOKE: PuffSettings = { particles: 28, life: 9, rise: 1.4, drift: [0.9, -0.4], sway: 0.35, scatter: 0, size: [1.2, 0.9], opacity: 0.5, color: '#7d7b7c' }
const PLUME: PuffSettings = { particles: 300, life: 48, rise: 230, drift: [150, 95], sway: 60, scatter: 350, size: [900, 110], opacity: 0.95, color: '#463e37' }
const ASH: PuffSettings = { particles: 700, life: 70, rise: -4.5, drift: [1.2, 0.8], sway: 1.5, scatter: 450, size: [0.35, 0], opacity: 0.9, color: '#3c3732' }
const BEACON_SMOKE: PuffSettings = { particles: 40, life: 14, rise: 4, drift: [3, -1.5], sway: 1.2, scatter: 0.6, size: [3, 2.2], opacity: 0.45, color: '#5d5550' }
const BIRDS_PER_FLOCK = 22
const DENSITY: Record<QualityTier, number> = { low: 0.5, medium: 1, high: 1 }

function seeded(index: number): number {
  const value = Math.sin(index * 127.1 + 311.7) * 43758.5453
  return value - Math.floor(value)
}

function markMoved(mesh: InstancedMesh) {
  mesh.instanceMatrix.needsUpdate = true
}

function markOpacity(attribute: InstancedBufferAttribute) {
  attribute.needsUpdate = true
}

export function standingGeometry(source: Mesh): BufferGeometry {
  source.updateWorldMatrix(true, false)
  const geometry = source.geometry.clone().applyMatrix4(source.matrixWorld)
  geometry.computeBoundingBox()
  const box = geometry.boundingBox
  if (box) geometry.translate(-(box.min.x + box.max.x) / 2, -box.min.y, -(box.min.z + box.max.z) / 2)
  return geometry
}

interface Walker {
  route: Route
  variant: number
  slot: number
  offset: number
  speed: number
}

function planWalkers(routes: Map<string, Vector3[]>, variants: number, density: number): Walker[] {
  const plan: Walker[] = []
  const slots = new Array<number>(variants).fill(0)
  let index = 0
  for (const points of routes.values()) {
    if (points.length < 2) continue
    const route = routeFrom(points)
    const count = Math.max(1, Math.round(walkerCount(route.total, WALKER_SPACING, WALKERS_PER_ROUTE) * density))
    for (let walker = 0; walker < count; walker += 1) {
      const variant = Math.floor(seeded(index) * variants) % variants
      plan.push({ route, variant, slot: slots[variant]!, offset: seeded(index + 1) * route.total * 2, speed: 1 + seeded(index + 2) * 0.5 })
      slots[variant]! += 1
      index += 3
    }
  }
  return plan
}

function Walkers({ model, density, shadows }: { model: SceneModel; density: number; shadows: boolean }) {
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])
  const plan = useMemo(() => planWalkers(model.routes, model.walkers.length, density), [model, density])
  const meshes = useMemo(
    () =>
      model.walkers.map((source: Mesh, variant) => {
        const count = plan.filter((walker) => walker.variant === variant).length
        const mesh = new InstancedMesh(standingGeometry(source), source.material, Math.max(1, count))
        mesh.count = count
        mesh.frustumCulled = false
        return mesh
      }),
    [model, plan],
  )
  const live = useRef(meshes)
  useEffect(() => {
    live.current = meshes
    return () =>
      meshes.forEach((mesh) => {
        mesh.geometry.dispose()
        mesh.dispose()
      })
  }, [meshes])
  const scratchRef = useRef({ here: new Vector3(), ahead: new Vector3(), matrix: new Matrix4(), turn: new Quaternion(), euler: new Euler(), unit: new Vector3(1, 1, 1) })

  useFrame(({ clock }) => {
    const time = reducedMotion ? 0 : clock.elapsedTime
    const scratch = scratchRef.current
    for (const walker of plan) {
      const mesh = live.current[walker.variant]
      if (!mesh) continue
      const travelled = walker.offset + time * walker.speed
      const { distance, forward } = pingPong(travelled, walker.route.total)
      pointAlong(walker.route, distance, scratch.here)
      pointAlong(walker.route, distance + (forward ? 0.5 : -0.5), scratch.ahead)
      const dx = scratch.ahead.x - scratch.here.x
      const dz = scratch.ahead.z - scratch.here.z
      scratch.euler.set(0, Math.atan2(-dx, -dz), 0)
      scratch.turn.setFromEuler(scratch.euler)
      scratch.here.y += Math.abs(Math.sin(travelled * 3.4)) * 0.05
      scratch.matrix.compose(scratch.here, scratch.turn, scratch.unit)
      mesh.setMatrixAt(walker.slot, scratch.matrix)
    }
    live.current.forEach(markMoved)
  })

  return (
    <>
      {meshes.map((mesh, index) => (
        <primitive key={index} object={mesh} castShadow={shadows} receiveShadow={shadows} />
      ))}
    </>
  )
}

function smokeTexture(): CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = 64
  canvas.height = 64
  const context = canvas.getContext('2d')
  if (context) {
    const gradient = context.createRadialGradient(32, 32, 0, 32, 32, 32)
    gradient.addColorStop(0, 'rgba(255,255,255,1)')
    gradient.addColorStop(0.5, 'rgba(255,255,255,0.45)')
    gradient.addColorStop(1, 'rgba(255,255,255,0)')
    context.fillStyle = gradient
    context.fillRect(0, 0, 64, 64)
  }
  return new CanvasTexture(canvas)
}

function smokeMaterial(color: string): MeshBasicMaterial {
  const material = new MeshBasicMaterial({ map: smokeTexture(), color, transparent: true, depthWrite: false })
  material.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', ['attribute float puffOpacity;', 'varying float vPuffOpacity;', '#include <common>'].join('\n'))
      .replace('#include <begin_vertex>', ['#include <begin_vertex>', 'vPuffOpacity = puffOpacity;'].join('\n'))
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', ['varying float vPuffOpacity;', '#include <common>'].join('\n'))
      .replace('#include <opaque_fragment>', ['#include <opaque_fragment>', 'gl_FragColor.a *= vPuffOpacity;'].join('\n'))
  }
  return material
}

function Puffs({ sources, settings }: { sources: Vector3[]; settings: PuffSettings }) {
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])
  const puffs = useMemo(() => {
    const count = Math.max(1, sources.length * settings.particles)
    const geometry = new PlaneGeometry(1, 1)
    geometry.setAttribute('puffOpacity', new InstancedBufferAttribute(new Float32Array(count), 1))
    const mesh = new InstancedMesh(geometry, smokeMaterial(settings.color), count)
    mesh.frustumCulled = false
    mesh.renderOrder = 2
    return mesh
  }, [sources, settings])
  const live = useRef(puffs)
  useEffect(() => {
    live.current = puffs
    return () => {
      puffs.geometry.dispose()
      const material = puffs.material as MeshBasicMaterial
      material.map?.dispose()
      material.dispose()
      puffs.dispose()
    }
  }, [puffs])
  const scratchRef = useRef({ position: new Vector3(), scale: new Vector3(), matrix: new Matrix4() })

  useFrame(({ clock, camera }) => {
    const { particles, life, rise, drift, sway, scatter, size, opacity: strength } = settings
    const time = reducedMotion ? life / 2 : clock.elapsedTime
    const scratch = scratchRef.current
    const mesh = live.current
    const opacity = mesh.geometry.getAttribute('puffOpacity') as InstancedBufferAttribute
    const start = rise < 0 ? -rise * life : 0
    sources.forEach((source, sourceIndex) => {
      for (let particle = 0; particle < particles; particle += 1) {
        const index = sourceIndex * particles + particle
        const age = (time + (particle / particles) * life) % life
        const spread = age * sway
        const angle = seeded(index) * Math.PI * 2
        const radius = Math.sqrt(seeded(index + 1)) * scatter
        scratch.position.set(
          source.x + Math.cos(angle) * radius + age * drift[0] + Math.sin(age * 1.3 + particle) * spread,
          source.y + start + age * rise,
          source.z + Math.sin(angle) * radius + age * drift[1] + Math.cos(age * 1.1 + particle) * spread,
        )
        const scale = size[0] + age * size[1]
        scratch.scale.set(scale, scale, scale)
        scratch.matrix.compose(scratch.position, camera.quaternion, scratch.scale)
        mesh.setMatrixAt(index, scratch.matrix)
        opacity.setX(index, strength * Math.min(1, (age / life) * 8) * (1 - age / life))
      }
    })
    markMoved(mesh)
    markOpacity(opacity)
  })

  return <primitive object={puffs} />
}

function birdGeometry(): BufferGeometry {
  const geometry = new BufferGeometry()
  geometry.setAttribute(
    'position',
    new BufferAttribute(new Float32Array([0, 0, 0.12, -0.45, 0.12, -0.05, 0, 0, -0.12, 0, 0, 0.12, 0, 0, -0.12, 0.45, 0.12, -0.05]), 3),
  )
  geometry.computeVertexNormals()
  return geometry
}

function Flocks({ centres, density }: { centres: Vector3[]; density: number }) {
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])
  const perFlock = Math.max(6, Math.round(BIRDS_PER_FLOCK * density))
  const mesh = useMemo(() => {
    const birds = new InstancedMesh(birdGeometry(), new MeshLambertMaterial({ color: '#2b211a', side: DoubleSide }), Math.max(1, centres.length * perFlock))
    birds.frustumCulled = false
    return birds
  }, [centres, perFlock])
  const live = useRef(mesh)
  useEffect(() => {
    live.current = mesh
    return () => {
      mesh.geometry.dispose()
      ;(mesh.material as MeshLambertMaterial).dispose()
      mesh.dispose()
    }
  }, [mesh])
  const scratchRef = useRef({ position: new Vector3(), matrix: new Matrix4(), turn: new Quaternion(), euler: new Euler(), scale: new Vector3() })

  useFrame(({ clock }) => {
    const time = reducedMotion ? 0 : clock.elapsedTime
    const scratch = scratchRef.current
    centres.forEach((centre, flock) => {
      for (let bird = 0; bird < perFlock; bird += 1) {
        const index = flock * perFlock + bird
        const radius = 18 + seeded(index) * 45
        const speed = (0.16 + seeded(index + 7) * 0.12) * (seeded(index + 3) > 0.5 ? 1 : -1)
        const angle = seeded(index + 11) * Math.PI * 2 + time * speed
        scratch.position.set(
          centre.x + Math.cos(angle) * radius,
          centre.y + Math.sin(time * 0.7 + bird) * 4 + seeded(index + 5) * 10,
          centre.z + Math.sin(angle) * radius,
        )
        scratch.euler.set(0, -angle + (speed > 0 ? 0 : Math.PI), 0)
        scratch.turn.setFromEuler(scratch.euler)
        const flap = reducedMotion ? 1 : 0.4 + Math.abs(Math.sin(time * 9 + bird * 1.7)) * 1.2
        scratch.scale.set(1.4, 1.4 * flap, 1.4)
        scratch.matrix.compose(scratch.position, scratch.turn, scratch.scale)
        live.current.setMatrixAt(index, scratch.matrix)
      }
    })
    live.current.instanceMatrix.needsUpdate = true
  })

  return <primitive object={mesh} />
}

function glowTexture(): CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = 128
  const context = canvas.getContext('2d')!
  const gradient = context.createRadialGradient(64, 64, 0, 64, 64, 64)
  gradient.addColorStop(0, 'rgba(255,240,200,1)')
  gradient.addColorStop(0.18, 'rgba(255,190,90,0.85)')
  gradient.addColorStop(0.5, 'rgba(255,120,30,0.25)')
  gradient.addColorStop(1, 'rgba(255,90,20,0)')
  context.fillStyle = gradient
  context.fillRect(0, 0, 128, 128)
  return new CanvasTexture(canvas)
}

function Beacon({ position }: { position: Vector3 }) {
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])
  const smoke = useMemo(() => [position.clone().setY(position.y + 3)], [position])
  const parts = useMemo(() => {
    const material = new SpriteMaterial({ map: glowTexture(), blending: AdditiveBlending, depthWrite: false, toneMapped: false })
    material.color.setScalar(2.4)
    const glow = new Sprite(material)
    glow.position.copy(position)
    glow.renderOrder = 3
    const light = new PointLight('#ffa64d', 9000, 900, 1.6)
    light.position.copy(position)
    return { glow, light }
  }, [position])
  const live = useRef(parts)
  useEffect(
    () => {
      live.current = parts
      return () => {
        parts.glow.material.map?.dispose()
        parts.glow.material.dispose()
        parts.light.dispose()
      }
    },
    [parts],
  )
  useFrame(({ clock }) => {
    const time = reducedMotion ? 0 : clock.elapsedTime
    const flicker = 0.85 + 0.1 * Math.sin(time * 13.0) + 0.05 * Math.sin(time * 31.0 + 1.3)
    live.current.glow.scale.setScalar(26 * flicker)
    live.current.light.intensity = 9000 * flicker
  })
  return (
    <>
      <primitive object={parts.glow} />
      <primitive object={parts.light} />
      <Puffs sources={smoke} settings={BEACON_SMOKE} />
    </>
  )
}

export function Life({ model, quality, shadows }: { model: SceneModel; quality: QualityTier; shadows: boolean }) {
  const density = DENSITY[quality]
  return (
    <>
      {model.walkers.length > 0 && model.routes.size > 0 && <Walkers model={model} density={density} shadows={shadows} />}
      {model.smokes.length > 0 && <Puffs sources={model.smokes} settings={SMOKE} />}
      {model.anchors.has('eruption_vent') && <Puffs sources={[model.anchors.get('eruption_vent')!]} settings={PLUME} />}
      {model.ashes.length > 0 && <Puffs sources={model.ashes} settings={ASH} />}
      {model.anchors.has('beacon') && <Beacon position={model.anchors.get('beacon')!} />}
      {model.flocks.length > 0 && <Flocks centres={model.flocks} density={density} />}
    </>
  )
}
