import { z } from 'zod'

export const SIDES = ['rome', 'carthage'] as const
export const ACTIONS = ['stand', 'march', 'charge', 'fight', 'skirmish', 'flee'] as const
export const ARROW_KINDS = ['move', 'attack', 'flee'] as const

const slug = z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, 'expected a lowercase ascii slug')
const label = z.string().trim().min(1)
const point = z.tuple([z.number(), z.number()])

const stateFields = {
  at: point,
  facing: z.number().min(-360).max(720),
  width: z.number().positive(),
  depth: z.number().positive(),
  bulge: z.number(),
  action: z.enum(ACTIONS),
  losses: z.number().min(0).max(1),
}

export const unitStartSchema = z.strictObject({
  ...stateFields,
  bulge: stateFields.bulge.optional(),
  action: stateFields.action.optional(),
  losses: stateFields.losses.optional(),
})

export const keyframeSchema = z
  .strictObject({
    phase: z.number().int().min(1),
    via: z.array(point).min(1).optional(),
    at: stateFields.at.optional(),
    facing: stateFields.facing.optional(),
    width: stateFields.width.optional(),
    depth: stateFields.depth.optional(),
    bulge: stateFields.bulge.optional(),
    action: stateFields.action.optional(),
    losses: stateFields.losses.optional(),
  })
  .refine((frame) => frame.via === undefined || frame.at !== undefined, 'via needs a destination')

export const unitSchema = z
  .strictObject({
    id: slug,
    label,
    side: z.enum(SIDES),
    troop: slug,
    soldiers: z.number().int().positive(),
    labelled: z.boolean().optional(),
    start: unitStartSchema,
    moves: z.array(keyframeSchema),
  })
  .refine(
    (unit) => unit.moves.every((frame, index) => index === 0 || frame.phase > unit.moves[index - 1]!.phase),
    'moves must be in strictly increasing phase order',
  )

export const arrowSchema = z.strictObject({
  side: z.enum(SIDES),
  kind: z.enum(ARROW_KINDS),
  path: z.array(point).min(2),
})

export const counterSchema = z.strictObject({
  label,
  from: z.number().int().min(0),
  to: z.number().int().min(0),
})

export const phaseSchema = z.strictObject({
  id: slug,
  hour: z.number().min(0).max(24),
  clock: label,
  seconds: z.number().positive(),
  focus: point,
  span: z.number().positive(),
  ground: z.strictObject({ unit: slug, along: z.number(), across: z.number(), look: z.number().positive(), turn: z.number().optional() }),
  arrows: z.array(arrowSchema),
  counters: z.array(counterSchema).optional(),
})

export const battleSchema = z
  .strictObject({
    scale: z.number().int().positive(),
    latitude: z.number().min(-90).max(90),
    declination: z.number().min(-24).max(24),
    tacticalScale: z.number().min(1),
    sides: z.strictObject({ rome: label, carthage: label }),
    phases: z.array(phaseSchema).min(1),
    units: z.array(unitSchema).min(1),
  })
  .refine(
    (battle) => battle.units.every((unit) => unit.moves.every((frame) => frame.phase <= battle.phases.length)),
    'a move refers to a phase that does not exist',
  )
  .refine((battle) => new Set(battle.units.map((unit) => unit.id)).size === battle.units.length, 'duplicate unit id')
  .refine((battle) => battle.phases.every((phase) => battle.units.some((unit) => unit.id === phase.ground.unit)), 'ground view on an unknown unit')
  .refine((battle) => new Set(battle.phases.map((phase) => phase.id)).size === battle.phases.length, 'duplicate phase id')

export type Point = z.infer<typeof point>
export type Side = (typeof SIDES)[number]
export type Action = (typeof ACTIONS)[number]
export type Keyframe = z.infer<typeof keyframeSchema>
export type Unit = z.infer<typeof unitSchema>
export type Arrow = z.infer<typeof arrowSchema>
export type Counter = z.infer<typeof counterSchema>
export type Phase = z.infer<typeof phaseSchema>
export type Battle = z.infer<typeof battleSchema>

export function parseBattle(input: unknown): Battle {
  return battleSchema.parse(input)
}
