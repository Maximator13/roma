import { describe, expect, it } from 'vitest'
import {
  awardSeries,
  buildSeries,
  canOpenDaily,
  claimExploration,
  craft,
  CRAFT_COST,
  dayKey,
  drawPack,
  DUPLICATE_VALUE,
  emptyState,
  EPIC_PITY,
  EVENT_REWARD,
  LEGENDARY_PITY,
  openBonus,
  openDaily,
  PACK_SIZE,
  packRarities,
  rank,
  RARITY_ORDER,
  RARITY_WEIGHTS,
  rollRarity,
  type PoolCard,
} from './game.ts'
import { seededRandom } from './random.ts'

const pool: PoolCard[] = RARITY_ORDER.flatMap((rarity, index) =>
  Array.from({ length: 12 - index * 2 }, (_, number): PoolCard => ({
    id: `${rarity}-${number}`,
    rarity,
    kind: number % 2 === 0 ? 'person' : 'place',
    era: number % 3 === 0 ? 'royaute' : 'haut-empire',
  })),
).concat([{ id: 'scene-card', rarity: 'rare', kind: 'place', era: 'haut-empire', scene: 'colisee' }])

describe('seededRandom', () => {
  it('repeats the same sequence for the same seed and differs between seeds', () => {
    const first = seededRandom('joueur:2026-10-22')
    const second = seededRandom('joueur:2026-10-22')
    const other = seededRandom('joueur:2026-10-23')
    const values = [first(), first(), first()]
    expect([second(), second(), second()]).toEqual(values)
    expect([other(), other(), other()]).not.toEqual(values)
    values.forEach((value) => expect(value >= 0 && value < 1).toBe(true))
  })
})

describe('rarities', () => {
  it('follows the announced probabilities', () => {
    const random = seededRandom('probabilites')
    const draws = 200_000
    const counts = new Map(RARITY_ORDER.map((rarity) => [rarity, 0]))
    for (let index = 0; index < draws; index += 1) {
      const rarity = rollRarity(random)
      counts.set(rarity, (counts.get(rarity) ?? 0) + 1)
    }
    const total = Object.values(RARITY_WEIGHTS).reduce((sum, weight) => sum + weight, 0)
    for (const rarity of RARITY_ORDER) expect((counts.get(rarity) ?? 0) / draws).toBeCloseTo(RARITY_WEIGHTS[rarity] / total, 2)
  })

  it('never goes below the requested minimum', () => {
    const random = seededRandom('minimum')
    for (let index = 0; index < 2_000; index += 1) expect(rank(rollRarity(random, 'rare'))).toBeGreaterThanOrEqual(rank('rare'))
  })

  it('puts at least one rare card in every pack', () => {
    for (let index = 0; index < 2_000; index += 1) {
      const rarities = packRarities(seededRandom(`paquet-${index}`), 0, 0)
      expect(rarities).toHaveLength(PACK_SIZE)
      expect(Math.max(...rarities.map(rank))).toBeGreaterThanOrEqual(rank('rare'))
    }
  })

  it('guarantees an epic and a legendary card when the counters run out', () => {
    for (let index = 0; index < 500; index += 1) {
      expect(Math.max(...packRarities(seededRandom(`epique-${index}`), EPIC_PITY - 1, 0).map(rank))).toBeGreaterThanOrEqual(rank('epic'))
      expect(packRarities(seededRandom(`legendaire-${index}`), 0, LEGENDARY_PITY - 1)).toContain('legendary')
    }
  })
})

describe('packs', () => {
  it('draws the same pack for the same seed, without repeating a card', () => {
    const state = emptyState('joueur')
    const first = drawPack(state, pool, 'graine', '2026-10-22')
    const second = drawPack(state, pool, 'graine', '2026-10-22')
    expect(first.pulls).toEqual(second.pulls)
    expect(new Set(first.pulls.map((pull) => pull.id)).size).toBe(PACK_SIZE)
    expect(Object.keys(first.state.owned)).toHaveLength(PACK_SIZE)
    expect(first.state.packsOpened).toBe(1)
  })

  it('turns duplicates into deniers', () => {
    const owned = Object.fromEntries(pool.map((card) => [card.id, '2026-01-01']))
    const { state, pulls } = drawPack({ ...emptyState('joueur'), owned }, pool, 'doublons', '2026-10-22')
    expect(pulls.every((pull) => pull.duplicate)).toBe(true)
    expect(state.deniers).toBe(pulls.reduce((sum, pull) => sum + DUPLICATE_VALUE[pull.rarity], 0))
  })

  it('opens one daily pack per day and cannot be rerolled', () => {
    const state = emptyState('joueur')
    const today = openDaily(state, pool, '2026-10-22')
    expect(today.pulls).toHaveLength(PACK_SIZE)
    expect(canOpenDaily(today.state, '2026-10-22')).toBe(false)
    expect(openDaily(today.state, pool, '2026-10-22').pulls).toEqual([])
    expect(openDaily(state, pool, '2026-10-22').pulls).toEqual(today.pulls)
    expect(canOpenDaily(today.state, '2026-10-23')).toBe(true)
  })

  it('gives every player a legendary card within the guarantee', () => {
    for (let player = 0; player < 50; player += 1) {
      let state = emptyState(`joueur-${player}`)
      let legendary = false
      for (let day = 0; day < LEGENDARY_PITY; day += 1) {
        const opened = openDaily(state, pool, `jour-${day}`)
        state = opened.state
        legendary ||= opened.pulls.some((pull) => pull.rarity === 'legendary')
      }
      expect(legendary).toBe(true)
    }
  })

  it('draws an epic or legendary card not yet owned while some remain', () => {
    const missing = pool.find((card) => card.rarity === 'legendary') as PoolCard
    const owned = Object.fromEntries(pool.filter((card) => card.id !== missing.id).map((card) => [card.id, '2026-01-01']))
    for (let index = 0; index < 20; index += 1) {
      const state = { ...emptyState(`joueur-${index}`), owned, sinceLegendary: LEGENDARY_PITY - 1 }
      const legendary = drawPack(state, pool, `graine-${index}`, '2026-10-22').pulls.find((pull) => pull.rarity === 'legendary')
      expect(legendary).toEqual({ id: missing.id, rarity: 'legendary', duplicate: false, deniers: 0 })
    }
  })

  it('opens bonus packs only when some are available', () => {
    const state = emptyState('joueur')
    expect(openBonus(state, pool, '2026-10-22').pulls).toEqual([])
    const opened = openBonus({ ...state, bonusPacks: 1 }, pool, '2026-10-22')
    expect(opened.pulls).toHaveLength(PACK_SIZE)
    expect(opened.state.bonusPacks).toBe(0)
    expect(opened.state.bonusOpened).toBe(1)
  })

  it('formats the local day', () => {
    expect(dayKey(new Date(2026, 0, 5, 23, 59))).toBe('2026-01-05')
  })
})

describe('crafting and rewards', () => {
  const rare = pool.find((card) => card.rarity === 'rare') as PoolCard

  it('crafts a missing card for its price only', () => {
    const poor = { ...emptyState('joueur'), deniers: CRAFT_COST.rare - 1 }
    expect(craft(poor, rare, '2026-10-22')).toBe(poor)
    const crafted = craft({ ...poor, deniers: CRAFT_COST.rare + 3 }, rare, '2026-10-22')
    expect(crafted.owned[rare.id]).toBe('2026-10-22')
    expect(crafted.deniers).toBe(3)
    expect(craft(crafted, rare, '2026-10-22')).toBe(crafted)
  })

  it('rewards a scene card and read events once', () => {
    const visits = { scenes: ['colisee', 'colisee', 'inconnue'], events: ['a', 'b', 'b', 'faux'] }
    const known = new Set(['a', 'b'])
    const first = claimExploration(emptyState('joueur'), visits, pool, known, '2026-10-22')
    expect(first.state.owned['scene-card']).toBe('2026-10-22')
    expect(first.state.deniers).toBe(2 * EVENT_REWARD)
    expect(first.rewards).toHaveLength(2)
    const again = claimExploration(first.state, visits, pool, known, '2026-10-22')
    expect(again.rewards).toEqual([])
    expect(again.state).toEqual(first.state)
  })

  it('awards a bonus pack once per completed series', () => {
    const series = buildSeries(pool, ['royaute', 'haut-empire'], ['person', 'place'])
    const royaute = series.find((item) => item.id === 'epoque-royaute')
    const owned = Object.fromEntries((royaute?.cards ?? []).map((id) => [id, '2026-10-22']))
    const first = awardSeries({ ...emptyState('joueur'), owned }, series)
    expect(first.completed).toEqual(['epoque-royaute'])
    expect(first.state.bonusPacks).toBe(1)
    expect(awardSeries(first.state, series).completed).toEqual([])
  })
})
