import { PerformanceMonitor } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { EffectComposer, ToneMapping, Vignette } from '@react-three/postprocessing'
import { ToneMappingMode } from 'postprocessing'
import { useMemo } from 'react'
import { HalfFloatType, UnsignedByteType } from 'three'
import { eras } from '../data/eras.ts'
import { UI } from '../data/ui.ts'
import { useApp } from '../store.ts'
import { Backdrop } from './Backdrop.tsx'
import { DebugHud, StatsProbe } from './DebugHud.tsx'
import { gradingAt } from './grading.ts'
import { GradingEffect } from './GradingEffect.ts'
import { QUALITY, isDebug, stepQuality } from './quality.ts'

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

export default function Stage() {
  const quality = useApp((state) => state.quality)
  const settings = QUALITY[quality]
  const debug = useMemo(() => isDebug(), [])
  return (
    <>
      <div className="stage" aria-hidden="true">
        <Canvas
          dpr={[1, settings.maxDpr]}
          shadows={settings.shadows ? 'percentage' : false}
          camera={{ position: [0, 2.2, 9], fov: 45, near: 0.1, far: 400 }}
          gl={{ antialias: false, stencil: false, powerPreference: 'high-performance' }}
          fallback={<p className="stage__fallback">{UI.webglMissing}</p>}
        >
          <PerformanceMonitor
            flipflops={3}
            onIncline={() => changeQuality(1)}
            onDecline={() => changeQuality(-1)}
            onFallback={() => useApp.getState().setQuality('low')}
          />
          <Backdrop shadows={settings.shadows} />
          <Effects key={quality} multisampling={settings.multisampling} halfFloat={settings.halfFloat} />
          {debug && <StatsProbe />}
        </Canvas>
      </div>
      {debug && <DebugHud />}
    </>
  )
}
