import { useDeferredValue, useEffect, useMemo, useRef, useState } from 'react'
import { routeToHash } from '../core/route.ts'
import { events } from '../data/events.ts'
import { people } from '../data/people.ts'
import { places } from '../data/places.ts'
import { LEARN } from '../data/ui.ts'
import { Panel } from '../ui/panels.tsx'
import { search } from './games.ts'

export function SearchPanel() {
  const [query, setQuery] = useState('')
  const input = useRef<HTMLInputElement>(null)
  useEffect(() => {
    const frame = requestAnimationFrame(() => input.current?.focus())
    return () => cancelAnimationFrame(frame)
  }, [])
  const deferred = useDeferredValue(query)
  const hits = useMemo(() => search(deferred, { events, people, places }), [deferred])
  return (
    <Panel kind="search" labelId="panel-title" focusKey="recherche">
      <h2 id="panel-title" className="panel__title" tabIndex={-1}>
        {LEARN.searchTitle}
      </h2>
      <label className="learn__search">
        <span className="visually-hidden">{LEARN.searchLabel}</span>
        <input ref={input} type="search" value={query} onChange={(change) => setQuery(change.target.value)} placeholder={LEARN.searchLabel} />
      </label>
      {deferred.trim().length > 1 && hits.length === 0 && <p>{LEARN.searchEmpty}</p>}
      <ul className="learn__hits">
        {hits.map((hit) => (
          <li key={`${hit.kind}-${hit.id}`}>
            {hit.eventId ? <a href={routeToHash({ name: 'event', id: hit.eventId })}>{hit.title}</a> : <span>{hit.title}</span>}{' '}
            <span className="learn__kind">
              {LEARN.kinds[hit.kind]}
              {hit.detail ? `, ${hit.detail}` : ''}
            </span>
          </li>
        ))}
      </ul>
    </Panel>
  )
}
