import { execFileSync } from 'node:child_process'
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import {
  changedAssets,
  contentAddressedName,
  manifestFile,
  mergeManifest,
  nextReleaseNumber,
  parseManifest,
  releaseTag,
  repository,
  serializeManifest,
  sha256Of,
  type LocalAsset,
  type ManifestEntry,
} from './asset-manifest.ts'

const buildRoot = '.cache/build'
const stagingRoot = '.cache/publish'
const windowsGh = 'C:\\Program Files\\GitHub CLI\\gh.exe'
const gh = existsSync(windowsGh) ? windowsGh : 'gh'

function localAssets(): LocalAsset[] {
  if (!existsSync(buildRoot)) return []
  return readdirSync(buildRoot, { recursive: true, withFileTypes: true })
    .filter((entry) => entry.isFile())
    .map((entry) => {
      const absolute = path.join(entry.parentPath, entry.name)
      const bytes = readFileSync(absolute)
      return { path: path.relative(buildRoot, absolute).split(path.sep).join('/'), bytes: bytes.length, sha256: sha256Of(bytes) }
    })
}

function runGh(args: string[]): string {
  return execFileSync(gh, [...args, '--repo', repository], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'inherit'] })
}

function existingReleaseTags(): string[] {
  const releases = JSON.parse(runGh(['release', 'list', '--limit', '1000', '--json', 'tagName'])) as { tagName: string }[]
  return releases.map((release) => release.tagName)
}

function stageFiles(release: string, entries: ManifestEntry[]): string[] {
  const folder = path.join(stagingRoot, release)
  mkdirSync(folder, { recursive: true })
  const staged = new Map(entries.map((entry) => [entry.file, path.join(buildRoot, ...entry.path.split('/'))]))
  for (const [file, source] of staged) copyFileSync(source, path.join(folder, file))
  return [...staged.keys()].map((file) => path.join(folder, file))
}

function publish(release: string, entries: ManifestEntry[]) {
  const files = stageFiles(release, entries)
  const notes = `Content addressed heavy assets:\n${entries.map((entry) => `- ${entry.path} as ${entry.file}`).join('\n')}`
  runGh(['release', 'create', release, '--draft', '--prerelease', '--title', release, '--notes', notes])
  runGh(['release', 'upload', release, ...files])
  runGh(['release', 'edit', release, '--draft=false'])
}

function main() {
  const dryRun = process.argv.includes('--dry-run')
  const manifest = parseManifest(readFileSync(manifestFile, 'utf8'))
  const only = process.argv.filter((argument) => argument.startsWith('--only=')).map((argument) => argument.slice('--only='.length))
  const changed = changedAssets(manifest, localAssets()).filter((asset) => only.length === 0 || only.includes(asset.path))
  if (changed.length === 0) {
    console.log(`Nothing to publish: ${manifestFile} matches ${buildRoot}.`)
    return
  }
  const knownTags = [...manifest.assets.map((entry) => entry.release), ...(dryRun ? [] : existingReleaseTags())]
  const release = releaseTag(nextReleaseNumber(knownTags))
  const entries = changed.map((asset) => ({ ...asset, release, file: contentAddressedName(asset.path, asset.sha256) }))
  console.table(Object.fromEntries(entries.map((entry) => [entry.path, { bytes: entry.bytes, file: entry.file }])))
  if (dryRun) {
    console.log(`Dry run, no network call: would create the draft prerelease ${release} on ${repository} (number taken from the manifest only), upload ${entries.length} file(s), publish it and rewrite ${manifestFile}.`)
    return
  }
  publish(release, entries)
  writeFileSync(manifestFile, serializeManifest(mergeManifest(manifest, entries)))
  console.log(`Published ${release} and updated ${manifestFile}.`)
}

if (import.meta.main) main()
