import { useFrame } from '@react-three/fiber'
import { useRef } from 'react'
import { create } from 'zustand'
import { useApp } from '../store.ts'

export interface HudSample {
  fps: number
  frameMs: number
  calls: number
  triangles: number
  geometries: number
  textures: number
  programs: number
  heapMb: number | null
  dpr: number
  renderer: string
}

const useHud = create<{ sample: HudSample | null }>()(() => ({ sample: null }))

const SAMPLE_SECONDS = 0.5

function rendererName(context: WebGLRenderingContext | WebGL2RenderingContext): string {
  const extension = context.getExtension('WEBGL_debug_renderer_info')
  return String(context.getParameter(extension ? extension.UNMASKED_RENDERER_WEBGL : context.RENDERER))
}

function heapMegabytes(): number | null {
  const memory = (performance as Performance & { memory?: { usedJSHeapSize: number } }).memory
  return memory ? memory.usedJSHeapSize / 1048576 : null
}

export function StatsProbe() {
  const frames = useRef(0)
  const elapsed = useRef(0)
  const renderer = useRef('')

  useFrame(({ gl }, delta) => {
    if (gl.info.autoReset) {
      gl.info.autoReset = false
      renderer.current = rendererName(gl.getContext())
    }
    frames.current += 1
    elapsed.current += delta
    if (elapsed.current < SAMPLE_SECONDS) return
    const count = frames.current
    useHud.setState({
      sample: {
        fps: count / elapsed.current,
        frameMs: (elapsed.current / count) * 1000,
        calls: gl.info.render.calls / count,
        triangles: gl.info.render.triangles / count,
        geometries: gl.info.memory.geometries,
        textures: gl.info.memory.textures,
        programs: gl.info.programs?.length ?? 0,
        heapMb: heapMegabytes(),
        dpr: gl.getPixelRatio(),
        renderer: renderer.current,
      },
    })
    gl.info.reset()
    frames.current = 0
    elapsed.current = 0
  }, -1)

  return null
}

function format(value: number, digits = 0): string {
  return value.toLocaleString('fr-FR', { maximumFractionDigits: digits, minimumFractionDigits: digits })
}

export function DebugHud() {
  const sample = useHud((state) => state.sample)
  const quality = useApp((state) => state.quality)
  if (!sample) return null
  const rows: [string, string][] = [
    ['FPS', format(sample.fps, 0)],
    ['Image', `${format(sample.frameMs, 1)} ms`],
    ['Appels de dessin', format(sample.calls, 0)],
    ['Triangles', format(sample.triangles, 0)],
    ['Géométries', format(sample.geometries)],
    ['Textures', format(sample.textures)],
    ['Programmes', format(sample.programs)],
    ['Mémoire JS', sample.heapMb === null ? 'n. d.' : `${format(sample.heapMb, 0)} Mo`],
    ['Qualité', quality],
    ['Densité de pixels', format(sample.dpr, 2)],
  ]
  return (
    <div className="debug-hud" aria-hidden="true">
      <dl>
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <p>{sample.renderer}</p>
    </div>
  )
}
