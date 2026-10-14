import { useEffect, useRef, type ReactNode } from 'react'
import { formatDate, formatRange } from '../core/dates.ts'
import { eras } from '../data/eras.ts'
import type { Page } from '../data/pages.ts'
import { people } from '../data/people.ts'
import { places } from '../data/places.ts'
import type { HistoricalEvent, Source } from '../data/schema.ts'
import { CATEGORY, CERTAINTY, UI } from '../data/ui.ts'
import { navigate } from '../store.ts'
import { Markdown } from './Markdown.tsx'

function Panel({ kind, labelId, focusKey, children }: { kind: string; labelId: string; focusKey: string; children: ReactNode }) {
  const ref = useRef<HTMLElement>(null)
  useEffect(() => {
    ref.current?.querySelector<HTMLElement>(`#${labelId}`)?.focus()
  }, [focusKey, labelId])
  return (
    <aside ref={ref} className={`panel panel--${kind}`} aria-labelledby={labelId} data-native-keys>
      <button type="button" className="panel__close" onClick={() => navigate({ name: 'home' })} aria-label={UI.close}>
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
          {event.certaintyNote ?? certainty.description}
        </span>
      </p>
      <p className="panel__summary">{event.summary}</p>
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
      <SourceList title={UI.ancientSources} sources={event.sources.filter((source) => source.kind === 'ancient')} />
      <SourceList title={UI.modernSources} sources={event.sources.filter((source) => source.kind === 'modern')} />
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
      <p>{UI.notFoundText}</p>
      <p>
        <a href="#/">{UI.backHome}</a>
      </p>
    </Panel>
  )
}

export function EraCaption({ index }: { index: number }) {
  const era = eras[index]
  if (!era) return null
  return (
    <section className="era-caption" aria-live="polite">
      <h2 className="era-caption__name">{era.name}</h2>
      <p className="era-caption__range">{formatRange(era.start, era.end)}</p>
      <p className="era-caption__summary">{era.summary}</p>
      <p className="era-caption__note">{era.boundsNote}</p>
    </section>
  )
}
