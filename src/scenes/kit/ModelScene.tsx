import { useMemo } from 'react'
import { Vector3 } from 'three'
import { QUALITY } from '../../stage/quality.ts'
import type { SceneProps } from '../registry.ts'
import { Atmosphere, type HazeSettings, type SunSettings } from './Atmosphere.tsx'
import { GuidedRail } from './GuidedRail.tsx'
import { markerForward, useSceneModel } from './model.ts'
import { overviewStop, stopFromMarker, type CameraStop } from './rail.ts'

export interface ModelSceneConfig {
  model: string
  sun: SunSettings
  haze: HazeSettings
  overview: { azimuth: number; elevation: number }
}

export function ModelScene({ config, scene, point, insets, quality }: SceneProps & { config: ModelSceneConfig }) {
  const shadows = QUALITY[quality].shadows
  const model = useSceneModel(config.model, shadows)
  const stops = useMemo<CameraStop[]>(() => {
    const overview = overviewStop(model.bounds, config.overview.azimuth, config.overview.elevation)
    const points = (scene.points ?? []).map((item) => {
      const marker = model.markers.get(item.id)
      return marker ? stopFromMarker(marker.getWorldPosition(new Vector3()), markerForward(marker)) : overview
    })
    return [overview, ...points]
  }, [model, scene, config])
  return (
    <>
      <Atmosphere sun={config.sun} haze={config.haze} shadows={shadows} />
      <primitive object={model.root} />
      <GuidedRail stops={stops} index={point} insets={insets} />
    </>
  )
}
