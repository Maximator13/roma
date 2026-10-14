import { describe, expect, it } from 'vitest'
import { FIRST_YEAR, LAST_YEAR } from '../core/dates.ts'
import { MAX_SPAN, MIN_SPAN, clampViewport, fullView, panBy, viewAround, xToYear, yearToX, zoomAt } from './viewport.ts'

const width = 1000

describe('viewport', () => {
  it('shows the whole domain in the full view', () => {
    const view = fullView()
    expect(xToYear(0, view, width)).toBeLessThan(FIRST_YEAR)
    expect(xToYear(width, view, width)).toBeGreaterThan(LAST_YEAR)
  })

  it('maps years and pixels both ways', () => {
    const view = { center: 0, span: 100 }
    expect(yearToX(0, view, width)).toBe(500)
    expect(yearToX(50, view, width)).toBe(1000)
    expect(xToYear(250, view, width)).toBe(-25)
  })

  it('keeps the year under the cursor fixed while zooming', () => {
    const view = { center: 0, span: 400 }
    const zoomed = zoomAt(view, 0.5, 800, width)
    expect(zoomed.span).toBe(200)
    expect(xToYear(800, zoomed, width)).toBeCloseTo(xToYear(800, view, width))
  })

  it('limits zoom between a decade and the whole domain', () => {
    expect(zoomAt({ center: 0, span: 20 }, 0.1, 500, width).span).toBe(MIN_SPAN)
    expect(zoomAt({ center: 0, span: 2000 }, 10, 500, width).span).toBe(MAX_SPAN)
  })

  it('stops panning past the ends of the domain', () => {
    const view = panBy({ center: FIRST_YEAR, span: 100 }, 5000, width)
    expect(xToYear(0, view, width)).toBeGreaterThan(FIRST_YEAR - 100)
    expect(clampViewport({ center: 99999, span: 100 }).center).toBeLessThan(LAST_YEAR + 100)
  })

  it('frames a period with some padding', () => {
    const view = viewAround(-263, -240)
    expect(view.center).toBe(-251.5)
    expect(view.span).toBeGreaterThan(23)
  })
})
