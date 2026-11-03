import { Battlefield, type BattleConfig } from '../battle/Battlefield.tsx'
import type { SceneProps } from '../registry.ts'
import { ALESIA } from './battle.ts'

const CONFIG: BattleConfig = {
  model: 'scenes/alesia/alesia.glb',
  battle: ALESIA,
  haze: { color: '#d3d6cf', density: 0.00004 },
  sunColor: '#fff0d8',
  sunIntensity: 2.5,
}

export default function Alesia(props: SceneProps) {
  return <Battlefield {...props} config={CONFIG} />
}
