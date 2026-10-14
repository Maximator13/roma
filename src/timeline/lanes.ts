import type { HistoricalEvent, Track } from '../data/schema.ts'
import { estimateLabelWidth, isVisibleAt, placeLabels } from './layout.ts'
import { xToYear, yearToX, type Viewport } from './viewport.ts'

export const LANE_ROWS = [3, 1, 1, 1] as const

export interface TrackSegment {
  id: string
  name: string
  from: number
  to: number
}

export interface PlacedEvent {
  event: HistoricalEvent
  x: number
  endX: number | null
  row: number | null
}

export interface LaneLayout {
  lane: number
  rows: number
  segments: TrackSegment[]
  events: PlacedEvent[]
}

function laneOf(tracks: Track[], trackId: string): number {
  return tracks.find((track) => track.id === trackId)?.lane ?? 0
}

export function layoutLanes(
  view: Viewport,
  width: number,
  tracks: Track[],
  events: HistoricalEvent[],
  selectedId: string | null,
): LaneLayout[] {
  const viewStart = xToYear(0, view, width)
  const viewEnd = xToYear(width, view, width)
  const labelReach = view.span * 0.15
  return LANE_ROWS.map((rows, lane) => {
    const segments = tracks
      .filter((track) => track.lane === lane)
      .flatMap((track) =>
        track.spans
          .filter((span) => span.end >= viewStart && span.start <= viewEnd)
          .map((span) => ({
            id: `${track.id}-${span.start}`,
            name: track.name,
            from: yearToX(span.start, view, width),
            to: yearToX(span.end, view, width),
          })),
      )
    const shown = events.filter(
      (event) =>
        laneOf(tracks, event.track) === lane &&
        (isVisibleAt(event.importance, view.span) || event.id === selectedId) &&
        (event.end ?? event.start) >= viewStart - labelReach &&
        event.start <= viewEnd,
    )
    const candidates = shown.map((event) => ({
      id: event.id,
      x: yearToX(event.start, view, width),
      width: estimateLabelWidth(event.title),
      importance: event.id === selectedId ? (1 as const) : event.importance,
      start: event.start,
    }))
    const slots = new Map(placeLabels(candidates, rows).map((slot) => [slot.id, slot.row]))
    const placed = shown.map((event) => ({
      event,
      x: yearToX(event.start, view, width),
      endX: event.end !== undefined && event.end > event.start ? yearToX(event.end, view, width) : null,
      row: slots.get(event.id) ?? null,
    }))
    return { lane, rows, segments, events: placed }
  }).filter((layout) => layout.lane === 0 || layout.segments.length > 0)
}
