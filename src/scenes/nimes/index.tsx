import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const NIMES: ModelSceneConfig = {
  model: 'scenes/nimes/nimes.glb',
  sun: { azimuth: 291, elevation: 12, color: '#ffc58a', intensity: 2.6 },
  haze: { color: '#dcc9ad', density: 0.00007 },
  overview: { azimuth: 150, elevation: 30 },
}

export default function Nimes(props: SceneProps) {
  return <ModelScene {...props} config={NIMES} />
}
