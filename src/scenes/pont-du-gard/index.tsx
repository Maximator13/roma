import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const PONT_DU_GARD: ModelSceneConfig = {
  model: 'scenes/pont-du-gard/pont-du-gard.glb',
  sun: { azimuth: 291, elevation: 12, color: '#ffb877', intensity: 2.6 },
  haze: { color: '#dcc9ad', density: 0.00011 },
  overview: { azimuth: 200, elevation: 25 },
  views: { 'le-canal': { position: [-15.6, 58, -2.2], target: [-20.2, 47.6, -24] } },
}

export default function PontDuGard(props: SceneProps) {
  return <ModelScene {...props} config={PONT_DU_GARD} />
}
