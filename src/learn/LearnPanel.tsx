import { useMemo, useState } from 'react'
import { formatDate, fromHistorical, type Side } from '../core/dates.ts'
import { GAME_IDS, routeToHash, type GameId } from '../core/route.ts'
import { eras } from '../data/eras.ts'
import { events } from '../data/events.ts'
import { places } from '../data/places.ts'
import type { EraId, HistoricalEvent } from '../data/schema.ts'
import { tracks } from '../data/tracks.ts'
import { LEARN } from '../data/ui.ts'
import { useApp } from '../store.ts'
import { Panel } from '../ui/panels.tsx'
import { dateScore, distanceKm, inEra, orderRound, orderScore, pick, playable, quizRound, seededRandom, whereScore } from './games.ts'
import { readProgress, recordScore } from './progress.ts'

type EraChoice = EraId | 'toutes'

function eventLink(event: HistoricalEvent) {
  return (
    <a href={routeToHash({ name: 'event', id: event.id })} className="learn__link">
      {LEARN.open}
    </a>
  )
}

function Finished({ game, score, total, onAgain }: { game: GameId; score: number; total: number; onAgain: () => void }) {
  const [saved] = useState(() => recordScore(game, score))
  return (
    <div className="learn__result" role="status">
      <p className="learn__score">{LEARN.score(score, total)}</p>
      <p>{LEARN.best(saved.best[game] ?? score)}</p>
      <button type="button" className="button button--primary" onClick={onAgain}>
        {LEARN.again}
      </button>
    </div>
  )
}

function QuizGame({ era, seed, onAgain }: { era: EraChoice; seed: number; onAgain: () => void }) {
  const questions = useMemo(() => quizRound(inEra(events, era), { tracks, places }, seededRandom(seed)), [era, seed])
  const [index, setIndex] = useState(0)
  const [chosen, setChosen] = useState<string | null>(null)
  const [score, setScore] = useState(0)
  const question = questions[index]
  if (!question) return <Finished game="quiz" score={score} total={questions.length} onAgain={onAgain} />
  const answered = chosen !== null
  const choose = (choice: string) => {
    if (answered) return
    setChosen(choice)
    if (choice === question.answer) setScore(score + 1)
  }
  return (
    <div className="learn__game">
      <p className="learn__step">
        {index + 1} / {questions.length}
      </p>
      <h3 className="learn__question">{question.prompt}</h3>
      <div className="learn__choices">
        {question.choices.map((choice) => (
          <button
            key={choice}
            type="button"
            className={`learn__choice${answered && choice === question.answer ? ' is-right' : ''}${answered && choice === chosen && choice !== question.answer ? ' is-wrong' : ''}`}
            onClick={() => choose(choice)}
            aria-pressed={choice === chosen}
          >
            {choice}
          </button>
        ))}
      </div>
      {answered && (
        <div className="learn__feedback" role="status">
          <p>{chosen === question.answer ? LEARN.correct : LEARN.wrong(question.answer)}</p>
          <p className="learn__date">{formatDate(question.event)}</p>
          <button type="button" className="button" onClick={() => {
              setIndex(index + 1)
              setChosen(null)
            }}>
            {LEARN.next}
          </button>
        </div>
      )}
    </div>
  )
}

function OrderGame({ era, seed, onAgain }: { era: EraChoice; seed: number; onAgain: () => void }) {
  const initial = useMemo(() => orderRound(inEra(events, era), seededRandom(seed)), [era, seed])
  const [items, setItems] = useState(initial)
  const [checked, setChecked] = useState(false)
  const move = (index: number, step: number) => {
    const target = index + step
    if (target < 0 || target >= items.length) return
    const next = [...items]
    ;[next[index], next[target]] = [next[target]!, next[index]!]
    setItems(next)
  }
  if (checked) {
    const sorted = [...items].sort((a, b) => a.start - b.start)
    return (
      <div className="learn__game">
        <ol className="learn__order">
          {sorted.map((event, index) => (
            <li key={event.id} className={items[index]?.id === event.id ? 'is-right' : 'is-wrong'}>
              <span>{event.title}</span> <span className="learn__date">{formatDate(event)}</span> {eventLink(event)}
            </li>
          ))}
        </ol>
        <Finished game="ordre" score={orderScore(items)} total={items.length} onAgain={onAgain} />
      </div>
    )
  }
  return (
    <div className="learn__game">
      <ol className="learn__order">
        {items.map((event, index) => (
          <li key={event.id}>
            <span>{event.title}</span>
            <span className="learn__moves">
              <button type="button" onClick={() => move(index, -1)} aria-label={`${LEARN.up} : ${event.title}`} disabled={index === 0}>
                ↑
              </button>
              <button type="button" onClick={() => move(index, 1)} aria-label={`${LEARN.down} : ${event.title}`} disabled={index === items.length - 1}>
                ↓
              </button>
            </span>
          </li>
        ))}
      </ol>
      <button type="button" className="button button--primary" onClick={() => setChecked(true)}>
        {LEARN.check}
      </button>
    </div>
  )
}

function DateGame({ era, seed, onAgain }: { era: EraChoice; seed: number; onAgain: () => void }) {
  const rounds = useMemo(() => pick(playable(inEra(events, era)), 5, seededRandom(seed)), [era, seed])
  const [index, setIndex] = useState(0)
  const [value, setValue] = useState('')
  const [side, setSide] = useState<Side>('bc')
  const [points, setPoints] = useState<number | null>(null)
  const [total, setTotal] = useState(0)
  const event = rounds[index]
  if (!event) return <Finished game="date" score={total} total={rounds.length * 100} onAgain={onAgain} />
  const submit = () => {
    const year = Number.parseInt(value, 10)
    if (!Number.isFinite(year) || year < 1) return
    const score = dateScore(fromHistorical(year, side), event)
    setPoints(score)
    setTotal(total + score)
  }
  return (
    <div className="learn__game">
      <p className="learn__step">
        {index + 1} / {rounds.length}
      </p>
      <h3 className="learn__question">{event.title}</h3>
      <form
        className="learn__year"
        onSubmit={(formEvent) => {
          formEvent.preventDefault()
          if (points === null) submit()
        }}
      >
        <label>
          {LEARN.yearLabel}{' '}
          <input type="number" min={1} max={1500} inputMode="numeric" value={value} onChange={(change) => setValue(change.target.value)} disabled={points !== null} />
        </label>
        <label>
          <span className="visually-hidden">{LEARN.sideLabel}</span>
          <select value={side} onChange={(change) => setSide(change.target.value as Side)} disabled={points !== null}>
            <option value="bc">{LEARN.bc}</option>
            <option value="ad">{LEARN.ad}</option>
          </select>
        </label>
        {points === null && (
          <button type="submit" className="button button--primary">
            {LEARN.check}
          </button>
        )}
      </form>
      {points !== null && (
        <div className="learn__feedback" role="status">
          <p>
            {formatDate(event)} : {points} / 100
          </p>
          {eventLink(event)}
          <button type="button" className="button" onClick={() => {
              setIndex(index + 1)
              setValue('')
              setPoints(null)
            }}>
            {LEARN.next}
          </button>
        </div>
      )}
    </div>
  )
}

function WhereGame({ era, seed, onAgain }: { era: EraChoice; seed: number; onAgain: () => void }) {
  const rounds = useMemo(
    () => pick(playable(inEra(events, era)).filter((event) => places.some((place) => place.id === event.placeId)), 5, seededRandom(seed)),
    [era, seed],
  )
  const [index, setIndex] = useState(0)
  const [result, setResult] = useState<{ km: number; score: number } | null>(null)
  const [total, setTotal] = useState(0)
  const mapPick = useApp((state) => state.mapPick)
  const { setMapPick, setMapMarks } = useApp.getState()
  const event = rounds[index]
  const place = places.find((candidate) => candidate.id === event?.placeId)
  if (!event || !place) return <Finished game="ou" score={total} total={rounds.length * 100} onAgain={onAgain} />
  const submit = () => {
    if (!mapPick) return
    const km = Math.round(distanceKm(mapPick, place))
    const score = whereScore(km)
    setResult({ km, score })
    setTotal(total + score)
    setMapMarks([
      { ...mapPick, kind: 'guess' },
      { lon: place.lon, lat: place.lat, kind: 'answer' },
    ])
  }
  const next = () => {
    setIndex(index + 1)
    setResult(null)
    setMapPick(null)
    setMapMarks([])
  }
  return (
    <div className="learn__game">
      <p className="learn__step">
        {index + 1} / {rounds.length}
      </p>
      <h3 className="learn__question">{event.title}</h3>
      <p className="learn__date">{formatDate(event)}</p>
      {!result && (
        <>
          <p>{mapPick ? LEARN.picked : LEARN.pickOnMap}</p>
          <button type="button" className="button button--primary" onClick={submit} disabled={!mapPick}>
            {LEARN.check}
          </button>
        </>
      )}
      {result && (
        <div className="learn__feedback" role="status">
          <p>
            {LEARN.distance(result.km)} {place.name} : {result.score} / 100
          </p>
          {eventLink(event)}
          <button type="button" className="button" onClick={next}>
            {LEARN.next}
          </button>
        </div>
      )}
    </div>
  )
}

const GAMES: Record<GameId, typeof QuizGame> = { quiz: QuizGame, ordre: OrderGame, date: DateGame, ou: WhereGame }

export function LearnPanel({ game }: { game?: GameId }) {
  const [era, setEra] = useState<EraChoice>('toutes')
  const [seed, setSeed] = useState(() => Date.now())
  const progress = useMemo(() => readProgress(), [])
  const Game = game ? GAMES[game] : null
  return (
    <Panel kind={game === 'ou' ? 'map-game' : 'learn'} labelId="panel-title" focusKey={game ?? 'apprendre'}>
      <p className="panel__eyebrow">{LEARN.navLearn}</p>
      <h2 id="panel-title" className="panel__title" tabIndex={-1}>
        {game ? LEARN.games[game].title : LEARN.title}
      </h2>
      {!game && <p>{LEARN.intro}</p>}
      <label className="learn__era">
        {LEARN.era}{' '}
        <select value={era} onChange={(change) => {
            setEra(change.target.value as EraChoice)
            setSeed(Date.now())
          }}>
          <option value="toutes">{LEARN.allEras}</option>
          {eras.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
      </label>
      {Game ? (
        <>
          <Game key={`${era}-${seed}`} era={era} seed={seed} onAgain={() => setSeed(Date.now())} />
          <p>
            <a href={routeToHash({ name: 'learn' })}>{LEARN.back}</a>
          </p>
        </>
      ) : (
        <>
          <p className="learn__progress">{LEARN.seen(progress.seen.filter((id) => events.some((event) => event.id === id)).length, events.length)}</p>
          <ul className="learn__games">
            {GAME_IDS.map((id) => (
              <li key={id}>
                <a href={routeToHash({ name: 'learn', game: id })} className="learn__card">
                  <strong>{LEARN.games[id].title}</strong>
                  <span>{LEARN.games[id].text}</span>
                  {progress.best[id] !== undefined && <span className="learn__best">{LEARN.best(progress.best[id])}</span>}
                </a>
              </li>
            ))}
          </ul>
        </>
      )}
    </Panel>
  )
}
