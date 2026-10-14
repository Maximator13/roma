import { describe, expect, it } from 'vitest'
import { parseHash, routeToHash } from './route.ts'

describe('parseHash', () => {
  it('reads the home route', () => {
    expect(parseHash('')).toEqual({ name: 'home' })
    expect(parseHash('#')).toEqual({ name: 'home' })
    expect(parseHash('#/')).toEqual({ name: 'home' })
  })

  it('reads event and page routes', () => {
    expect(parseHash('#/evenement/bataille-de-cannes')).toEqual({ name: 'event', id: 'bataille-de-cannes' })
    expect(parseHash('#/evenement/bataille-de-cannes/')).toEqual({ name: 'event', id: 'bataille-de-cannes' })
    expect(parseHash('#/mentions-legales')).toEqual({ name: 'page', id: 'mentions-legales' })
  })

  it('reports anything else as not found', () => {
    expect(parseHash('#/evenement/Cannes')).toEqual({ name: 'not-found', path: 'evenement/Cannes' })
    expect(parseHash('#/evenement')).toEqual({ name: 'not-found', path: 'evenement' })
    expect(parseHash('#/inconnu')).toEqual({ name: 'not-found', path: 'inconnu' })
  })
})

describe('routeToHash', () => {
  it('round trips every route kind', () => {
    for (const hash of ['#/', '#/evenement/chute-de-constantinople', '#/sources']) {
      expect(routeToHash(parseHash(hash))).toBe(hash)
    }
  })
})
