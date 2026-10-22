import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const ALEXANDRIE: ModelSceneConfig = {
  model: 'scenes/alexandrie/alexandrie.glb',
  sun: { azimuth: 291, elevation: 12, color: '#ffb36b', intensity: 2.4 },
  haze: { color: '#e3c9a2', density: 0.00008 },
  overview: { azimuth: 200, elevation: 28 },
}

export default function Alexandrie(props: SceneProps) {
  return <ModelScene {...props} config={ALEXANDRIE} />
}
