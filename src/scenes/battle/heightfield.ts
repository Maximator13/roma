export interface HeightField {
  x0: number
  z0: number
  cell: number
  columns: number
  rows: number
  heights: Float32Array
}

function fillHoles(field: HeightField) {
  const { columns, rows, heights } = field
  for (let pass = 0; pass < 4; pass += 1) {
    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        const index = row * columns + column
        if (!Number.isNaN(heights[index]!)) continue
        let sum = 0
        let count = 0
        for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]] as const) {
          const r = row + dr
          const c = column + dc
          if (r < 0 || c < 0 || r >= rows || c >= columns) continue
          const value = heights[r * columns + c]!
          if (Number.isNaN(value)) continue
          sum += value
          count += 1
        }
        if (count > 0) heights[index] = sum / count
      }
    }
  }
  for (let index = 0; index < heights.length; index += 1) if (Number.isNaN(heights[index]!)) heights[index] = 0
}

export function rasterize(positions: ArrayLike<number>, index: ArrayLike<number> | null, cell: number): HeightField {
  let minX = Infinity
  let minZ = Infinity
  let maxX = -Infinity
  let maxZ = -Infinity
  for (let i = 0; i < positions.length; i += 3) {
    minX = Math.min(minX, positions[i]!)
    maxX = Math.max(maxX, positions[i]!)
    minZ = Math.min(minZ, positions[i + 2]!)
    maxZ = Math.max(maxZ, positions[i + 2]!)
  }
  const columns = Math.floor((maxX - minX) / cell) + 1
  const rows = Math.floor((maxZ - minZ) / cell) + 1
  const field: HeightField = { x0: minX, z0: minZ, cell, columns, rows, heights: new Float32Array(columns * rows).fill(Number.NaN) }
  const count = index ? index.length : positions.length / 3
  const vertex = (k: number) => (index ? index[k]! : k) * 3
  for (let k = 0; k + 2 < count; k += 3) {
    const a = vertex(k)
    const b = vertex(k + 1)
    const c = vertex(k + 2)
    const ax = positions[a]!
    const az = positions[a + 2]!
    const bx = positions[b]!
    const bz = positions[b + 2]!
    const cx = positions[c]!
    const cz = positions[c + 2]!
    const area = (bx - ax) * (cz - az) - (cx - ax) * (bz - az)
    if (Math.abs(area) < 1e-9) continue
    const c0 = Math.max(0, Math.ceil((Math.min(ax, bx, cx) - minX) / cell))
    const c1 = Math.min(columns - 1, Math.floor((Math.max(ax, bx, cx) - minX) / cell))
    const r0 = Math.max(0, Math.ceil((Math.min(az, bz, cz) - minZ) / cell))
    const r1 = Math.min(rows - 1, Math.floor((Math.max(az, bz, cz) - minZ) / cell))
    for (let row = r0; row <= r1; row += 1) {
      const z = minZ + row * cell
      for (let column = c0; column <= c1; column += 1) {
        const x = minX + column * cell
        const wa = ((bx - x) * (cz - z) - (cx - x) * (bz - z)) / area
        const wb = ((cx - x) * (az - z) - (ax - x) * (cz - z)) / area
        const wc = 1 - wa - wb
        if (wa < -1e-6 || wb < -1e-6 || wc < -1e-6) continue
        field.heights[row * columns + column] = wa * positions[a + 1]! + wb * positions[b + 1]! + wc * positions[c + 1]!
      }
    }
  }
  fillHoles(field)
  return field
}

export function heightAt(field: HeightField, x: number, z: number): number {
  const column = Math.min(field.columns - 1.001, Math.max(0, (x - field.x0) / field.cell))
  const row = Math.min(field.rows - 1.001, Math.max(0, (z - field.z0) / field.cell))
  const c0 = Math.floor(column)
  const r0 = Math.floor(row)
  const fx = column - c0
  const fz = row - r0
  const h = field.heights
  const width = field.columns
  const top = h[r0 * width + c0]! * (1 - fx) + h[r0 * width + c0 + 1]! * fx
  const bottom = h[(r0 + 1) * width + c0]! * (1 - fx) + h[(r0 + 1) * width + c0 + 1]! * fx
  return top * (1 - fz) + bottom * fz
}
