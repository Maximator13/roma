import type { GameId } from '../core/route.ts'

const KEY = 'roma.progress'

export interface Progress {
  seen: string[]
  best: Partial<Record<GameId, number>>
}

function empty(): Progress {
  return { seen: [], best: {} }
}

export function readProgress(storage: Pick<Storage, 'getItem'> | undefined = globalThis.localStorage): Progress {
  try {
    const parsed: unknown = JSON.parse(storage?.getItem(KEY) ?? 'null')
    if (typeof parsed !== 'object' || parsed === null) return empty()
    const { seen, best } = parsed as Partial<Progress>
    return {
      seen: Array.isArray(seen) ? seen.filter((id): id is string => typeof id === 'string') : [],
      best: typeof best === 'object' && best !== null ? best : {},
    }
  } catch {
    return empty()
  }
}

function writeProgress(progress: Progress, storage: Pick<Storage, 'setItem'> | undefined) {
  try {
    storage?.setItem(KEY, JSON.stringify(progress))
  } catch {
    return
  }
}

export function markSeen(id: string, storage: Storage | undefined = globalThis.localStorage): Progress {
  const progress = readProgress(storage)
  if (progress.seen.includes(id)) return progress
  const next = { ...progress, seen: [...progress.seen, id] }
  writeProgress(next, storage)
  return next
}

export function recordScore(game: GameId, score: number, storage: Storage | undefined = globalThis.localStorage): Progress {
  const progress = readProgress(storage)
  if ((progress.best[game] ?? -1) >= score) return progress
  const next = { ...progress, best: { ...progress.best, [game]: score } }
  writeProgress(next, storage)
  return next
}
