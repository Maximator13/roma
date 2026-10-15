import { Billboard, Line, Text } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { AdditiveBlending, DoubleSide, Vector3, type Group, type Mesh, type MeshBasicMaterial } from 'three'
import type { Line2 } from 'three-stdlib'
import cinzelUrl from '@fontsource/cinzel/files/cinzel-latin-600-normal.woff?url'
import garamondItalicUrl from '@fontsource/eb-garamond/files/eb-garamond-latin-400-italic.woff?url'
import { prefersReducedMotion } from '../core/motion.ts'
import { cities } from '../data/cities.ts'
import { events } from '../data/events.ts'
import { itineraries } from '../data/itineraries.ts'
import { places } from '../data/places.ts'
import type { City, HistoricalEvent, Itinerary } from '../data/schema.ts'
import { isVisibleAt } from '../timeline/layout.ts'
import { useApp } from '../store.ts'
import { project } from './geo.ts'
import type { HeightSampler } from './reliefSampler.ts'

const LABEL_SCALE = 0.016
const FADE_SECONDS = 0.6
const LIFT = 0.03
const PATH_STEPS_PER_LEG = 24

function pointOnMap(lon: number, lat: number, height: HeightSampler): Vector3 {
  const point = project(lon, lat)
  return new Vector3(point.x, height(lon, lat) + LIFT, point.z)
}

function importanceLimit(distance: number): number {
  if (distance > 26) return 1
  if (distance > 11) return 2
  return 3
}

function fade(current: number, target: number, delta: number, reducedMotion: boolean): number {
  if (reducedMotion) return target
  const step = delta / FADE_SECONDS
  return target > current ? Math.min(target, current + step) : Math.max(target, current - step)
}

function CityLabel({ city, height }: { city: City; height: HeightSampler }) {
  const group = useRef<Group>(null)
  const label = useRef<{ fillOpacity: number; outlineOpacity: number } | null>(null)
  const dot = useRef<Mesh>(null)
  const opacity = useRef(0)
  const position = useMemo(() => pointOnMap(city.lon, city.lat, height), [city, height])
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])

  useFrame(({ camera }, delta) => {
    const year = useApp.getState().view.center
    const distance = camera.position.distanceTo(position)
    const alive = year >= city.from && year <= (city.to ?? Infinity)
    const target = alive && city.importance <= importanceLimit(distance) ? 1 : 0
    opacity.current = fade(opacity.current, target, delta, reducedMotion)
    const current = group.current
    if (!current) return
    current.visible = opacity.current > 0.01
    current.scale.setScalar(distance * LABEL_SCALE)
    if (label.current) {
      label.current.fillOpacity = opacity.current
      label.current.outlineOpacity = opacity.current * 0.8
    }
    if (dot.current) (dot.current.material as MeshBasicMaterial).opacity = opacity.current
  })

  return (
    <group ref={group} position={position} visible={false}>
      <mesh ref={dot} rotation-x={-Math.PI / 2}>
        <circleGeometry args={[city.importance === 1 ? 0.22 : 0.15, 20]} />
        <meshBasicMaterial color="#fff2cf" transparent opacity={0} depthWrite={false} />
      </mesh>
      <Billboard position={[0, 0.9, 0]}>
        <Text
          ref={label}
          font={cinzelUrl}
          fontSize={city.importance === 1 ? 0.95 : 0.72}
          color="#f6ead2"
          outlineWidth={0.06}
          outlineColor="#1b130c"
          anchorX="center"
          anchorY="bottom"
          fillOpacity={0}
          outlineOpacity={0}
        >
          {city.name}
        </Text>
      </Billboard>
    </group>
  )
}

function CityLabels({ height }: { height: HeightSampler }) {
  return (
    <>
      {cities.map((city) => (
        <CityLabel key={city.id} city={city} height={height} />
      ))}
    </>
  )
}

function selectedEventPlace() {
  const { route } = useApp.getState()
  if (route.name !== 'event') return null
  const event = events.find((candidate) => candidate.id === route.id)
  const place = places.find((candidate) => candidate.id === event?.placeId)
  return event && place ? { event, place } : null
}

function EventMarker({ height }: { height: HeightSampler }) {
  const group = useRef<Group>(null)
  const ring = useRef<Mesh>(null)
  const halo = useRef<Mesh>(null)
  const label = useRef<{ text: string; fillOpacity: number; outlineOpacity: number; sync: () => void } | null>(null)
  const shown = useRef('')
  const opacity = useRef(0)
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])

  useFrame(({ camera, clock }, delta) => {
    const current = group.current
    if (!current) return
    const selection = selectedEventPlace()
    opacity.current = fade(opacity.current, selection ? 1 : 0, delta, reducedMotion)
    current.visible = opacity.current > 0.01
    if (!selection) return
    const position = pointOnMap(selection.place.lon, selection.place.lat, height)
    current.position.copy(position)
    current.scale.setScalar(camera.position.distanceTo(position) * LABEL_SCALE)
    const pulse = reducedMotion ? 0.5 : (clock.elapsedTime * 0.7) % 1
    ring.current?.scale.setScalar(1 + pulse * 2.4)
    if (ring.current) (ring.current.material as MeshBasicMaterial).opacity = (1 - pulse) * opacity.current
    if (halo.current) (halo.current.material as MeshBasicMaterial).opacity = 0.9 * opacity.current
    if (label.current) {
      const name = selection.place.name.split(' (')[0] ?? selection.place.name
      if (shown.current !== name) {
        shown.current = name
        label.current.text = name
        label.current.sync()
      }
      label.current.fillOpacity = opacity.current
      label.current.outlineOpacity = opacity.current * 0.8
    }
  })

  return (
    <group ref={group} visible={false}>
      <mesh ref={halo} rotation-x={-Math.PI / 2}>
        <circleGeometry args={[0.32, 32]} />
        <meshBasicMaterial color="#ffd27a" transparent opacity={0} blending={AdditiveBlending} depthWrite={false} />
      </mesh>
      <mesh ref={ring} rotation-x={-Math.PI / 2}>
        <ringGeometry args={[0.45, 0.6, 48]} />
        <meshBasicMaterial color="#ffd27a" transparent opacity={0} side={DoubleSide} blending={AdditiveBlending} depthWrite={false} />
      </mesh>
      <Billboard position={[0, 1.3, 0]}>
        <Text
          ref={label}
          font={garamondItalicUrl}
          fontSize={1.25}
          color="#ffe3a8"
          outlineWidth={0.07}
          outlineColor="#1b130c"
          anchorX="center"
          anchorY="bottom"
          fillOpacity={0}
          outlineOpacity={0}
        >
          {' '}
        </Text>
      </Billboard>
    </group>
  )
}

const PIN_WINDOW = 0.07

function EventPin({ event, lon, lat, height }: { event: HistoricalEvent; lon: number; lat: number; height: HeightSampler }) {
  const group = useRef<Group>(null)
  const label = useRef<{ fillOpacity: number; outlineOpacity: number } | null>(null)
  const pin = useRef<Mesh>(null)
  const opacity = useRef(0)
  const position = useMemo(() => pointOnMap(lon, lat, height), [lon, lat, height])
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])

  useFrame(({ camera }, delta) => {
    const { view, route } = useApp.getState()
    const selected = route.name === 'event' && route.id === event.id
    const near = Math.abs(event.start - view.center) <= Math.max(3, view.span * PIN_WINDOW)
    const target = !selected && near && isVisibleAt(event.importance, view.span) ? 1 : 0
    opacity.current = fade(opacity.current, target, delta, reducedMotion)
    const current = group.current
    if (!current) return
    current.visible = opacity.current > 0.01
    current.scale.setScalar(camera.position.distanceTo(position) * LABEL_SCALE)
    if (label.current) {
      label.current.fillOpacity = opacity.current
      label.current.outlineOpacity = opacity.current * 0.8
    }
    if (pin.current) (pin.current.material as MeshBasicMaterial).opacity = opacity.current
  })

  return (
    <group ref={group} position={position} visible={false}>
      <mesh ref={pin} rotation-x={-Math.PI / 2} rotation-z={Math.PI / 4}>
        <planeGeometry args={[0.32, 0.32]} />
        <meshBasicMaterial color="#ffc978" transparent opacity={0} side={DoubleSide} depthWrite={false} />
      </mesh>
      <Billboard position={[0, -0.35, 0]}>
        <Text
          ref={label}
          font={garamondItalicUrl}
          fontSize={0.72}
          maxWidth={9}
          textAlign="center"
          color="#ffe7bd"
          outlineWidth={0.06}
          outlineColor="#1b130c"
          anchorX="center"
          anchorY="top"
          fillOpacity={0}
          outlineOpacity={0}
        >
          {event.title}
        </Text>
      </Billboard>
    </group>
  )
}

function EventPins({ height }: { height: HeightSampler }) {
  const located = useMemo(
    () =>
      events.flatMap((event) => {
        const place = places.find((candidate) => candidate.id === event.placeId)
        return place ? [{ event, lon: place.lon, lat: place.lat }] : []
      }),
    [],
  )
  return (
    <>
      {located.map(({ event, lon, lat }) => (
        <EventPin key={event.id} event={event} lon={lon} lat={lat} height={height} />
      ))}
    </>
  )
}

function waypointTime(waypoint: Itinerary['waypoints'][number]): number {
  return waypoint.year + ((waypoint.month ?? 6) - 0.5) / 12
}

function densePath(itinerary: Itinerary, height: HeightSampler): { points: Vector3[]; times: number[] } {
  const points: Vector3[] = []
  const times: number[] = []
  itinerary.waypoints.slice(1).forEach((to, index) => {
    const from = itinerary.waypoints[index]!
    for (let step = 0; step < PATH_STEPS_PER_LEG; step += 1) {
      const t = step / PATH_STEPS_PER_LEG
      const lon = from.lon + (to.lon - from.lon) * t
      const lat = from.lat + (to.lat - from.lat) * t
      points.push(pointOnMap(lon, lat, height).add(new Vector3(0, 0.02, 0)))
      times.push(waypointTime(from) + (waypointTime(to) - waypointTime(from)) * t)
    }
  })
  const last = itinerary.waypoints.at(-1)!
  points.push(pointOnMap(last.lon, last.lat, height).add(new Vector3(0, 0.02, 0)))
  times.push(waypointTime(last))
  return { points, times }
}

function ItineraryPath({ itinerary, height }: { itinerary: Itinerary; height: HeightSampler }) {
  const path = useMemo(() => densePath(itinerary, height), [itinerary, height])
  const line = useRef<Line2>(null)
  const ghost = useRef<Line2>(null)
  const head = useRef<Mesh>(null)
  const label = useRef<{ text: string; fillOpacity: number; outlineOpacity: number; sync: () => void } | null>(null)
  const labelGroup = useRef<Group>(null)
  const shown = useRef('')
  const opacity = useRef(0)
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])
  const start = waypointTime(itinerary.waypoints[0]!)
  const end = waypointTime(itinerary.waypoints.at(-1)!)

  useFrame(({ camera, clock }, delta) => {
    const year = useApp.getState().view.center + 0.5
    const active = year >= start - 1.5 && year <= end + 1.5
    opacity.current = fade(opacity.current, active ? 1 : 0, delta, reducedMotion)
    const reached = path.times.findLastIndex((time) => time <= year)
    const segments = Math.max(0, reached)
    for (const target of [line.current, ghost.current]) {
      if (!target) continue
      target.visible = opacity.current > 0.01
    }
    if (line.current) {
      line.current.geometry.instanceCount = segments
      line.current.material.opacity = opacity.current
      line.current.material.dashOffset = reducedMotion ? 0 : -clock.elapsedTime * 0.6
    }
    if (ghost.current) ghost.current.material.opacity = 0.25 * opacity.current
    const headPoint = path.points[Math.max(0, Math.min(path.points.length - 1, reached))]!
    if (head.current) {
      head.current.visible = opacity.current > 0.01 && reached >= 0
      head.current.position.copy(headPoint)
      head.current.scale.setScalar(camera.position.distanceTo(headPoint) * LABEL_SCALE * (1 + 0.25 * Math.sin(clock.elapsedTime * 4)))
      ;(head.current.material as MeshBasicMaterial).opacity = opacity.current
    }
    const lastWaypoint = itinerary.waypoints.filter((waypoint) => waypointTime(waypoint) <= year && waypoint.label).at(-1)
    if (labelGroup.current && label.current) {
      labelGroup.current.visible = opacity.current > 0.01 && Boolean(lastWaypoint)
      if (lastWaypoint?.label) {
        const position = pointOnMap(lastWaypoint.lon, lastWaypoint.lat, height)
        labelGroup.current.position.copy(position)
        labelGroup.current.scale.setScalar(camera.position.distanceTo(position) * LABEL_SCALE)
        if (shown.current !== lastWaypoint.label) {
          shown.current = lastWaypoint.label
          label.current.text = lastWaypoint.label
          label.current.sync()
        }
      }
      label.current.fillOpacity = opacity.current
      label.current.outlineOpacity = opacity.current * 0.8
    }
  })

  return (
    <>
      <Line ref={ghost} points={path.points} color="#e8a07a" lineWidth={1.5} transparent opacity={0} dashed dashSize={0.12} gapSize={0.1} depthTest={false} renderOrder={2} />
      <Line ref={line} points={path.points} color="#ff8a5c" lineWidth={3.5} transparent opacity={0} dashed dashSize={0.3} gapSize={0.12} depthTest={false} renderOrder={3} />
      <mesh ref={head} visible={false}>
        <sphereGeometry args={[0.35, 16, 12]} />
        <meshBasicMaterial color="#ffb47a" transparent opacity={0} blending={AdditiveBlending} depthWrite={false} />
      </mesh>
      <group ref={labelGroup} visible={false}>
        <Billboard position={[0, 1.1, 0]}>
          <Text
            ref={label}
            font={garamondItalicUrl}
            fontSize={0.9}
            color="#ffd3b4"
            outlineWidth={0.06}
            outlineColor="#1b130c"
            anchorX="center"
            anchorY="bottom"
            fillOpacity={0}
            outlineOpacity={0}
          >
            {' '}
          </Text>
        </Billboard>
      </group>
    </>
  )
}

export function MapOverlays({ height }: { height: HeightSampler }) {
  return (
    <>
      <CityLabels height={height} />
      <EventPins height={height} />
      <EventMarker height={height} />
      {itineraries.map((itinerary) => (
        <ItineraryPath key={itinerary.id} itinerary={itinerary} height={height} />
      ))}
    </>
  )
}
