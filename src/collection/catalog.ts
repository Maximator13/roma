import { formatRange, formatYear } from '../core/dates.ts'
import type { Card, CardArt, CardKind, City, Era, EraId, Person, Place, Rarity, Source } from '../data/schema.ts'
import type { PoolCard } from './game.ts'

export interface CardView {
  id: string
  kind: CardKind
  rarity: Rarity
  era: EraId
  year: number
  name: string
  subtitle: string
  dateLabel: string | null
  text: string
  sources: Source[]
  scene?: string
  art?: CardArt
}

export interface CatalogSources {
  cards: Card[]
  art: CardArt[]
  eras: Era[]
  people: Person[]
  cities: City[]
  places: Place[]
}

export function eraOf(year: number, eras: Era[]): EraId {
  const era = eras.find((candidate) => year >= candidate.start && year <= candidate.end) ?? (year < (eras[0]?.start ?? 0) ? eras[0] : eras.at(-1))
  if (!era) throw new Error('No era defined')
  return era.id
}

function withoutParenthesis(name: string): string {
  return name.replace(/\s*\(.*\)\s*$/, '')
}

function firstAncientName(name: string | undefined): string | undefined {
  return name?.split(',')[0]?.trim()
}

function personDates(person: Person): string | null {
  if (person.born !== undefined && person.died !== undefined) return formatRange(person.born, person.died)
  if (person.died !== undefined) return `mort en ${formatYear(person.died)}`
  return null
}

function describe(card: Card, data: CatalogSources): { name: string; subtitle: string; dateLabel: string | null } {
  const person = card.person ? data.people.find((candidate) => candidate.id === card.person) : undefined
  if (person) return { name: card.name ?? withoutParenthesis(person.name), subtitle: card.subtitle ?? person.role, dateLabel: personDates(person) }
  const city = card.city ? data.cities.find((candidate) => candidate.id === card.city) : undefined
  if (city) return { name: card.name ?? city.name, subtitle: card.subtitle ?? firstAncientName(city.ancientName) ?? '', dateLabel: null }
  const place = card.place ? data.places.find((candidate) => candidate.id === card.place) : undefined
  if (place) return { name: card.name ?? withoutParenthesis(place.name), subtitle: card.subtitle ?? firstAncientName(place.ancientName) ?? '', dateLabel: null }
  return { name: card.name ?? card.id, subtitle: card.subtitle ?? '', dateLabel: null }
}

export function buildCatalog(data: CatalogSources): CardView[] {
  return data.cards.map((card) => {
    const view: CardView = {
      id: card.id,
      kind: card.kind,
      rarity: card.rarity,
      era: eraOf(card.year, data.eras),
      year: card.year,
      ...describe(card, data),
      text: card.text,
      sources: card.sources,
    }
    const art = data.art.find((item) => item.card === card.id)
    if (card.scene) view.scene = card.scene
    if (art) view.art = art
    return view
  })
}

export function toPool(catalog: CardView[]): PoolCard[] {
  return catalog.map((card) => (card.scene ? { id: card.id, rarity: card.rarity, kind: card.kind, era: card.era, scene: card.scene } : { id: card.id, rarity: card.rarity, kind: card.kind, era: card.era }))
}
