import { Battlefield, type BattleConfig } from '../battle/Battlefield.tsx'
import type { SceneProps } from '../registry.ts'
import { ACTIUM } from './battle.ts'

const CONFIG: BattleConfig = {
  model: 'scenes/actium/actium.glb',
  battle: ACTIUM,
  haze: { color: '#cdd8dd', density: 0.000045 },
  sunColor: '#fff2dc',
  sunIntensity: 2.6,
}

export default function Actium(props: SceneProps) {
  return <Battlefield {...props} config={CONFIG} />
}
