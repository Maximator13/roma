import { Vector3 } from 'three'
import { describe, expect, it } from 'vitest'
import { groupRoutes, pingPong, pointAlong, routeFrom, walkerCount } from './paths.ts'

const route = routeFrom([new Vector3(0, 0, 0), new Vector3(10, 0, 0), new Vector3(10, 0, 20)])

describe('routes', () => {
  it('measures a polyline', () => {
    expect(route.total).toBe(30)
    expect(route.lengths).toEqual([0, 10, 30])
  })

  it('finds a point along the route', () => {
    expect(pointAlong(route, 5).point.toArray()).toEqual([5, 0, 0])
    expect(pointAlong(route, 20).point.toArray()).toEqual([10, 0, 10])
    expect(pointAlong(route, 99).point.toArray()).toEqual([10, 0, 20])
  })

  it('walks back and forth', () => {
    expect(pingPong(10, 30)).toEqual({ distance: 10, forward: true })
    expect(pingPong(40, 30)).toEqual({ distance: 20, forward: false })
    expect(pingPong(-5, 30)).toEqual({ distance: 5, forward: false })
  })

  it('groups numbered markers into ordered routes', () => {
    const routes = groupRoutes(
      [
        { name: 'walk_forum_01', position: new Vector3(1, 0, 0) },
        { name: 'walk_forum_00', position: new Vector3(0, 0, 0) },
        { name: 'walk_via_00', position: new Vector3(5, 0, 0) },
        { name: 'poi_forum', position: new Vector3(9, 0, 0) },
      ],
      'walk_',
    )
    expect([...routes.keys()]).toEqual(['forum', 'via'])
    expect(routes.get('forum')?.map((point) => point.x)).toEqual([0, 1])
  })

  it('spaces walkers within bounds', () => {
    expect(walkerCount(300, 25, 10)).toBe(10)
    expect(walkerCount(10, 25, 10)).toBe(1)
  })
})
