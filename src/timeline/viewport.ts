import { FIRST_YEAR, LAST_YEAR, type Year } from '../core/dates.ts'

export interface Viewport {
  center: number
  span: number
}

export const DOMAIN_LENGTH = LAST_YEAR - FIRST_YEAR
export const MIN_SPAN = 10
export const MAX_SPAN = DOMAIN_LENGTH * 1.08
const EDGE_MARGIN = DOMAIN_LENGTH * 0.04

export function clampViewport(view: Viewport): Viewport {
  const span = Math.min(MAX_SPAN, Math.max(MIN_SPAN, view.span))
  const lowest = FIRST_YEAR - EDGE_MARGIN + span / 2
  const highest = LAST_YEAR + EDGE_MARGIN - span / 2
  const center = lowest > highest ? (FIRST_YEAR + LAST_YEAR) / 2 : Math.min(highest, Math.max(lowest, view.center))
  return { center, span }
}

export function fullView(): Viewport {
  return clampViewport({ center: (FIRST_YEAR + LAST_YEAR) / 2, span: MAX_SPAN })
}

export function yearToX(year: number, view: Viewport, width: number): number {
  return ((year - view.center) / view.span) * width + width / 2
}

export function xToYear(x: number, view: Viewport, width: number): number {
  return view.center + ((x - width / 2) / width) * view.span
}

export function zoomAt(view: Viewport, factor: number, anchorX: number, width: number): Viewport {
  const anchorYear = xToYear(anchorX, view, width)
  const span = Math.min(MAX_SPAN, Math.max(MIN_SPAN, view.span * factor))
  return clampViewport({ center: anchorYear - ((anchorX - width / 2) / width) * span, span })
}

export function panBy(view: Viewport, deltaX: number, width: number): Viewport {
  return clampViewport({ center: view.center - (deltaX / width) * view.span, span: view.span })
}

export function viewAround(start: Year, end: Year, padding = 0.15): Viewport {
  const length = Math.max(end - start, 0)
  return clampViewport({ center: (start + end) / 2, span: Math.max(MIN_SPAN * 4, length * (1 + 2 * padding)) })
}
