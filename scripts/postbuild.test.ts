import { describe, expect, it } from 'vitest'
import type { HistoricalEvent } from '../src/data/schema.ts'
import { escapeHtml, sharePage, sitemap } from './postbuild.ts'

const cannes: HistoricalEvent = {
  id: 'bataille-de-cannes',
  title: 'Bataille de Cannes',
  start: -215,
  month: 8,
  day: 2,
  precision: 'day',
  certainty: 'attested',
  era: 'republique',
  track: 'rome',
  category: 'war',
  importance: 1,
  summary: 'Hannibal encercle et détruit l\'armée romaine "consulaire".',
  body: 'Texte.',
  sources: [{ kind: 'ancient', author: 'Polybe', work: 'Histoires', locus: 'III, 107 à 117' }],
}

describe('share pages', () => {
  it('escapes html special characters', () => {
    expect(escapeHtml(`<a href="x">l'"&</a>`)).toBe('&#60;a href=&#34;x&#34;&#62;l&#39;&#34;&#38;&#60;/a&#62;')
  })

  it('gives each event its own title, description, canonical url and redirect', () => {
    const page = sharePage(cannes)
    expect(page).toContain('<title>Bataille de Cannes (2 août 216 av. J.-C.) | Roma</title>')
    expect(page).toContain('content="Hannibal encercle et détruit l&#39;armée romaine &#34;consulaire&#34;."')
    expect(page).toContain('<link rel="canonical" href="https://maximator13.github.io/roma/evenement/bataille-de-cannes/" />')
    expect(page).toContain('location.replace("/roma/#/evenement/bataille-de-cannes")')
  })

  it('lists the home page and every event page in the sitemap', () => {
    const xml = sitemap([cannes], '2026-10-15')
    expect(xml).toContain('<loc>https://maximator13.github.io/roma/</loc>')
    expect(xml).toContain('<loc>https://maximator13.github.io/roma/evenement/bataille-de-cannes/</loc><lastmod>2026-10-15</lastmod>')
  })
})
