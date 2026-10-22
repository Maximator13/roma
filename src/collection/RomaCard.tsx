import type { PointerEvent } from 'react'
import { frenchSpacing } from '../core/typography.ts'
import { ERA_SHORT, KIND_LABEL, RARITY_LABEL } from '../data/collectionUi.ts'
import type { CardKind } from '../data/schema.ts'
import { SITE } from '../site.ts'
import type { CardView } from './catalog.ts'
import { rank } from './game.ts'

const KIND_ICON: Record<CardKind, string> = {
  person: 'M12 3a4 4 0 1 1 0 8a4 4 0 0 1 0-8zm-7 18c0-4 3.1-7 7-7s7 3 7 7z',
  place: 'M3 21h18v-2H3zm2-3h2v-7H5zm4 0h2v-7H9zm4 0h2v-7h-2zm4 0h2v-7h-2zM2 10h20L12 3z',
  relic: 'M9 2h6v2l-1 1v2c3 1 5 4 5 8c0 4-3 7-7 7s-7-3-7-7c0-4 2-7 5-8V5L9 4z',
  unit: 'M12 2l8 3v6c0 5-3.4 9.4-8 11c-4.6-1.6-8-6-8-11V5zm0 4l-3 3l3 3l3-3z',
}

export function KindIcon({ kind }: { kind: CardKind }) {
  return (
    <svg className="kind-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d={KIND_ICON[kind]} />
    </svg>
  )
}

export function cardImage(id: string, size: 'small' | 'large'): string {
  return `${SITE.base}cards/${id}${size === 'small' ? '-s' : ''}.webp`
}

function trackPointer(event: PointerEvent<HTMLDivElement>) {
  const element = event.currentTarget
  const box = element.getBoundingClientRect()
  const x = (event.clientX - box.left) / box.width
  const y = (event.clientY - box.top) / box.height
  element.style.setProperty('--mx', `${(x * 100).toFixed(1)}%`)
  element.style.setProperty('--my', `${(y * 100).toFixed(1)}%`)
  element.style.setProperty('--rx', `${((0.5 - y) * 14).toFixed(2)}deg`)
  element.style.setProperty('--ry', `${((x - 0.5) * 18).toFixed(2)}deg`)
  element.style.setProperty('--hover', '1')
}

const POINTER_PROPERTIES = ['--mx', '--my', '--rx', '--ry', '--hover']

function resetPointer(event: PointerEvent<HTMLDivElement>) {
  const element = event.currentTarget
  POINTER_PROPERTIES.forEach((name) => element.style.removeProperty(name))
}

export function RomaCard({ card, size = 'small', interactive = true }: { card: CardView; size?: 'small' | 'large'; interactive?: boolean }) {
  const pips = rank(card.rarity) + 1
  return (
    <div
      className={`rcard rcard--${card.rarity} rcard--${size}`}
      onPointerMove={interactive ? trackPointer : undefined}
      onPointerLeave={interactive ? resetPointer : undefined}
    >
      <div className="rcard__frame">
        <div className="rcard__window">
          {card.art && (
            <img
              className="rcard__art"
              src={cardImage(card.id, size)}
              alt=""
              loading="lazy"
              decoding="async"
              width={size === 'small' ? 320 : 640}
              height={size === 'small' ? 448 : 896}
            />
          )}
          <div className="rcard__shade" />
        </div>
        <div className="rcard__top">
          <span className="rcard__kind">
            <KindIcon kind={card.kind} />
            {KIND_LABEL[card.kind].one}
          </span>
          <span className="rcard__pips" aria-label={RARITY_LABEL[card.rarity]}>
            {Array.from({ length: pips }, (_, index) => (
              <span key={index} className="rcard__pip" />
            ))}
          </span>
        </div>
        <div className="rcard__plate">
          <p className="rcard__name">{card.name}</p>
          <p className="rcard__subtitle">{frenchSpacing(card.subtitle)}</p>
          <p className="rcard__meta">
            <span>{RARITY_LABEL[card.rarity]}</span>
            <span aria-hidden="true">·</span>
            <span>{ERA_SHORT[card.era]}</span>
          </p>
        </div>
        <div className="rcard__foil" />
        <div className="rcard__glare" />
      </div>
    </div>
  )
}

export function CardBack({ rarity }: { rarity?: CardView['rarity'] }) {
  return (
    <div className={rarity ? `rcard rcard--back rcard--hint-${rarity}` : 'rcard rcard--back'}>
      <div className="rcard__frame">
        <div className="rcard__backface">
          <span className="rcard__laurel" aria-hidden="true">
            SPQR
          </span>
        </div>
      </div>
    </div>
  )
}
