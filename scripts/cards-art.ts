import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import sharp from 'sharp'
import { cards } from '../src/data/cards.ts'
import type { CardArt } from '../src/data/schema.ts'
import { SITE } from '../src/site.ts'

const RAW = '.cache/cards/raw'
const META = '.cache/cards/meta'
const OUTPUT = 'public/cards'
const LARGE = { width: 640, height: 896, quality: 80 }
const SMALL = { width: 320, height: 448, quality: 72 }
const PROJECT_LICENSE = { license: 'CC BY 4.0', licenseUrl: 'https://creativecommons.org/licenses/by/4.0/deed.fr' }

interface Source {
  file: string
  focusX: number
  focusY: number
  zoom: number
  grade: boolean
  art: CardArt
}

interface Meta {
  file?: string
  title: string
  creator: string
  date?: string
  license: string
  licenseUrl?: string
  sourceUrl?: string
  focusX?: number
  focusY?: number
}

function render(card: string, file: string, title: string, script: string, focusX = 0.5, focusY = 0.5, zoom = 1): Source {
  return {
    file,
    focusX,
    focusY,
    zoom,
    grade: true,
    art: { card, title, creator: 'Projet Roma, rendu Blender', ...PROJECT_LICENSE, sourceUrl: `${SITE.repository}/blob/main/blender/${script}.py` },
  }
}

const CREDITS_HEADING = '## Illustrations des cartes'
const SCENES = '.cache/scenes'
const RENDERS = '.cache/cards/renders'

const RENDERED: Record<string, Source> = {
  colisee: render('colisee', `${SCENES}/colisee/previews/facade.png`, 'Le Colisée vers 107, rendu 3D de la scène du site', 'colisee', 0.42),
  'sainte-sophie': render('sainte-sophie', `${SCENES}/constantinople/previews/interieur.png`, 'Sainte-Sophie sous sa coupole, rendu 3D de la scène du site', 'constantinople', 0.5, 0.45),
  pantheon: render('pantheon', `${SCENES}/pantheon/previews/rotonde.png`, "La coupole du Panthéon et son oculus, rendu 3D de la scène du site", 'pantheon', 0.5, 0.5),
  alexandrie: render('alexandrie', `${SCENES}/alexandrie/previews/le-phare.png`, "Le phare d'Alexandrie, rendu 3D de la scène du site", 'alexandrie', 0.5, 0.45),
  pompei: render('pompei', `${SCENES}/pompei/previews/la-rue.png`, "La rue de l'Abondance en 79, rendu 3D de la scène du site", 'pompei', 0.47, 0.5),
  'pont-du-gard': render('pont-du-gard', `${SCENES}/pont-du-gard/previews/le_pont.png`, 'Le pont du Gard vers 130, rendu 3D de la scène du site', 'pont_du_gard', 0.55, 0.45),
  nimes: render('nimes', `${SCENES}/nimes/previews/forum.png`, 'La Maison Carrée et le forum de Nîmes, rendu 3D de la scène du site', 'nimes', 0.42, 0.45),
  arles: render('arles', `${SCENES}/arles/previews/amphitheatre.png`, "L'amphithéâtre d'Arles, rendu 3D de la scène du site", 'arles', 0.72, 0.45),
  cannes: render('cannes', `${RENDERS}/cannes.png`, 'Les légions et la ligne gauloise à Cannes, rendu 3D des figurines du site', 'cards', 0.5, 0.56, 1.45),
  velites: render('velites', `${RENDERS}/velites.png`, 'Vélites en ordre dispersé, rendu 3D des figurines du site', 'cards', 0.45, 0.58, 1.5),
  hastats: render('hastats', `${RENDERS}/hastats.png`, 'Manipule de hastats, rendu 3D des figurines du site', 'cards', 0.5, 0.55, 1.05),
  triaires: render('triaires', `${RENDERS}/triaires.png`, 'Triaires à la lance, rendu 3D des figurines du site', 'cards', 0.5, 0.5, 1.05),
  'cavaliers-numides': render('cavaliers-numides', `${RENDERS}/cavaliers-numides.png`, 'Cavaliers numides, rendu 3D des figurines du site', 'cards', 0.47, 0.58, 1.6),
}

function rawFile(id: string, meta: Meta): string {
  if (meta.file && existsSync(join(RAW, meta.file))) return join(RAW, meta.file)
  const match = readdirSync(RAW).find((name) => name.startsWith(`${id}.`))
  if (!match) throw new Error(`No raw image for ${id}`)
  return join(RAW, match)
}

function fromMeta(id: string): Source {
  const meta = JSON.parse(readFileSync(join(META, `${id}.json`), 'utf8')) as Meta
  const art: CardArt = { card: id, title: meta.title.trim(), creator: meta.creator.trim(), license: meta.license.trim() }
  if (meta.date) art.date = meta.date.trim()
  if (meta.licenseUrl) art.licenseUrl = meta.licenseUrl.replace(/^\/\//, 'https://')
  if (meta.sourceUrl) art.sourceUrl = meta.sourceUrl
  return { file: rawFile(id, meta), focusX: meta.focusX ?? 0.5, focusY: meta.focusY ?? 0.4, zoom: 1, grade: false, art }
}

function cropBox(width: number, height: number, source: Source) {
  const ratio = LARGE.width / LARGE.height
  let cropWidth = Math.min(width, height * ratio) / source.zoom
  let cropHeight = cropWidth / ratio
  cropWidth = Math.round(cropWidth)
  cropHeight = Math.round(cropHeight)
  const left = Math.round(Math.min(Math.max(source.focusX * width - cropWidth / 2, 0), width - cropWidth))
  const top = Math.round(Math.min(Math.max(source.focusY * height - cropHeight / 2, 0), height - cropHeight))
  return { left, top, width: cropWidth, height: cropHeight }
}

async function produce(id: string, source: Source): Promise<number> {
  const upright = await sharp(source.file, { limitInputPixels: false }).rotate().toBuffer()
  const image = sharp(upright, { limitInputPixels: false })
  const { width = 0, height = 0 } = await image.metadata()
  const box = cropBox(width, height, source)
  let pipeline = image.extract(box)
  if (source.grade) pipeline = pipeline.modulate({ saturation: 1.3, brightness: 1.02 }).linear(1.1, -10)
  const cropped = await pipeline.toBuffer()
  let bytes = 0
  for (const [suffix, size] of [['', LARGE], ['-s', SMALL]] as const) {
    const path = join(OUTPUT, `${id}${suffix}.webp`)
    await sharp(cropped).resize(size.width, size.height, { fit: 'cover', kernel: 'lanczos3' }).webp({ quality: size.quality, effort: 6 }).toFile(path)
    bytes += statSync(path).size
  }
  return bytes
}

function dataFile(entries: CardArt[]): string {
  const body = JSON.stringify(entries, null, 2)
  return `import type { CardArt } from './schema.ts'\n\nexport const cardArt: CardArt[] = ${body}\n`
}

function escapeCell(text: string): string {
  return text.replaceAll('|', '/').replace(/\s+/g, ' ')
}

function creditsSection(entries: CardArt[]): string {
  const rows = entries.map((art) => {
    const work = art.sourceUrl ? `[${escapeCell(art.title)}](${art.sourceUrl})` : escapeCell(art.title)
    const date = art.date ? `, ${escapeCell(art.date)}` : ''
    return `| ${art.card} | ${work} | ${escapeCell(art.creator)}${date} | ${art.license} |`
  })
  return [
    CREDITS_HEADING,
    '',
    "Illustrations de la page Collection (`public/cards/`), recadrées au format 5:7 et réduites en WebP (640 et 320 px de large) par `scripts/cards-art.ts` ; les rendus du projet sont légèrement saturés et contrastés. Chaque image garde sa licence ; les dérivés de photographies sous CC BY-SA restent sous CC BY-SA. Fichiers produits par `blender/cards.py` et par les scripts des scènes pour les rendus du projet.",
    '',
    '| Carte | Œuvre | Auteur | Licence |',
    '|---|---|---|---|',
    ...rows,
    '',
  ].join('\n')
}

function writeCredits(entries: CardArt[]) {
  const credits = readFileSync('CREDITS.md', 'utf8')
  const section = creditsSection(entries)
  const start = credits.indexOf(CREDITS_HEADING)
  if (start < 0) {
    writeFileSync('CREDITS.md', `${credits.trimEnd()}\n\n${section}`)
    return
  }
  const next = credits.indexOf('\n## ', start + CREDITS_HEADING.length)
  writeFileSync('CREDITS.md', `${credits.slice(0, start)}${section}${next < 0 ? '' : credits.slice(next + 1)}`)
}

async function main() {
  mkdirSync(OUTPUT, { recursive: true })
  const only = process.argv.slice(2)
  const entries: CardArt[] = []
  let total = 0
  const missing: string[] = []
  for (const card of cards) {
    const source = RENDERED[card.id] ?? (existsSync(join(META, `${card.id}.json`)) ? fromMeta(card.id) : undefined)
    if (!source) {
      missing.push(card.id)
      continue
    }
    entries.push(source.art)
    if (only.length > 0 && !only.includes(card.id)) continue
    const bytes = await produce(card.id, source)
    total += bytes
    console.log(`${card.id}: ${(bytes / 1024).toFixed(0)} KB`)
  }
  writeFileSync('src/data/cardArt.ts', dataFile(entries))
  writeCredits(entries)
  console.log(`${entries.length} illustrations, ${(total / 1e6).toFixed(2)} MB written.${missing.length > 0 ? ` Missing: ${missing.join(', ')}` : ''}`)
}

await main()
