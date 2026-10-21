import type { Material, MeshStandardMaterial } from 'three'

export const WATER_TIME = { value: 0 }

const WATER_NAMES = /^(water|sea|river|river_water)(\.\d+)?$/

export function isWaterMaterial(material: Material): material is MeshStandardMaterial {
  return WATER_NAMES.test(material.name) && 'roughness' in material
}

const waveChunk = `
uniform float waterTime;
varying vec3 vWaterWorld;
vec2 waterSlope(vec2 p, float footprint) {
  vec2 slope = vec2(0.0);
  vec4 waves[5];
  waves[0] = vec4(0.8, 0.6, 0.55, 0.05);
  waves[1] = vec4(-0.5, 0.86, 1.3, 0.035);
  waves[2] = vec4(0.97, -0.24, 2.9, 0.03);
  waves[3] = vec4(-0.2, -0.98, 6.1, 0.022);
  waves[4] = vec4(0.6, -0.8, 11.0, 0.016);
  for (int i = 0; i < 5; i++) {
    vec2 direction = waves[i].xy;
    float frequency = waves[i].z;
    float weight = waves[i].w * (1.0 - smoothstep(0.08, 0.35, footprint * frequency / 6.2832));
    float phase = dot(direction, p) * frequency + waterTime * sqrt(9.8 * frequency) * 0.9;
    slope += direction * cos(phase) * weight * frequency * 0.9;
  }
  return slope;
}
`

export function makeWater(material: MeshStandardMaterial) {
  if (material.userData.water) return
  material.userData.water = true
  material.roughness = 0.07
  material.metalness = 0
  material.envMapIntensity = 2.2
  material.color.multiplyScalar(0.8)
  material.onBeforeCompile = (shader) => {
    shader.uniforms.waterTime = WATER_TIME
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWaterWorld;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvWaterWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;')
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\n${waveChunk}`)
      .replace(
        '#include <normal_fragment_maps>',
        `#include <normal_fragment_maps>
        vec2 waterFootprint = fwidth(vWaterWorld.xz);
        vec2 waterGradient = waterSlope(vWaterWorld.xz, max(waterFootprint.x, waterFootprint.y));
        normal = normalize((viewMatrix * vec4(normalize(vec3(-waterGradient.x, 1.0, -waterGradient.y)), 0.0)).xyz);`,
      )
  }
  material.needsUpdate = true
}
