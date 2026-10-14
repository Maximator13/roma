import { FIRST_YEAR, LAST_YEAR } from '../core/dates.ts'
import type { Era } from '../data/schema.ts'
import { fullView, panBy, viewAround, zoomAt, type Viewport } from './viewport.ts'

export interface KeyAction {
  view: Viewport
  seconds: number
}

const PAN_FRACTION = 0.2
const ZOOM_STEP = 0.6

export function eraIndexAt(year: number, eras: Era[]): number {
  const index = eras.findIndex((era) => year >= era.start && year < era.end)
  if (index >= 0) return index
  return year < (eras[0]?.start ?? 0) ? 0 : eras.length - 1
}

function eraView(era: Era): Viewport {
  return viewAround(era.start, era.end, 0.04)
}

export function keyAction(key: string, view: Viewport, width: number, eras: Era[]): KeyAction | null {
  const eraIndex = eraIndexAt(view.center, eras)
  switch (key) {
    case 'ArrowLeft':
      return { view: panBy(view, width * PAN_FRACTION, width), seconds: 0.35 }
    case 'ArrowRight':
      return { view: panBy(view, -width * PAN_FRACTION, width), seconds: 0.35 }
    case '+':
    case '=':
      return { view: zoomAt(view, ZOOM_STEP, width / 2, width), seconds: 0.35 }
    case '-':
    case '_':
      return { view: zoomAt(view, 1 / ZOOM_STEP, width / 2, width), seconds: 0.35 }
    case 'Home':
      return { view: viewAround(FIRST_YEAR, FIRST_YEAR + 60), seconds: 0.9 }
    case 'End':
      return { view: viewAround(LAST_YEAR - 60, LAST_YEAR), seconds: 0.9 }
    case 'PageUp': {
      const era = eras[Math.max(0, eraIndex - 1)]
      return era ? { view: eraView(era), seconds: 0.9 } : null
    }
    case 'PageDown': {
      const era = eras[Math.min(eras.length - 1, eraIndex + 1)]
      return era ? { view: eraView(era), seconds: 0.9 } : null
    }
    case '0':
      return { view: fullView(), seconds: 0.9 }
    default:
      return null
  }
}
