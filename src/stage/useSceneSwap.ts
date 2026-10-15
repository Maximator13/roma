import gsap from 'gsap'
import { useEffect, useState, type RefObject } from 'react'
import { EASE, motionDuration } from '../core/motion.ts'
import { findScene, isPlayable, preloadScene } from '../scenes/registry.ts'
import { useApp } from '../store.ts'

const DIVE_SECONDS = 1.3
const VEIL_IN_SECONDS = 0.45
const VEIL_OUT_SECONDS = 0.9

function wait(seconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, seconds * 1000))
}

function fadeVeil(element: HTMLElement | null, opacity: number, seconds: number): Promise<void> {
  if (!element) return Promise.resolve()
  return new Promise((resolve) => {
    gsap.to(element, { opacity, duration: seconds, ease: EASE, overwrite: true, onComplete: resolve, onInterrupt: resolve })
  })
}

export function wantedScene(state: { route: { name: string; id?: string }; failedScene: string | null }): string | null {
  if (state.route.name !== 'scene' || !state.route.id || state.route.id === state.failedScene) return null
  return isPlayable(findScene(state.route.id)) ? state.route.id : null
}

export function useSceneSwap(veil: RefObject<HTMLDivElement | null>) {
  const wanted = useApp(wantedScene)
  const [shown, setShown] = useState<string | null>(null)
  const [ready, setReady] = useState<string | null>(null)

  useEffect(() => {
    if (wanted === shown) return
    let cancelled = false
    const swap = async () => {
      if (wanted) await Promise.all([preloadScene(wanted), wait(motionDuration(DIVE_SECONDS))])
      if (cancelled) return
      await fadeVeil(veil.current, 1, VEIL_IN_SECONDS)
      if (!cancelled) setShown(wanted)
    }
    void swap()
    return () => {
      cancelled = true
    }
  }, [wanted, shown, veil])

  useEffect(() => {
    if (wanted !== shown) return
    if (shown === null || ready === shown) void fadeVeil(veil.current, 0, VEIL_OUT_SECONDS)
  }, [wanted, shown, ready, veil])


  return { shown, loading: shown !== null && ready !== shown, onReady: setReady }
}
