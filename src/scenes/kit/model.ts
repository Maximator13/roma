import { useLoader, useThree } from '@react-three/fiber'
import { useEffect, useMemo } from 'react'
import { Box3, Mesh, Quaternion, Vector3, type Material, type Object3D, type WebGLRenderer } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader.js'
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js'

const MARKER_PREFIX = 'poi_'
const DISPOSE_DELAY_MS = 1000

const pendingDisposals = new Map<string, ReturnType<typeof setTimeout>>()

let ktx2: KTX2Loader | null = null

function ktx2For(renderer: WebGLRenderer): KTX2Loader {
  ktx2 ??= new KTX2Loader().setTranscoderPath(`${import.meta.env.BASE_URL}basis/`).detectSupport(renderer)
  return ktx2
}

export function assetUrl(path: string): string {
  return `${import.meta.env.BASE_URL}assets/${path}`
}

export interface SceneModel {
  root: Object3D
  markers: Map<string, Object3D>
  bounds: Box3
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
  const model = useMemo(() => {
    const markers = new Map<string, Object3D>()
    gltf.scene.traverse((child) => {
      if (child.name.startsWith(MARKER_PREFIX)) markers.set(child.name.slice(MARKER_PREFIX.length), child)
    })
    gltf.scene.updateMatrixWorld(true)
    return { root: gltf.scene, markers, bounds: new Box3().setFromObject(gltf.scene) }
  }, [gltf])
  useEffect(() => {
    model.root.traverse((child) => {
      if (!(child instanceof Mesh)) return
      child.castShadow = shadows
      child.receiveShadow = shadows
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
