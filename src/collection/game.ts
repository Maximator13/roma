import type { CardKind, EraId, Rarity } from '../data/schema.ts'
import { pickIndex, seededRandom, type Random } from './random.ts'

export const RARITY_ORDER: Rarity[] = ['common', 'uncommon', 'rare', 'epic', 'legendary']
export const RARITY_WEIGHTS: Record<Rarity, number> = { common: 60, uncommon: 25, rare: 10, epic: 4, legendary: 1 }
export const DUPLICATE_VALUE: Record<Rarity, number> = { common: 5, uncommon: 15, rare: 50, epic: 150, legendary: 500 }
export const CRAFT_COST: Record<Rarity, number> = { common: 20, uncommon: 60, rare: 200, epic: 600, legendary: 2000 }
export const PACK_SIZE = 5
export const EPIC_PITY = 10
export const LEGENDARY_PITY = 30
export const EVENT_REWARD = 5

export interface PoolCard {
  id: string
  rarity: Rarity
  kind: CardKind
  era: EraId
  scene?: string
}

export interface CollectionState {
  version: 1
  player: string
  owned: Record<string, string>
  deniers: number
  packsOpened: number
  sinceEpic: number
  sinceLegendary: number
  lastDaily: string | null
  bonusPacks: number
  bonusOpened: number
  rewardedScenes: string[]
  rewardedEvents: string[]
  completedSeries: string[]
}

export interface Pull {
  id: string
  rarity: Rarity
  duplicate: boolean
  deniers: number
}

export interface Visits {
  scenes: string[]
  events: string[]
}

export interface Series {
  id: string
  cards: string[]
}

export function emptyState(player: string): CollectionState {
  return {
    version: 1,
    player,
    owned: {},
    deniers: 0,
    packsOpened: 0,
    sinceEpic: 0,
    sinceLegendary: 0,
    lastDaily: null,
    bonusPacks: 0,
    bonusOpened: 0,
    rewardedScenes: [],
    rewardedEvents: [],
    completedSeries: [],
  }
}

export function dayKey(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

export function rank(rarity: Rarity): number {
  return RARITY_ORDER.indexOf(rarity)
}

export function rollRarity(random: Random, minimum: Rarity = 'common'): Rarity {
  const allowed = RARITY_ORDER.filter((rarity) => rank(rarity) >= rank(minimum))
  const total = allowed.reduce((sum, rarity) => sum + RARITY_WEIGHTS[rarity], 0)
  let roll = random() * total
  for (const rarity of allowed) {
    roll -= RARITY_WEIGHTS[rarity]
    if (roll < 0) return rarity
  }
  return allowed[allowed.length - 1] ?? minimum
}

export function packRarities(random: Random, sinceEpic: number, sinceLegendary: number): Rarity[] {
  const rarities = Array.from({ length: PACK_SIZE - 1 }, () => rollRarity(random))
  const best = () => Math.max(...rarities.map(rank))
  rarities.push(rollRarity(random, best() >= rank('rare') ? 'common' : 'rare'))
  const last = rarities.length - 1
  if (sinceEpic + 1 >= EPIC_PITY && best() < rank('epic')) rarities[last] = 'epic'
  if (sinceLegendary + 1 >= LEGENDARY_PITY && best() < rank('legendary')) rarities[last] = 'legendary'
  return rarities
}

function pickCard(random: Random, pool: PoolCard[], rarity: Rarity, taken: Set<string>, owned: Record<string, string>): PoolCard | undefined {
  const all = pool.filter((card) => card.rarity === rarity && !taken.has(card.id))
  const fresh = all.filter((card) => owned[card.id] === undefined)
  const candidates = rank(rarity) >= rank('epic') && fresh.length > 0 ? fresh : all
  if (candidates.length > 0) return candidates[pickIndex(random, candidates.length)]
  const fallback = pool.filter((card) => !taken.has(card.id))
  return fallback.length > 0 ? fallback[pickIndex(random, fallback.length)] : undefined
}

function addCard(state: CollectionState, card: { id: string; rarity: Rarity }, day: string): { state: CollectionState; pull: Pull } {
  if (state.owned[card.id] !== undefined) {
    const deniers = DUPLICATE_VALUE[card.rarity]
    return { state: { ...state, deniers: state.deniers + deniers }, pull: { id: card.id, rarity: card.rarity, duplicate: true, deniers } }
  }
  return { state: { ...state, owned: { ...state.owned, [card.id]: day } }, pull: { id: card.id, rarity: card.rarity, duplicate: false, deniers: 0 } }
}

export function drawPack(state: CollectionState, pool: PoolCard[], seed: string, day: string): { state: CollectionState; pulls: Pull[] } {
  const random = seededRandom(seed)
  const rarities = packRarities(random, state.sinceEpic, state.sinceLegendary)
  const taken = new Set<string>()
  const pulls: Pull[] = []
  let next = state
  for (const rarity of rarities) {
    const card = pickCard(random, pool, rarity, taken, next.owned)
    if (!card) continue
    taken.add(card.id)
    const added = addCard(next, card, day)
    next = added.state
    pulls.push(added.pull)
  }
  const best = Math.max(...pulls.map((pull) => rank(pull.rarity)))
  next = {
    ...next,
    packsOpened: next.packsOpened + 1,
    sinceEpic: best >= rank('epic') ? 0 : next.sinceEpic + 1,
    sinceLegendary: best >= rank('legendary') ? 0 : next.sinceLegendary + 1,
  }
  return { state: next, pulls }
}

export function canOpenDaily(state: CollectionState, day: string): boolean {
  return state.lastDaily !== day
}

export function openDaily(state: CollectionState, pool: PoolCard[], day: string): { state: CollectionState; pulls: Pull[] } {
  if (!canOpenDaily(state, day)) return { state, pulls: [] }
  const drawn = drawPack(state, pool, `${state.player}:jour:${day}`, day)
  return { state: { ...drawn.state, lastDaily: day }, pulls: drawn.pulls }
}

export function openBonus(state: CollectionState, pool: PoolCard[], day: string): { state: CollectionState; pulls: Pull[] } {
  if (state.bonusPacks <= 0) return { state, pulls: [] }
  const drawn = drawPack(state, pool, `${state.player}:bonus:${state.bonusOpened}`, day)
  return { state: { ...drawn.state, bonusPacks: drawn.state.bonusPacks - 1, bonusOpened: drawn.state.bonusOpened + 1 }, pulls: drawn.pulls }
}

export function craft(state: CollectionState, card: PoolCard, day: string): CollectionState {
  const cost = CRAFT_COST[card.rarity]
  if (state.owned[card.id] !== undefined || state.deniers < cost) return state
  return { ...state, deniers: state.deniers - cost, owned: { ...state.owned, [card.id]: day } }
}

export type Reward = { type: 'card'; id: string; duplicate: boolean; deniers: number } | { type: 'deniers'; amount: number; events: number }

export function claimExploration(
  state: CollectionState,
  visits: Visits,
  pool: PoolCard[],
  knownEvents: Set<string>,
  day: string,
): { state: CollectionState; rewards: Reward[] } {
  const rewards: Reward[] = []
  let next = state
  const newScenes = [...new Set(visits.scenes)].filter((scene) => !state.rewardedScenes.includes(scene))
  for (const scene of newScenes) {
    const card = pool.find((candidate) => candidate.scene === scene)
    if (!card) continue
    const added = addCard(next, card, day)
    next = { ...added.state, rewardedScenes: [...added.state.rewardedScenes, scene] }
    rewards.push({ type: 'card', id: card.id, duplicate: added.pull.duplicate, deniers: added.pull.deniers })
  }
  const newEvents = [...new Set(visits.events)].filter((event) => knownEvents.has(event) && !state.rewardedEvents.includes(event))
  if (newEvents.length > 0) {
    const amount = newEvents.length * EVENT_REWARD
    next = { ...next, deniers: next.deniers + amount, rewardedEvents: [...next.rewardedEvents, ...newEvents] }
    rewards.push({ type: 'deniers', amount, events: newEvents.length })
  }
  return { state: next, rewards }
}

export function buildSeries(pool: PoolCard[], eras: EraId[], kinds: CardKind[]): Series[] {
  return [
    ...eras.map((era) => ({ id: `epoque-${era}`, cards: pool.filter((card) => card.era === era).map((card) => card.id) })),
    ...kinds.map((kind) => ({ id: `type-${kind}`, cards: pool.filter((card) => card.kind === kind).map((card) => card.id) })),
  ].filter((series) => series.cards.length > 0)
}

export function isComplete(state: CollectionState, series: Series): boolean {
  return series.cards.every((id) => state.owned[id] !== undefined)
}

export function awardSeries(state: CollectionState, series: Series[]): { state: CollectionState; completed: string[] } {
  const completed = series.filter((item) => !state.completedSeries.includes(item.id) && isComplete(state, item)).map((item) => item.id)
  if (completed.length === 0) return { state, completed }
  return {
    state: { ...state, bonusPacks: state.bonusPacks + completed.length, completedSeries: [...state.completedSeries, ...completed] },
    completed,
  }
}
