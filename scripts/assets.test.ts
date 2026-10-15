import { Document, Logger } from '@gltf-transform/core'
import { describe, expect, it } from 'vitest'
import { optimiseDocument } from './assets.ts'

function sceneWithMarker(): Document {
  const document = new Document().setLogger(new Logger(Logger.Verbosity.SILENT))
  const buffer = document.createBuffer()
  const positions = document.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0])).setBuffer(buffer)
  const primitive = document.createPrimitive().setAttribute('POSITION', positions)
  const scene = document.createScene()
  scene.addChild(document.createNode('ground').setMesh(document.createMesh().addPrimitive(primitive)))
  scene.addChild(document.createNode('poi_forum').setTranslation([1, 2, 3]))
  return document
}

describe('optimiseDocument', () => {
  it('keeps the empty marker nodes that drive the camera rail', async () => {
    const document = sceneWithMarker()
    await optimiseDocument(document, false)
    const names = document.getRoot().listNodes().map((node) => node.getName())
    expect(names).toContain('poi_forum')
    expect(document.getRoot().listExtensionsUsed().map((extension) => extension.extensionName)).toContain('EXT_meshopt_compression')
  })
})
