import { existsSync, readdirSync } from 'node:fs'
import { dataset } from '../src/data/index.ts'
import { validateDataset } from '../src/data/validate.ts'

const SCENE_SHARED_FOLDERS = new Set(['kit', 'battle'])

export function sceneFileErrors(scenes: { id: string; status: string }[], folders: string[], exists: (path: string) => boolean): string[] {
  const ids = new Set(scenes.map((scene) => scene.id))
  const missingFiles = scenes
    .filter((scene) => scene.status === 'ready')
    .flatMap((scene) =>
      [[`src/scenes/${scene.id}/index.tsx`], [`blender/${scene.id}.py`, `blender/${scene.id.replaceAll('-', '_')}.py`]]
        .filter((paths) => !paths.some(exists))
        .map((paths) => `scene ${scene.id}: ready scene without ${paths[0]}`),
    )
  const orphans = folders
    .filter((folder) => !SCENE_SHARED_FOLDERS.has(folder) && !ids.has(folder))
    .map((folder) => `src/scenes/${folder}: no matching entry in src/data/scenes.ts`)
  return [...missingFiles, ...orphans]
}

function sceneFolders(): string[] {
  return readdirSync('src/scenes', { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
}

if (import.meta.main) {
  const problems = [...validateDataset(dataset), ...sceneFileErrors(dataset.scenes, sceneFolders(), existsSync)]
  if (problems.length > 0) {
    console.error(problems.join('\n'))
    process.exit(1)
  }
  const counts = Object.entries(dataset).map(([name, items]) => `${items.length} ${name}`)
  console.log(`Data valid: ${counts.join(', ')}.`)
}
