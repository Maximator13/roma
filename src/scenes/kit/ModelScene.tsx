import { useMemo } from 'react'
import { Vector3, type Object3D } from 'three'
import { QUALITY } from '../../stage/quality.ts'
import type { SceneProps } from '../registry.ts'
import { Atmosphere, type HazeSettings, type SunSettings } from './Atmosphere.tsx'
import { GuidedRail } from './GuidedRail.tsx'
import { Life } from './Life.tsx'
import { markerForward, useSceneModel } from './model.ts'
import { overviewStop, stopFromMarker, type CameraStop } from './rail.ts'

export interface ModelSceneConfig {
  model: string
  sun: SunSettings
  haze: HazeSettings
  overview: { azimuth: number; elevation: number }
}

const OVERVIEW_MARKER = 'vue-d-ensemble'
const TARGET_SUFFIX = '_target'

function worldPosition(marker: Object3D): Vector3 {
  return marker.getWorldPosition(new Vector3())
}

export function markerStop(markers: Map<string, Object3D>, id: string): CameraStop | null {
  const eye = markers.get(id)
  if (!eye) return null
  const target = markers.get(`${id}${TARGET_SUFFIX}`)
  return target ? { position: worldPosition(eye), target: worldPosition(target) } : stopFromMarker(worldPosition(eye), markerForward(eye))
}

export function ModelScene({ config, scene, point, insets, quality }: SceneProps & { config: ModelSceneConfig }) {
  const shadows = QUALITY[quality].shadows
  const model = useSceneModel(config.model, shadows)
  const stops = useMemo<CameraStop[]>(() => {
    const overview =
      markerStop(model.markers, OVERVIEW_MARKER) ?? overviewStop(model.bounds, config.overview.azimuth, config.overview.elevation)
    const points = (scene.points ?? []).map((item) => markerStop(model.markers, item.id) ?? overview)
    return [overview, ...points]
  }, [model, scene, config])
  return (
    <>
      <Atmosphere sun={config.sun} haze={config.haze} shadows={shadows} />
      <primitive object={model.root} />
      <Life model={model} quality={quality} shadows={shadows} />
      <GuidedRail stops={stops} index={point} insets={insets} />
    </>
  )
}
