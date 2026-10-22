import { describe, expect, it } from 'vitest'
import { internalRoute, parseHash, routeFromLocation, routeToHash } from './route.ts'

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

  it('reads scene routes', () => {
    expect(parseHash('#/scene/nimes')).toEqual({ name: 'scene', id: 'nimes' })
    expect(parseHash('#/scene/pont-du-gard/')).toEqual({ name: 'scene', id: 'pont-du-gard' })
    expect(parseHash('#/scene/Nimes')).toEqual({ name: 'not-found', path: 'scene/Nimes' })
    expect(parseHash('#/scene/nimes/forum')).toEqual({ name: 'not-found', path: 'scene/nimes/forum' })
  })

  it('reads learn and search routes', () => {
    expect(parseHash('#/apprendre')).toEqual({ name: 'learn' })
    expect(parseHash('#/apprendre/ou')).toEqual({ name: 'learn', game: 'ou' })
    expect(parseHash('#/apprendre/inconnu')).toEqual({ name: 'not-found', path: 'apprendre/inconnu' })
    expect(parseHash('#/recherche')).toEqual({ name: 'search' })
    expect(routeToHash({ name: 'learn', game: 'quiz' })).toBe('#/apprendre/quiz')
    expect(routeToHash({ name: 'learn' })).toBe('#/apprendre')
    expect(routeToHash({ name: 'search' })).toBe('#/recherche')
  })

  it('reports anything else as not found', () => {
    expect(parseHash('#/evenement/Cannes')).toEqual({ name: 'not-found', path: 'evenement/Cannes' })
    expect(parseHash('#/evenement')).toEqual({ name: 'not-found', path: 'evenement' })
    expect(parseHash('#/inconnu')).toEqual({ name: 'not-found', path: 'inconnu' })
  })
})

describe('routeToHash', () => {
  it('round trips every route kind', () => {
    for (const hash of ['#/', '#/evenement/chute-de-constantinople', '#/scene/arles', '#/sources']) {
      expect(routeToHash(parseHash(hash))).toBe(hash)
    }
  })
})

describe('routeFromLocation', () => {
  it('prefers the hash route', () => {
    expect(routeFromLocation('/roma/evenement/a/', '#/sources', '/roma/')).toEqual({ name: 'page', id: 'sources' })
  })

  it('boots share pages into their event', () => {
    expect(routeFromLocation('/roma/evenement/bataille-de-cannes/', '', '/roma/')).toEqual({
      name: 'event',
      id: 'bataille-de-cannes',
    })
  })

  it('treats the site root as home', () => {
    expect(routeFromLocation('/roma/', '', '/roma/')).toEqual({ name: 'home' })
    expect(routeFromLocation('/roma/index.html', '#/', '/roma/')).toEqual({ name: 'home' })
  })
})

describe('internalRoute', () => {
  it('recognises internal links in both forms and ignores the rest', () => {
    expect(internalRoute('#/sources', '/roma/')).toEqual({ name: 'page', id: 'sources' })
    expect(internalRoute('/roma/#/evenement/x', '/roma/')).toEqual({ name: 'event', id: 'x' })
    expect(internalRoute('https://example.org/', '/roma/')).toBeNull()
  })
})
