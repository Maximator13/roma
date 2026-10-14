import gsap from 'gsap'
import { EASE, motionDuration } from '../core/motion.ts'
import type { HistoricalEvent } from '../data/schema.ts'
import { useApp } from '../store.ts'
import { clampViewport, viewAround, type Viewport } from './viewport.ts'

gsap.ticker.lagSmoothing(0)

let current: gsap.core.Tween | null = null

export function stopViewAnimation() {
  current?.kill()
  current = null
}

export function animateView(target: Viewport, seconds = 0.8) {
  stopViewAnimation()
  const from = useApp.getState().view
  const to = clampViewport(target)
  const duration = motionDuration(seconds)
  if (duration === 0) {
    useApp.getState().setView(to)
    return
  }
  const progress = { value: 0 }
  const logFrom = Math.log(from.span)
  const logTo = Math.log(to.span)
  current = gsap.to(progress, {
    value: 1,
    duration,
    ease: EASE,
    onUpdate: () => {
      const t = progress.value
      useApp.getState().setView(
        clampViewport({ center: from.center * (1 - t) + to.center * t, span: Math.exp(logFrom * (1 - t) + logTo * t) }),
      )
    },
    onComplete: () => {
      current = null
    },
  })
}

const SPAN_BY_IMPORTANCE = { 1: 240, 2: 120, 3: 50 } as const

export function viewForEvent(event: HistoricalEvent): Viewport {
  if (event.end !== undefined && event.end > event.start) return viewAround(event.start, event.end, 0.4)
  return clampViewport({ center: event.start, span: SPAN_BY_IMPORTANCE[event.importance] })
}
