import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const HALICARNASSE: ModelSceneConfig = {
  model: 'scenes/halicarnasse/halicarnasse.glb',
  sun: { azimuth: 255.0, elevation: 17.0, color: '#ffc58a', intensity: 2.6 },
  haze: { color: '#e0cfb4', density: 0.00007 },
  overview: { azimuth: 200, elevation: 30 },
}

export default function Halicarnasse(props: SceneProps) {
  return <ModelScene {...props} config={HALICARNASSE} />
}
