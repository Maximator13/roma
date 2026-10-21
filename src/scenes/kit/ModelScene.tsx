import { useFrame } from '@react-three/fiber'
import { useEffect, useMemo } from 'react'
import { Vector3, type Object3D } from 'three'
import { SCENE_LOOK } from '../../stage/grading.ts'
import { QUALITY } from '../../stage/quality.ts'
import type { SceneProps } from '../registry.ts'
import { Atmosphere, type HazeSettings, type InteriorSettings, type SkySettings, type SunSettings } from './Atmosphere.tsx'
import { GuidedRail } from './GuidedRail.tsx'
import { Life } from './Life.tsx'
import { LightShaft } from './LightShaft.tsx'
import { markerForward, useSceneModel } from './model.ts'
import { overviewStop, stopFromMarker, type CameraStop } from './rail.ts'
import { WATER_TIME } from './Water.ts'

export interface ModelSceneConfig {
  model: string
  sun: SunSettings
  haze: HazeSettings
  overview: { azimuth: number; elevation: number }
  forceShadows?: boolean
  interior?: InteriorSettings
  lightShaftRadius?: number
  sky?: SkySettings
  exposure?: number
  views?: Record<string, { position: [number, number, number]; target: [number, number, number] }>
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
  const shadows = QUALITY[quality].shadows || config.forceShadows === true
  const model = useSceneModel(config.model, shadows)
  useFrame(({ clock }) => {
    WATER_TIME.value = clock.elapsedTime
  })
  useEffect(() => {
    SCENE_LOOK.exposure = config.exposure ?? 1
    return () => {
      SCENE_LOOK.exposure = 1
    }
  }, [config.exposure])
  const stops = useMemo<CameraStop[]>(() => {
    const viewStop = (id: string): CameraStop | null => {
      const view = config.views?.[id]
      return view ? { position: new Vector3(...view.position), target: new Vector3(...view.target) } : null
    }
    const overview =
      viewStop(OVERVIEW_MARKER) ??
      markerStop(model.markers, OVERVIEW_MARKER) ??
      overviewStop(model.bounds, config.overview.azimuth, config.overview.elevation)
    const points = (scene.points ?? []).map((item) => viewStop(item.id) ?? markerStop(model.markers, item.id) ?? overview)
    return [overview, ...points]
  }, [model, scene, config])
  return (
    <>
      <Atmosphere sun={config.sun} haze={config.haze} shadows={shadows} shadowMapSize={QUALITY[quality].shadowMapSize} interior={config.interior} sky={config.sky} />
      <primitive object={model.root} />
      <Life model={model} quality={quality} shadows={shadows} />
      {model.anchors.has('oculus') && model.anchors.has('sunbeam_target') && (
        <LightShaft from={model.anchors.get('oculus')!} to={model.anchors.get('sunbeam_target')!} radius={config.lightShaftRadius ?? 4} />
      )}
      <GuidedRail stops={stops} index={point} insets={insets} />
    </>
  )
}
