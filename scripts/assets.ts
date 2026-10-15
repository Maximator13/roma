import { existsSync, mkdirSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'
import { Logger, NodeIO, Primitive, type Document } from '@gltf-transform/core'
import { ALL_EXTENSIONS } from '@gltf-transform/extensions'
import { dedup, instance, meshopt, prune, textureCompress, weld } from '@gltf-transform/functions'
import { Mode, TrustedCommand, commandExists, toktx } from '@gltf-transform/cli'
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer'
import sharp from 'sharp'

const scenesRoot = '.cache/scenes'
const buildRoot = '.cache/build/scenes'
const ktxFolder = 'C:\\Program Files\\KTX-Software\\bin'
const maxTextureSize: [number, number] = [1024, 1024]
const maxSceneBytes = 20_000_000

type SceneReport = { raw: number; optimised: number; triangles: number; meshes: number; materials: number; textures: number }

function sceneIds(): string[] {
  if (!existsSync(scenesRoot)) return []
  return readdirSync(scenesRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(path.join(scenesRoot, entry.name, `${entry.name}.glb`)))
    .map((entry) => entry.name)
}

function textureTransforms(ktxAvailable: boolean) {
  if (!ktxAvailable) return [textureCompress({ encoder: sharp, targetFormat: 'webp', resize: maxTextureSize })]
  const shared = { encoder: sharp, resize: maxTextureSize }
  return [toktx({ ...shared, mode: Mode.UASTC, slots: /normalTexture/i, level: 4, rdo: true, rdoLambda: 4 }), toktx({ ...shared, mode: Mode.ETC1S, quality: 255 })]
}

function primitiveTriangles(primitive: Primitive): number {
  const count = primitive.getIndices()?.getCount() ?? primitive.getAttribute('POSITION')?.getCount() ?? 0
  const mode = primitive.getMode()
  if (mode === Primitive.Mode.TRIANGLES) return Math.floor(count / 3)
  if (mode === Primitive.Mode.TRIANGLE_STRIP || mode === Primitive.Mode.TRIANGLE_FAN) return Math.max(0, count - 2)
  return 0
}

function countTriangles(document: Document): number {
  return document.getRoot().listMeshes().flatMap((mesh) => mesh.listPrimitives()).reduce((sum, primitive) => sum + primitiveTriangles(primitive), 0)
}

export async function optimiseDocument(document: Document, ktxAvailable: boolean): Promise<void> {
  await MeshoptEncoder.ready
  await document.transform(
    dedup(),
    instance(),
    prune({ keepLeaves: true }),
    weld(),
    ...textureTransforms(ktxAvailable),
    meshopt({ encoder: MeshoptEncoder, level: 'high' }),
  )
}

async function optimiseScene(io: NodeIO, id: string, ktxAvailable: boolean): Promise<SceneReport> {
  const source = path.join(scenesRoot, id, `${id}.glb`)
  const target = path.join(buildRoot, id, `${id}.glb`)
  const document = await io.read(source)
  document.setLogger(new Logger(Logger.Verbosity.WARN))
  await optimiseDocument(document, ktxAvailable)
  mkdirSync(path.dirname(target), { recursive: true })
  await io.write(target, document)
  const root = document.getRoot()
  return {
    raw: statSync(source).size,
    optimised: statSync(target).size,
    triangles: countTriangles(document),
    meshes: root.listMeshes().length,
    materials: root.listMaterials().length,
    textures: root.listTextures().length,
  }
}

async function main() {
  process.env.PATH = `${ktxFolder}${path.delimiter}${process.env.PATH ?? ''}`
  const ids = sceneIds()
  if (ids.length === 0) {
    console.log(`No scene found: expected ${scenesRoot}/<id>/<id>.glb.`)
    return
  }
  const ktxAvailable = await commandExists(TrustedCommand.KTX)
  if (!ktxAvailable) console.warn(`WARNING: ktx (KTX-Software) not found in ${ktxFolder} nor on PATH. Textures fall back to WebP: smaller downloads but no GPU compression. Install KTX-Software 4.4 or later to get KTX2.`)
  await Promise.all([MeshoptEncoder.ready, MeshoptDecoder.ready])
  const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder })
  const reports: Record<string, SceneReport> = {}
  for (const id of ids) reports[id] = await optimiseScene(io, id, ktxAvailable)
  console.table(reports)
  const oversized = ids.filter((id) => reports[id]!.optimised > maxSceneBytes)
  if (oversized.length > 0) {
    console.error(`Over the ${maxSceneBytes} bytes scene budget: ${oversized.join(', ')}`)
    process.exitCode = 1
  }
}

if (import.meta.main) await main()
