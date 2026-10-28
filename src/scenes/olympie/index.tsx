import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const OLYMPIE: ModelSceneConfig = {
  model: 'scenes/olympie/olympie.glb',
  sun: { azimuth: 250.0, elevation: 40.0, color: '#ffd6a0', intensity: 2.6 },
  haze: { color: '#e0cfb4', density: 0.00007 },
  overview: { azimuth: 200, elevation: 30 },
  interior: { center: [0.0, 35.24, 0], radius: 15, height: 14, ambientScale: 0.4 },
}

export default function Olympie(props: SceneProps) {
  return <ModelScene {...props} config={OLYMPIE} />
}
