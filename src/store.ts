import { create } from 'zustand'
import { routeFromLocation, routeToHash, type Route } from './core/route.ts'
import { SITE } from './site.ts'
import { initialQuality, type QualityTier } from './stage/quality.ts'
import { fullView, type Viewport } from './timeline/viewport.ts'

interface AppState {
  route: Route
  view: Viewport
  quality: QualityTier
  setRoute: (route: Route) => void
  setView: (view: Viewport) => void
  setQuality: (quality: QualityTier) => void
}

export function currentRoute(): Route {
  return routeFromLocation(location.pathname, location.hash, SITE.base)
}

export const useApp = create<AppState>()((set) => ({
  route: currentRoute(),
  view: fullView(),
  quality: initialQuality(),
  setRoute: (route) => set({ route }),
  setView: (view) => set({ view }),
  setQuality: (quality) => set({ quality }),
}))

export function navigate(route: Route) {
  const url = `${SITE.base}${routeToHash(route)}`
  if (`${location.pathname}${location.hash}` !== url) history.pushState(null, '', url)
  useApp.getState().setRoute(route)
}
