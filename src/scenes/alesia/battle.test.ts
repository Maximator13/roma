import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { parseBattle } from '../battle/schema.ts'
import { figureCount } from '../battle/timeline.ts'
import { ALESIA } from './battle.ts'

const TROOPS = ['legionnaire', 'cavalier', 'germain', 'cesar', 'gaulois', 'noble', 'cavalier-gaulois', 'archer', 'civil', 'armee']
const PHASES = [
  'les-lignes-de-cesar',
  'l-armee-de-secours',
  'le-combat-de-cavalerie',
  'l-attaque-de-nuit',
  'vercassivellaunos-au-rea',
  'la-sortie-de-vercingetorix',
  'labienus-et-cesar',
  'la-deroute',
  'la-reddition-de-vercingetorix',
]

describe('Alésia', () => {
  it('is a valid battle', () => {
    expect(() => parseBattle(ALESIA)).not.toThrow()
  })

  it('follows the nine phases of the verified proposal', () => {
    expect(ALESIA.phases.map((phase) => phase.id)).toEqual(PHASES)
  })

  it('uses only models made in Blender', () => {
    const script = readFileSync('blender/kit/alesia_figures.py', 'utf8')
    for (const troop of TROOPS) expect(script).toContain(`"${troop}": (`)
    for (const unit of ALESIA.units) expect(TROOPS).toContain(unit.troop)
  })

  it('draws one figure for 60 soldiers and stays well under the Cannae budget', () => {
    const figures = ALESIA.units.filter((unit) => unit.troop !== 'armee').reduce((sum, unit) => sum + figureCount(unit, ALESIA.scale), 0)
    expect(ALESIA.scale).toBe(60)
    expect(figures).toBeGreaterThan(1800)
    expect(figures).toBeLessThan(2800)
  })

  it('gives Vercassivellaunos the 60 000 men of Caesar and Caesar a single figure', () => {
    expect(ALESIA.units.find((unit) => unit.id === 'vercassivellaunos')?.soldiers).toBe(60000)
    const caesar = ALESIA.units.find((unit) => unit.id === 'cesar')!
    expect(figureCount(caesar, ALESIA.scale)).toBe(1)
    expect(caesar.label).toContain('interprétation')
  })
})
