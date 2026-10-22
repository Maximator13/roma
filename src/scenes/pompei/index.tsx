import { ModelScene, type ModelSceneConfig } from '../kit/ModelScene.tsx'
import type { SceneProps } from '../registry.ts'

const POMPEI: ModelSceneConfig = {
  model: 'scenes/pompei/pompei.glb',
  sun: { azimuth: 225, elevation: 55, color: '#ff9452', intensity: 1.4 },
  haze: { color: '#76685a', density: 0.00022 },
  overview: { azimuth: 160, elevation: 30 },
  sky: { turbidity: 20, rayleigh: 3.5 },
  exposure: 0.78,
  clouds: 0,
  views: { 'vue-d-ensemble': { position: [900, 600, 3200], target: [-2400, 1500, -4300] } },
}

export default function Pompei(props: SceneProps) {
  return <ModelScene {...props} config={POMPEI} />
}
