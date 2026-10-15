import { z } from 'zod'
import { FIRST_YEAR, LAST_YEAR } from '../core/dates.ts'

export const ERA_IDS = [
  'royaute',
  'republique',
  'haut-empire',
  'crise-du-iiie-siecle',
  'bas-empire',
  'empire-romain-d-orient',
] as const

export const TRACK_IDS = [
  'rome',
  'occident',
  'orient',
  'empire-des-gaules',
  'palmyre',
  'empire-latin',
  'nicee',
  'epire',
  'trebizonde',
] as const

export const CERTAINTIES = ['attested', 'traditional', 'legendary', 'debated'] as const
export const CATEGORIES = ['politics', 'war', 'building', 'religion', 'society', 'culture'] as const
export const PRECISIONS = ['day', 'month', 'year', 'decade', 'century'] as const

const slug = z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, 'expected a lowercase ascii slug')
const label = z.string().trim().min(1)
const projectYear = z.number().int().min(FIRST_YEAR).max(LAST_YEAR)
const anyYear = z.number().int()

export const sourceSchema = z.strictObject({
  kind: z.enum(['ancient', 'modern']),
  author: label,
  work: label,
  locus: label.optional(),
  url: z.url().optional(),
})

export const eventSchema = z
  .strictObject({
    id: slug,
    title: label.max(90),
    start: projectYear,
    end: projectYear.optional(),
    month: z.number().int().min(1).max(12).optional(),
    day: z.number().int().min(1).max(31).optional(),
    precision: z.enum(PRECISIONS),
    certainty: z.enum(CERTAINTIES),
    certaintyNote: label.optional(),
    era: z.enum(ERA_IDS),
    track: z.enum(TRACK_IDS),
    category: z.enum(CATEGORIES),
    importance: z.union([z.literal(1), z.literal(2), z.literal(3)]),
    placeId: slug.optional(),
    people: z.array(slug).optional(),
    summary: label.max(450),
    body: label,
    sources: z.array(sourceSchema).min(1),
    scene: slug.optional(),
  })
  .refine((event) => event.end === undefined || event.end >= event.start, 'end is before start')
  .refine(
    (event) => (event.precision === 'day' || event.precision === 'month') === (event.month !== undefined),
    'month is required exactly for day and month precision',
  )
  .refine((event) => (event.precision === 'day') === (event.day !== undefined), 'day is required exactly for day precision')

export const eraSchema = z.strictObject({
  id: z.enum(ERA_IDS),
  name: label,
  start: projectYear,
  end: projectYear,
  summary: label,
  boundsNote: label,
})

export const trackSchema = z.strictObject({
  id: z.enum(TRACK_IDS),
  name: label,
  lane: z.number().int().min(0).max(4),
  spans: z.array(z.strictObject({ start: projectYear, end: projectYear })).min(1),
  note: label.optional(),
})

export const placeSchema = z.strictObject({
  id: slug,
  name: label,
  ancientName: label.optional(),
  lat: z.number().min(-90).max(90),
  lon: z.number().min(-180).max(180),
  pleiadesId: z.number().int().positive().optional(),
})

export const personSchema = z.strictObject({
  id: slug,
  name: label,
  role: label,
  born: anyYear.optional(),
  died: anyYear.optional(),
  certainty: z.enum(CERTAINTIES),
})

export const citySchema = z.strictObject({
  id: slug,
  name: label,
  ancientName: label.optional(),
  lat: z.number().min(-90).max(90),
  lon: z.number().min(-180).max(180),
  pleiadesId: z.number().int().positive().optional(),
  from: anyYear,
  to: anyYear.optional(),
  importance: z.union([z.literal(1), z.literal(2), z.literal(3)]),
  note: label,
  scene: slug.optional(),
})

export const waypointSchema = z.strictObject({
  lon: z.number().min(-180).max(180),
  lat: z.number().min(-90).max(90),
  label: label.optional(),
  year: anyYear,
  month: z.number().int().min(1).max(12).optional(),
  certainty: z.enum(CERTAINTIES),
  note: label.optional(),
})

export const itinerarySchema = z.strictObject({
  id: slug,
  title: label,
  summary: label,
  from: projectYear,
  to: projectYear,
  waypoints: z.array(waypointSchema).min(2),
  sources: z.array(label).min(1),
})

export const sceneSchema = z.strictObject({
  id: slug,
  title: label,
  status: z.enum(['planned', 'ready']),
})

export type EraId = (typeof ERA_IDS)[number]
export type TrackId = (typeof TRACK_IDS)[number]
export type Certainty = (typeof CERTAINTIES)[number]
export type Category = (typeof CATEGORIES)[number]
export type Source = z.infer<typeof sourceSchema>
export type HistoricalEvent = z.infer<typeof eventSchema>
export type Era = z.infer<typeof eraSchema>
export type Track = z.infer<typeof trackSchema>
export type Place = z.infer<typeof placeSchema>
export type Person = z.infer<typeof personSchema>
export type Scene = z.infer<typeof sceneSchema>
export type City = z.infer<typeof citySchema>
export type Waypoint = z.infer<typeof waypointSchema>
export type Itinerary = z.infer<typeof itinerarySchema>
