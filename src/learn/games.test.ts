import { describe, expect, it } from 'vitest'
import { events } from '../data/events.ts'
import { people } from '../data/people.ts'
import { places } from '../data/places.ts'
import type { HistoricalEvent } from '../data/schema.ts'
import { tracks } from '../data/tracks.ts'
import { markSeen, readProgress, recordScore } from './progress.ts'
import { dateScore, distanceKm, orderRound, orderScore, quizRound, search, seededRandom, whereScore } from './games.ts'

const cannes = events.find((event) => event.id === 'bataille-de-cannes')!

describe('order game', () => {
  it('draws distinct, spaced events and scores the positions that are right', () => {
    const round = orderRound(events, seededRandom(1))
    expect(round).toHaveLength(5)
    expect(new Set(round.map((event) => event.id)).size).toBe(5)
    const sorted = [...round].sort((a, b) => a.start - b.start)
    expect(orderScore(sorted)).toBe(5)
    expect(orderScore([...sorted].reverse())).toBe(1)
  })
})

describe('date game', () => {
  it('gives full marks within the precision and less the further the guess', () => {
    const event = { ...cannes, precision: 'year' } as HistoricalEvent
    expect(dateScore(event.start, event)).toBe(100)
    expect(dateScore(event.start + 2, event)).toBe(100)
    expect(dateScore(event.start + 77, event)).toBe(50)
    expect(dateScore(event.start - 500, event)).toBe(0)
  })
})

describe('quiz', () => {
  it('builds ten questions whose answer is always among four choices', () => {
    const round = quizRound(events, { tracks, places }, seededRandom(7))
    expect(round).toHaveLength(10)
    for (const question of round) {
      expect(question.choices).toHaveLength(4)
      expect(question.choices).toContain(question.answer)
      expect(new Set(question.choices).size).toBe(4)
    }
  })

  it('is reproducible for a given seed', () => {
    expect(quizRound(events, { tracks, places }, seededRandom(3)).map((q) => q.prompt)).toEqual(
      quizRound(events, { tracks, places }, seededRandom(3)).map((q) => q.prompt),
    )
  })
})

describe('where game', () => {
  it('measures great circle distances and scores them', () => {
    expect(distanceKm({ lon: 12.4964, lat: 41.9028 }, { lon: 14.2681, lat: 40.8518 })).toBeGreaterThan(180)
    expect(distanceKm({ lon: 12.4964, lat: 41.9028 }, { lon: 14.2681, lat: 40.8518 })).toBeLessThan(200)
    expect(whereScore(10)).toBe(100)
    expect(whereScore(480)).toBe(50)
    expect(whereScore(2000)).toBe(0)
  })
})

describe('search', () => {
  it('finds events, people and places without accents or case', () => {
    const hits = search('cannes', { events, people, places })
    expect(hits[0]?.id).toBe('bataille-de-cannes')
    expect(search('CESAR', { events, people, places }).some((hit) => hit.kind === 'person')).toBe(true)
    expect(search('x', { events, people, places })).toEqual([])
  })
})

describe('progress', () => {
  function memory(): Storage {
    const values = new Map<string, string>()
    return {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => void values.set(key, value),
      removeItem: (key: string) => void values.delete(key),
      clear: () => values.clear(),
      key: () => null,
      length: 0,
    }
  }

  it('remembers seen events once and keeps the best score', () => {
    const storage = memory()
    markSeen('bataille-de-cannes', storage)
    markSeen('bataille-de-cannes', storage)
    recordScore('quiz', 7, storage)
    recordScore('quiz', 4, storage)
    expect(readProgress(storage)).toEqual({ seen: ['bataille-de-cannes'], best: { quiz: 7 } })
  })

  it('survives a broken or missing storage', () => {
    const broken = { getItem: () => '{oops' } as unknown as Storage
    expect(readProgress(broken)).toEqual({ seen: [], best: {} })
    expect(readProgress(undefined)).toEqual({ seen: [], best: {} })
  })
})
