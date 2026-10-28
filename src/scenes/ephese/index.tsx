import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const EPHESE: ModelSceneConfig = {
  model: 'scenes/ephese/ephese.glb',
  sun: { azimuth: 245.0, elevation: 34.0, color: '#fff0d8', intensity: 2.6 },
  haze: { color: '#e0cfb4', density: 0.00007 },
  overview: { azimuth: 200, elevation: 30 },
}

export default function Ephese(props: SceneProps) {
  return <ModelScene {...props} config={EPHESE} />
}
