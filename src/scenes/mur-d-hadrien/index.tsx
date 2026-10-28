import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const MUR_D_HADRIEN: ModelSceneConfig = {
  model: 'scenes/mur-d-hadrien/mur-d-hadrien.glb',
  sun: { azimuth: 245.0, elevation: 17.0, color: '#ffd9a8', intensity: 2.6 },
  haze: { color: '#c9d2d6', density: 0.00009 },
  overview: { azimuth: 200, elevation: 25 },
}

export default function MurDHadrien(props: SceneProps) {
  return <ModelScene {...props} config={MUR_D_HADRIEN} />
}
