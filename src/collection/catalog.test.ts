import { describe, expect, it } from 'vitest'
import { cardArt } from '../data/cardArt.ts'
import { cards } from '../data/cards.ts'
import { cities, eras, people, places } from '../data/index.ts'
import { CARD_KINDS, ERA_IDS } from '../data/schema.ts'
import { buildCatalog, eraOf, toPool } from './catalog.ts'
import { buildSeries } from './game.ts'

const catalog = buildCatalog({ cards, art: cardArt, eras, people, cities, places })

describe('card catalog', () => {
  it('gives every card a short name and a subtitle', () => {
    for (const card of catalog) {
      expect(card.name.length, card.id).toBeLessThanOrEqual(32)
      expect(card.name, card.id).not.toMatch(/\(/)
      expect(card.subtitle.length, card.id).toBeGreaterThan(0)
    }
  })

  it('keeps the announced rarity distribution', () => {
    const counts = Object.fromEntries(['common', 'uncommon', 'rare', 'epic', 'legendary'].map((rarity) => [rarity, catalog.filter((card) => card.rarity === rarity).length]))
    expect(counts).toEqual({ common: 38, uncommon: 32, rare: 26, epic: 17, legendary: 8 })
  })

  it('assigns border years to the earlier era', () => {
    expect(eraOf(-752, eras)).toBe('royaute')
    expect(eraOf(-508, eras)).toBe('royaute')
    expect(eraOf(476, eras)).toBe('bas-empire')
    expect(eraOf(1453, eras)).toBe('empire-romain-d-orient')
  })

  it('builds a series for every era and every kind', () => {
    const series = buildSeries(toPool(catalog), [...ERA_IDS], [...CARD_KINDS])
    expect(series.map((item) => item.id).sort()).toEqual([...ERA_IDS.map((era) => `epoque-${era}`), ...CARD_KINDS.map((kind) => `type-${kind}`)].sort())
  })
})
