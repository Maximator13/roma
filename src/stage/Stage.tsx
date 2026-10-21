import { PerformanceMonitor, useProgress } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { Bloom, EffectComposer, N8AO, ToneMapping, Vignette } from '@react-three/postprocessing'
import { ToneMappingMode } from 'postprocessing'
import { Component, Suspense, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { HalfFloatType, UnsignedByteType } from 'three'
import { eras } from '../data/eras.ts'
import { UI } from '../data/ui.ts'
import { MapStage, type UiInsets } from '../map/MapStage.tsx'
import { findScene } from '../scenes/registry.ts'
import { useApp } from '../store.ts'
import { DebugHud, StatsProbe } from './DebugHud.tsx'
import { gradingAt, SCENE_LOOK } from './grading.ts'
import { GradingEffect } from './GradingEffect.ts'
import { QUALITY, isDebug, stepQuality, type QualityTier } from './quality.ts'
import { SceneHost } from './SceneHost.tsx'
import { useSceneSwap } from './useSceneSwap.ts'

const TERRAIN_SEGMENTS = { low: 320, medium: 640, high: 1024 } as const
const TERRAIN_DETAIL = { low: 0.4, medium: 1, high: 1 } as const
const SCENE_EXPOSURE = 1.12
const SCENE_SATURATION = 1.15

function Effects({
  multisampling,
  halfFloat,
  ambientOcclusion,
  bloom,
}: {
  multisampling: number
  halfFloat: boolean
  ambientOcclusion: AmbientOcclusion
  bloom: boolean
}) {
  const grading = useMemo(() => new GradingEffect(), [])
  useFrame(() => {
    const { view, route } = useApp.getState()
    const base = gradingAt(view.center, eras)
    grading.applyGrading(route.name === 'scene' ? { ...base, exposure: base.exposure * SCENE_EXPOSURE * SCENE_LOOK.exposure, saturation: base.saturation * SCENE_SATURATION } : base)
  })
  return (
    <EffectComposer multisampling={multisampling} frameBufferType={halfFloat ? HalfFloatType : UnsignedByteType}>
      <N8AO
        enabled={ambientOcclusion !== 'off'}
        halfRes={ambientOcclusion === 'half'}
        quality="performance"
        aoRadius={2.5}
        distanceFalloff={1}
        intensity={2.2}
      />
      {bloom ? <Bloom mipmapBlur luminanceThreshold={1.6} luminanceSmoothing={0.3} intensity={0.45} radius={0.7} /> : <></>}
      <ToneMapping mode={ToneMappingMode.NEUTRAL} />
      <primitive object={grading} dispose={null} />
      <Vignette offset={0.35} darkness={0.4} />
    </EffectComposer>
  )
}

class SceneBoundary extends Component<{ id: string; children: ReactNode }, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  componentDidCatch() {
    useApp.getState().setFailedScene(this.props.id)
  }

  render() {
    return this.state.failed ? null : this.props.children
  }
}

type AmbientOcclusion = 'off' | 'half' | 'full'

function ambientOcclusionFor(sceneShown: boolean, quality: QualityTier): AmbientOcclusion {
  if (!sceneShown || quality === 'low') return 'off'
  return quality === 'high' ? 'full' : 'half'
}

function changeQuality(direction: 1 | -1) {
  const { quality, setQuality } = useApp.getState()
  setQuality(stepQuality(quality, direction))
}

function measureInsets(): UiInsets {
  const header = document.querySelector('.header')?.getBoundingClientRect()
  const timeline = document.querySelector('.timeline')?.getBoundingClientRect()
  const side = document.querySelector('.main__side')?.getBoundingClientRect()
  const panel = document.querySelector('.panel')?.getBoundingClientRect()
  const sheet = document.querySelector('.panel--scene')?.getBoundingClientRect()
  const wide = window.innerWidth > 720
  const timelineInset = timeline && timeline.height > 0 ? window.innerHeight - timeline.top : 0
  return {
    left: wide && side ? Math.min(side.right + 16, window.innerWidth * 0.45) : 0,
    right: wide && panel ? Math.max(0, window.innerWidth - panel.left + 16) : 0,
    top: header?.bottom ?? 0,
    bottom: !wide && sheet ? Math.max(timelineInset, window.innerHeight - sheet.top) : timelineInset,
  }
}

function useUiInsets(): UiInsets {
  const [insets, setInsets] = useState<UiInsets>({ left: 0, right: 0, top: 0, bottom: 0 })
  useEffect(() => {
    const update = () => setInsets(measureInsets())
    const observer = new ResizeObserver(update)
    observer.observe(document.body)
    const timeline = document.querySelector('.timeline')
    if (timeline) observer.observe(timeline)
    update()
    const unsubscribe = useApp.subscribe((state, previous) => {
      if (state.route !== previous.route) requestAnimationFrame(update)
    })
    return () => {
      observer.disconnect()
      unsubscribe()
    }
  }, [])
  return insets
}

export default function Stage() {
  const quality = useApp((state) => state.quality)
  const settings = QUALITY[quality]
  const debug = useMemo(() => isDebug(), [])
  const insets = useUiInsets()
  const veil = useRef<HTMLDivElement>(null)
  const { shown, loading, onReady } = useSceneSwap(veil)
  const loadingTitle = shown && loading ? findScene(shown)?.title : undefined
  const progress = useProgress((state) => state.progress)
  return (
    <>
      <div className="stage" aria-hidden="true">
        <Canvas
          shadows="percentage"
          dpr={[1, settings.maxDpr]}
          camera={{ position: [0, 40, 20], fov: 40, near: 0.05, far: 400 }}
          gl={{ antialias: false, stencil: false, powerPreference: 'high-performance' }}
          fallback={<p className="stage__fallback">{UI.webglMissing}</p>}
        >
          <PerformanceMonitor
            flipflops={3}
            onIncline={() => changeQuality(1)}
            onDecline={() => changeQuality(-1)}
            onFallback={() => useApp.getState().setQuality('low')}
          />
          <Suspense fallback={null}>
            <MapStage segments={TERRAIN_SEGMENTS[quality]} insets={insets} detail={TERRAIN_DETAIL[quality]} active={shown === null} />
          </Suspense>
          {shown && (
            <SceneBoundary key={shown} id={shown}>
              <SceneHost id={shown} insets={insets} quality={quality} onReady={onReady} />
            </SceneBoundary>
          )}
          <Effects
            key={quality}
            multisampling={settings.multisampling}
            halfFloat={settings.halfFloat}
            ambientOcclusion={ambientOcclusionFor(shown !== null, quality)}
            bloom={settings.halfFloat}
          />
          {debug && <StatsProbe />}
        </Canvas>
        <div ref={veil} className="veil">
          {loadingTitle && <p className="veil__status">{UI.sceneLoading(loadingTitle)} ({Math.round(progress)} %)</p>}
        </div>
      </div>
      {debug && <DebugHud />}
    </>
  )
}
