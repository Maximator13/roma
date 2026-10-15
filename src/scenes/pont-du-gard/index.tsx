import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const PONT_DU_GARD: ModelSceneConfig = {
  model: 'scenes/pont-du-gard/pont-du-gard.glb',
  sun: { azimuth: 291, elevation: 12, color: '#ffc58a', intensity: 2.6 },
  haze: { color: '#c9d6e6', density: 0.00009 },
  overview: { azimuth: 200, elevation: 25 },
}

export default function PontDuGard(props: SceneProps) {
  return <ModelScene {...props} config={PONT_DU_GARD} />
}
