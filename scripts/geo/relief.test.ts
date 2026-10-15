import { statSync } from 'node:fs'
import sharp from 'sharp'
import { beforeAll, describe, expect, it } from 'vitest'
import { MAP_BOUNDS, RELIEF_SIZE, decodeElevation } from '../../src/map/geo.ts'
import { RELIEF_FILE } from './relief.ts'

let pixels: Uint8Array

function byteAt(lon: number, lat: number): number {
  const column = Math.floor(((lon - MAP_BOUNDS.west) / (MAP_BOUNDS.east - MAP_BOUNDS.west)) * RELIEF_SIZE.width)
  const row = Math.floor(((MAP_BOUNDS.north - lat) / (MAP_BOUNDS.north - MAP_BOUNDS.south)) * RELIEF_SIZE.height)
  return pixels[row * RELIEF_SIZE.width + column] ?? NaN
}

function metersAt(lon: number, lat: number): number {
  return decodeElevation(byteAt(lon, lat))
}

describe('relief raster', () => {
  beforeAll(async () => {
    const { data, info } = await sharp(RELIEF_FILE).extractChannel(0).raw().toBuffer({ resolveWithObject: true })
    expect([info.width, info.height, info.channels]).toEqual([RELIEF_SIZE.width, RELIEF_SIZE.height, 1])
    pixels = new Uint8Array(data)
  })

  it('has the map size and stays under the weight target', () => {
    expect(pixels.length).toBe(RELIEF_SIZE.width * RELIEF_SIZE.height)
    expect(statSync(RELIEF_FILE).size).toBeLessThanOrEqual(1_000_000)
  })

  it('keeps a clear gap between water and land around sea level', () => {
    expect(pixels.some((byte) => byte >= 126 && byte <= 129)).toBe(false)
  })

  it('puts land, sea and summits where they belong', () => {
    expect(metersAt(12.5, 41.9)).toBeGreaterThan(0)
    expect(metersAt(12.5, 41.9)).toBeLessThan(300)
    expect(metersAt(12.5, 40)).toBeLessThan(-2500)
    expect(metersAt(14.99, 37.75)).toBeGreaterThan(2200)
    expect(byteAt(6.865, 45.833)).toBeGreaterThanOrEqual(235)
    expect(metersAt(31, 30.8)).toBeGreaterThan(0)
    expect(metersAt(28, 40.8)).toBeLessThan(-500)
  })

  it('reads land below sea level as land and inland seas and lakes as water', () => {
    expect(metersAt(27, 29.6)).toBeGreaterThan(0)
    expect(metersAt(51, 42)).toBeLessThan(-200)
    expect(metersAt(42.9, 38.6)).toBeLessThan(0)
  })
})
