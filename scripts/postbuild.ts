import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { formatDate } from '../src/core/dates.ts'
import { events } from '../src/data/events.ts'
import type { HistoricalEvent } from '../src/data/schema.ts'
import { SITE, SITE_URL } from '../src/site.ts'

const DIST = 'dist'
const OG_IMAGE = `${SITE_URL}og-image.png`

export function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (character) => `&#${character.charCodeAt(0)};`)
}

export function eventPath(event: HistoricalEvent): string {
  return `evenement/${event.id}/`
}

export function eventAppUrl(event: HistoricalEvent): string {
  return `${SITE.base}#/evenement/${event.id}`
}

function socialMeta(title: string, description: string, url: string): string {
  return [
    `<meta property="og:type" content="article" />`,
    `<meta property="og:locale" content="fr_FR" />`,
    `<meta property="og:site_name" content="${SITE.name}" />`,
    `<meta property="og:title" content="${escapeHtml(title)}" />`,
    `<meta property="og:description" content="${escapeHtml(description)}" />`,
    `<meta property="og:url" content="${url}" />`,
    `<meta property="og:image" content="${OG_IMAGE}" />`,
    `<meta name="twitter:card" content="summary_large_image" />`,
    `<meta name="twitter:title" content="${escapeHtml(title)}" />`,
    `<meta name="twitter:description" content="${escapeHtml(description)}" />`,
    `<meta name="twitter:image" content="${OG_IMAGE}" />`,
  ].join('\n    ')
}

const PAGE_STYLE =
  'body{margin:0;background:#1b1410;color:#f1e6d2;font:18px/1.6 Georgia,serif}main{max-width:40rem;margin:0 auto;padding:3rem 1.25rem}a{color:#e2bd6b}h1{font-weight:normal;letter-spacing:.06em;text-transform:uppercase}'

export function sharePage(event: HistoricalEvent): string {
  const date = formatDate(event)
  const title = `${event.title} (${date})`
  const url = `${SITE_URL}${eventPath(event)}`
  const target = eventAppUrl(event)
  return `<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${escapeHtml(title)} | ${SITE.name}</title>
    <meta name="description" content="${escapeHtml(event.summary)}" />
    <link rel="canonical" href="${url}" />
    <link rel="icon" href="${SITE.base}favicon.svg" type="image/svg+xml" />
    ${socialMeta(title, event.summary, url)}
    <style>${PAGE_STYLE}</style>
    <script>location.replace(${JSON.stringify(target)})</script>
  </head>
  <body>
    <main>
      <h1>${escapeHtml(event.title)}</h1>
      <p>${escapeHtml(date)}</p>
      <p>${escapeHtml(event.summary)}</p>
      <p><a href="${target}">Voir dans la frise chronologique</a></p>
    </main>
  </body>
</html>
`
}

export function notFoundPage(): string {
  return `<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Page introuvable | ${SITE.name}</title>
    <meta name="robots" content="noindex" />
    <link rel="icon" href="${SITE.base}favicon.svg" type="image/svg+xml" />
    <style>${PAGE_STYLE}</style>
  </head>
  <body>
    <main>
      <h1>Page introuvable</h1>
      <p>Cette adresse ne correspond à aucune page du site.</p>
      <p><a href="${SITE.base}">Revenir à la frise chronologique</a></p>
    </main>
  </body>
</html>
`
}

export function sitemap(items: HistoricalEvent[], lastModified: string): string {
  const urls = [SITE_URL, ...items.map((event) => `${SITE_URL}${eventPath(event)}`)]
  const entries = urls.map((url) => `  <url><loc>${url}</loc><lastmod>${lastModified}</lastmod></url>`)
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${entries.join('\n')}
</urlset>
`
}

function writePage(relativePath: string, content: string) {
  const file = join(DIST, relativePath)
  mkdirSync(join(file, '..'), { recursive: true })
  writeFileSync(file, content)
}

function main() {
  events.forEach((event) => writePage(join(eventPath(event), 'index.html'), sharePage(event)))
  writePage('404.html', notFoundPage())
  writePage('sitemap.xml', sitemap(events, new Date().toISOString().slice(0, 10)))
  console.log(`Postbuild: ${events.length} share pages, 404.html, sitemap.xml.`)
}

if (import.meta.main) main()
