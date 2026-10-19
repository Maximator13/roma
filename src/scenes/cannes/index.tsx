import { Battlefield, type BattleConfig } from '../battle/Battlefield.tsx'
import type { SceneProps } from '../registry.ts'
import { CANNAE } from './battle.ts'

const CANNES: BattleConfig = {
  model: 'scenes/cannes/cannes.glb',
  battle: CANNAE,
  haze: { color: '#d8ccb4', density: 0.00007 },
  sunColor: '#fff0d8',
  sunIntensity: 2.5,
}

export default function Cannes(props: SceneProps) {
  return <Battlefield {...props} config={CANNES} />
}
