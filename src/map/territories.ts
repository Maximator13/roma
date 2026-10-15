import type { TrackId } from '../data/schema.ts'

export type Ring = [number, number][]
export type Polygon = Ring[]
export type Bounds = [west: number, south: number, east: number, north: number]

export interface TerritorySlice {
  track: TrackId
  polity: string
  from: number
  to: number
  bounds: Bounds
  polygons: Polygon[]
}

export interface TerritoryData {
  attribution: string
  slices: TerritorySlice[]
}

export const MAIN_TRACKS: readonly TrackId[] = ['rome', 'occident', 'orient', 'nicee']

export function isMainTrack(track: TrackId): boolean {
  return MAIN_TRACKS.includes(track)
}

export function activeSlices(slices: TerritorySlice[], year: number): TerritorySlice[] {
  const rounded = Math.round(year)
  return slices.filter((slice) => rounded >= slice.from && rounded <= slice.to)
}

export function sliceKey(slices: TerritorySlice[]): string {
  return slices.map((slice) => `${slice.track}:${slice.from}`).join('|')
}

export function unionBounds(slices: TerritorySlice[]): Bounds | null {
  if (slices.length === 0) return null
  return slices.reduce<Bounds>(
    (union, slice) => [
      Math.min(union[0], slice.bounds[0]),
      Math.min(union[1], slice.bounds[1]),
      Math.max(union[2], slice.bounds[2]),
      Math.max(union[3], slice.bounds[3]),
    ],
    [Infinity, Infinity, -Infinity, -Infinity],
  )
}
