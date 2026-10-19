import { Html } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { Vector3, type Group } from 'three'
import type { UiInsets } from '../../map/MapStage.tsx'
import { heightAt, type HeightField } from './heightfield.ts'
import type { Battle } from './schema.ts'
import { useBattle } from './store.ts'
import { stateAt, type UnitState, type UnitTrack } from './timeline.ts'

const LABEL_LIFT = 60
const LABEL_MARGIN = 12

export function Labels({ battle, tracks, field, insets }: { battle: Battle; tracks: UnitTrack[]; field: HeightField; insets: UiInsets }) {
  const view = useBattle((state) => state.view)
  const labelled = useMemo(() => battle.units.flatMap((unit, index) => (unit.labelled ? [index] : [])), [battle])
  const anchors = useRef<(Group | null)[]>([])
  const elements = useRef<(HTMLDivElement | null)[]>([])
  const projected = useMemo(() => new Vector3(), [])
  const scratch = useMemo(() => ({}) as UnitState, [])

  useFrame(({ camera, size }) => {
    const { time, controlsHeight } = useBattle.getState()
    labelled.forEach((unit, order) => {
      const anchor = anchors.current[order]
      if (!anchor) return
      const state = stateAt(tracks[unit]!, time, scratch)
      anchor.position.set(state.x, heightAt(field, state.x, -state.y) + LABEL_LIFT, -state.y)
      const element = elements.current[order]
      if (!element) return
      projected.copy(anchor.position).project(camera)
      const x = ((projected.x + 1) / 2) * size.width
      const y = ((1 - projected.y) / 2) * size.height
      const hidden = projected.z > 1 || x < insets.left || x > size.width - insets.right || y < insets.top || y > size.height - insets.bottom - controlsHeight - LABEL_MARGIN
      element.style.visibility = hidden ? 'hidden' : 'visible'
    })
  })

  if (view !== 'tactical') return null
  return (
    <>
      {labelled.map((unit, order) => {
        const item = battle.units[unit]!
        return (
          <group
            key={item.id}
            ref={(node) => {
              anchors.current[order] = node
            }}
          >
            <Html
              center
              zIndexRange={[0, 0]}
              className={`battle-label battle-label--${item.side}`}
              ref={(node) => {
                elements.current[order] = node
              }}
            >
              {item.label}
            </Html>
          </group>
        )
      })}
    </>
  )
}
