import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const GIZEH: ModelSceneConfig = {
  model: 'scenes/gizeh/gizeh.glb',
  sun: { azimuth: 110.0, elevation: 14.0, color: '#ffbe7a', intensity: 2.6 },
  haze: { color: '#e0cfb4', density: 0.00007 },
  overview: { azimuth: 200, elevation: 30 },
}

export default function Gizeh(props: SceneProps) {
  return <ModelScene {...props} config={GIZEH} />
}
