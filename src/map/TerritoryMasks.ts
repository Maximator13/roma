import { CanvasTexture, LinearFilter, type Texture } from 'three'
import { MAP_BOUNDS } from './geo.ts'
import { isMainTrack, type TerritorySlice } from './territories.ts'

const WIDTH = 2048
const HEIGHT = 1152
const SOFT_WIDTH = 256
const SOFT_HEIGHT = 144
const EDGE_BLUR = 4
const SPREAD_BLUR = 22

interface MaskLayer {
  sharp: HTMLCanvasElement
  soft: HTMLCanvasElement
  sharpTexture: CanvasTexture
  softTexture: CanvasTexture
}

function createCanvas(width = WIDTH, height = HEIGHT): HTMLCanvasElement {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  return canvas
}

function createTexture(canvas: HTMLCanvasElement): CanvasTexture {
  const texture = new CanvasTexture(canvas)
  texture.minFilter = LinearFilter
  texture.magFilter = LinearFilter
  texture.generateMipmaps = false
  return texture
}

function createLayer(): MaskLayer {
  const sharp = createCanvas()
  const soft = createCanvas(SOFT_WIDTH, SOFT_HEIGHT)
  return { sharp, soft, sharpTexture: createTexture(sharp), softTexture: createTexture(soft) }
}

function context(canvas: HTMLCanvasElement): CanvasRenderingContext2D {
  const result = canvas.getContext('2d')
  if (!result) throw new Error('Canvas 2D is not available')
  return result
}

function toPixel(lon: number, lat: number): [number, number] {
  return [
    ((lon - MAP_BOUNDS.west) / (MAP_BOUNDS.east - MAP_BOUNDS.west)) * WIDTH,
    ((MAP_BOUNDS.north - lat) / (MAP_BOUNDS.north - MAP_BOUNDS.south)) * HEIGHT,
  ]
}

function tracePolygons(ctx: CanvasRenderingContext2D, slice: TerritorySlice) {
  ctx.beginPath()
  for (const polygon of slice.polygons) {
    for (const ring of polygon) {
      ring.forEach(([lon, lat], index) => {
        const [x, y] = toPixel(lon, lat)
        if (index === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      })
      ctx.closePath()
    }
  }
}

function drawSlices(layer: MaskLayer, slices: TerritorySlice[]) {
  const scratch = createCanvas()
  const scratchContext = context(scratch)
  scratchContext.globalCompositeOperation = 'lighter'
  for (const slice of slices) {
    scratchContext.fillStyle = isMainTrack(slice.track) ? 'rgb(255 0 0)' : 'rgb(0 0 255)'
    tracePolygons(scratchContext, slice)
    scratchContext.fill('evenodd')
  }
  const sharp = context(layer.sharp)
  sharp.clearRect(0, 0, WIDTH, HEIGHT)
  sharp.filter = `blur(${EDGE_BLUR}px)`
  sharp.drawImage(scratch, 0, 0)
  sharp.filter = 'none'
  const soft = context(layer.soft)
  soft.clearRect(0, 0, SOFT_WIDTH, SOFT_HEIGHT)
  soft.filter = `blur(${SPREAD_BLUR}px)`
  soft.drawImage(scratch, 0, 0, SOFT_WIDTH, SOFT_HEIGHT)
  soft.drawImage(scratch, 0, 0, SOFT_WIDTH, SOFT_HEIGHT)
  soft.filter = 'none'
  layer.sharpTexture.needsUpdate = true
  layer.softTexture.needsUpdate = true
}

function copyLayer(source: MaskLayer, target: MaskLayer) {
  for (const key of ['sharp', 'soft'] as const) {
    const ctx = context(target[key])
    ctx.clearRect(0, 0, target[key].width, target[key].height)
    ctx.drawImage(source[key], 0, 0)
  }
  target.sharpTexture.needsUpdate = true
  target.softTexture.needsUpdate = true
}

export class TerritoryMasks {
  private readonly from = createLayer()
  private readonly to = createLayer()
  private currentKey: string | null = null

  get textures(): Record<'fromSharp' | 'fromSoft' | 'toSharp' | 'toSoft', Texture> {
    return {
      fromSharp: this.from.sharpTexture,
      fromSoft: this.from.softTexture,
      toSharp: this.to.sharpTexture,
      toSoft: this.to.softTexture,
    }
  }

  show(slices: TerritorySlice[], key: string): boolean {
    if (key === this.currentKey) return false
    const first = this.currentKey === null
    this.currentKey = key
    if (!first) copyLayer(this.to, this.from)
    drawSlices(this.to, slices)
    if (first) copyLayer(this.to, this.from)
    return !first
  }

  dispose() {
    for (const layer of [this.from, this.to]) {
      layer.sharpTexture.dispose()
      layer.softTexture.dispose()
    }
  }
}
