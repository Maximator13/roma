import { PerformanceMonitor } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { EffectComposer, ToneMapping, Vignette } from '@react-three/postprocessing'
import { ToneMappingMode } from 'postprocessing'
import { Suspense, useEffect, useMemo, useState } from 'react'
import { HalfFloatType, UnsignedByteType } from 'three'
import { eras } from '../data/eras.ts'
import { UI } from '../data/ui.ts'
import { MapStage, type UiInsets } from '../map/MapStage.tsx'
import { useApp } from '../store.ts'
import { DebugHud, StatsProbe } from './DebugHud.tsx'
import { gradingAt } from './grading.ts'
import { GradingEffect } from './GradingEffect.ts'
import { QUALITY, isDebug, stepQuality } from './quality.ts'

const TERRAIN_SEGMENTS = { low: 256, medium: 448, high: 640 } as const
const TERRAIN_DETAIL = { low: 0.4, medium: 1, high: 1 } as const

function Effects({ multisampling, halfFloat }: { multisampling: number; halfFloat: boolean }) {
  const grading = useMemo(() => new GradingEffect(), [])
  useFrame(() => grading.applyGrading(gradingAt(useApp.getState().view.center, eras)))
  return (
    <EffectComposer multisampling={multisampling} frameBufferType={halfFloat ? HalfFloatType : UnsignedByteType}>
      <ToneMapping mode={ToneMappingMode.ACES_FILMIC} />
      <primitive object={grading} dispose={null} />
      <Vignette offset={0.3} darkness={0.55} />
    </EffectComposer>
  )
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
  const wide = window.innerWidth > 720
  return {
    left: wide && side ? Math.min(side.right + 16, window.innerWidth * 0.45) : 0,
    right: wide && panel ? Math.max(0, window.innerWidth - panel.left + 16) : 0,
    top: header?.bottom ?? 0,
    bottom: timeline ? window.innerHeight - timeline.top : 0,
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
  return (
    <>
      <div className="stage" aria-hidden="true">
        <Canvas
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
            <MapStage segments={TERRAIN_SEGMENTS[quality]} insets={insets} detail={TERRAIN_DETAIL[quality]} />
          </Suspense>
          <Effects key={quality} multisampling={settings.multisampling} halfFloat={settings.halfFloat} />
          {debug && <StatsProbe />}
        </Canvas>
      </div>
      {debug && <DebugHud />}
    </>
  )
}
