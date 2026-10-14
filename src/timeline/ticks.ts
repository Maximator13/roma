import { fromHistorical, type Year } from '../core/dates.ts'
import { xToYear, type Viewport } from './viewport.ts'

const STEPS = [1, 2, 5, 10, 25, 50, 100, 250, 500]
const MIN_TICK_SPACING = 90

export function tickStep(span: number, width: number): number {
  return STEPS.find((step) => (step / span) * width >= MIN_TICK_SPACING) ?? STEPS[STEPS.length - 1]!
}

export function ticks(view: Viewport, width: number): Year[] {
  const step = tickStep(view.span, width)
  const first = Math.floor(xToYear(0, view, width))
  const last = Math.ceil(xToYear(width, view, width))
  const years = new Set<Year>()
  for (let historical = step; 1 - historical >= first; historical += step) {
    const year = fromHistorical(historical, 'bc')
    if (year <= last) years.add(year)
  }
  for (let historical = step; historical <= last; historical += step) {
    if (historical >= first) years.add(historical)
  }
  if (first <= 1 && last >= 1 && step >= 25) years.add(1)
  return [...years].sort((a, b) => a - b)
}
