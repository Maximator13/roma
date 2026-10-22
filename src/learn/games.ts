import { formatYear } from '../core/dates.ts'
import type { EraId, HistoricalEvent, Place, Track } from '../data/schema.ts'

export type Random = () => number

const MAIN_TRACK = 'rome'
const FULL_MARKS_KM = 60
const ZERO_MARKS_KM = 900

export function seededRandom(seed: number): Random {
  let state = seed >>> 0
  return () => {
    state = (state + 0x6d2b79f5) >>> 0
    let mixed = Math.imul(state ^ (state >>> 15), 1 | state)
    mixed = (mixed + Math.imul(mixed ^ (mixed >>> 7), 61 | mixed)) ^ mixed
    return ((mixed ^ (mixed >>> 14)) >>> 0) / 4294967296
  }
}

export function shuffled<T>(items: readonly T[], random: Random): T[] {
  const copy = [...items]
  for (let index = copy.length - 1; index > 0; index--) {
    const other = Math.floor(random() * (index + 1))
    ;[copy[index], copy[other]] = [copy[other]!, copy[index]!]
  }
  return copy
}

export function pick<T>(items: readonly T[], count: number, random: Random): T[] {
  return shuffled(items, random).slice(0, count)
}

export function inEra(events: readonly HistoricalEvent[], era: EraId | 'toutes'): HistoricalEvent[] {
  return era === 'toutes' ? [...events] : events.filter((event) => event.era === era)
}

export function playable(events: readonly HistoricalEvent[]): HistoricalEvent[] {
  return events.filter((event) => event.importance <= 2 && event.certainty !== 'legendary')
}

export function orderRound(events: readonly HistoricalEvent[], random: Random, size = 5): HistoricalEvent[] {
  const pool = playable(events)
  const chosen: HistoricalEvent[] = []
  for (const event of shuffled(pool, random)) {
    if (chosen.every((other) => Math.abs(other.start - event.start) >= 3)) chosen.push(event)
    if (chosen.length === size) break
  }
  return shuffled(chosen, random)
}

export function orderScore(answer: readonly HistoricalEvent[]): number {
  const sorted = [...answer].sort((a, b) => a.start - b.start)
  return answer.filter((event, index) => event.id === sorted[index]?.id).length
}

export function dateScore(guess: number, event: HistoricalEvent): number {
  const tolerance = { day: 1, month: 1, year: 2, decade: 10, century: 50 }[event.precision]
  const end = event.end ?? event.start
  const error = guess < event.start ? event.start - guess : guess > end ? guess - end : 0
  if (error <= tolerance) return 100
  return Math.max(0, Math.round(100 - ((error - tolerance) / 150) * 100))
}

export interface QuizQuestion {
  event: HistoricalEvent
  kind: 'date' | 'power' | 'place'
  prompt: string
  choices: string[]
  answer: string
}

function distinctFrom<T>(items: readonly T[], keep: (item: T) => boolean, count: number, random: Random): T[] {
  return pick(items.filter(keep), count, random)
}

function dateChoices(event: HistoricalEvent, random: Random): string[] {
  const offsets = shuffled([-150, -90, -60, -35, -20, 20, 35, 60, 90, 150], random).slice(0, 3)
  return shuffled([event.start, ...offsets.map((offset) => event.start + offset)].map(formatYear), random)
}

export function quizQuestion(
  event: HistoricalEvent,
  kind: QuizQuestion['kind'],
  context: { tracks: readonly Track[]; places: readonly Place[] },
  random: Random,
): QuizQuestion | null {
  if (kind === 'date') {
    return { event, kind, prompt: `En quelle année ? ${event.title}`, choices: dateChoices(event, random), answer: formatYear(event.start) }
  }
  if (kind === 'power') {
    const track = context.tracks.find((candidate) => candidate.id === event.track)
    if (!track || track.id === MAIN_TRACK) return null
    const others = distinctFrom(context.tracks, (candidate) => candidate.id !== track.id, 3, random)
    return { event, kind, prompt: `Quelle puissance ? ${event.title}`, choices: shuffled([track, ...others].map((item) => item.name), random), answer: track.name }
  }
  const place = context.places.find((candidate) => candidate.id === event.placeId)
  if (!place) return null
  const others = distinctFrom(context.places, (candidate) => candidate.name !== place.name, 3, random)
  return { event, kind, prompt: `Où ? ${event.title}`, choices: shuffled([place, ...others].map((item) => item.name), random), answer: place.name }
}

export function quizRound(
  events: readonly HistoricalEvent[],
  context: { tracks: readonly Track[]; places: readonly Place[] },
  random: Random,
  size = 10,
): QuizQuestion[] {
  const kinds: QuizQuestion['kind'][] = ['date', 'power', 'place']
  const questions: QuizQuestion[] = []
  for (const event of shuffled(playable(events), random)) {
    const kind = kinds[questions.length % kinds.length]!
    const question = quizQuestion(event, kind, context, random) ?? quizQuestion(event, 'date', context, random)
    if (question) questions.push(question)
    if (questions.length === size) break
  }
  return questions
}

export function distanceKm(a: { lon: number; lat: number }, b: { lon: number; lat: number }): number {
  const radians = Math.PI / 180
  const dLat = (b.lat - a.lat) * radians
  const dLon = (b.lon - a.lon) * radians
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * radians) * Math.cos(b.lat * radians) * Math.sin(dLon / 2) ** 2
  return 2 * 6371 * Math.asin(Math.sqrt(h))
}

export function whereScore(kilometres: number): number {
  if (kilometres <= FULL_MARKS_KM) return 100
  return Math.max(0, Math.round(100 - ((kilometres - FULL_MARKS_KM) / (ZERO_MARKS_KM - FULL_MARKS_KM)) * 100))
}

function folded(text: string): string {
  return text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

export interface SearchHit {
  kind: 'event' | 'person' | 'place'
  id: string
  title: string
  detail: string
  eventId?: string
}

export function search(
  query: string,
  data: { events: readonly HistoricalEvent[]; people: readonly { id: string; name: string; role: string }[]; places: readonly Place[] },
  limit = 30,
): SearchHit[] {
  const words = folded(query).split(/\s+/).filter((word) => word.length > 1)
  if (words.length === 0) return []
  const matches = (text: string) => {
    const haystack = folded(text)
    return words.every((word) => haystack.includes(word))
  }
  const firstEvent = (test: (event: HistoricalEvent) => boolean) => data.events.filter(test).sort((a, b) => a.importance - b.importance)[0]
  const events = data.events
    .filter((event) => matches(`${event.title} ${event.summary}`))
    .sort((a, b) => a.importance - b.importance || a.start - b.start)
    .map((event): SearchHit => ({ kind: 'event', id: event.id, title: event.title, detail: formatYear(event.start), eventId: event.id }))
  const persons = data.people
    .filter((person) => matches(`${person.name} ${person.role}`))
    .map((person): SearchHit => ({ kind: 'person', id: person.id, title: person.name, detail: person.role, eventId: firstEvent((event) => event.people?.includes(person.id) ?? false)?.id }))
  const places = data.places
    .filter((place) => matches(`${place.name} ${place.ancientName ?? ''}`))
    .map((place): SearchHit => ({ kind: 'place', id: place.id, title: place.name, detail: place.ancientName ?? '', eventId: firstEvent((event) => event.placeId === place.id)?.id }))
  return [...events, ...persons, ...places].slice(0, limit)
}
