import { BoxGeometry, BufferAttribute, Group, Mesh } from 'three'
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

  it('keeps the size of a quantized template far from the origin', () => {
    const geometry = new BoxGeometry(2, 2, 2)
    const source = geometry.getAttribute('position')
    const quantized = new Int16Array(source.count * 3)
    for (let index = 0; index < quantized.length; index += 1) quantized[index] = Math.round((source.array[index] as number) * 32767)
    geometry.setAttribute('position', new BufferAttribute(quantized, 3, true))
    const mesh = new Mesh(geometry)
    mesh.position.set(0, -1000, 0)
    mesh.scale.setScalar(24)
    const standing = standingGeometry(mesh)
    standing.computeBoundingBox()
    expect(standing.boundingBox!.min.y).toBeCloseTo(0)
    expect(standing.boundingBox!.max.y).toBeCloseTo(48, 1)
  })
})
