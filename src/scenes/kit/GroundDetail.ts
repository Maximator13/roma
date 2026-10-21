import type { Material, MeshStandardMaterial } from 'three'

const GROUND_NAMES = /^(terrain|ground)/

export function isGroundMaterial(material: Material): material is MeshStandardMaterial {
  return GROUND_NAMES.test(material.name) && 'roughness' in material && !material.name.endsWith('_far')
}

const noiseChunk = `
varying vec3 vGroundWorld;
float groundHash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}
float groundNoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(groundHash(i), groundHash(i + vec2(1.0, 0.0)), u.x), mix(groundHash(i + vec2(0.0, 1.0)), groundHash(i + vec2(1.0, 1.0)), u.x), u.y);
}
`

export function addGroundDetail(material: MeshStandardMaterial) {
  if (material.userData.groundDetail) return
  material.userData.groundDetail = true
  material.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vGroundWorld;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvGroundWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;')
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\n${noiseChunk}`)
      .replace(
        '#include <map_fragment>',
        `#include <map_fragment>
        vec2 groundFootprint = fwidth(vGroundWorld.xz);
        float groundBlur = max(groundFootprint.x, groundFootprint.y);
        float groundFine = (groundNoise(vGroundWorld.xz * 1.7) - 0.5) * (1.0 - smoothstep(0.05, 0.35, groundBlur));
        float groundCoarse = (groundNoise(vGroundWorld.xz * 0.23) - 0.5) * (1.0 - smoothstep(0.4, 2.5, groundBlur));
        diffuseColor.rgb *= 1.0 + groundFine * 0.22 + groundCoarse * 0.18;`,
      )
  }
  material.needsUpdate = true
}
