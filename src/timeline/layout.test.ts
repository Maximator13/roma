import { describe, expect, it } from 'vitest'
import { importanceThreshold, isVisibleAt, placeLabels } from './layout.ts'

describe('semantic zoom', () => {
  it('shows only capital events on the whole timeline and everything at decade scale', () => {
    expect(importanceThreshold(2300)).toBe(1)
    expect(importanceThreshold(400)).toBe(2)
    expect(importanceThreshold(40)).toBe(3)
    expect(isVisibleAt(3, 2300)).toBe(false)
    expect(isVisibleAt(1, 2300)).toBe(true)
  })
})

describe('placeLabels', () => {
  it('stacks overlapping labels on the next free row, most important first', () => {
    const slots = placeLabels(
      [
        { id: 'detail', x: 100, width: 120, importance: 3, start: -100 },
        { id: 'capital', x: 110, width: 120, importance: 1, start: -90 },
        { id: 'apart', x: 600, width: 120, importance: 2, start: 200 },
      ],
      2,
    )
    expect(slots).toEqual([
      { id: 'detail', row: 1 },
      { id: 'capital', row: 0 },
      { id: 'apart', row: 0 },
    ])
  })

  it('falls back to a bare marker when every row is taken', () => {
    const slots = placeLabels(
      [
        { id: 'a', x: 0, width: 200, importance: 1, start: 0 },
        { id: 'b', x: 10, width: 200, importance: 2, start: 1 },
      ],
      1,
    )
    expect(slots[1]).toEqual({ id: 'b', row: null })
  })
})
