import { useEffect, useRef } from 'react'
import type { Material } from 'three'

const DISPOSE_DELAY_MS = 1000

const DETAIL_COMMON = `#include <common>
varying vec3 vBattleWorld;
float battleHash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float battleNoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(mix(battleHash(i), battleHash(i + vec2(1.0, 0.0)), f.x), mix(battleHash(i + vec2(0.0, 1.0)), battleHash(i + vec2(1.0, 1.0)), f.x), f.y);
}`

const DETAIL_FRAGMENT = `#include <map_fragment>
float battleDistance = length(vViewPosition);
float battleFine = 1.0 - smoothstep(60.0, 420.0, battleDistance);
float battleMid = 1.0 - smoothstep(600.0, 3000.0, battleDistance);
float battleDetail = (battleNoise(vBattleWorld.xz * 2.7) - 0.5) * 0.22 * battleFine
  + (battleNoise(vBattleWorld.xz * 0.45) - 0.5) * 0.24 * battleFine
  + (battleNoise(vBattleWorld.xz * 0.045) - 0.5) * 0.18 * battleMid;
diffuseColor.rgb *= 1.0 + battleDetail;`

export function addGroundDetail(material: Material) {
  material.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vBattleWorld;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvBattleWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;')
    shader.fragmentShader = shader.fragmentShader.replace('#include <common>', DETAIL_COMMON).replace('#include <map_fragment>', DETAIL_FRAGMENT)
  }
  material.customProgramCacheKey = () => 'battle-ground-detail'
  material.needsUpdate = true
}

export function useDeferredDispose(dispose: () => void) {
  const pending = useRef<{ dispose: () => void; timer: ReturnType<typeof setTimeout> } | null>(null)
  useEffect(() => {
    if (pending.current?.dispose === dispose) clearTimeout(pending.current.timer)
    return () => {
      pending.current = { dispose, timer: setTimeout(dispose, DISPOSE_DELAY_MS) }
    }
  }, [dispose])
}
