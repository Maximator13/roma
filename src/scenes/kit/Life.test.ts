import { BoxGeometry, Group, Mesh } from 'three'
import { describe, expect, it } from 'vitest'
import { standingGeometry } from './Life.tsx'

describe('standingGeometry', () => {
  it('puts the feet of a walker template at the origin whatever its transforms', () => {
    const holder = new Group()
    holder.position.set(6000, 0, 0)
    holder.scale.setScalar(0.01)
    const mesh = new Mesh(new BoxGeometry(50, 170, 30))
    mesh.position.set(10, 80, 0)
    holder.add(mesh)
    const geometry = standingGeometry(mesh)
    geometry.computeBoundingBox()
    const box = geometry.boundingBox!
    expect(box.min.y).toBeCloseTo(0)
    expect(box.max.y).toBeCloseTo(1.7)
    expect((box.min.x + box.max.x) / 2).toBeCloseTo(0)
  })
})
