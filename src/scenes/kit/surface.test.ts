import { BoxGeometry, Group, Mesh, PlaneGeometry, Vector3 } from 'three'
import { describe, expect, it } from 'vitest'
import { drape, floorOf } from './surface.ts'

function scene() {
  const root = new Group()
  const ground = new Mesh(new PlaneGeometry(40, 40, 8, 8).rotateX(-Math.PI / 2))
  const hump = new Mesh(new BoxGeometry(4, 0.3, 40))
  hump.position.set(0, 0.15, 0)
  const bench = new Mesh(new BoxGeometry(1, 0.9, 1))
  bench.position.set(10, 0.45, 0)
  const walker = new Mesh(new BoxGeometry(1, 5, 1))
  walker.name = 'walker_a'
  root.add(ground, hump, bench, walker)
  return root
}

describe('surface', () => {
  const route = [new Vector3(-15, 0, 0), new Vector3(15, 0, 0)]
  const floor = floorOf(scene(), [route], (mesh) => mesh.name.startsWith('walker_'))
  const draped = drape(route, floor)

  it('climbs a low step that a straight line would cut through', () => {
    expect(draped.find((point) => Math.abs(point.x) < 0.1)!.y).toBeCloseTo(0.3)
  })

  it('stays on the ground beside a bench too high to step on', () => {
    expect(draped.find((point) => Math.abs(point.x - 10) < 0.1)!.y).toBeCloseTo(0)
  })

  it('climbs back onto a raised sidewalk after a gap', () => {
    const root = new Group()
    const street = new Mesh(new PlaneGeometry(40, 40).rotateX(-Math.PI / 2))
    const left = new Mesh(new BoxGeometry(10, 0.45, 4))
    left.position.set(-10, 0.225, 0)
    const right = new Mesh(new BoxGeometry(10, 0.45, 4))
    right.position.set(10, 0.225, 0)
    root.add(street, left, right)
    const sidewalk = [new Vector3(-14, 0.45, 0), new Vector3(14, 0.45, 0)]
    const result = drape(sidewalk, floorOf(root, [sidewalk], () => false))
    expect(result.find((point) => Math.abs(point.x) < 0.1)!.y).toBeCloseTo(0)
    expect(result.find((point) => Math.abs(point.x - 10) < 0.1)!.y).toBeCloseTo(0.45)
  })

  it('ignores skipped meshes and keeps the route ends', () => {
    expect(draped[0]!.toArray()).toEqual([-15, 0, 0])
    expect(draped.at(-1)!.x).toBe(15)
    expect(draped.length).toBe(61)
  })
})
