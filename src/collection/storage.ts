import { emptyState, type CollectionState } from './game.ts'

export const STORAGE_KEY = 'roma.collection'

export interface KeyValueStore {
  getItem: (key: string) => string | null
  setItem: (key: string, value: string) => void
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function count(value: unknown): number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 0 ? value : 0
}

function strings(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : []
}

function ownedCards(value: unknown): Record<string, string> {
  if (!isRecord(value)) return {}
  return Object.fromEntries(Object.entries(value).filter((entry): entry is [string, string] => typeof entry[1] === 'string'))
}

export function newPlayerId(random: () => number = Math.random): string {
  return Array.from({ length: 12 }, () => Math.floor(random() * 36).toString(36)).join('')
}

export function parseState(raw: string | null, fallbackPlayer: string): CollectionState {
  let value: unknown
  try {
    value = raw === null ? null : JSON.parse(raw)
  } catch {
    value = null
  }
  if (!isRecord(value) || value.version !== 1 || typeof value.player !== 'string' || value.player === '') return emptyState(fallbackPlayer)
  return {
    version: 1,
    player: value.player,
    owned: ownedCards(value.owned),
    deniers: count(value.deniers),
    packsOpened: count(value.packsOpened),
    sinceEpic: count(value.sinceEpic),
    sinceLegendary: count(value.sinceLegendary),
    lastDaily: typeof value.lastDaily === 'string' ? value.lastDaily : null,
    bonusPacks: count(value.bonusPacks),
    bonusOpened: count(value.bonusOpened),
    rewardedScenes: strings(value.rewardedScenes),
    rewardedEvents: strings(value.rewardedEvents),
    completedSeries: strings(value.completedSeries),
  }
}

export function loadState(store: KeyValueStore | null): CollectionState {
  try {
    return parseState(store?.getItem(STORAGE_KEY) ?? null, newPlayerId())
  } catch {
    return parseState(null, newPlayerId())
  }
}

export function saveState(store: KeyValueStore | null, state: CollectionState): boolean {
  try {
    store?.setItem(STORAGE_KEY, JSON.stringify(state))
    return store !== null
  } catch {
    return false
  }
}
