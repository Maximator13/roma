import { Color, ShaderMaterial, Vector2, Vector3, type Texture } from 'three'
import { MAP_SIZE, RELIEF_ENCODING, RELIEF_SIZE } from './geo.ts'

export const LAND_SCALE = 0.55 / RELIEF_ENCODING.maxLand

const decodeChunk = `
float decodeElevation(float value) {
  float s = (value - 0.5) * 2.0;
  return s >= 0.0 ? s * s * ${RELIEF_ENCODING.maxLand.toFixed(1)} : -s * s * ${RELIEF_ENCODING.maxDepth.toFixed(1)};
}
`

const vertexShader = `
uniform sampler2D relief;
uniform float landScale;
varying vec2 vUv;
varying vec3 vWorld;
${decodeChunk}
void main() {
  vUv = uv;
  float elevation = decodeElevation(texture2D(relief, uv).r);
  vec3 displaced = position + vec3(0.0, max(elevation, 0.0) * landScale, 0.0);
  vec4 world = modelMatrix * vec4(displaced, 1.0);
  vWorld = world.xyz;
  gl_Position = projectionMatrix * viewMatrix * world;
}
`

const fragmentShader = `
uniform sampler2D relief;
uniform sampler2D fromSharp;
uniform sampler2D fromSoft;
uniform sampler2D toSharp;
uniform sampler2D toSoft;
uniform vec2 texel;
uniform vec2 mapSize;
uniform float landScale;
uniform float transition;
uniform float time;
uniform vec3 sunDirection;
uniform vec3 sunColor;
uniform vec3 ambientColor;
uniform vec3 fogColor;
uniform float fogNear;
uniform float fogFar;
uniform vec3 territoryColor;
uniform vec3 secondaryColor;
uniform float detail;
varying vec2 vUv;
varying vec3 vWorld;
${decodeChunk}
float elevationAt(vec2 uv) {
  return decodeElevation(texture2D(relief, uv).r);
}

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float reveal(float from, float to, float fromSoft, float toSoft, float progress, float jitter) {
  if (progress >= 1.0) return to;
  float order = to > from ? 1.0 - clamp(fromSoft * 1.6, 0.0, 1.0) : clamp(toSoft * 1.6, 0.0, 1.0);
  float switchAt = smoothstep(order - 0.12, order + 0.12, progress * 1.5 - 0.25 + jitter);
  return mix(from, to, switchAt);
}

vec3 groundColor(float h) {
  vec3 lowland = vec3(0.39, 0.43, 0.24);
  vec3 hills = vec3(0.53, 0.43, 0.26);
  vec3 mountain = vec3(0.44, 0.36, 0.30);
  vec3 snow = vec3(0.86, 0.86, 0.84);
  vec3 color = mix(lowland, hills, smoothstep(80.0, 700.0, h));
  color = mix(color, mountain, smoothstep(700.0, 2300.0, h));
  return mix(color, snow, smoothstep(2700.0, 3700.0, h));
}

void main() {
  float h = elevationAt(vUv);
  float hl = max(elevationAt(vUv - vec2(texel.x, 0.0)), 0.0);
  float hr = max(elevationAt(vUv + vec2(texel.x, 0.0)), 0.0);
  float hd = max(elevationAt(vUv - vec2(0.0, texel.y)), 0.0);
  float hu = max(elevationAt(vUv + vec2(0.0, texel.y)), 0.0);
  float relief = landScale * 3.0;
  vec3 normal = normalize(vec3(-(hr - hl) * relief / (2.0 * texel.x * mapSize.x), 1.0, -(hd - hu) * relief / (2.0 * texel.y * mapSize.y)));

  float coastWidth = max(fwidth(h), 1.0);
  float land = smoothstep(-coastWidth, coastWidth, h);

  vec3 ground = groundColor(h) * (0.88 + 0.16 * noise(vUv * vec2(1400.0, 780.0)) * detail + 0.08 * noise(vUv * vec2(7000.0, 3900.0)) * detail);
  float diffuse = max(dot(normal, sunDirection), 0.0);
  vec3 landLit = ground * (ambientColor + sunColor * diffuse * 1.15);

  float depth = clamp(-h / 3500.0, 0.0, 1.0);
  vec3 water = mix(vec3(0.08, 0.34, 0.42), vec3(0.01, 0.06, 0.16), sqrt(depth));
  vec2 waveUv = vWorld.xz * 9.0;
  float waveA = noise(waveUv + vec2(time * 0.35, time * 0.12)) + 0.5 * noise(waveUv * 2.7 - vec2(time * 0.2, time * 0.4));
  float waveB = noise(waveUv.yx * 1.3 + vec2(time * 0.18, -time * 0.3)) + 0.5 * noise(waveUv * 3.1 + vec2(-time * 0.25, time * 0.1));
  vec3 waveNormal = normalize(vec3((waveA - 0.75) * 0.12 * detail, 1.0, (waveB - 0.75) * 0.12 * detail));
  vec3 viewDirection = normalize(cameraPosition - vWorld);
  float glint = pow(max(dot(waveNormal, normalize(sunDirection + viewDirection)), 0.0), 140.0);
  float foam = (1.0 - smoothstep(0.0, 40.0, -h)) * (0.5 + 0.5 * sin(time * 1.1 + waveA * 5.0));
  vec3 sea = water * (ambientColor * 1.1 + sunColor * 0.2) + sunColor * glint * 0.35 + vec3(0.55, 0.6, 0.6) * foam * 0.12;

  vec3 color = mix(sea, landLit, land);

  vec4 a = texture2D(fromSharp, vUv);
  vec4 b = texture2D(toSharp, vUv);
  vec4 aSoft = texture2D(fromSoft, vUv);
  vec4 bSoft = texture2D(toSoft, vUv);
  float jitter = (noise(vUv * vec2(70.0, 40.0)) - 0.5) * 0.22;
  float roman = reveal(a.r, b.r, aSoft.r, bSoft.r, transition, jitter);
  float rival = reveal(a.b, b.b, aSoft.b, bSoft.b, transition, jitter);

  float landBorder = smoothstep(0.0, 40.0, h);
  float romanFill = smoothstep(0.3, 0.7, roman) * land;
  float rivalFill = smoothstep(0.3, 0.7, rival) * land;
  float romanLine = 1.0 - smoothstep(0.0, max(fwidth(roman) * 2.4, 0.001), abs(roman - 0.5));
  float rivalLine = 1.0 - smoothstep(0.0, max(fwidth(rival) * 2.0, 0.001), abs(rival - 0.5));
  float romanGlow = 1.0 - smoothstep(0.0, 0.42, abs(roman - 0.5));
  float pulse = 0.8 + 0.2 * sin(time * 1.6 - (vWorld.x + vWorld.z) * 0.5);

  float outside = land * (1.0 - max(romanFill, rivalFill));
  vec3 muted = vec3(dot(color, vec3(0.3, 0.59, 0.11)));
  color = mix(color, mix(muted, color, 0.6) * 0.78, outside);
  color = mix(color, color * (0.7 + territoryColor * 0.75) * 1.1, romanFill);
  color = mix(color, color * (0.65 + secondaryColor * 0.8), rivalFill);
  color += territoryColor * (romanLine * 1.5 + romanGlow * 0.3) * pulse * landBorder;
  color += secondaryColor * (rivalLine * 1.1 + (1.0 - smoothstep(0.0, 0.35, abs(rival - 0.5))) * 0.2) * landBorder;

  vec2 cloudUv = vWorld.xz * 0.11 + vec2(time * 0.012, time * 0.004);
  float clouds = noise(cloudUv) * 0.6 + noise(cloudUv * 2.3 + 7.0) * 0.3 + noise(cloudUv * 5.1 - 3.0) * 0.1;
  color *= 1.0 - smoothstep(0.5, 0.78, clouds) * 0.28 * detail;

  vec2 edge = min(vUv, 1.0 - vUv) * vec2(${MAP_SIZE.width.toFixed(2)}, ${MAP_SIZE.depth.toFixed(2)});
  float mapEdge = smoothstep(0.0, 2.5, min(edge.x, edge.y));

  float distanceToCamera = length(cameraPosition - vWorld);
  color = mix(color, fogColor, max(smoothstep(fogNear, fogFar, distanceToCamera), 1.0 - mapEdge));
  gl_FragColor = vec4(color, 1.0);
}
`

export interface TerrainTextures {
  relief: Texture
  fromSharp: Texture
  fromSoft: Texture
  toSharp: Texture
  toSoft: Texture
}

export function createTerrainMaterial(textures: TerrainTextures): ShaderMaterial {
  return new ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: {
      relief: { value: textures.relief },
      fromSharp: { value: textures.fromSharp },
      fromSoft: { value: textures.fromSoft },
      toSharp: { value: textures.toSharp },
      toSoft: { value: textures.toSoft },
      texel: { value: new Vector2(1 / RELIEF_SIZE.width, 1 / RELIEF_SIZE.height) },
      mapSize: { value: new Vector2(MAP_SIZE.width, MAP_SIZE.depth) },
      landScale: { value: LAND_SCALE },
      transition: { value: 1 },
      time: { value: 0 },
      sunDirection: { value: new Vector3(-0.5, 0.6, 0.3).normalize() },
      sunColor: { value: new Color(1, 0.9, 0.75) },
      ambientColor: { value: new Color(0.35, 0.36, 0.4) },
      fogColor: { value: new Color(0.6, 0.6, 0.65) },
      fogNear: { value: 20 },
      fogFar: { value: 80 },
      territoryColor: { value: new Color(0.85, 0.66, 0.3) },
      secondaryColor: { value: new Color(0.62, 0.32, 0.4) },
      detail: { value: 1 },
    },
  })
}
