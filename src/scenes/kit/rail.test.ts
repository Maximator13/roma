import { Box3, Vector3 } from 'three'
import { describe, expect, it } from 'vitest'
import { clampLook, lookDirection, overviewStop, stopFromMarker, travelCurve, travelSeconds } from './rail.ts'

const near = { position: new Vector3(0, 2, 0), target: new Vector3(0, 2, -50) }
const far = { position: new Vector3(1200, 2, 0), target: new Vector3(1200, 2, -50) }

describe('travel between stops', () => {
  it('scales the duration with the distance within bounds', () => {
    expect(travelSeconds(near, near)).toBe(2.4)
    expect(travelSeconds(near, far)).toBeCloseTo(1.6 + 1200 / 280)
    expect(travelSeconds(near, { ...far, position: new Vector3(9000, 2, 0) })).toBe(6.5)
  })

  it('lifts the path like a crane between both ends', () => {
    const curve = travelCurve(near, far)
    expect(curve.getPoint(0).distanceTo(near.position)).toBeLessThan(1e-6)
    expect(curve.getPoint(1).distanceTo(far.position)).toBeLessThan(1e-6)
    expect(curve.getPoint(0.5).y).toBeGreaterThan(150)
  })
})

describe('free look', () => {
  it('keeps the gaze within its limits', () => {
    expect(clampLook(2, -2)).toEqual({ yaw: 0.45, pitch: -0.22 })
    expect(clampLook(0.1, 0.1)).toEqual({ yaw: 0.1, pitch: 0.1 })
  })

  it('turns the gaze around the vertical axis', () => {
    const straight = lookDirection(near.position, near.target, 0, 0)
    expect(straight.z).toBeCloseTo(-1)
    const turned = lookDirection(near.position, near.target, Math.PI / 2, 0)
    expect(turned.x).toBeCloseTo(-1)
    expect(turned.length()).toBeCloseTo(1)
  })
})

describe('stops', () => {
  it('aims a marker stop along its forward direction', () => {
    const stop = stopFromMarker(new Vector3(10, 2, 0), new Vector3(0, 0, -3), 20)
    expect(stop.target.toArray()).toEqual([10, 2, -20])
  })

  it('places the overview above the model, looking at its centre', () => {
    const stop = overviewStop(new Box3(new Vector3(-1000, 0, -1000), new Vector3(1000, 100, 1000)), 180, 40)
    expect(stop.position.z).toBeGreaterThan(0)
    expect(stop.position.y).toBeGreaterThan(500)
    expect(stop.target.toArray()).toEqual([0, 0, 0])
  })
})
