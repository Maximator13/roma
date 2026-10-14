import { z } from 'zod'
import { FIRST_YEAR, LAST_YEAR } from '../core/dates.ts'
import { eraSchema, eventSchema, personSchema, placeSchema, sceneSchema, trackSchema } from './schema.ts'

export interface Dataset {
  eras: unknown[]
  tracks: unknown[]
  events: unknown[]
  places: unknown[]
  people: unknown[]
  scenes: unknown[]
}

const forbiddenDash = new RegExp(`[${String.fromCharCode(0x2013, 0x2014)}]`)

function schemaErrors(name: string, schema: z.ZodType, items: unknown[]): string[] {
  return items.flatMap((item, index) => {
    const result = schema.safeParse(item)
    if (result.success) return []
    const id = typeof item === 'object' && item !== null && 'id' in item ? String(item.id) : `#${index}`
    return result.error.issues.map((issue) => `${name} ${id}: ${issue.path.join('.') || '(root)'} ${issue.message}`)
  })
}

function duplicateErrors(name: string, items: { id: string }[]): string[] {
  const seen = new Set<string>()
  return items.flatMap((item) => {
    if (seen.has(item.id)) return [`${name} ${item.id}: duplicate id`]
    seen.add(item.id)
    return []
  })
}

function dashErrors(value: unknown, path: string): string[] {
  if (typeof value === 'string') return forbiddenDash.test(value) ? [`${path}: em or en dash`] : []
  if (Array.isArray(value)) return value.flatMap((item, index) => dashErrors(item, `${path}[${index}]`))
  if (typeof value === 'object' && value !== null) {
    return Object.entries(value).flatMap(([key, item]) => dashErrors(item, `${path}.${key}`))
  }
  return []
}

function eraContinuityErrors(eras: z.infer<typeof eraSchema>[]): string[] {
  const errors: string[] = []
  if (eras[0]?.start !== FIRST_YEAR) errors.push(`eras: first era must start in ${FIRST_YEAR}`)
  if (eras.at(-1)?.end !== LAST_YEAR) errors.push(`eras: last era must end in ${LAST_YEAR}`)
  eras.slice(1).forEach((era, index) => {
    const previous = eras[index]
    if (previous && previous.end !== era.start) errors.push(`eras: ${previous.id} must end where ${era.id} starts`)
  })
  return errors
}

function referenceErrors(data: {
  eras: z.infer<typeof eraSchema>[]
  tracks: z.infer<typeof trackSchema>[]
  events: z.infer<typeof eventSchema>[]
  places: z.infer<typeof placeSchema>[]
  people: z.infer<typeof personSchema>[]
  scenes: z.infer<typeof sceneSchema>[]
}): string[] {
  const placeIds = new Set(data.places.map((place) => place.id))
  const personIds = new Set(data.people.map((person) => person.id))
  const sceneIds = new Set(data.scenes.map((scene) => scene.id))
  return data.events.flatMap((event) => {
    const errors: string[] = []
    const era = data.eras.find((candidate) => candidate.id === event.era)
    if (!era || event.start < era.start || event.start > era.end) errors.push(`event ${event.id}: start outside era ${event.era}`)
    const track = data.tracks.find((candidate) => candidate.id === event.track)
    const trackActive = track?.spans.some((span) => event.start >= span.start && event.start <= span.end)
    if (!trackActive) errors.push(`event ${event.id}: track ${event.track} inactive at start`)
    if (event.placeId && !placeIds.has(event.placeId)) errors.push(`event ${event.id}: unknown place ${event.placeId}`)
    event.people?.forEach((person) => {
      if (!personIds.has(person)) errors.push(`event ${event.id}: unknown person ${person}`)
    })
    if (event.scene && !sceneIds.has(event.scene)) errors.push(`event ${event.id}: unknown scene ${event.scene}`)
    return errors
  })
}

export function validateDataset(dataset: Dataset): string[] {
  const schemaProblems = [
    ...schemaErrors('era', eraSchema, dataset.eras),
    ...schemaErrors('track', trackSchema, dataset.tracks),
    ...schemaErrors('event', eventSchema, dataset.events),
    ...schemaErrors('place', placeSchema, dataset.places),
    ...schemaErrors('person', personSchema, dataset.people),
    ...schemaErrors('scene', sceneSchema, dataset.scenes),
  ]
  const textProblems = dashErrors(dataset, 'data')
  if (schemaProblems.length > 0) return [...schemaProblems, ...textProblems]
  const data = {
    eras: dataset.eras.map((item) => eraSchema.parse(item)),
    tracks: dataset.tracks.map((item) => trackSchema.parse(item)),
    events: dataset.events.map((item) => eventSchema.parse(item)),
    places: dataset.places.map((item) => placeSchema.parse(item)),
    people: dataset.people.map((item) => personSchema.parse(item)),
    scenes: dataset.scenes.map((item) => sceneSchema.parse(item)),
  }
  return [
    ...textProblems,
    ...duplicateErrors('era', data.eras),
    ...duplicateErrors('track', data.tracks),
    ...duplicateErrors('event', data.events),
    ...duplicateErrors('place', data.places),
    ...duplicateErrors('person', data.people),
    ...duplicateErrors('scene', data.scenes),
    ...eraContinuityErrors(data.eras),
    ...referenceErrors(data),
  ]
}
