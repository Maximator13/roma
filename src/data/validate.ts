import { z } from 'zod'
import { FIRST_YEAR, LAST_YEAR } from '../core/dates.ts'
import { citySchema, eraSchema, eventSchema, personSchema, placeSchema, itinerarySchema, sceneSchema, trackSchema } from './schema.ts'

export interface Dataset {
  eras: unknown[]
  tracks: unknown[]
  events: unknown[]
  places: unknown[]
  people: unknown[]
  scenes: unknown[]
  cities: unknown[]
  itineraries: unknown[]
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

const READY_SCENE_FIELDS = ['year', 'lat', 'lon', 'summary', 'points'] as const

function sceneErrors(scenes: z.infer<typeof sceneSchema>[]): string[] {
  return scenes.flatMap((scene) => {
    const missing = scene.status === 'ready' ? READY_SCENE_FIELDS.filter((field) => scene[field] === undefined) : []
    const errors = missing.map((field) => `scene ${scene.id}: ready scene without ${field}`)
    if (scene.status === 'ready' && scene.points?.length === 0) errors.push(`scene ${scene.id}: ready scene without points`)
    const pointIds = scene.points?.map((point) => point.id) ?? []
    const repeated = pointIds.filter((id, index) => pointIds.indexOf(id) !== index)
    return [...errors, ...repeated.map((id) => `scene ${scene.id}: duplicate point ${id}`)]
  })
}

function cityErrors(cities: z.infer<typeof citySchema>[], sceneIds: Set<string>): string[] {
  return cities.flatMap((city) => {
    const errors: string[] = []
    if (city.to !== undefined && city.to < city.from) errors.push(`city ${city.id}: to is before from`)
    if (city.scene && !sceneIds.has(city.scene)) errors.push(`city ${city.id}: unknown scene ${city.scene}`)
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
    ...schemaErrors('city', citySchema, dataset.cities),
    ...schemaErrors('itinerary', itinerarySchema, dataset.itineraries),
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
    cities: dataset.cities.map((item) => citySchema.parse(item)),
    itineraries: dataset.itineraries.map((item) => itinerarySchema.parse(item)),
  }
  return [
    ...textProblems,
    ...duplicateErrors('era', data.eras),
    ...duplicateErrors('track', data.tracks),
    ...duplicateErrors('event', data.events),
    ...duplicateErrors('place', data.places),
    ...duplicateErrors('person', data.people),
    ...duplicateErrors('scene', data.scenes),
    ...duplicateErrors('city', data.cities),
    ...duplicateErrors('itinerary', data.itineraries),
    ...sceneErrors(data.scenes),
    ...cityErrors(data.cities, new Set(data.scenes.map((scene) => scene.id))),
    ...eraContinuityErrors(data.eras),
    ...referenceErrors(data),
  ]
}
