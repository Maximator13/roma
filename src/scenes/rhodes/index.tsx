import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const RHODES: ModelSceneConfig = {
  model: 'scenes/rhodes/rhodes.glb',
  sun: { azimuth: 104.0, elevation: 25.0, color: '#fff2dc', intensity: 2.6 },
  haze: { color: '#e0cfb4', density: 0.00007 },
  overview: { azimuth: 200, elevation: 30 },
}

export default function Rhodes(props: SceneProps) {
  return <ModelScene {...props} config={RHODES} />
}
