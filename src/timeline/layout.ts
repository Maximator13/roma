export type Importance = 1 | 2 | 3

export interface LabelCandidate {
  id: string
  x: number
  width: number
  importance: Importance
  start: number
}

export interface LabelSlot {
  id: string
  row: number | null
}

export function importanceThreshold(span: number): Importance {
  if (span > 700) return 1
  if (span > 160) return 2
  return 3
}

export function isVisibleAt(importance: Importance, span: number): boolean {
  return importance <= importanceThreshold(span)
}

function overlaps(intervals: [number, number][], from: number, to: number): boolean {
  return intervals.some(([start, end]) => from < end && to > start)
}

export function placeLabels(candidates: LabelCandidate[], rowCount: number, gap = 12): LabelSlot[] {
  const rows: [number, number][][] = Array.from({ length: rowCount }, () => [])
  const ordered = [...candidates].sort((a, b) => a.importance - b.importance || a.start - b.start)
  const slots = new Map<string, number | null>()
  for (const candidate of ordered) {
    const from = candidate.x - gap / 2
    const to = candidate.x + candidate.width + gap / 2
    const row = rows.findIndex((intervals) => !overlaps(intervals, from, to))
    if (row >= 0) rows[row]!.push([from, to])
    slots.set(candidate.id, row >= 0 ? row : null)
  }
  return candidates.map((candidate) => ({ id: candidate.id, row: slots.get(candidate.id) ?? null }))
}

export function estimateLabelWidth(text: string, characterWidth = 7.4): number {
  return Math.ceil(text.length * characterWidth) + 18
}
