import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const NIMES: ModelSceneConfig = {
  model: 'scenes/nimes/nimes.glb',
  sun: { azimuth: 295, elevation: 12, color: '#ffc58a', intensity: 3.2 },
  haze: { color: '#d8b48c', density: 0.00022 },
  overview: { azimuth: 150, elevation: 30 },
}

export default function Nimes(props: SceneProps) {
  return <ModelScene {...props} config={NIMES} />
}
