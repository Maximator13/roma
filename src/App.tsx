import { lazy, Suspense, useEffect } from 'react'
import { formatDate } from './core/dates.ts'
import { frenchSpacing } from './core/typography.ts'
import { internalRoute, routeToHash, type Route } from './core/route.ts'
import { eras } from './data/eras.ts'
import { events } from './data/events.ts'
import { pages } from './data/pages.ts'
import { PAGE_LINKS, UI } from './data/ui.ts'
import { SITE } from './site.ts'
import { gradingAt, readableAccent, rgbToCss } from './stage/grading.ts'
import { currentRoute, navigate, useApp } from './store.ts'
import { eraIndexAt } from './timeline/keys.ts'
import { isVisibleAt } from './timeline/layout.ts'
import { Timeline } from './timeline/Timeline.tsx'
import { animateView, viewForEvent } from './timeline/viewAnimation.ts'
import { viewAround, xToYear } from './timeline/viewport.ts'
import { ConsentBanner } from './ui/ConsentBanner.tsx'
import { findScene, isPlayable } from './scenes/registry.ts'
import { EraCaption, EventPanel, NotFoundPanel, PagePanel, ScenePanel, SceneShortcuts } from './ui/panels.tsx'

const Stage = lazy(() => import('./stage/Stage.tsx'))

function documentTitle(route: Route): string {
  if (route.name === 'event') {
    const event = events.find((candidate) => candidate.id === route.id)
    if (event) return `${event.title} (${formatDate(event)}) | ${SITE.name}`
  }
  if (route.name === 'page') {
    const page = pages.find((candidate) => candidate.id === route.id)
    if (page) return `${page.title} | ${SITE.name}`
  }
  if (route.name === 'scene') {
    const scene = findScene(route.id)
    if (scene) return `${scene.title} | ${SITE.name}`
  }
  if (route.name === 'not-found') return `${UI.notFoundTitle} | ${SITE.name}`
  return SITE.title
}

function useHashRoute() {
  const route = useApp((state) => state.route)
  useEffect(() => {
    const sync = () => useApp.getState().setRoute(currentRoute())
    const onClick = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey) return
      const link = event.target instanceof Element ? event.target.closest('a') : null
      const target = link ? internalRoute(link.getAttribute('href') ?? '', SITE.base) : null
      if (!target) return
      event.preventDefault()
      navigate(target)
    }
    window.addEventListener('hashchange', sync)
    window.addEventListener('popstate', sync)
    document.addEventListener('click', onClick)
    return () => {
      window.removeEventListener('hashchange', sync)
      window.removeEventListener('popstate', sync)
      document.removeEventListener('click', onClick)
    }
  }, [])
  useEffect(() => {
    document.title = documentTitle(route)
  }, [route])
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && useApp.getState().route.name !== 'home') navigate({ name: 'home' })
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])
}

function useEraAccent() {
  useEffect(() => {
    const root = document.documentElement
    const apply = (center: number) => {
      const { accent } = gradingAt(center, eras)
      root.style.setProperty('--accent', rgbToCss(accent))
      root.style.setProperty('--accent-ink', rgbToCss(readableAccent(accent)))
    }
    apply(useApp.getState().view.center)
    return useApp.subscribe((state, previous) => {
      if (state.view.center !== previous.view.center) apply(state.view.center)
    })
  }, [])
}

function useFocusOnSelectedEvent() {
  const route = useApp((state) => state.route)
  useEffect(() => {
    if (route.name !== 'event') return
    const event = events.find((candidate) => candidate.id === route.id)
    if (!event) return
    const { view } = useApp.getState()
    const width = window.innerWidth
    const inView = event.start >= xToYear(width * 0.1, view, width) && event.start <= xToYear(width * 0.6, view, width)
    if (!inView || !isVisibleAt(event.importance, view.span)) animateView(viewForEvent(event), 1)
  }, [route])
}

function ActivePanel({ route }: { route: Route }) {
  if (route.name === 'event') {
    const event = events.find((candidate) => candidate.id === route.id)
    return event ? <EventPanel event={event} /> : <NotFoundPanel />
  }
  if (route.name === 'page') {
    const page = pages.find((candidate) => candidate.id === route.id)
    return page ? <PagePanel page={page} /> : <NotFoundPanel />
  }
  if (route.name === 'scene') {
    const scene = findScene(route.id)
    return scene ? <ScenePanel scene={scene} /> : <NotFoundPanel />
  }
  if (route.name === 'not-found') return <NotFoundPanel />
  return null
}

function useSceneKeys() {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const { route, scenePoint, setScenePoint } = useApp.getState()
      if (route.name !== 'scene' || event.altKey || event.ctrlKey || event.metaKey) return
      const target = event.target instanceof Element ? event.target : null
      if (target?.closest('input, textarea, select')) return
      const step = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0
      if (step === 0) return
      event.preventDefault()
      const last = findScene(route.id)?.points?.length ?? 0
      setScenePoint(Math.max(0, Math.min(last, scenePoint + step)))
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])
}

function Intro() {
  const first = eras[0]
  if (!first) return null
  return (
    <div className="intro">
      <p className="intro__tagline">{frenchSpacing(UI.tagline)}</p>
      <button type="button" className="button button--primary" onClick={() => animateView(viewAround(first.start, first.end, 0.04), 1.2)}>
        {UI.startCta}
      </button>
    </div>
  )
}

export function App() {
  const route = useApp((state) => state.route)
  const eraIndex = useApp((state) => eraIndexAt(state.view.center, eras))
  useHashRoute()
  useEraAccent()
  useFocusOnSelectedEvent()
  useSceneKeys()
  const inScene = route.name === 'scene' && isPlayable(findScene(route.id))
  return (
    <>
      <Suspense fallback={null}>
        <Stage />
      </Suspense>
      <div className={inScene ? 'app app--scene' : 'app'}>
        <header className="header">
          <a className="brand" href="#/">
            <span className="brand__name">{UI.brand}</span>
            <span className="brand__subtitle">{UI.subtitle}</span>
          </a>
          <nav className="site-nav" aria-label={UI.footerLabel}>
            {PAGE_LINKS.map((link) => (
              <a key={link.id} href={routeToHash({ name: 'page', id: link.id })}>
                {link.label}
              </a>
            ))}
          </nav>
        </header>
        <main className="main">
          {!inScene && (
            <div className="main__side">
              <EraCaption index={eraIndex} />
              <SceneShortcuts index={eraIndex} />
              {route.name === 'home' && <Intro />}
            </div>
          )}
          <ActivePanel route={route} />
        </main>
        {!inScene && <Timeline />}
      </div>
      <ConsentBanner />
    </>
  )
}
