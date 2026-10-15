import { describe, expect, it } from 'vitest'
import {
  changedAssets,
  contentAddressedName,
  hasSha256,
  mergeManifest,
  nextReleaseNumber,
  parseManifest,
  releaseAssetUrl,
  serializeManifest,
  sha256Of,
  staleEntries,
  type Manifest,
  type ManifestEntry,
} from './asset-manifest.ts'

const helloSha = '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
const otherSha = 'a'.repeat(64)

function entry(assetPath: string, sha256: string, release: string): ManifestEntry {
  return { path: assetPath, bytes: 5, sha256, release, file: contentAddressedName(assetPath, sha256) }
}

const manifest: Manifest = {
  version: 1,
  assets: [entry('scenes/nimes/nimes.glb', helloSha, 'assets-v1'), entry('scenes/pont-du-gard/pont-du-gard.glb', otherSha, 'assets-v2')],
}

describe('asset naming', () => {
  it('prefixes the file name with the first 12 hex characters of its hash', () => {
    expect(contentAddressedName('scenes/nimes/nimes.glb', helloSha)).toBe('2cf24dba5fb0-nimes.glb')
  })

  it('builds the release download url', () => {
    expect(releaseAssetUrl(manifest.assets[0]!)).toBe('https://github.com/Maximator13/roma/releases/download/assets-v1/2cf24dba5fb0-nimes.glb')
  })
})

describe('sha256 verification', () => {
  const hello = new TextEncoder().encode('hello')

  it('hashes bytes', () => {
    expect(sha256Of(hello)).toBe(helloSha)
  })

  it('accepts matching bytes and rejects altered ones', () => {
    expect(hasSha256(hello, helloSha)).toBe(true)
    expect(hasSha256(new TextEncoder().encode('hellO'), helloSha)).toBe(false)
  })
})

describe('next release number', () => {
  it('starts at 1', () => {
    expect(nextReleaseNumber([])).toBe(1)
  })

  it('follows the highest assets release and ignores other tags', () => {
    expect(nextReleaseNumber(['assets-v2', 'v1.0.0', 'assets-v10', 'assets-v9', 'assets-vx'])).toBe(11)
  })
})

describe('manifest diff', () => {
  it('keeps only new or changed local assets', () => {
    const local = [
      { path: 'scenes/nimes/nimes.glb', bytes: 5, sha256: helloSha },
      { path: 'scenes/pont-du-gard/pont-du-gard.glb', bytes: 7, sha256: 'b'.repeat(64) },
      { path: 'scenes/cannes/cannes.glb', bytes: 9, sha256: 'c'.repeat(64) },
    ]
    expect(changedAssets(manifest, local).map((asset) => asset.path)).toEqual(['scenes/pont-du-gard/pont-du-gard.glb', 'scenes/cannes/cannes.glb'])
  })

  it('lists entries missing or different on disk', () => {
    const onDisk = new Map([['scenes/nimes/nimes.glb', helloSha], ['scenes/pont-du-gard/pont-du-gard.glb', 'b'.repeat(64)]])
    expect(staleEntries(manifest, onDisk).map((stale) => stale.path)).toEqual(['scenes/pont-du-gard/pont-du-gard.glb'])
    expect(staleEntries(manifest, new Map())).toHaveLength(2)
  })

  it('replaces published paths, keeps the others and sorts by path', () => {
    const republished = entry('scenes/nimes/nimes.glb', otherSha, 'assets-v3')
    const added = entry('scenes/cannes/cannes.glb', helloSha, 'assets-v3')
    const merged = mergeManifest(manifest, [republished, added])
    expect(merged.assets.map((asset) => [asset.path, asset.release])).toEqual([
      ['scenes/cannes/cannes.glb', 'assets-v3'],
      ['scenes/nimes/nimes.glb', 'assets-v3'],
      ['scenes/pont-du-gard/pont-du-gard.glb', 'assets-v2'],
    ])
  })
})

describe('manifest parsing', () => {
  it('round trips a valid manifest', () => {
    expect(parseManifest(serializeManifest(manifest))).toEqual(manifest)
  })

  it('rejects paths escaping the assets folder and names that are not content addressed', () => {
    const escaping = { version: 1, assets: [{ ...manifest.assets[0], path: '../secret.glb' }] }
    const renamed = { version: 1, assets: [{ ...manifest.assets[0], file: 'nimes.glb' }] }
    expect(() => parseManifest(JSON.stringify(escaping))).toThrow('unsafe path')
    expect(() => parseManifest(JSON.stringify(renamed))).toThrow('content addressed')
  })
})
