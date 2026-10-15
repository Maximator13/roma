import { Object3D } from 'three'
import { describe, expect, it } from 'vitest'
import { markerStop } from './ModelScene.tsx'

function marker(x: number, y: number, z: number): Object3D {
  const node = new Object3D()
  node.position.set(x, y, z)
  node.updateMatrixWorld()
  return node
}

describe('markerStop', () => {
  it('aims the camera from the marker to its target marker', () => {
    const markers = new Map([
      ['forum', marker(0, 2, 50)],
      ['forum_target', marker(0, 8, 0)],
    ])
    const stop = markerStop(markers, 'forum')
    expect(stop?.position.toArray()).toEqual([0, 2, 50])
    expect(stop?.target.toArray()).toEqual([0, 8, 0])
  })

  it('returns nothing for a missing marker', () => {
    expect(markerStop(new Map(), 'forum')).toBeNull()
  })
})
