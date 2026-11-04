import { Box3, InstancedMesh, Mesh, Vector3, type Object3D } from 'three'

const CELL = 2
const STEP = 0.5
const CLIMB = 0.35
const DROP = 0.6
const FLAT = 0.5
const SPAN = 65536
const BLOCK = 8

type Floor = (x: number, z: number, from: number) => number | undefined

function cellOf(value: number): number {
  return Math.floor(value / CELL) + SPAN / 2
}

function along(points: Vector3[], visit: (x: number, y: number, z: number) => void) {
  for (let index = 1; index < points.length; index += 1) {
    const start = points[index - 1]!
    const end = points[index]!
    const steps = Math.max(1, Math.ceil(Math.hypot(end.x - start.x, end.z - start.z) / STEP))
    for (let step = index === 1 ? 0 : 1; step <= steps; step += 1) {
      const t = step / steps
      visit(start.x + (end.x - start.x) * t, start.y + (end.y - start.y) * t, start.z + (end.z - start.z) * t)
    }
  }
}

export function floorOf(root: Object3D, routes: Vector3[][], skip: (mesh: Mesh) => boolean): Floor {
  const wanted = new Set<number>()
  const blocks = new Set<number>()
  const corridor = new Box3()
  for (const points of routes) {
    along(points, (x, y, z) => {
      wanted.add(cellOf(x) * SPAN + cellOf(z))
      blocks.add(Math.floor(cellOf(x) / BLOCK) * SPAN + Math.floor(cellOf(z) / BLOCK))
      corridor.expandByPoint(new Vector3(x, y, z))
    })
  }
  corridor.expandByScalar(CELL)
  const cells = new Map<number, number[]>()
  const triangles: number[] = []
  const box = new Box3()
  root.updateMatrixWorld(true)
  const add = (key: number, slot: number) => {
    const list = cells.get(key)
    if (list) list.push(slot)
    else cells.set(key, [slot])
  }
  root.traverse((child) => {
    if (!(child instanceof Mesh) || child instanceof InstancedMesh || skip(child)) return
    const geometry = child.geometry
    const position = geometry.getAttribute('position')
    if (!position) return
    if (!geometry.boundingBox) geometry.computeBoundingBox()
    box.copy(geometry.boundingBox!).applyMatrix4(child.matrixWorld)
    box.min.y = corridor.min.y
    box.max.y = corridor.max.y
    if (!box.intersectsBox(corridor)) return
    const index = geometry.getIndex()
    const world = new Float32Array(position.count * 3)
    const vertex = new Vector3()
    for (let at = 0; at < position.count; at += 1) {
      vertex.fromBufferAttribute(position, at).applyMatrix4(child.matrixWorld)
      world[at * 3] = vertex.x
      world[at * 3 + 1] = vertex.y
      world[at * 3 + 2] = vertex.z
    }
    const count = index ? index.count : position.count
    for (let offset = 0; offset + 2 < count; offset += 3) {
      const ia = (index ? index.getX(offset) : offset) * 3
      const ib = (index ? index.getX(offset + 1) : offset + 1) * 3
      const ic = (index ? index.getX(offset + 2) : offset + 2) * 3
      const ax = world[ia]!, ay = world[ia + 1]!, az = world[ia + 2]!
      const bx = world[ib]!, by = world[ib + 1]!, bz = world[ib + 2]!
      const cx = world[ic]!, cy = world[ic + 1]!, cz = world[ic + 2]!
      const minX = Math.min(ax, bx, cx)
      const maxX = Math.max(ax, bx, cx)
      const minZ = Math.min(az, bz, cz)
      const maxZ = Math.max(az, bz, cz)
      if (maxX < corridor.min.x || minX > corridor.max.x || maxZ < corridor.min.z || minZ > corridor.max.z) continue
      const ux = bx - ax, uy = by - ay, uz = bz - az
      const vx = cx - ax, vy = cy - ay, vz = cz - az
      const nx = uy * vz - uz * vy
      const ny = uz * vx - ux * vz
      const nz = ux * vy - uy * vx
      const length = Math.hypot(nx, ny, nz)
      if (length === 0 || Math.abs(ny) / length < FLAT) continue
      const x0 = cellOf(Math.max(minX, corridor.min.x))
      const x1 = cellOf(Math.min(maxX, corridor.max.x))
      const z0 = cellOf(Math.max(minZ, corridor.min.z))
      const z1 = cellOf(Math.min(maxZ, corridor.max.z))
      const bx0 = Math.floor(x0 / BLOCK)
      const bx1 = Math.floor(x1 / BLOCK)
      const bz0 = Math.floor(z0 / BLOCK)
      const bz1 = Math.floor(z1 / BLOCK)
      const slot = triangles.length
      let used = false
      for (let blockX = bx0; blockX <= bx1; blockX += 1) {
        for (let blockZ = bz0; blockZ <= bz1; blockZ += 1) {
          if (!blocks.has(blockX * SPAN + blockZ)) continue
          for (let x = Math.max(x0, blockX * BLOCK); x <= Math.min(x1, blockX * BLOCK + BLOCK - 1); x += 1) {
            for (let z = Math.max(z0, blockZ * BLOCK); z <= Math.min(z1, blockZ * BLOCK + BLOCK - 1); z += 1) {
              const key = x * SPAN + z
              if (!wanted.has(key)) continue
              add(key, slot)
              used = true
            }
          }
        }
      }
      if (used) triangles.push(ax, ay, az, bx, by, bz, cx, cy, cz)
    }
  })
  return (x, z, from) => {
    let best: number | undefined
    for (const t of cells.get(cellOf(x) * SPAN + cellOf(z)) ?? []) {
      const ax = triangles[t]!, ay = triangles[t + 1]!, az = triangles[t + 2]!
      const bx = triangles[t + 3]!, by = triangles[t + 4]!, bz = triangles[t + 5]!
      const cx = triangles[t + 6]!, cy = triangles[t + 7]!, cz = triangles[t + 8]!
      const det = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
      if (det === 0) continue
      const u = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / det
      const v = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / det
      if (u < 0 || v < 0 || u + v > 1) continue
      const height = u * ay + v * by + (1 - u - v) * cy
      if (height > from + CLIMB || height < from - DROP) continue
      if (best === undefined || height > best) best = height
    }
    return best
  }
}

export function drape(points: Vector3[], floor: Floor): Vector3[] {
  const result: Vector3[] = []
  let previous: number | undefined
  along(points, (x, y, z) => {
    const height = floor(x, z, Math.max(previous ?? y, y))
    previous = height ?? y
    result.push(new Vector3(x, previous, z))
  })
  return result
}
