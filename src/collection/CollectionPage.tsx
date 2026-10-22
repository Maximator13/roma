import { useEffect, useMemo, useState } from 'react'
import { readExplore } from '../core/explore.ts'
import { frenchSpacing } from '../core/typography.ts'
import { cardArt } from '../data/cardArt.ts'
import { cards } from '../data/cards.ts'
import { cities } from '../data/cities.ts'
import { COLLECTION_UI, ERA_SHORT, KIND_LABEL, RARITY_LABEL, RARITY_RULE } from '../data/collectionUi.ts'
import { eras } from '../data/eras.ts'
import { events } from '../data/events.ts'
import { people } from '../data/people.ts'
import { places } from '../data/places.ts'
import { CARD_KINDS, ERA_IDS, type CardKind, type EraId, type Rarity } from '../data/schema.ts'
import { buildCatalog, toPool, type CardView } from './catalog.ts'
import { CardDialog } from './CardDialog.tsx'
import {
  awardSeries,
  buildSeries,
  canOpenDaily,
  claimExploration,
  craft,
  CRAFT_COST,
  dayKey,
  DUPLICATE_VALUE,
  openBonus,
  openDaily,
  rank,
  RARITY_ORDER,
  RARITY_WEIGHTS,
  type CollectionState,
  type Pull,
} from './game.ts'
import { PackOpening, SealedPack } from './PackOpening.tsx'
import { KindIcon, RomaCard } from './RomaCard.tsx'
import { loadState, saveState } from './storage.ts'
import './collection.css'

const catalog = buildCatalog({ cards, art: cardArt, eras, people, cities, places })
const byId = new Map(catalog.map((card) => [card.id, card]))
const pool = toPool(catalog)
const series = buildSeries(pool, [...ERA_IDS], [...CARD_KINDS])
const knownEvents = new Set(events.map((event) => event.id))
const totalWeight = Object.values(RARITY_WEIGHTS).reduce((sum, weight) => sum + weight, 0)

function browserStore(): Storage | null {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

function seriesName(id: string): string {
  const era = ERA_IDS.find((candidate) => id === `epoque-${candidate}`)
  if (era) return COLLECTION_UI.seriesEra(ERA_SHORT[era])
  const kind = CARD_KINDS.find((candidate) => id === `type-${candidate}`)
  return kind ? COLLECTION_UI.seriesKind(KIND_LABEL[kind].many) : id
}

function untilMidnight(now: Date): string {
  const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1)
  const minutes = Math.max(1, Math.ceil((midnight.getTime() - now.getTime()) / 60_000))
  const hours = Math.floor(minutes / 60)
  return hours > 0 ? `${hours} h ${String(minutes % 60).padStart(2, '0')}` : `${minutes} min`
}

function useNow(): Date {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 30_000)
    return () => window.clearInterval(timer)
  }, [])
  return now
}

function initialSession(): { state: CollectionState; notices: string[]; saved: boolean } {
  const store = browserStore()
  const loaded = loadState(store)
  const today = dayKey(new Date())
  const explored = claimExploration(loaded, readExplore(), pool, knownEvents, today)
  const awarded = awardSeries(explored.state, series)
  const notices = [
    ...explored.rewards.map((reward) => {
      if (reward.type === 'deniers') return COLLECTION_UI.rewardDeniers(reward.amount, reward.events)
      const name = byId.get(reward.id)?.name ?? reward.id
      return reward.duplicate ? COLLECTION_UI.rewardDuplicate(name, reward.deniers) : COLLECTION_UI.rewardCard(name)
    }),
    ...awarded.completed.map((id) => COLLECTION_UI.seriesDone(seriesName(id))),
  ]
  return { state: awarded.state, notices, saved: saveState(store, awarded.state) }
}

interface Filters {
  kind: CardKind | 'all'
  era: EraId | 'all'
  rarity: Rarity | 'all'
  ownedOnly: boolean
}

function sortCards(list: CardView[]): CardView[] {
  return [...list].sort((a, b) => rank(b.rarity) - rank(a.rarity) || a.year - b.year)
}

export default function CollectionPage() {
  const [session] = useState(initialSession)
  const [state, setState] = useState(session.state)
  const [notices, setNotices] = useState(session.notices)
  const [opening, setOpening] = useState<{ pulls: Pull[]; label: string } | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [filters, setFilters] = useState<Filters>({ kind: 'all', era: 'all', rarity: 'all', ownedOnly: false })
  const now = useNow()
  const today = dayKey(now)

  const commit = (next: CollectionState) => {
    const awarded = awardSeries(next, series)
    if (awarded.completed.length > 0) setNotices((current) => [...current, ...awarded.completed.map((id) => COLLECTION_UI.seriesDone(seriesName(id)))])
    setState(awarded.state)
    saveState(browserStore(), awarded.state)
  }

  const openPack = (kind: 'daily' | 'bonus') => {
    const result = kind === 'daily' ? openDaily(state, pool, today) : openBonus(state, pool, today)
    if (result.pulls.length === 0) return
    commit(result.state)
    setOpening({ pulls: result.pulls, label: kind === 'daily' ? COLLECTION_UI.dailyKicker : COLLECTION_UI.bonusKicker })
  }

  const visible = useMemo(
    () =>
      sortCards(
        catalog.filter(
          (card) =>
            (filters.kind === 'all' || card.kind === filters.kind) &&
            (filters.era === 'all' || card.era === filters.era) &&
            (filters.rarity === 'all' || card.rarity === filters.rarity) &&
            (!filters.ownedOnly || state.owned[card.id] !== undefined),
        ),
      ),
    [filters, state.owned],
  )

  const ownedCount = catalog.filter((card) => state.owned[card.id] !== undefined).length
  const dailyReady = canOpenDaily(state, today)
  const selectedCard = selected ? byId.get(selected) : undefined
  const dateLabel = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }).format(now)

  return (
    <div className="collection">
      <div className="collection__inner">
        <header className="collection__header">
          <a className="collection__back" href="#/">
            {COLLECTION_UI.back}
          </a>
          <h1 className="collection__title">{COLLECTION_UI.title}</h1>
          <p className="collection__stats">
            <span>{COLLECTION_UI.owned(ownedCount, catalog.length)}</span>
            <span className="collection__deniers">{COLLECTION_UI.deniers(state.deniers)}</span>
          </p>
        </header>

        {!session.saved && <p className="collection__warning">{COLLECTION_UI.storageWarning}</p>}

        <section className="daily" aria-labelledby="daily-title">
          <div className="daily__pack">
            <SealedPack label={COLLECTION_UI.dailyKicker} date={dateLabel} />
          </div>
          <div className="daily__text">
            <h2 id="daily-title" className="daily__title">
              {dailyReady ? COLLECTION_UI.dailyKicker : COLLECTION_UI.dailyDone}
            </h2>
            <p className="daily__intro">{frenchSpacing(COLLECTION_UI.intro)}</p>
            {dailyReady ? (
              <button type="button" className="button button--primary daily__open" onClick={() => openPack('daily')}>
                {COLLECTION_UI.dailyOpen}
              </button>
            ) : (
              <p className="daily__next">{COLLECTION_UI.dailyNext(untilMidnight(now))}</p>
            )}
            {state.bonusPacks > 0 && (
              <button type="button" className="button daily__bonus" onClick={() => openPack('bonus')}>
                {COLLECTION_UI.bonusOpen(state.bonusPacks)}
              </button>
            )}
            {notices.length > 0 && (
              <div className="notices" role="status">
                <p className="notices__title">{COLLECTION_UI.rewardsTitle}</p>
                <ul>
                  {notices.map((notice, index) => (
                    <li key={index}>{frenchSpacing(notice)}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>

        <section className="binder" aria-labelledby="binder-title">
          <h2 id="binder-title" className="section-title">
            {COLLECTION_UI.owned(ownedCount, catalog.length)}
          </h2>
          <div className="filters" role="group" aria-label={COLLECTION_UI.filtersLabel}>
            <div className="filters__kinds">
              {(['all', ...CARD_KINDS] as const).map((kind) => (
                <button
                  key={kind}
                  type="button"
                  className="chip"
                  aria-pressed={filters.kind === kind}
                  onClick={() => setFilters((current) => ({ ...current, kind }))}
                >
                  {kind !== 'all' && <KindIcon kind={kind} />}
                  {kind === 'all' ? COLLECTION_UI.allKinds : KIND_LABEL[kind].many}
                </button>
              ))}
            </div>
            <div className="filters__selects">
              <label>
                <span className="visually-hidden">{COLLECTION_UI.eraFilter}</span>
                <select value={filters.era} onChange={(event) => setFilters((current) => ({ ...current, era: event.target.value as Filters['era'] }))}>
                  <option value="all">{COLLECTION_UI.allEras}</option>
                  {ERA_IDS.map((era) => (
                    <option key={era} value={era}>
                      {ERA_SHORT[era]}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span className="visually-hidden">{COLLECTION_UI.rarityFilter}</span>
                <select value={filters.rarity} onChange={(event) => setFilters((current) => ({ ...current, rarity: event.target.value as Filters['rarity'] }))}>
                  <option value="all">{COLLECTION_UI.allRarities}</option>
                  {[...RARITY_ORDER].reverse().map((rarity) => (
                    <option key={rarity} value={rarity}>
                      {RARITY_LABEL[rarity]}
                    </option>
                  ))}
                </select>
              </label>
              <label className="filters__toggle">
                <input type="checkbox" checked={filters.ownedOnly} onChange={(event) => setFilters((current) => ({ ...current, ownedOnly: event.target.checked }))} />
                {COLLECTION_UI.ownedOnly}
              </label>
            </div>
          </div>
          {visible.length === 0 ? (
            <p className="binder__empty">{COLLECTION_UI.empty}</p>
          ) : (
            <ul className="binder__grid">
              {visible.map((card) => {
                const owned = state.owned[card.id] !== undefined
                return (
                  <li key={card.id}>
                    <button
                      type="button"
                      className={owned ? 'binder__slot' : `binder__slot binder__slot--missing binder__slot--${card.rarity}`}
                      aria-label={owned ? COLLECTION_UI.open(card.name) : COLLECTION_UI.openMissing(card.name)}
                      onClick={() => setSelected(card.id)}
                    >
                      {owned ? (
                        <RomaCard card={card} />
                      ) : (
                        <span className="ghost">
                          <KindIcon kind={card.kind} />
                          <span className="ghost__name">{card.name}</span>
                          <span className="ghost__rarity">{RARITY_LABEL[card.rarity]}</span>
                        </span>
                      )}
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </section>

        <section className="series" aria-labelledby="series-title">
          <h2 id="series-title" className="section-title">
            {COLLECTION_UI.seriesTitle}
          </h2>
          <ul className="series__list">
            {series.map((item) => {
              const owned = item.cards.filter((id) => state.owned[id] !== undefined).length
              const done = state.completedSeries.includes(item.id)
              return (
                <li key={item.id} className={done ? 'series__item series__item--done' : 'series__item'}>
                  <span className="series__name">{seriesName(item.id)}</span>
                  <span className="series__count">{COLLECTION_UI.seriesProgress(owned, item.cards.length)}</span>
                  <span className="series__bar" aria-hidden="true">
                    <span style={{ width: `${(owned / item.cards.length) * 100}%` }} />
                  </span>
                </li>
              )
            })}
          </ul>
        </section>

        <details className="rules">
          <summary>{COLLECTION_UI.rulesTitle}</summary>
          <ul>
            {COLLECTION_UI.rules.map((rule) => (
              <li key={rule}>{frenchSpacing(rule)}</li>
            ))}
          </ul>
          <div className="rules__table">
            <table>
              <thead>
                <tr>
                  {COLLECTION_UI.oddsHeader.map((header) => (
                    <th key={header} scope="col">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[...RARITY_ORDER].reverse().map((rarity) => (
                  <tr key={rarity}>
                    <th scope="row" className={`rules__rarity rules__rarity--${rarity}`}>
                      {RARITY_LABEL[rarity]}
                    </th>
                    <td>{frenchSpacing(`${((RARITY_WEIGHTS[rarity] / totalWeight) * 100).toLocaleString('fr-FR')} %`)}</td>
                    <td>{DUPLICATE_VALUE[rarity]}</td>
                    <td>{CRAFT_COST[rarity]}</td>
                    <td>{RARITY_RULE[rarity]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </div>

      {opening && <PackOpening pulls={opening.pulls} catalog={byId} label={opening.label} onDone={() => setOpening(null)} />}
      {selectedCard && (
        <CardDialog
          card={selectedCard}
          owned={state.owned[selectedCard.id] !== undefined}
          deniers={state.deniers}
          onCraft={() => commit(craft(state, selectedCard, today))}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  )
}
