import { useLoader, useThree } from '@react-three/fiber'
import { useEffect, useMemo } from 'react'
import { Box3, Mesh, Quaternion, Vector3, type Material, type Object3D, type WebGLRenderer } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader.js'
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js'
import { groupRoutes } from './paths.ts'
import { addGroundDetail, isGroundMaterial } from './GroundDetail.ts'
import { isWaterMaterial, makeWater } from './Water.ts'

const MARKER_PREFIX = 'poi_'
const ROUTE_PREFIX = 'walk_'
const WALKER_PREFIX = 'walker_'
const SMOKE_PREFIX = 'smoke_'
const FLOCK_PREFIX = 'birds_'
const ASH_PREFIX = 'ash_'
const DISPOSE_DELAY_MS = 1000

const pendingDisposals = new Map<string, ReturnType<typeof setTimeout>>()

let ktx2: KTX2Loader | null = null

function ktx2For(renderer: WebGLRenderer): KTX2Loader {
  if (ktx2) return ktx2
  ktx2 = new KTX2Loader()
  if (import.meta.env.DEV) ktx2.setTranscoderPath(`${import.meta.env.BASE_URL}basis/`)
  return ktx2.detectSupport(renderer)
}

export function assetUrl(path: string): string {
  return `${import.meta.env.BASE_URL}assets/${path}`
}

export interface SceneModel {
  root: Object3D
  markers: Map<string, Object3D>
  bounds: Box3
  routes: Map<string, Vector3[]>
  walkers: Mesh[]
  smokes: Vector3[]
  flocks: Vector3[]
  ashes: Vector3[]
  anchors: Map<string, Vector3>
}

const ANCHOR_NAMES = new Set(['oculus', 'sunbeam_target', 'eruption_vent', 'beacon'])

export function castsShadow(node: Object3D): boolean {
  for (let current: Object3D | null = node; current; current = current.parent) {
    const flag: unknown = current.userData.cast_shadow
    if (typeof flag === 'boolean') return flag
  }
  return true
}

function worldPosition(node: Object3D): Vector3 {
  return node.getWorldPosition(new Vector3())
}

function readModel(root: Object3D): SceneModel {
  root.updateMatrixWorld(true)
  const markers = new Map<string, Object3D>()
  const named: { name: string; position: Vector3 }[] = []
  const walkers: Mesh[] = []
  const smokes: Vector3[] = []
  const flocks: Vector3[] = []
  const ashes: Vector3[] = []
  const bounds = new Box3()
  const anchors = new Map<string, Vector3>()
  root.traverse((child) => {
    if (ANCHOR_NAMES.has(child.name)) anchors.set(child.name, worldPosition(child))
    if (child.name.startsWith(MARKER_PREFIX)) markers.set(child.name.slice(MARKER_PREFIX.length), child)
    else if (child.name.startsWith(ROUTE_PREFIX)) named.push({ name: child.name, position: worldPosition(child) })
    else if (child.name.startsWith(SMOKE_PREFIX)) smokes.push(worldPosition(child))
    else if (child.name.startsWith(FLOCK_PREFIX)) flocks.push(worldPosition(child))
    else if (child.name.startsWith(ASH_PREFIX)) ashes.push(worldPosition(child))
    if (!(child instanceof Mesh)) return
    if (child.name.startsWith(WALKER_PREFIX)) walkers.push(child)
    else bounds.expandByObject(child)
  })
  return { root, markers, bounds, routes: groupRoutes(named, ROUTE_PREFIX), walkers, smokes, flocks, ashes, anchors }
}

function materialsOf(mesh: Mesh): Material[] {
  return Array.isArray(mesh.material) ? mesh.material : [mesh.material]
}

function disposeModel(root: Object3D) {
  root.traverse((child) => {
    if (!(child instanceof Mesh)) return
    child.geometry.dispose()
    for (const material of materialsOf(child)) {
      for (const value of Object.values(material)) {
        if (value && typeof value === 'object' && 'isTexture' in value) (value as { dispose: () => void }).dispose()
      }
      material.dispose()
    }
  })
}

export function useSceneModel(path: string, shadows: boolean): SceneModel {
  const renderer = useThree((state) => state.gl)
  const url = assetUrl(path)
  const gltf = useLoader(GLTFLoader, url, (loader) => {
    loader.setMeshoptDecoder(MeshoptDecoder)
    loader.setKTX2Loader(ktx2For(renderer))
  })
  const model = useMemo(() => readModel(gltf.scene), [gltf])
  useEffect(() => {
    model.root.traverse((child) => {
      if (!(child instanceof Mesh)) return
      const water = materialsOf(child).filter(isWaterMaterial)
      water.forEach(makeWater)
      materialsOf(child).filter(isGroundMaterial).forEach(addGroundDetail)
      child.castShadow = shadows && water.length === 0 && castsShadow(child)
      child.receiveShadow = shadows
      if (child.name.startsWith(WALKER_PREFIX)) child.visible = false
    })
  }, [model, shadows])
  useEffect(() => {
    clearTimeout(pendingDisposals.get(url))
    return () => {
      pendingDisposals.set(
        url,
        setTimeout(() => {
          pendingDisposals.delete(url)
          disposeModel(model.root)
          useLoader.clear(GLTFLoader, url)
        }, DISPOSE_DELAY_MS),
      )
    }
  }, [model, url])
  return model
}

export function markerForward(marker: Object3D): Vector3 {
  return new Vector3(0, 0, -1).applyQuaternion(marker.getWorldQuaternion(new Quaternion()))
}
