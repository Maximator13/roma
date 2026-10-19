import { mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { formatDate, formatYear } from '../src/core/dates.ts'
import { events } from '../src/data/events.ts'
import { scenes } from '../src/data/scenes.ts'
import type { HistoricalEvent, Scene } from '../src/data/schema.ts'
import { CERTAINTY } from '../src/data/ui.ts'
import { SITE, SITE_URL } from '../src/site.ts'

const DIST = 'dist'
const SITE_BUDGET = 600_000_000
const FILE_LIMIT = 100_000_000

export interface PageMeta {
  title: string
  description: string
  url: string
}

export function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (character) => `&#${character.charCodeAt(0)};`)
}

export function eventPath(event: HistoricalEvent): string {
  return `evenement/${event.id}/`
}

export function scenePath(scene: Scene): string {
  return `scene/${scene.id}/`
}

export function shortDescription(text: string, limit = 155): string {
  if (text.length <= limit) return text
  const cut = text.slice(0, limit - 1)
  return `${cut.slice(0, cut.lastIndexOf(' ')).replace(/[\s,;:.]+$/, '')}…`
}

function replaceOnce(html: string, pattern: RegExp, replacement: string): string {
  if (!pattern.test(html)) throw new Error(`Template is missing ${pattern.source}`)
  return html.replace(pattern, () => replacement)
}

function replaceMeta(html: string, attribute: 'name' | 'property', key: string, content: string): string {
  const pattern = new RegExp(`<meta ${attribute}="${key}" content="[^"]*" />`)
  return replaceOnce(html, pattern, `<meta ${attribute}="${key}" content="${escapeHtml(content)}" />`)
}

export function withPageMeta(template: string, meta: PageMeta, rootContent: string): string {
  const steps: ((html: string) => string)[] = [
    (html) => replaceOnce(html, /<title>[^<]*<\/title>/, `<title>${escapeHtml(meta.title)}</title>`),
    (html) => replaceMeta(html, 'name', 'description', meta.description),
    (html) => replaceOnce(html, /<link rel="canonical" href="[^"]*" \/>/, `<link rel="canonical" href="${meta.url}" />`),
    (html) => replaceMeta(html, 'property', 'og:type', 'article'),
    (html) => replaceMeta(html, 'property', 'og:title', meta.title),
    (html) => replaceMeta(html, 'property', 'og:description', meta.description),
    (html) => replaceMeta(html, 'property', 'og:url', meta.url),
    (html) => replaceMeta(html, 'name', 'twitter:title', meta.title),
    (html) => replaceMeta(html, 'name', 'twitter:description', meta.description),
    (html) => replaceOnce(html, /<div id="root"><\/div>/, `<div id="root">${rootContent}</div>`),
  ]
  return steps.reduce((html, step) => step(html), template)
}

function staticCartel(event: HistoricalEvent): string {
  const sources = event.sources
    .map((source) => `<li>${escapeHtml([source.author, source.work, source.locus].filter(Boolean).join(', '))}</li>`)
    .join('')
  return [
    '<article>',
    `<h1>${escapeHtml(event.title)}</h1>`,
    `<p>${escapeHtml(formatDate(event))}. Certitude : ${escapeHtml(CERTAINTY[event.certainty].label.toLowerCase())}.</p>`,
    `<p>${escapeHtml(event.summary)}</p>`,
    `<ul>${sources}</ul>`,
    `<p><a href="${SITE.base}#/evenement/${event.id}">Voir dans la frise chronologique</a></p>`,
    '</article>',
  ].join('')
}

export function sharePage(template: string, event: HistoricalEvent): string {
  const title = `${event.title} (${formatDate(event)}) | ${SITE.name}`
  const meta = { title, description: shortDescription(event.summary), url: `${SITE_URL}${eventPath(event)}` }
  return withPageMeta(template, meta, staticCartel(event))
}

function staticScene(scene: Scene): string {
  const points = (scene.points ?? []).map((point) => `<li>${escapeHtml(point.title)}</li>`).join('')
  return [
    '<article>',
    `<h1>${escapeHtml(scene.title)}</h1>`,
    `<p>${escapeHtml(scene.summary ?? '')}</p>`,
    `<ul>${points}</ul>`,
    `<p><a href="${SITE.base}#/scene/${scene.id}">Visiter la scène en 3D</a></p>`,
    '</article>',
  ].join('')
}

export function sceneSharePage(template: string, scene: Scene): string {
  const year = scene.year === undefined ? '' : ` (vers ${formatYear(scene.year)})`
  const meta = {
    title: `${scene.title}${year}, scène 3D | ${SITE.name}`,
    description: shortDescription(scene.summary ?? scene.title),
    url: `${SITE_URL}${scenePath(scene)}`,
  }
  return withPageMeta(template, meta, staticScene(scene))
}

const NOT_FOUND_STYLE =
  'body{margin:0;background:#120d0a;color:#f3ead8;font:18px/1.6 Georgia,serif}main{max-width:40rem;margin:0 auto;padding:3rem 1.25rem}a{color:#e8d19c}h1{font-weight:normal;letter-spacing:.06em;text-transform:uppercase}'

export function notFoundPage(): string {
  return `<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Page introuvable | ${SITE.name}</title>
    <meta name="robots" content="noindex" />
    <link rel="icon" href="${SITE.base}favicon.svg" type="image/svg+xml" />
    <style>${NOT_FOUND_STYLE}</style>
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

export function sitemap(items: HistoricalEvent[], lastModified: string, extraPaths: string[] = []): string {
  const urls = [SITE_URL, ...items.map((event) => `${SITE_URL}${eventPath(event)}`), ...extraPaths.map((path) => `${SITE_URL}${path}`)]
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

export function filesIn(directory: string): { path: string; bytes: number }[] {
  return readdirSync(directory, { recursive: true, withFileTypes: true })
    .filter((entry) => entry.isFile())
    .map((entry) => {
      const path = join(entry.parentPath, entry.name)
      return { path, bytes: statSync(path).size }
    })
}

function checkSiteBudget() {
  const files = filesIn(DIST)
  const total = files.reduce((sum, file) => sum + file.bytes, 0)
  const oversized = files.filter((file) => file.bytes > FILE_LIMIT)
  console.log(`Site weight: ${(total / 1e6).toFixed(2)} MB of ${SITE_BUDGET / 1e6} MB, ${files.length} files.`)
  if (total > SITE_BUDGET || oversized.length > 0) {
    console.error(`Budget exceeded: ${oversized.map((file) => file.path).join(', ') || 'total site weight'}`)
    process.exit(1)
  }
}

function main() {
  const template = readFileSync(join(DIST, 'index.html'), 'utf8')
  events.forEach((event) => writePage(join(eventPath(event), 'index.html'), sharePage(template, event)))
  const ready = scenes.filter((scene) => scene.status === 'ready')
  ready.forEach((scene) => writePage(join(scenePath(scene), 'index.html'), sceneSharePage(template, scene)))
  writePage('404.html', notFoundPage())
  writePage('sitemap.xml', sitemap(events, new Date().toISOString().slice(0, 10), ready.map(scenePath)))
  console.log(`Postbuild: ${events.length} event and ${ready.length} scene share pages, 404.html, sitemap.xml.`)
  checkSiteBudget()
}

if (import.meta.main) main()
