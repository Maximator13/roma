import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const ARLES: ModelSceneConfig = {
  model: 'scenes/arles/arles.glb',
  sun: { azimuth: 288, elevation: 14, color: '#ffc58a', intensity: 2.6 },
  haze: { color: '#c9d6e6', density: 0.00007 },
  overview: { azimuth: 150, elevation: 30 },
}

export default function Arles(props: SceneProps) {
  return <ModelScene {...props} config={ARLES} />
}
