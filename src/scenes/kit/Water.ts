import type { Material, MeshStandardMaterial } from 'three'

export const WATER_TIME = { value: 0 }

const WATER_NAMES = /^(water|sea|river|river_water)(\.\d+)?$/

export function isWaterMaterial(material: Material): material is MeshStandardMaterial {
  return WATER_NAMES.test(material.name) && 'roughness' in material
}

const waveChunk = `
uniform float waterTime;
varying vec3 vWaterWorld;
float waterHash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}
float waterNoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(waterHash(i), waterHash(i + vec2(1.0, 0.0)), u.x), mix(waterHash(i + vec2(0.0, 1.0)), waterHash(i + vec2(1.0, 1.0)), u.x), u.y);
}
vec2 waterNoiseSlope(vec2 p) {
  float centre = waterNoise(p);
  return vec2(waterNoise(p + vec2(0.2, 0.0)) - centre, waterNoise(p + vec2(0.0, 0.2)) - centre) * 5.0;
}
vec2 waterSlope(vec2 p, float footprint) {
  vec2 slope = vec2(0.0);
  vec4 waves[5];
  waves[0] = vec4(0.8, 0.6, 0.55, 0.035);
  waves[1] = vec4(-0.5, 0.86, 1.3, 0.025);
  waves[2] = vec4(0.97, -0.24, 2.9, 0.018);
  waves[3] = vec4(-0.2, -0.98, 6.1, 0.012);
  waves[4] = vec4(0.6, -0.8, 11.0, 0.009);
  float warp = waterNoise(p * 0.04) * 9.0 + waterNoise(p * 0.11) * 4.0;
  for (int i = 0; i < 5; i++) {
    vec2 direction = waves[i].xy;
    float frequency = waves[i].z;
    float weight = waves[i].w * (1.0 - smoothstep(0.08, 0.35, footprint * frequency / 6.2832));
    float phase = dot(direction, p) * frequency + warp * (1.0 + float(i) * 0.4) + waterTime * sqrt(9.8 * frequency) * 0.9;
    slope += direction * cos(phase) * weight * frequency * 0.9;
  }
  vec2 drift = vec2(waterTime * 0.07, waterTime * 0.04);
  slope += waterNoiseSlope(p * 0.45 + drift) * 0.05 * (1.0 - smoothstep(0.15, 0.6, footprint * 0.45));
  slope += waterNoiseSlope(p * 1.6 - drift * 1.7) * 0.035 * (1.0 - smoothstep(0.15, 0.6, footprint * 1.6));
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
