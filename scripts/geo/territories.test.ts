import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { tracks } from '../../src/data/tracks.ts'
import { MAP_BOUNDS } from '../../src/map/geo.ts'
import {
  SIZE_TARGET,
  TERRITORIES_FILE,
  cleanRing,
  mergedRuns,
  planTrack,
  territoriesSchema,
  toAstronomical,
  uncoveredYears,
  withBridgedGaps,
} from './territories.ts'
import type { Row, Slice } from './territories.ts'

const text = readFileSync(TERRITORIES_FILE, 'utf8')
const { attribution, slices } = territoriesSchema.parse(JSON.parse(text))
const square: Row['geometry'] = { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] }
const row = (polity: string, from: number, to: number): Row => ({ polity, from, to, geometry: square })

describe('Cliopatria years', () => {
  it('reads negative years as historical BCE years and the filler year 0 as 1 BCE', () => {
    expect(toAstronomical(-753)).toBe(-752)
    expect(toAstronomical(-31)).toBe(-30)
    expect(toAstronomical(-1)).toBe(0)
    expect(toAstronomical(0)).toBe(0)
    expect(toAstronomical(1)).toBe(1)
    expect(toAstronomical(1453)).toBe(1453)
  })
})

describe('slice planning', () => {
  it('lets the later row win from its start and stretches the edges to the track span', () => {
    const plans = planTrack(
      'rome',
      [{ start: -752, end: 395 }],
      [row('Roman Kingdom', -749, -500), row('Roman Kingdom', -499, -480), row('Roman Republic', -499, -31), row('Roman Empire', -30, 394)],
      [],
    )
    expect(plans.map(({ polity, from, to }) => [polity, from, to])).toEqual([
      ['Roman Kingdom', -752, -500],
      ['Roman Republic', -499, -31],
      ['Roman Empire', -30, 395],
    ])
  })

  it('clamps rows to every span and leaves edges far from the span alone', () => {
    const plans = planTrack(
      'orient',
      [
        { start: 395, end: 1204 },
        { start: 1261, end: 1453 },
      ],
      [row('Byzantine Empire', 420, 1205), row('Byzantine Empire', 1206, 1226), row('Byzantine Empire', 1279, 1467)],
      [],
    )
    expect(plans.map(({ from, to }) => [from, to])).toEqual([
      [420, 1204],
      [1279, 1453],
    ])
  })

  it('moves the nearest row into a span that no row reaches', () => {
    const latest = { ...row('Palmyrene Empire', 265, 269), geometry: { ...square } }
    const plans = planTrack('palmyre', [{ start: 270, end: 273 }], [row('Palmyrene Empire', 261, 262), latest], [])
    expect(plans.map(({ from, to }) => [from, to])).toEqual([[270, 273]])
    expect(plans[0]?.rows[0]?.geometry).toBe(latest.geometry)
  })

  it('bridges gaps of at most ten years between rows of one polity with identical geometry', () => {
    const larger: Row = { ...row('Nicaean Empire', 1449, 1453), geometry: { type: 'Polygon', coordinates: [[[0, 0], [2, 0], [2, 2], [0, 0]]] } }
    const rows = [
      row('Byzantine Empire', 1395, 1401),
      row('Byzantine Empire', 1407, 1414),
      row('Byzantine Empire', 1425, 1430),
      row('Byzantine Empire', 1442, 1444),
      row('Nicaean Empire', 1446, 1447),
      larger,
    ]
    expect(withBridgedGaps(rows).map(({ polity, from, to }) => [polity, from, to])).toEqual([
      ['Byzantine Empire', 1395, 1430],
      ['Byzantine Empire', 1442, 1444],
      ['Nicaean Empire', 1446, 1447],
      ['Nicaean Empire', 1449, 1453],
    ])
    expect(rows[0]?.to).toBe(1401)
  })

  it('bridges such gaps on main tracks only', () => {
    const spans = [{ start: 1261, end: 1453 }]
    const rows = [row('Byzantine Empire', 1261, 1401), row('Byzantine Empire', 1407, 1453)]
    expect(planTrack('orient', spans, rows, []).map(({ from, to }) => [from, to])).toEqual([[1261, 1453]])
    expect(planTrack('trebizonde', spans, rows, []).map(({ from, to }) => [from, to])).toEqual([
      [1261, 1401],
      [1407, 1453],
    ])
  })

  it('splits a slice where merged territory joins it', () => {
    const plans = planTrack('rome', [{ start: 270, end: 282 }], [row('Roman Empire', 270, 282)], [row('Gallic Empire', 275, 282)])
    expect(plans.map(({ from, to, rows }) => [from, to, rows.map((part) => part.polity)])).toEqual([
      [270, 274, ['Roman Empire']],
      [275, 282, ['Roman Empire', 'Gallic Empire']],
    ])
  })
})

describe('geometry cleaning', () => {
  it('rounds to two decimals, drops repeated points and closes the ring', () => {
    expect(cleanRing([[1.234, 2.001], [3.001, 2.004], [3.004, 4], [1.2, 4.001]])).toEqual([
      [1.23, 2],
      [3, 2],
      [3, 4],
      [1.2, 4],
      [1.23, 2],
    ])
  })

  it('rejects rings that collapse when rounded', () => {
    expect(cleanRing([[1, 1], [1.001, 1.001], [1.002, 1], [1, 1]])).toBeNull()
    expect(cleanRing([[0, 0], [1, 1], [2, 2], [0, 0]])).toBeNull()
  })

  it('joins consecutive identical slices of the same polity', () => {
    const base: Slice = { track: 'rome', polity: 'Roman Kingdom', from: -752, to: -700, bounds: [0, 0, 1, 1], polygons: [] }
    expect(mergedRuns([base, { ...base, from: -699, to: -500 }, { ...base, polity: 'Roman Republic', from: -499, to: -480 }])).toEqual([
      { ...base, to: -500 },
      { ...base, polity: 'Roman Republic', from: -499, to: -480 },
    ])
  })
})

describe('territories file', () => {
  it('credits Cliopatria under CC BY 4.0 and states the changes', () => {
    for (const part of ['J. S. Bennett, E. Mutch, A. Tollefson et al.', 'v0.2.1', 'https://github.com/Seshat-Global-History-Databank/cliopatria', 'CC BY 4.0', 'modifié']) {
      expect(attribution).toContain(part)
    }
  })

  it('stays within the size target', () => {
    expect(Buffer.byteLength(text)).toBeLessThanOrEqual(SIZE_TARGET)
  })

  it('keeps every slice inside the spans of a known track', () => {
    for (const slice of slices) {
      const track = tracks.find((candidate) => candidate.id === slice.track)
      expect(track, slice.track).toBeDefined()
      expect(slice.from).toBeLessThanOrEqual(slice.to)
      expect(track?.spans.some((span) => span.start <= slice.from && slice.to <= span.end), `${slice.track} ${slice.from}`).toBe(true)
    }
  })

  it('sorts slices by track then start and never overlaps them within a track', () => {
    const order = tracks.map((track) => track.id)
    slices.forEach((slice, index) => {
      const previous = slices[index - 1]
      if (!previous) return
      const trackStep = order.indexOf(slice.track) - order.indexOf(previous.track)
      expect(trackStep, `${slice.track} ${slice.from}`).toBeGreaterThanOrEqual(0)
      if (trackStep === 0) expect(slice.from, `${slice.track} ${slice.from}`).toBeGreaterThan(previous.to)
    })
  })

  it('covers every span of every track', () => {
    for (const track of tracks) {
      const uncovered = track.spans.flatMap((span) => uncoveredYears(slices, [track.id], span.start, span.end))
      expect(uncovered, track.id).toEqual([])
    }
  })

  it('shows a Roman state on rome, orient or nicee every year from 750 BCE to 1453', () => {
    expect(uncoveredYears(slices, ['rome', 'orient', 'nicee'], -750, 1453)).toEqual([])
  })

  it('stores closed rings of at least four points inside the map bounds', () => {
    for (const slice of slices) {
      expect(slice.polygons.length, `${slice.track} ${slice.from}`).toBeGreaterThan(0)
      const [west, south, east, north] = slice.bounds
      for (const ring of slice.polygons.flat()) {
        expect(ring.length).toBeGreaterThanOrEqual(4)
        expect(ring.at(-1)).toEqual(ring[0])
        for (const [lon, lat] of ring) {
          expect(lon >= MAP_BOUNDS.west && lon <= MAP_BOUNDS.east && lat >= MAP_BOUNDS.south && lat <= MAP_BOUNDS.north).toBe(true)
          expect(lon >= west && lon <= east && lat >= south && lat <= north).toBe(true)
        }
      }
    }
  })
})
