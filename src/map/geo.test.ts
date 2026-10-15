import { describe, expect, it } from 'vitest'
import { MAP_BOUNDS, MAP_SIZE, decodeElevation, encodeElevation, project, toTextureUv } from './geo.ts'

describe('projection', () => {
  it('centres the map on the middle of its bounds', () => {
    const center = project((MAP_BOUNDS.west + MAP_BOUNDS.east) / 2, (MAP_BOUNDS.south + MAP_BOUNDS.north) / 2)
    expect(center.x).toBeCloseTo(0)
    expect(center.z).toBeCloseTo(0)
  })

  it('puts north away from the viewer and east to the right', () => {
    const rome = project(12.49, 41.89)
    const constantinople = project(28.97, 41.01)
    const alexandria = project(29.92, 31.2)
    expect(constantinople.x).toBeGreaterThan(rome.x)
    expect(alexandria.z).toBeGreaterThan(constantinople.z)
  })

  it('spans the whole map size between the corners', () => {
    const southWest = project(MAP_BOUNDS.west, MAP_BOUNDS.south)
    const northEast = project(MAP_BOUNDS.east, MAP_BOUNDS.north)
    expect(northEast.x - southWest.x).toBeCloseTo(MAP_SIZE.width)
    expect(southWest.z - northEast.z).toBeCloseTo(MAP_SIZE.depth)
  })

  it('maps the bounds to texture coordinates from 0 to 1', () => {
    expect(toTextureUv(MAP_BOUNDS.west, MAP_BOUNDS.south)).toEqual({ u: 0, v: 0 })
    expect(toTextureUv(MAP_BOUNDS.east, MAP_BOUNDS.north)).toEqual({ u: 1, v: 1 })
  })
})

describe('elevation encoding', () => {
  it('keeps sea level between the two middle bytes', () => {
    expect(encodeElevation(1)).toBe(129)
    expect(encodeElevation(-1)).toBe(126)
    expect(decodeElevation(128)).toBeGreaterThan(0)
    expect(decodeElevation(127)).toBeLessThan(0)
  })

  it('round trips mountains and deep sea within a few percent', () => {
    for (const meters of [4800, 2000, 300, -200, -3000, -6000]) {
      expect(Math.abs(decodeElevation(encodeElevation(meters)) - meters)).toBeLessThan(Math.abs(meters) * 0.05 + 40)
    }
  })

  it('clamps beyond the encoded range', () => {
    expect(encodeElevation(9000)).toBe(255)
    expect(encodeElevation(-11000)).toBe(0)
  })
})
