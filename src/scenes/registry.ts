import { lazy, type ComponentType, type LazyExoticComponent } from 'react'
import { scenes } from '../data/scenes.ts'
import type { Scene } from '../data/schema.ts'
import type { UiInsets } from '../map/MapStage.tsx'
import type { QualityTier } from '../stage/quality.ts'

export interface SceneProps {
  scene: Scene
  point: number
  insets: UiInsets
  quality: QualityTier
}

type SceneComponent = ComponentType<SceneProps>
type SceneModule = { default: SceneComponent }

const modules = import.meta.glob<SceneModule>('./*/index.tsx')

function idOf(path: string): string {
  return path.split('/')[1] ?? ''
}

export const SCENE_COMPONENTS: Readonly<Record<string, LazyExoticComponent<SceneComponent> | undefined>> = Object.fromEntries(
  Object.entries(modules).map(([path, loader]) => [idOf(path), lazy(loader)]),
)

function loaderFor(id: string): (() => Promise<SceneModule>) | undefined {
  return modules[`./${id}/index.tsx`]
}

export function sceneModuleIds(): string[] {
  return Object.keys(modules).map(idOf)
}

export function findScene(id: string): Scene | undefined {
  return scenes.find((scene) => scene.id === id)
}

export function isPlayable(scene: Scene | undefined): scene is Scene {
  return scene?.status === 'ready' && loaderFor(scene.id) !== undefined
}

export function preloadScene(id: string): Promise<unknown> {
  return loaderFor(id)?.() ?? Promise.resolve()
}
