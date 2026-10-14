import { describe, expect, it } from 'vitest'
import { tickStep, ticks } from './ticks.ts'

describe('ticks', () => {
  it('picks a step that keeps labels apart', () => {
    expect(tickStep(2300, 1000)).toBe(250)
    expect(tickStep(100, 1000)).toBe(10)
    expect(tickStep(10, 1000)).toBe(1)
  })

  it('lands on round historical years on both sides of the era change, never on year zero', () => {
    const years = ticks({ center: 0, span: 1000 }, 1000)
    expect(years).toContain(-99)
    expect(years).toContain(-199)
    expect(years).toContain(100)
    expect(years).toContain(1)
    expect(years).not.toContain(0)
  })

  it('counts every year when zoomed in close', () => {
    expect(ticks({ center: 0.5, span: 9 }, 1000)).toEqual([-4, -3, -2, -1, 0, 1, 2, 3, 4, 5])
  })
})
