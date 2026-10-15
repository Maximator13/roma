import { useThree } from '@react-three/fiber'
import { Suspense, useEffect } from 'react'
import type { UiInsets } from '../map/MapStage.tsx'
import { findScene, SCENE_COMPONENTS } from '../scenes/registry.ts'
import { useApp } from '../store.ts'
import type { QualityTier } from './quality.ts'

const COMPILE_TIMEOUT_MS = 4000

function ReadySignal({ id, onReady }: { id: string; onReady: (id: string) => void }) {
  const renderer = useThree((state) => state.gl)
  const scene = useThree((state) => state.scene)
  const camera = useThree((state) => state.camera)
  useEffect(() => {
    let live = true
    const timeout = new Promise((resolve) => setTimeout(resolve, COMPILE_TIMEOUT_MS))
    Promise.race([renderer.compileAsync(scene, camera), timeout])
      .catch(() => undefined)
      .then(() => {
        if (live) requestAnimationFrame(() => live && onReady(id))
      })
    return () => {
      live = false
    }
  }, [renderer, scene, camera, id, onReady])
  return null
}

export function SceneHost({
  id,
  insets,
  quality,
  onReady,
}: {
  id: string
  insets: UiInsets
  quality: QualityTier
  onReady: (id: string) => void
}) {
  const point = useApp((state) => state.scenePoint)
  const scene = findScene(id)
  const SceneView = SCENE_COMPONENTS[id]
  if (!scene || !SceneView) return null
  return (
    <Suspense fallback={null}>
      <SceneView scene={scene} point={point} insets={insets} quality={quality} />
      <ReadySignal id={id} onReady={onReady} />
    </Suspense>
  )
}
