import { describe, expect, it } from 'vitest'
import { MAX_DISTANCE, MIN_DISTANCE, approach, approachGoal, fitDistance, goalForBounds, goalForPlace } from './camera.ts'
import { activeSlices, sliceKey, unionBounds, type TerritorySlice } from './territories.ts'

const slice = (track: TerritorySlice['track'], from: number, to: number, bounds: TerritorySlice['bounds']): TerritorySlice => ({
  track,
  polity: track,
  from,
  to,
  bounds,
  polygons: [],
})

const republic = slice('rome', -508, -264, [10, 38, 18, 46])
const empire = slice('rome', -26, 395, [-10, 25, 45, 56])
const gaul = slice('empire-des-gaules', 260, 274, [-5, 42, 10, 55])

describe('territory slices', () => {
  it('selects the slices active at a year, inclusive', () => {
    expect(activeSlices([republic, empire, gaul], -264)).toEqual([republic])
    expect(activeSlices([republic, empire, gaul], 265)).toEqual([empire, gaul])
    expect(activeSlices([republic, empire, gaul], -100)).toEqual([])
  })

  it('identifies a set of slices so transitions start only on change', () => {
    expect(sliceKey([empire, gaul])).toBe('rome:-26|empire-des-gaules:260')
    expect(sliceKey(activeSlices([empire], 100))).toBe(sliceKey(activeSlices([empire], 200)))
  })

  it('unions bounds', () => {
    expect(unionBounds([republic, gaul])).toEqual([-5, 38, 18, 55])
    expect(unionBounds([])).toBeNull()
  })
})

describe('camera goals', () => {
  it('pulls back as the territory grows', () => {
    const small = goalForBounds(republic.bounds, 40, 16 / 9)
    const large = goalForBounds(empire.bounds, 40, 16 / 9)
    expect(large.distance).toBeGreaterThan(small.distance)
  })

  it('keeps the distance within limits', () => {
    expect(fitDistance(0.1, 0.1, 40, 1.5)).toBe(MIN_DISTANCE)
    expect(fitDistance(500, 500, 40, 1.5)).toBe(MAX_DISTANCE)
  })

  it('centres a place close up', () => {
    const rome = goalForPlace(12.49, 41.89)
    expect(rome.distance).toBeLessThan(10)
  })

  it('approaches the goal smoothly and reaches it immediately without a time constant', () => {
    expect(approach(0, 10, 0.5, 0)).toBe(10)
    const step = approach(0, 10, 0.5, 0.5)
    expect(step).toBeGreaterThan(5)
    expect(step).toBeLessThan(10)
    const goal = approachGoal({ x: 0, z: 0, distance: 4 }, { x: 10, z: 10, distance: 16 }, 10, 0.5)
    expect(goal.x).toBeCloseTo(10)
    expect(goal.distance).toBeCloseTo(16)
  })
})
