import { useMemo, useRef } from 'react'
import { formatDate, formatRange, formatYear } from '../core/dates.ts'
import { eras } from '../data/eras.ts'
import { events } from '../data/events.ts'
import type { Era, HistoricalEvent } from '../data/schema.ts'
import { tracks } from '../data/tracks.ts'
import { CERTAINTY, UI } from '../data/ui.ts'
import { navigate, useApp } from '../store.ts'
import { useElementWidth } from '../ui/useElementWidth.ts'
import { eraIndexAt } from './keys.ts'
import { layoutLanes, type LaneLayout, type PlacedEvent } from './lanes.ts'
import { ticks } from './ticks.ts'
import { useTimelineGestures, useTimelineKeys } from './useTimelineInput.ts'
import { animateView } from './viewAnimation.ts'
import { viewAround, yearToX, type Viewport } from './viewport.ts'

const ROW_HEIGHT = 28
const BASELINE_HEIGHT = 14

function eventLabel(event: HistoricalEvent): string {
  return `${event.title}, ${formatDate(event)}, ${CERTAINTY[event.certainty].label.toLowerCase()}`
}

function EraBand({ view, width }: { view: Viewport; width: number }) {
  const current = eraIndexAt(view.center, eras)
  return (
    <ol className="eras" aria-label="Époques">
      {eras.map((era: Era, index) => {
        const from = Math.max(0, yearToX(era.start, view, width))
        const to = Math.min(width, yearToX(era.end, view, width))
        if (to <= from) return null
        return (
          <li key={era.id} className="eras__item" style={{ left: from, width: to - from }}>
            <button
              type="button"
              className={index === current ? 'eras__button is-current' : 'eras__button'}
              onClick={() => animateView(viewAround(era.start, era.end, 0.04), 0.9)}
              aria-label={`${era.name}, ${formatRange(era.start, era.end)}`}
            >
              <span className={to - from < 64 ? 'visually-hidden' : undefined}>{era.name}</span>
            </button>
          </li>
        )
      })}
    </ol>
  )
}

function Ticks({ view, width }: { view: Viewport; width: number }) {
  return (
    <div className="ticks" aria-hidden="true">
      {ticks(view, width).map((year) => (
        <span key={year} className="ticks__tick" style={{ transform: `translateX(${yearToX(year, view, width)}px)` }}>
          {formatYear(year)}
        </span>
      ))}
    </div>
  )
}

function EventItem({ placed, selected }: { placed: PlacedEvent; selected: boolean }) {
  const { event, x, row } = placed
  const className = `event event--${event.certainty}${selected ? ' is-selected' : ''}${row === null ? ' is-compact' : ''}`
  const top = row === null ? undefined : row * ROW_HEIGHT
  return (
    <button
      type="button"
      className={className}
      style={{ transform: `translateX(${x}px)`, top }}
      onClick={() => navigate({ name: 'event', id: event.id })}
      aria-label={eventLabel(event)}
      aria-current={selected ? 'true' : undefined}
    >
      <span className="event__marker" />
      {row !== null && <span className="event__label">{event.title}</span>}
    </button>
  )
}

function Lane({ layout, selectedId }: { layout: LaneLayout; selectedId: string | null }) {
  const height = layout.rows * ROW_HEIGHT + BASELINE_HEIGHT
  return (
    <div className={`lane lane--${layout.lane}`} style={{ height }}>
      {layout.segments.map((segment) => (
        <div
          key={segment.id}
          className="lane__segment"
          style={{ left: segment.from, width: Math.max(2, segment.to - segment.from) }}
        >
          <span className="lane__name" style={{ left: Math.max(0, -segment.from) + 6 }}>
            {segment.name}
          </span>
        </div>
      ))}
      {layout.events.map((placed) =>
        placed.endX === null ? null : (
          <span
            key={`${placed.event.id}-span`}
            className="lane__duration"
            aria-hidden="true"
            style={{ left: placed.x, width: Math.max(2, placed.endX - placed.x) }}
          />
        ),
      )}
      {layout.events.map((placed) => (
        <EventItem key={placed.event.id} placed={placed} selected={placed.event.id === selectedId} />
      ))}
    </div>
  )
}

function Legend() {
  return (
    <ul className="legend" aria-label={UI.legend}>
      {Object.entries(CERTAINTY).map(([certainty, { label, description }]) => (
        <li key={certainty} className={`legend__item event--${certainty}`} title={description}>
          <span className="event__marker" aria-hidden="true" />
          {label}
        </li>
      ))}
    </ul>
  )
}

export function Timeline() {
  const ref = useRef<HTMLElement>(null)
  const width = useElementWidth(ref)
  const view = useApp((state) => state.view)
  const route = useApp((state) => state.route)
  const selectedId = route.name === 'event' ? route.id : null
  useTimelineGestures(ref, width)
  useTimelineKeys(width)
  const lanes = useMemo(
    () => (width > 0 ? layoutLanes(view, width, tracks, events, selectedId) : []),
    [view, width, selectedId],
  )
  return (
    <section ref={ref} className="timeline" aria-label={UI.timelineLabel} aria-describedby="timeline-help">
      <div className="timeline__now" aria-hidden="true">
        <span className="timeline__year" title={UI.currentYear}>
          {formatYear(Math.round(view.center))}
        </span>
      </div>
      {width > 0 && (
        <>
          <EraBand view={view} width={width} />
          <Ticks view={view} width={width} />
          <div className="lanes">
            {lanes.map((layout) => (
              <Lane key={layout.lane} layout={layout} selectedId={selectedId} />
            ))}
          </div>
        </>
      )}
      <div className="timeline__footer">
        <p id="timeline-help" className="timeline__help">
          {UI.timelineHelp}
        </p>
        <Legend />
      </div>
    </section>
  )
}
