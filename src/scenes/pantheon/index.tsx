import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const PANTHEON: ModelSceneConfig = {
  model: 'scenes/pantheon/pantheon.glb',
  sun: { azimuth: 180, elevation: 59.5, color: '#fff1dc', intensity: 3.4 },
  haze: { color: '#cdd8e6', density: 0.00012 },
  overview: { azimuth: 200, elevation: 35 },
  forceShadows: true,
  interior: { center: [0, -0.5, 0], radius: 21.65, height: 44, ambientScale: 0.2 },
  lightShaftRadius: 3.85,
}

export default function Pantheon(props: SceneProps) {
  return <ModelScene {...props} config={PANTHEON} />
}
