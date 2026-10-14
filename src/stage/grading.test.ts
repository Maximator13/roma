import { describe, expect, it } from 'vitest'
import { eras } from '../data/eras.ts'
import { BACKGROUND, ERA_GRADING, contrastRatio, gradingAt, mixGrading, readableAccent, rgbToCss } from './grading.ts'

describe('gradingAt', () => {
  it('uses the era grading well inside an era', () => {
    expect(gradingAt(-650, eras)).toEqual(ERA_GRADING.royaute)
    expect(gradingAt(900, eras)).toEqual(ERA_GRADING['empire-romain-d-orient'])
    expect(gradingAt(260, eras)).toEqual(ERA_GRADING['crise-du-iiie-siecle'])
  })

  it('blends two eras halfway at their boundary', () => {
    const boundary = gradingAt(-26, eras)
    const halfway = mixGrading(ERA_GRADING.republique, ERA_GRADING['haut-empire'], 0.5)
    expect(boundary.exposure).toBeCloseTo(halfway.exposure)
    expect(boundary.accent[0]).toBeCloseTo(halfway.accent[0])
  })

  it('moves monotonically across a boundary', () => {
    const values = [-60, -40, -26, -10, 10].map((year) => gradingAt(year, eras).saturation)
    const rising = values.every((value, index) => index === 0 || value >= values[index - 1]!)
    expect(rising).toBe(true)
  })
})

describe('rgbToCss', () => {
  it('clamps channels', () => {
    expect(rgbToCss([1.2, 0.5, -0.1])).toBe('rgb(255 128 0)')
  })
})

describe('readableAccent', () => {
  it('keeps text and markers readable on the dark background in every era and transition', () => {
    for (let year = -752; year <= 1453; year += 7) {
      const accent = readableAccent(gradingAt(year, eras).accent)
      expect(contrastRatio(accent, BACKGROUND)).toBeGreaterThanOrEqual(4.5)
    }
  })

  it('computes the reference contrast of black on white', () => {
    expect(contrastRatio([1, 1, 1], [0, 0, 0])).toBeCloseTo(21)
  })
})
