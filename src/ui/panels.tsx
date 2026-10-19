import { useEffect, useRef, type ReactNode } from 'react'
import { formatDate, formatRange, formatYear } from '../core/dates.ts'
import { frenchSpacing } from '../core/typography.ts'
import { eras } from '../data/eras.ts'
import { scenes } from '../data/scenes.ts'
import type { Page } from '../data/pages.ts'
import { people } from '../data/people.ts'
import { places } from '../data/places.ts'
import type { HistoricalEvent, Scene, Source } from '../data/schema.ts'
import { CATEGORY, CERTAINTY, UI } from '../data/ui.ts'
import { findScene, isPlayable } from '../scenes/registry.ts'
import { navigate, useApp } from '../store.ts'
import { Markdown } from './Markdown.tsx'

function Panel({
  kind,
  labelId,
  focusKey,
  closeLabel = UI.close,
  children,
}: {
  kind: string
  labelId: string
  focusKey: string
  closeLabel?: string
  children: ReactNode
}) {
  const ref = useRef<HTMLElement>(null)
  useEffect(() => {
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
    return () => {
      if (opener?.isConnected) opener.focus()
    }
  }, [])
  useEffect(() => {
    ref.current?.querySelector<HTMLElement>(`#${labelId}`)?.focus()
  }, [focusKey, labelId])
  return (
    <aside ref={ref} className={`panel panel--${kind}`} aria-labelledby={labelId} data-native-keys>
      <button type="button" className="panel__close" onClick={() => navigate({ name: 'home' })} aria-label={closeLabel}>
        <span aria-hidden="true">×</span>
      </button>
      {children}
    </aside>
  )
}

function SourceItem({ source }: { source: Source }) {
  return (
    <li>
      {source.author}, <cite>{source.work}</cite>
      {source.locus ? `, ${source.locus}` : ''}
      {source.url && (
        <>
          {' '}
          (
          <a href={source.url} target="_blank" rel="noopener noreferrer">
            {UI.openSource}
          </a>
          )
        </>
      )}
    </li>
  )
}

function SourceList({ title, sources }: { title: string; sources: Source[] }) {
  if (sources.length === 0) return null
  return (
    <section className="panel__sources">
      <h3>{title}</h3>
      <ul>
        {sources.map((source) => (
          <SourceItem key={`${source.author}-${source.work}-${source.locus ?? ''}`} source={source} />
        ))}
      </ul>
    </section>
  )
}

export function EventPanel({ event }: { event: HistoricalEvent }) {
  const era = eras.find((candidate) => candidate.id === event.era)
  const place = places.find((candidate) => candidate.id === event.placeId)
  const persons = people.filter((person) => event.people?.includes(person.id))
  const certainty = CERTAINTY[event.certainty]
  return (
    <Panel kind="event" labelId="panel-title" focusKey={event.id}>
      <p className="panel__eyebrow">
        {era?.name} · {CATEGORY[event.category]}
      </p>
      <h2 id="panel-title" className="panel__title" tabIndex={-1}>
        {event.title}
      </h2>
      <p className="panel__date">{formatDate(event)}</p>
      <p className={`certainty event--${event.certainty}`}>
        <span className="event__marker" aria-hidden="true" />
        <span>
          <strong>
            {UI.certainty} : {certainty.label.toLowerCase()}.
          </strong>{' '}
          {frenchSpacing(event.certaintyNote ?? certainty.description)}
        </span>
      </p>
      <p className="panel__summary">{frenchSpacing(event.summary)}</p>
      <Markdown className="panel__body prose" source={event.body} />
      {(place || persons.length > 0) && (
        <dl className="panel__facts">
          {place && (
            <>
              <dt>{UI.place}</dt>
              <dd>
                {place.name}
                {place.ancientName ? ` (${place.ancientName})` : ''}
              </dd>
            </>
          )}
          {persons.length > 0 && (
            <>
              <dt>{UI.people}</dt>
              <dd>{persons.map((person) => person.name).join(', ')}</dd>
            </>
          )}
        </dl>
      )}
      <SceneLink id={event.scene} />
      <SourceList title={UI.ancientSources} sources={event.sources.filter((source) => source.kind === 'ancient')} />
      <SourceList title={UI.modernSources} sources={event.sources.filter((source) => source.kind === 'modern')} />
    </Panel>
  )
}

function SceneLink({ id }: { id: string | undefined }) {
  const scene = id ? findScene(id) : undefined
  if (!isPlayable(scene)) return null
  return (
    <p className="panel__scene">
      <a className="button button--primary" href={`#/scene/${scene.id}`}>
        {UI.sceneEnter(scene.title)}
      </a>
    </p>
  )
}

function clampPoint(scene: Scene, point: number): number {
  return Math.max(0, Math.min(scene.points?.length ?? 0, point))
}

function ScenePoints({ scene, point }: { scene: Scene; point: number }) {
  const labels = [UI.sceneOverview, ...(scene.points ?? []).map((item) => item.title)]
  const setPoint = (next: number) => useApp.getState().setScenePoint(clampPoint(scene, next))
  return (
    <nav className="scene-nav" aria-label={UI.sceneSteps}>
      <button type="button" className="button" onClick={() => setPoint(point - 1)} disabled={point === 0}>
        {UI.scenePrevious}
      </button>
      <ol className="scene-nav__steps">
        {labels.map((label, index) => (
          <li key={label}>
            <button
              type="button"
              className="scene-nav__step"
              aria-current={index === point ? 'step' : undefined}
              aria-label={`${UI.sceneStep(index + 1, labels.length)} : ${label}`}
              onClick={() => setPoint(index)}
            />
          </li>
        ))}
      </ol>
      <button
        type="button"
        className="button button--primary"
        onClick={() => setPoint(point + 1)}
        disabled={point === labels.length - 1}
      >
        {UI.sceneNext}
      </button>
    </nav>
  )
}

function SoundToggle() {
  const soundOn = useApp((state) => state.soundOn)
  return (
    <button type="button" className="scene__sound" aria-pressed={soundOn} aria-label={UI.soundLabel} onClick={() => useApp.getState().setSoundOn(!soundOn)}>
      {soundOn ? UI.soundOn : UI.soundOff}
    </button>
  )
}

export function ScenePanel({ scene }: { scene: Scene }) {
  const point = useApp((state) => state.scenePoint)
  const failed = useApp((state) => state.failedScene === scene.id)
  const playable = isPlayable(scene) && !failed
  const current = point > 0 ? scene.points?.[point - 1] : undefined
  const total = (scene.points?.length ?? 0) + 1
  return (
    <Panel kind="scene" labelId="panel-title" focusKey={scene.id} closeLabel={UI.sceneBack}>
      <p className="panel__eyebrow">
        {UI.sceneKicker}
        {scene.year !== undefined && ` · vers ${formatYear(scene.year)}`}
      </p>
      <h2 id="panel-title" className="panel__title" tabIndex={-1}>
        {scene.title}
      </h2>
      {!playable && <p className="panel__summary">{frenchSpacing(failed ? UI.sceneFailed : UI.scenePlanned)}</p>}
      {playable && (
        <>
          <div className="scene__status">
            <p className="scene__step">{UI.sceneStep(point + 1, total)}</p>
            {(scene.ambience?.length ?? 0) > 0 && <SoundToggle />}
          </div>
          <section className="scene__cartel" aria-live="polite">
            <h3 className="scene__point-title">{current ? current.title : UI.sceneOverview}</h3>
            <p>{frenchSpacing(current ? current.text : (scene.summary ?? ''))}</p>
            {current && (
              <details className="scene__sources">
                <summary>{UI.sources}</summary>
                <ul>
                  {current.sources.map((source) => (
                    <li key={source}>{source}</li>
                  ))}
                </ul>
              </details>
            )}
          </section>
          <ScenePoints scene={scene} point={point} />
          <p className="scene__help">{UI.sceneHelp}</p>
        </>
      )}
    </Panel>
  )
}

export function PagePanel({ page }: { page: Page }) {
  return (
    <Panel kind="page" labelId="panel-title" focusKey={page.id}>
      <h2 id="panel-title" className="panel__title" tabIndex={-1}>
        {page.title}
      </h2>
      <Markdown className="prose" source={page.body} />
    </Panel>
  )
}

export function NotFoundPanel() {
  return (
    <Panel kind="page" labelId="panel-title" focusKey="not-found">
      <h2 id="panel-title" className="panel__title" tabIndex={-1}>
        {UI.notFoundTitle}
      </h2>
      <p>{frenchSpacing(UI.notFoundText)}</p>
      <p>
        <a href="#/">{UI.backHome}</a>
      </p>
    </Panel>
  )
}

export function SceneShortcuts({ index }: { index: number }) {
  const era = eras[index]
  if (!era) return null
  const available = scenes.filter((scene) => isPlayable(scene) && scene.year !== undefined && scene.year >= era.start && scene.year <= era.end)
  if (available.length === 0) return null
  return (
    <section className="scene-shortcuts" aria-labelledby="scene-shortcuts-title">
      <h3 id="scene-shortcuts-title" className="scene-shortcuts__title">
        {UI.sceneShortcuts}
      </h3>
      <ul>
        {available.map((scene) => (
          <li key={scene.id}>
            <a href={`#/scene/${scene.id}`}>{scene.title}</a>
            {scene.year !== undefined && <span className="scene-shortcuts__date"> · vers {formatYear(scene.year)}</span>}
          </li>
        ))}
      </ul>
    </section>
  )
}

export function EraCaption({ index }: { index: number }) {
  const era = eras[index]
  if (!era) return null
  return (
    <section className="era-caption" aria-live="polite">
      <h2 className="era-caption__name">{era.name}</h2>
      <p className="era-caption__range">{formatRange(era.start, era.end)}</p>
      <p className="era-caption__summary">{frenchSpacing(era.summary)}</p>
      <p className="era-caption__note">{frenchSpacing(era.boundsNote)}</p>
    </section>
  )
}
