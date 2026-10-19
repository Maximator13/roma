import { describe, expect, it } from 'vitest'
import { scenes } from '../../data/scenes.ts'
import { CANNAE } from '../cannes/battle.ts'
import { rasterize, heightAt } from './heightfield.ts'
import { parseBattle, type Unit } from './schema.ts'
import {
  deathTimes,
  figureCount,
  lerpAngle,
  placeFigure,
  pointForTime,
  slotsFor,
  stateAt,
  sunAt,
  timeForPoint,
  trackOf,
  type UnitState,
} from './timeline.ts'

const TROOPS = ['hastatus', 'princeps', 'triarius', 'velite', 'eques', 'libyen', 'celte', 'ibere', 'frondeur', 'lonchophore', 'numide', 'cavalier']

const unit: Unit = {
  id: 'essai',
  label: 'Essai',
  side: 'rome',
  troop: 'hastatus',
  soldiers: 200,
  start: { at: [0, 0], facing: 180, width: 100, depth: 20 },
  moves: [
    { phase: 1, at: [0, -100], action: 'march' },
    { phase: 2 },
    { phase: 3, via: [[100, -100]], at: [100, 0], facing: 90, losses: 0.5, action: 'fight' },
  ],
}

describe('battle timeline', () => {
  it('interpolates between keyframes and holds in between', () => {
    const track = trackOf(unit)
    const state = {} as UnitState
    expect(stateAt(track, 0, state).y).toBe(0)
    expect(stateAt(track, 0.5, state).y).toBeCloseTo(-50)
    expect(stateAt(track, 0.5, state).action).toBe('march')
    expect(stateAt(track, 1.5, state).y).toBeCloseTo(-100)
    expect(stateAt(track, 1.5, state).action).toBe('stand')
    expect(stateAt(track, 3, state)).toMatchObject({ x: 100, y: 0, facing: 90, losses: 0.5, action: 'fight' })
    expect(stateAt(track, 2.5, state).x).toBeCloseTo(100, 0)
  })

  it('keeps every figure inside its formation', () => {
    const slots = slotsFor(10, 100, 20, 1)
    const state = stateAt(trackOf(unit), 0, {} as UnitState)
    for (const slot of slots) {
      const placed = placeFigure(state, slot, { x: 0, y: 0, heading: 0 })
      expect(Math.abs(placed.x)).toBeLessThan(52)
      expect(Math.abs(placed.y)).toBeLessThan(12)
    }
  })

  it('kills the expected share of figures by the end', () => {
    const times = deathTimes(trackOf(unit), 100, 3, 1)
    const dead = [...times].filter((time) => time <= 3).length
    expect(dead).toBe(50)
    expect(Math.min(...times)).toBeGreaterThan(2)
  })

  it('maps time and scene points both ways', () => {
    expect(pointForTime(0, 8)).toBe(0)
    expect(pointForTime(0.01, 8)).toBe(1)
    expect(pointForTime(3, 8)).toBe(4)
    expect(pointForTime(8, 8)).toBe(8)
    expect(pointForTime(timeForPoint(5, false), 8)).toBe(5)
    expect(pointForTime(timeForPoint(5, true) - 1e-4, 8)).toBe(5)
  })

  it('turns by the shortest way', () => {
    expect(lerpAngle(350, 10, 0.5)).toBeCloseTo(360)
    expect((lerpAngle(90, 270, 1) + 360) % 360).toBeCloseTo(270)
  })

  it('places the summer sun of Cannae', () => {
    const noon = sunAt(12, 41.3, 21)
    expect(noon.azimuth).toBeCloseTo(180)
    expect(noon.elevation).toBeCloseTo(69.7, 0)
    expect(sunAt(8, 41.3, 21).azimuth).toBeGreaterThan(85)
    expect(sunAt(8, 41.3, 21).azimuth).toBeLessThan(100)
  })
})

describe('height field', () => {
  it('rasterizes a sloping square', () => {
    const positions = [0, 0, 0, 10, 10, 0, 10, 10, 10, 0, 0, 10]
    const field = rasterize(positions, [0, 3, 1, 1, 3, 2], 1)
    expect(heightAt(field, 5, 5)).toBeCloseTo(5)
    expect(heightAt(field, 2.5, 7)).toBeCloseTo(2.5)
  })
})

describe('Cannae data', () => {
  const scene = scenes.find((item) => item.id === 'cannes')

  it('is a valid battle', () => {
    expect(() => parseBattle(CANNAE)).not.toThrow()
  })

  it('has one scene point per phase, in the same order', () => {
    expect(scene?.points?.map((point) => point.id)).toEqual(CANNAE.phases.map((phase) => phase.id))
  })

  it('uses only figurines made in Blender', () => {
    for (const item of CANNAE.units) expect(TROOPS).toContain(item.troop)
  })

  it('fields about 76 000 Romans and allies and 48 000 Carthaginians', () => {
    const total = (side: Unit['side']) =>
      CANNAE.units.filter((item) => item.side === side && !item.id.startsWith('garnison') && !item.id.startsWith('garde')).reduce((sum, item) => sum + item.soldiers, 0)
    expect(total('rome')).toBe(76000)
    expect(total('carthage')).toBe(48000)
  })

  it('stays within the figure budget at one figurine for 20 soldiers', () => {
    const figures = CANNAE.units.reduce((sum, item) => sum + figureCount(item, CANNAE.scale), 0)
    expect(figures).toBeGreaterThan(6000)
    expect(figures).toBeLessThan(7000)
  })
})
