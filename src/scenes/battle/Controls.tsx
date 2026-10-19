import { useEffect, useRef } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { BATTLE_UI } from '../../data/battleUi.ts'
import type { Scene } from '../../data/schema.ts'
import { frenchSpacing } from '../../core/typography.ts'
import type { UiInsets } from '../../map/MapStage.tsx'
import { SIDE_COLORS } from './Markings.tsx'
import type { Battle } from './schema.ts'
import { useBattle, type BattleView } from './store.ts'
import { counterValue, phaseIndexAt } from './timeline.ts'
import './battle.css'

const NUMBER = new Intl.NumberFormat('fr-FR')
const COUNTER_SHARE = 0.95

function Counters({ battle }: { battle: Battle }) {
  const time = useBattle((state) => state.time)
  const index = phaseIndexAt(time, battle.phases.length)
  const counters = battle.phases[index]?.counters
  if (!counters || time <= index) return null
  return (
    <ul className="battle__counters">
      {counters.map((counter) => (
        <li key={counter.label}>
          <span>{frenchSpacing(counter.label)}</span>
          <strong>{frenchSpacing(NUMBER.format(counterValue(counter.from, counter.to, (time - index) / COUNTER_SHARE)))}</strong>
        </li>
      ))}
    </ul>
  )
}

function ViewSwitch() {
  const view = useBattle((state) => state.view)
  const choose = (next: BattleView) => useBattle.getState().setView(next)
  return (
    <div className="battle__views" role="group" aria-label={BATTLE_UI.views}>
      {(['tactical', 'ground'] as const).map((option) => (
        <button key={option} type="button" className="battle__view" aria-pressed={view === option} onClick={() => choose(option)}>
          {BATTLE_UI[option]}
        </button>
      ))}
    </div>
  )
}

function PlayButton({ battle }: { battle: Battle }) {
  const playing = useBattle((state) => state.playing)
  const ended = useBattle((state) => state.time >= battle.phases.length)
  const toggle = () => {
    const state = useBattle.getState()
    if (ended) state.setTime(0)
    state.setPlaying(!state.playing || ended)
  }
  return (
    <button type="button" className="button button--primary battle__play" onClick={toggle}>
      {playing ? BATTLE_UI.pause : ended ? BATTLE_UI.replay : BATTLE_UI.play}
    </button>
  )
}

function Scrubber({ battle, scene }: { battle: Battle; scene: Scene }) {
  const time = useBattle((state) => state.time)
  const total = battle.phases.length
  const index = phaseIndexAt(time, total)
  const title = scene.points?.[index]?.title ?? ''
  const status = time <= 0 ? BATTLE_UI.before : `${BATTLE_UI.phase(index + 1, total)} : ${title}`
  return (
    <div className="battle__timeline">
      <p className="battle__status" aria-live="polite">
        <span className="battle__phase">{frenchSpacing(status)}</span>
        {time > 0 && <span className="battle__clock">{frenchSpacing(BATTLE_UI.clock(battle.phases[index]!.clock))}</span>}
      </p>
      <input
        className="battle__range"
        type="range"
        min={0}
        max={total}
        step={0.001}
        value={time}
        aria-label={BATTLE_UI.scrubber}
        aria-valuetext={status}
        onChange={(event) => {
          const state = useBattle.getState()
          state.setPlaying(false)
          state.setTime(Number(event.currentTarget.value))
        }}
      />
      <ol className="battle__ticks" aria-hidden="true">
        {battle.phases.map((phase, position) => (
          <li key={phase.id} className={position === index && time > 0 ? 'battle__tick battle__tick--current' : 'battle__tick'} />
        ))}
      </ol>
    </div>
  )
}

function Legend({ battle }: { battle: Battle }) {
  const view = useBattle((state) => state.view)
  return (
    <p className="battle__legend">
      <span>{frenchSpacing(BATTLE_UI.scale(battle.scale))}</span>
      {view === 'tactical' && <span className="battle__note">{frenchSpacing(BATTLE_UI.exaggerated(battle.tacticalScale))}</span>}
      {(['rome', 'carthage'] as const).map((side) => (
        <span key={side} className="battle__side">
          <i style={{ background: SIDE_COLORS[side] }} />
          {battle.sides[side]}
        </span>
      ))}
    </p>
  )
}

function Panel({ battle, scene, insets }: { battle: Battle; scene: Scene; insets: UiInsets }) {
  const element = useRef<HTMLElement>(null)
  useEffect(() => {
    const target = element.current
    if (!target) return
    const observer = new ResizeObserver(() => useBattle.getState().setControlsHeight(target.getBoundingClientRect().height))
    observer.observe(target)
    return () => observer.disconnect()
  }, [])
  return (
    <section
      ref={element}
      className="battle"
      aria-label={BATTLE_UI.controls}
      style={{ left: insets.left, right: insets.right, bottom: insets.bottom }}
    >
      <Counters battle={battle} />
      <div className="battle__bar">
        <PlayButton battle={battle} />
        <Scrubber battle={battle} scene={scene} />
        <ViewSwitch />
      </div>
      <Legend battle={battle} />
      <p className="battle__help">{frenchSpacing(BATTLE_UI.help)}</p>
    </section>
  )
}

function isTyping(target: EventTarget | null): boolean {
  return target instanceof Element && target.closest('input, textarea, select, button') !== null
}

export function Controls({ battle, scene, insets }: { battle: Battle; scene: Scene; insets: UiInsets }) {
  const root = useRef<Root | null>(null)

  useEffect(() => {
    const element = document.createElement('div')
    element.className = 'battle-host'
    document.body.append(element)
    const created = createRoot(element)
    root.current = created
    return () => {
      root.current = null
      setTimeout(() => {
        created.unmount()
        element.remove()
      })
    }
  }, [])

  useEffect(() => {
    root.current?.render(<Panel battle={battle} scene={scene} insets={insets} />)
  }, [battle, scene, insets])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== ' ' || event.altKey || event.ctrlKey || event.metaKey || isTyping(event.target)) return
      event.preventDefault()
      const state = useBattle.getState()
      if (state.time >= battle.phases.length) state.setTime(0)
      state.setPlaying(!state.playing)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [battle])
  return null
}
