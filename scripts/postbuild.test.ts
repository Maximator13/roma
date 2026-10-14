import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import type { HistoricalEvent } from '../src/data/schema.ts'
import { escapeHtml, sharePage, sitemap } from './postbuild.ts'

const template = readFileSync('index.html', 'utf8')

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

  it('give each event its own title, description, canonical url and social card', () => {
    const page = sharePage(template, cannes)
    expect(page).toContain('<title>Bataille de Cannes (2 août 216 av. J.-C.) | Roma</title>')
    expect(page).toContain(
      '<meta name="description" content="Hannibal encercle et détruit l&#39;armée romaine &#34;consulaire&#34;." />',
    )
    expect(page).toContain('<link rel="canonical" href="https://maximator13.github.io/roma/evenement/bataille-de-cannes/" />')
    expect(page).toContain('<meta property="og:url" content="https://maximator13.github.io/roma/evenement/bataille-de-cannes/" />')
    expect(page).toContain('<meta property="og:type" content="article" />')
    expect(page).toContain('<meta name="twitter:title" content="Bataille de Cannes (2 août 216 av. J.-C.) | Roma" />')
  })

  it('keeps the application and adds a static cartel for crawlers', () => {
    const page = sharePage(template, cannes)
    expect(page).toContain('<script type="module" src="/src/main.tsx"></script>')
    expect(page).toContain('<div id="root"><article><h1>Bataille de Cannes</h1>')
    expect(page).toContain('<li>Polybe, Histoires, III, 107 à 117</li>')
  })

  it('lists the home page and every event page in the sitemap', () => {
    const xml = sitemap([cannes], '2026-10-15')
    expect(xml).toContain('<loc>https://maximator13.github.io/roma/</loc>')
    expect(xml).toContain(
      '<loc>https://maximator13.github.io/roma/evenement/bataille-de-cannes/</loc><lastmod>2026-10-15</lastmod>',
    )
  })
})
