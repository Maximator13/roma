import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const COLISEE: ModelSceneConfig = {
  model: 'scenes/colisee/colisee.glb',
  sun: { azimuth: 268, elevation: 37, color: '#ffc78c', intensity: 2.6 },
  haze: { color: '#dcc9ad', density: 0.00009 },
  overview: { azimuth: 150, elevation: 30 },
}

export default function Colisee(props: SceneProps) {
  return <ModelScene {...props} config={COLISEE} />
}
