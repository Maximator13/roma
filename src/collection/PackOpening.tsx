import { useEffect, useRef, useState, type CSSProperties } from 'react'
import { COLLECTION_UI } from '../data/collectionUi.ts'
import type { CardView } from './catalog.ts'
import type { Pull } from './game.ts'
import { Modal } from './Modal.tsx'
import { CardBack, RomaCard } from './RomaCard.tsx'

const BURST_MS = 1100

type Phase = 'sealed' | 'bursting' | 'reveal'

export function prefersReducedMotion(): boolean {
  return typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function SealedPack({ label, date }: { label: string; date?: string }) {
  return (
    <div className="pack" role="img" aria-label={COLLECTION_UI.packAlt}>
      <div className="pack__foil" />
      <div className="pack__crimp pack__crimp--top" />
      <p className="pack__kicker">{label}</p>
      <p className="pack__spqr">SPQR</p>
      <div className="pack__seal">
        <span>R</span>
      </div>
      {date && <p className="pack__date">{date}</p>}
      <div className="pack__crimp pack__crimp--bottom" />
    </div>
  )
}

export function PackOpening({ pulls, catalog, label, onDone }: { pulls: Pull[]; catalog: Map<string, CardView>; label: string; onDone: () => void }) {
  const reduced = prefersReducedMotion()
  const [phase, setPhase] = useState<Phase>(reduced ? 'reveal' : 'sealed')
  const [flipped, setFlipped] = useState<boolean[]>(() => pulls.map(() => reduced))
  const slots = useRef<(HTMLButtonElement | null)[]>([])
  const doneButton = useRef<HTMLButtonElement>(null)
  const allFlipped = flipped.every(Boolean)

  useEffect(() => {
    if (phase !== 'bursting') return
    const timer = window.setTimeout(() => setPhase('reveal'), BURST_MS)
    return () => window.clearTimeout(timer)
  }, [phase])

  useEffect(() => {
    if (phase !== 'reveal') return
    const next = flipped.findIndex((value) => !value)
    if (next >= 0) slots.current[next]?.focus()
    else doneButton.current?.focus()
  }, [phase, flipped])

  const flip = (index: number) => setFlipped((current) => current.map((value, position) => value || position === index))

  return (
    <Modal label={COLLECTION_UI.openingTitle} className={reduced ? 'opening opening--calm' : 'opening'} onClose={onDone}>
      <h2 className="visually-hidden">{COLLECTION_UI.openingTitle}</h2>
      {phase !== 'reveal' && (
        <div className={phase === 'bursting' ? 'opening__pack opening__pack--burst' : 'opening__pack'}>
          <SealedPack label={label} />
          <div className="opening__flash" />
          {phase === 'sealed' && (
            <button type="button" className="button button--primary opening__break" autoFocus onClick={() => setPhase('bursting')}>
              {COLLECTION_UI.breakSeal}
            </button>
          )}
        </div>
      )}
      {phase === 'reveal' && (
        <div className="opening__reveal">
          <ol className="opening__cards">
            {pulls.map((pull, index) => {
              const card = catalog.get(pull.id)
              if (!card) return null
              const isFlipped = flipped[index] ?? false
              return (
                <li key={pull.id} className={`slot slot--${pull.rarity}${isFlipped ? ' slot--flipped' : ''}`} style={{ '--slot': index } as CSSProperties}>
                  {isFlipped ? (
                    <div className="slot__inner">
                      <div className="slot__burst" />
                      <RomaCard card={card} />
                      <p className={pull.duplicate ? 'slot__badge slot__badge--duplicate' : 'slot__badge'}>
                        {pull.duplicate ? COLLECTION_UI.duplicate(pull.deniers) : COLLECTION_UI.newCard}
                      </p>
                    </div>
                  ) : (
                    <button
                      type="button"
                      ref={(element) => {
                        slots.current[index] = element
                      }}
                      className="slot__back"
                      aria-label={COLLECTION_UI.flip(index + 1)}
                      onClick={() => flip(index)}
                    >
                      <CardBack rarity={pull.rarity} />
                    </button>
                  )}
                </li>
              )
            })}
          </ol>
          <div className="opening__actions">
            {allFlipped ? (
              <button ref={doneButton} type="button" className="button button--primary" onClick={onDone}>
                {COLLECTION_UI.done}
              </button>
            ) : (
              <button type="button" className="button" onClick={() => setFlipped(pulls.map(() => true))}>
                {COLLECTION_UI.flipAll}
              </button>
            )}
          </div>
        </div>
      )}
    </Modal>
  )
}
