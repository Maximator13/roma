import { useEffect, type RefObject } from 'react'
import { eras } from '../data/eras.ts'
import { useApp } from '../store.ts'
import { keyAction } from './keys.ts'
import { animateView, stopViewAnimation } from './viewAnimation.ts'
import { panBy, zoomAt } from './viewport.ts'

const DRAG_THRESHOLD = 4
const WHEEL_ZOOM_RATE = 0.0015

interface TrackedPointer {
  x: number
  y: number
  startX: number
}

function distance(a: TrackedPointer, b: TrackedPointer): number {
  return Math.hypot(a.x - b.x, a.y - b.y)
}

function wheelUnit(event: WheelEvent, width: number): number {
  if (event.deltaMode === 1) return 16
  if (event.deltaMode === 2) return width
  return 1
}

export function useTimelineGestures(ref: RefObject<HTMLElement | null>, width: number) {
  useEffect(() => {
    const element = ref.current
    if (!element || width === 0) return
    const pointers = new Map<number, TrackedPointer>()
    let dragging = false
    const view = () => useApp.getState().view
    const setView = (next: ReturnType<typeof view>) => useApp.getState().setView(next)
    const localX = (clientX: number) => clientX - element.getBoundingClientRect().left

    const onWheel = (event: WheelEvent) => {
      event.preventDefault()
      stopViewAnimation()
      const unit = wheelUnit(event, width)
      const deltaX = event.deltaX * unit
      const deltaY = event.deltaY * unit
      if (Math.abs(deltaX) > Math.abs(deltaY)) setView(panBy(view(), -deltaX, width))
      else if (event.shiftKey) setView(panBy(view(), -deltaY, width))
      else setView(zoomAt(view(), Math.exp(deltaY * WHEEL_ZOOM_RATE), localX(event.clientX), width))
    }

    const onPointerDown = (event: PointerEvent) => {
      if (event.pointerType === 'mouse' && event.button !== 0) return
      if (pointers.size === 0) dragging = false
      pointers.set(event.pointerId, { x: event.clientX, y: event.clientY, startX: event.clientX })
      stopViewAnimation()
    }

    const onPointerMove = (event: PointerEvent) => {
      const previous = pointers.get(event.pointerId)
      if (!previous) return
      const next = { ...previous, x: event.clientX, y: event.clientY }
      const other = [...pointers.entries()].find(([id]) => id !== event.pointerId)?.[1]
      if (other) {
        dragging = true
        const factor = distance(previous, other) / Math.max(1, distance(next, other))
        setView(zoomAt(view(), factor, localX((next.x + other.x) / 2), width))
      } else if (dragging || Math.abs(next.x - next.startX) >= DRAG_THRESHOLD) {
        if (!dragging) element.setPointerCapture(event.pointerId)
        dragging = true
        setView(panBy(view(), next.x - previous.x, width))
      } else {
        return
      }
      pointers.set(event.pointerId, next)
    }

    const onPointerEnd = (event: PointerEvent) => {
      pointers.delete(event.pointerId)
    }

    const onClickCapture = (event: MouseEvent) => {
      if (!dragging) return
      event.preventDefault()
      event.stopPropagation()
      dragging = false
    }

    element.addEventListener('wheel', onWheel, { passive: false })
    element.addEventListener('pointerdown', onPointerDown)
    element.addEventListener('pointermove', onPointerMove)
    element.addEventListener('pointerup', onPointerEnd)
    element.addEventListener('pointercancel', onPointerEnd)
    element.addEventListener('click', onClickCapture, true)
    return () => {
      element.removeEventListener('wheel', onWheel)
      element.removeEventListener('pointerdown', onPointerDown)
      element.removeEventListener('pointermove', onPointerMove)
      element.removeEventListener('pointerup', onPointerEnd)
      element.removeEventListener('pointercancel', onPointerEnd)
      element.removeEventListener('click', onClickCapture, true)
    }
  }, [ref, width])
}

export function useTimelineKeys(width: number) {
  useEffect(() => {
    if (width === 0) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) return
      const target = event.target instanceof HTMLElement ? event.target : null
      if (target?.closest('input, textarea, select, [contenteditable="true"], [data-native-keys]')) return
      const action = keyAction(event.key, useApp.getState().view, width, eras)
      if (!action) return
      event.preventDefault()
      animateView(action.view, action.seconds)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [width])
}
