import { create } from 'zustand'
import { routeFromLocation, routeToHash, type Route } from './core/route.ts'
import { SITE } from './site.ts'
import { initialQuality, type QualityTier } from './stage/quality.ts'
import { fullView, type Viewport } from './timeline/viewport.ts'

interface AppState {
  route: Route
  view: Viewport
  quality: QualityTier
  scenePoint: number
  failedScene: string | null
  setRoute: (route: Route) => void
  setScenePoint: (point: number) => void
  setFailedScene: (id: string | null) => void
  setView: (view: Viewport) => void
  setQuality: (quality: QualityTier) => void
}

function isSameRoute(first: Route, second: Route): boolean {
  return routeToHash(first) === routeToHash(second)
}

export function currentRoute(): Route {
  return routeFromLocation(location.pathname, location.hash, SITE.base)
}

export const useApp = create<AppState>()((set) => ({
  route: currentRoute(),
  view: fullView(),
  quality: initialQuality(),
  scenePoint: 0,
  failedScene: null,
  setRoute: (route) =>
    set((state) => {
      if (route.name !== 'scene') return { route, failedScene: null }
      return isSameRoute(state.route, route) ? { route } : { route, scenePoint: 0 }
    }),
  setScenePoint: (scenePoint) => set({ scenePoint }),
  setFailedScene: (failedScene) => set({ failedScene }),
  setView: (view) => set({ view }),
  setQuality: (quality) => set({ quality }),
}))

export function navigate(route: Route) {
  const url = `${SITE.base}${routeToHash(route)}`
  if (`${location.pathname}${location.hash}` !== url) history.pushState(null, '', url)
  useApp.getState().setRoute(route)
}
