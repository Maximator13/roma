import { describe, expect, it } from 'vitest'
import { parseBattle } from '../battle/schema.ts'
import { ACTIUM } from './battle.ts'

const SHIPS = ['decere', 'hexere', 'quinquereme', 'egyptien', 'polyreme', 'trireme', 'liburne']

describe('Actium', () => {
  it('is a valid battle', () => {
    expect(() => parseBattle(ACTIUM)).not.toThrow()
  })

  it('uses only models made in Blender', () => {
    for (const unit of ACTIUM.units) expect([...SHIPS, 'armee']).toContain(unit.troop)
  })

  it('fields 400 ships for Octavian and 230 for Antony and Cleopatra, one model per ship', () => {
    const ships = (side: string) => ACTIUM.units.filter((unit) => unit.side === side && SHIPS.includes(unit.troop)).reduce((sum, unit) => sum + unit.soldiers, 0)
    expect(ACTIUM.scale).toBe(1)
    expect([ships('rome'), ships('enemy')]).toEqual([400, 230])
  })
})
