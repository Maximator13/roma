import { describe, expect, it } from 'vitest'
import { eras } from '../data/eras.ts'
import { ERA_GRADING, gradingAt, mixGrading, rgbToCss } from './grading.ts'

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
