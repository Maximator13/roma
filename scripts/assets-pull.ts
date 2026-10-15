import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { hasSha256, manifestFile, parseManifest, releaseAssetUrl, sha256Of, staleEntries, type ManifestEntry } from './asset-manifest.ts'

const publicRoot = 'public/assets'

function localPath(entry: ManifestEntry): string {
  return path.join(publicRoot, ...entry.path.split('/'))
}

function localHashes(entries: ManifestEntry[]): Map<string, string> {
  const present = entries.filter((entry) => existsSync(localPath(entry)))
  return new Map(present.map((entry) => [entry.path, sha256Of(readFileSync(localPath(entry)))]))
}

async function download(entry: ManifestEntry) {
  const url = releaseAssetUrl(entry)
  const response = await fetch(url, { redirect: 'follow' })
  if (!response.ok) throw new Error(`${entry.path}: HTTP ${response.status} for ${url}`)
  const bytes = new Uint8Array(await response.arrayBuffer())
  if (!hasSha256(bytes, entry.sha256)) throw new Error(`${entry.path}: sha256 mismatch for ${url} (got ${sha256Of(bytes)} on ${bytes.length} bytes, expected ${entry.sha256} on ${entry.bytes} bytes)`)
  const target = localPath(entry)
  const temporary = `${target}.${process.pid}.download`
  mkdirSync(path.dirname(target), { recursive: true })
  writeFileSync(temporary, bytes)
  renameSync(temporary, target)
  console.log(`Downloaded ${entry.path} (${bytes.length} bytes) from ${entry.release}.`)
}

async function main() {
  const manifest = parseManifest(readFileSync(manifestFile, 'utf8'))
  const stale = staleEntries(manifest, localHashes(manifest.assets))
  for (const entry of stale) await download(entry)
  console.log(`${manifest.assets.length - stale.length} asset(s) already up to date, ${stale.length} downloaded into ${publicRoot}.`)
}

if (import.meta.main) {
  await main().catch((error: unknown) => {
    console.error(`assets:pull failed: ${error instanceof Error ? error.message : String(error)}`)
    process.exitCode = 1
  })
}
