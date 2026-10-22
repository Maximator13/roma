import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const CONSTANTINOPLE: ModelSceneConfig = {
  model: 'scenes/constantinople/constantinople.glb',
  sun: { azimuth: 138, elevation: 13, color: '#ffd2a1', intensity: 2.6 },
  haze: { color: '#d6dbe2', density: 0.00007 },
  overview: { azimuth: 210, elevation: 30 },
  interior: { center: [205.1, 34.59, -116.38], radius: 36, height: 58, ambientScale: 0.35 },
}

export default function Constantinople(props: SceneProps) {
  return <ModelScene {...props} config={CONSTANTINOPLE} />
}
