import { describe, expect, it } from 'vitest'
import {
  FIRST_YEAR,
  LAST_YEAR,
  centuryOf,
  formatDate,
  formatRange,
  formatYear,
  fromHistorical,
  romanNumeral,
  toHistorical,
  yearsBetween,
} from './dates.ts'

describe('astronomical years', () => {
  it('converts historical years with no year zero', () => {
    expect(fromHistorical(753, 'bc')).toBe(-752)
    expect(fromHistorical(1, 'bc')).toBe(0)
    expect(fromHistorical(1, 'ad')).toBe(1)
    expect(fromHistorical(1453, 'ad')).toBe(1453)
  })

  it('converts back to historical years', () => {
    expect(toHistorical(-752)).toEqual({ year: 753, side: 'bc' })
    expect(toHistorical(0)).toEqual({ year: 1, side: 'bc' })
    expect(toHistorical(1)).toEqual({ year: 1, side: 'ad' })
  })

  it('round trips every year of the project', () => {
    for (let year = FIRST_YEAR; year <= LAST_YEAR; year += 1) {
      const historical = toHistorical(year)
      expect(fromHistorical(historical.year, historical.side)).toBe(year)
    }
  })

  it('rejects impossible historical years', () => {
    expect(() => fromHistorical(0, 'bc')).toThrow()
    expect(() => fromHistorical(2.5, 'ad')).toThrow()
  })

  it('counts 2205 years from 753 BC to 1453', () => {
    expect(FIRST_YEAR).toBe(-752)
    expect(LAST_YEAR).toBe(1453)
    expect(yearsBetween(FIRST_YEAR, LAST_YEAR)).toBe(2205)
    expect(yearsBetween(fromHistorical(1, 'bc'), fromHistorical(1, 'ad'))).toBe(1)
  })
})

describe('formatYear', () => {
  it('marks years before the common era', () => {
    expect(formatYear(-752)).toBe('753 av. J.-C.')
    expect(formatYear(0)).toBe('1 av. J.-C.')
  })

  it('marks only common era years below one hundred', () => {
    expect(formatYear(14)).toBe('14 apr. J.-C.')
    expect(formatYear(99)).toBe('99 apr. J.-C.')
    expect(formatYear(100)).toBe('100')
    expect(formatYear(1453)).toBe('1453')
  })
})

describe('formatRange', () => {
  it('writes the era suffix once when both bounds share it', () => {
    expect(formatRange(fromHistorical(509, 'bc'), fromHistorical(27, 'bc'))).toBe('de 509 à 27 av. J.-C.')
    expect(formatRange(9, 14)).toBe('de 9 à 14 apr. J.-C.')
  })

  it('crosses the start of the common era', () => {
    expect(formatRange(fromHistorical(27, 'bc'), 14)).toBe('de 27 av. J.-C. à 14 apr. J.-C.')
    expect(formatRange(fromHistorical(27, 'bc'), 235)).toBe('de 27 av. J.-C. à 235')
  })

  it('leaves later common era years bare', () => {
    expect(formatRange(284, 476)).toBe('de 284 à 476')
    expect(formatRange(98, 117)).toBe('de 98 apr. J.-C. à 117')
  })
})

describe('centuries', () => {
  it('finds the century of a year', () => {
    expect(centuryOf(fromHistorical(216, 'bc'))).toEqual({ century: 3, side: 'bc' })
    expect(centuryOf(fromHistorical(100, 'bc'))).toEqual({ century: 1, side: 'bc' })
    expect(centuryOf(100)).toEqual({ century: 1, side: 'ad' })
    expect(centuryOf(101)).toEqual({ century: 2, side: 'ad' })
    expect(centuryOf(1453)).toEqual({ century: 15, side: 'ad' })
  })

  it('writes roman numerals', () => {
    expect(romanNumeral(1)).toBe('I')
    expect(romanNumeral(4)).toBe('IV')
    expect(romanNumeral(9)).toBe('IX')
    expect(romanNumeral(14)).toBe('XIV')
    expect(romanNumeral(15)).toBe('XV')
  })
})

describe('formatDate', () => {
  it('formats each precision', () => {
    expect(formatDate({ start: -43, month: 3, day: 15, precision: 'day' })).toBe('15 mars 44 av. J.-C.')
    expect(formatDate({ start: 395, month: 1, day: 1, precision: 'day' })).toBe('1er janvier 395')
    expect(formatDate({ start: -48, month: 1, precision: 'month' })).toBe('janvier 49 av. J.-C.')
    expect(formatDate({ start: -215, precision: 'year' })).toBe('216 av. J.-C.')
    expect(formatDate({ start: 120, precision: 'decade' })).toBe('vers 120')
    expect(formatDate({ start: 250, precision: 'century' })).toBe('IIIe siècle')
    expect(formatDate({ start: 50, precision: 'century' })).toBe('Ier siècle apr. J.-C.')
    expect(formatDate({ start: -215, precision: 'century' })).toBe('IIIe siècle av. J.-C.')
  })

  it('formats spans as ranges', () => {
    expect(formatDate({ start: -263, end: -240, precision: 'year' })).toBe('de 264 à 241 av. J.-C.')
    expect(formatDate({ start: 1204, end: 1204, month: 4, day: 12, precision: 'day' })).toBe('12 avril 1204')
  })
})
