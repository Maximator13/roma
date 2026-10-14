import { describe, expect, it } from 'vitest'
import { frenchSpacing } from './typography.ts'

const nbsp = String.fromCharCode(0x00a0)
const nnbsp = String.fromCharCode(0x202f)

describe('frenchSpacing', () => {
  it('keeps digit groups together', () => {
    expect(frenchSpacing('jusqu’à 87 200 hommes et 1 000 000 de sesterces')).toBe(
      `jusqu’à 87${nnbsp}200 hommes et 1${nnbsp}000${nnbsp}000 de sesterces`,
    )
  })

  it('keeps era mentions with their year', () => {
    expect(frenchSpacing('en 216 av. J.-C. et en 14 apr. J.-C.')).toBe(
      `en 216${nbsp}av.${nbsp}J.-C. et en 14${nbsp}apr.${nbsp}J.-C.`,
    )
  })

  it('binds French punctuation and quotes to their words', () => {
    expect(frenchSpacing('Certitude : attesté ; « Bas-Empire » ?')).toBe(
      `Certitude${nbsp}: attesté${nnbsp}; «${nnbsp}Bas-Empire${nnbsp}»${nnbsp}?`,
    )
  })

  it('leaves years and urls alone', () => {
    expect(frenchSpacing('de 509 à 27 https://example.org/a')).toBe('de 509 à 27 https://example.org/a')
  })
})
