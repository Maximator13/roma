import type { Texture } from 'three'
import { MAP_BOUNDS, decodeElevation } from './geo.ts'

export type HeightSampler = (lon: number, lat: number) => number

export function createHeightSampler(relief: Texture, landScale: number): HeightSampler {
  const image = relief.image as CanvasImageSource & { width: number; height: number }
  const canvas = document.createElement('canvas')
  canvas.width = image.width
  canvas.height = image.height
  const context = canvas.getContext('2d', { willReadFrequently: true })
  if (!context) return () => 0
  context.drawImage(image, 0, 0)
  const { data, width, height } = context.getImageData(0, 0, canvas.width, canvas.height)
  return (lon, lat) => {
    const column = Math.round(((lon - MAP_BOUNDS.west) / (MAP_BOUNDS.east - MAP_BOUNDS.west)) * (width - 1))
    const row = Math.round(((MAP_BOUNDS.north - lat) / (MAP_BOUNDS.north - MAP_BOUNDS.south)) * (height - 1))
    if (column < 0 || row < 0 || column >= width || row >= height) return 0
    return Math.max(0, decodeElevation(data[(row * width + column) * 4] ?? 128)) * landScale
  }
}
