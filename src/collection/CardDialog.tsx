import { frenchSpacing } from '../core/typography.ts'
import { COLLECTION_UI, ERA_SHORT, KIND_LABEL, RARITY_LABEL } from '../data/collectionUi.ts'
import type { CardView } from './catalog.ts'
import { CRAFT_COST } from './game.ts'
import { Modal } from './Modal.tsx'
import { CardBack, RomaCard } from './RomaCard.tsx'

function sourceLine(source: CardView['sources'][number]): string {
  return [source.author, source.work, source.locus].filter(Boolean).join(', ')
}

export function CardDialog({
  card,
  owned,
  deniers,
  onCraft,
  onClose,
}: {
  card: CardView
  owned: boolean
  deniers: number
  onCraft: () => void
  onClose: () => void
}) {
  const cost = CRAFT_COST[card.rarity]
  return (
    <Modal label={card.name} className="card-dialog" onClose={onClose}>
      <button type="button" className="card-dialog__close" onClick={onClose} aria-label={COLLECTION_UI.close} autoFocus>
        ×
      </button>
      <div className="card-dialog__card">{owned ? <RomaCard card={card} size="large" /> : <CardBack rarity={card.rarity} />}</div>
      <div className="card-dialog__body">
        <p className={`card-dialog__kicker rarity-ink--${card.rarity}`}>
          {RARITY_LABEL[card.rarity]} · {KIND_LABEL[card.kind].one} · {ERA_SHORT[card.era]}
        </p>
        <h2 className="card-dialog__title">{card.name}</h2>
        <p className="card-dialog__subtitle">
          {frenchSpacing(card.subtitle)}
          {card.dateLabel && <span> ({frenchSpacing(card.dateLabel)})</span>}
        </p>
        {owned ? (
          <>
            <p className="card-dialog__text">{frenchSpacing(card.text)}</p>
            <h3 className="card-dialog__heading">{COLLECTION_UI.sources}</h3>
            <ul className="card-dialog__sources">
              {card.sources.map((source) => (
                <li key={sourceLine(source)}>{frenchSpacing(sourceLine(source))}</li>
              ))}
            </ul>
            {card.art && (
              <>
                <h3 className="card-dialog__heading">{COLLECTION_UI.illustration}</h3>
                <p className="card-dialog__credit">
                  {card.art.sourceUrl ? (
                    <a href={card.art.sourceUrl} target="_blank" rel="noopener noreferrer">
                      {card.art.title}
                    </a>
                  ) : (
                    card.art.title
                  )}
                  {`, ${card.art.creator}`}
                  {card.art.date && `, ${card.art.date}`}
                  {', '}
                  {card.art.licenseUrl ? (
                    <a href={card.art.licenseUrl} target="_blank" rel="noopener noreferrer license">
                      {card.art.license}
                    </a>
                  ) : (
                    card.art.license
                  )}
                </p>
              </>
            )}
            {card.scene && (
              <a className="button card-dialog__scene" href={`#/scene/${card.scene}`}>
                {COLLECTION_UI.visitScene}
              </a>
            )}
          </>
        ) : (
          <>
            <p className="card-dialog__text card-dialog__text--missing">{COLLECTION_UI.missing}</p>
            <button type="button" className="button button--primary" disabled={deniers < cost} onClick={onCraft}>
              {COLLECTION_UI.craft(cost)}
            </button>
            {deniers < cost && <p className="card-dialog__hint">{COLLECTION_UI.craftShort(cost, deniers)}</p>}
          </>
        )}
      </div>
    </Modal>
  )
}
