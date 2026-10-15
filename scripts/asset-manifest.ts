import { createHash } from 'node:crypto'
import path from 'node:path'

export const repository = 'Maximator13/roma'
export const manifestFile = 'assets.manifest.json'

export type LocalAsset = { path: string; bytes: number; sha256: string }
export type ManifestEntry = LocalAsset & { release: string; file: string }
export type Manifest = { version: 1; assets: ManifestEntry[] }

const releasePattern = /^assets-v(\d+)$/
const sha256Pattern = /^[0-9a-f]{64}$/

export function sha256Of(bytes: Uint8Array): string {
  return createHash('sha256').update(bytes).digest('hex')
}

export function hasSha256(bytes: Uint8Array, expected: string): boolean {
  return sha256Of(bytes) === expected
}

export function contentAddressedName(assetPath: string, sha256: string): string {
  return `${sha256.slice(0, 12)}-${path.posix.basename(assetPath)}`
}

export function releaseTag(releaseNumber: number): string {
  return `assets-v${releaseNumber}`
}

export function nextReleaseNumber(tags: string[]): number {
  const numbers = tags.map((tag) => releasePattern.exec(tag)?.[1]).filter((value) => value !== undefined).map(Number)
  return Math.max(0, ...numbers) + 1
}

export function changedAssets(manifest: Manifest, local: LocalAsset[]): LocalAsset[] {
  const publishedHashes = new Map(manifest.assets.map((entry) => [entry.path, entry.sha256]))
  return local.filter((asset) => publishedHashes.get(asset.path) !== asset.sha256)
}

export function staleEntries(manifest: Manifest, localHashes: Map<string, string>): ManifestEntry[] {
  return manifest.assets.filter((entry) => localHashes.get(entry.path) !== entry.sha256)
}

export function mergeManifest(manifest: Manifest, published: ManifestEntry[]): Manifest {
  const byPath = new Map(manifest.assets.map((entry) => [entry.path, entry]))
  for (const entry of published) byPath.set(entry.path, entry)
  return { version: 1, assets: [...byPath.values()].sort((a, b) => a.path.localeCompare(b.path)) }
}

export function releaseAssetUrl(entry: ManifestEntry): string {
  return `https://github.com/${repository}/releases/download/${entry.release}/${entry.file}`
}

function isSafeAssetPath(assetPath: string): boolean {
  return path.posix.normalize(assetPath) === assetPath && !assetPath.startsWith('..') && !path.posix.isAbsolute(assetPath) && !assetPath.includes('\\')
}

function entryProblem(entry: ManifestEntry): string | undefined {
  if (!isSafeAssetPath(entry.path)) return 'unsafe path'
  if (!Number.isInteger(entry.bytes) || entry.bytes < 0) return 'invalid bytes'
  if (!sha256Pattern.test(entry.sha256)) return 'invalid sha256'
  if (!releasePattern.test(entry.release)) return 'invalid release'
  if (entry.file !== contentAddressedName(entry.path, entry.sha256)) return 'file is not content addressed'
  return undefined
}

export function parseManifest(text: string): Manifest {
  const manifest = JSON.parse(text) as Manifest
  if (manifest.version !== 1 || !Array.isArray(manifest.assets)) throw new Error(`${manifestFile}: expected version 1 with an assets array`)
  for (const entry of manifest.assets) {
    const problem = entryProblem(entry)
    if (problem) throw new Error(`${manifestFile}: ${problem} in ${JSON.stringify(entry)}`)
  }
  return manifest
}

export function serializeManifest(manifest: Manifest): string {
  return `${JSON.stringify(manifest, null, 2)}\n`
}
