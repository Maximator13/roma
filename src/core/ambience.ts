import type { Scene } from '../data/schema.ts'

const FADE_SECONDS = 1.6
const OVERVIEW_POINT = 'vue-d-ensemble'

export function pointIdAt(scene: Scene, index: number): string {
  return index === 0 ? OVERVIEW_POINT : (scene.points?.[index - 1]?.id ?? OVERVIEW_POINT)
}

export function ambienceTargets(scene: Scene, pointId: string): Record<string, number> {
  const targets: Record<string, number> = {}
  for (const layer of scene.ambience ?? []) {
    const audible = !layer.points || layer.points.includes(pointId)
    targets[layer.layer] = Math.max(targets[layer.layer] ?? 0, audible ? layer.volume : 0)
  }
  return targets
}

interface Layer {
  gain: GainNode
  started: Promise<void>
}

let context: AudioContext | null = null
const layers = new Map<string, Layer>()

function audioExtension(): 'ogg' | 'mp3' {
  const probe = typeof document === 'undefined' ? null : document.createElement('audio')
  return probe?.canPlayType('audio/ogg; codecs="vorbis"') ? 'ogg' : 'mp3'
}

async function startLayer(audio: AudioContext, name: string, gain: GainNode): Promise<void> {
  const response = await fetch(`${import.meta.env.BASE_URL}audio/${name}.${audioExtension()}`)
  if (!response.ok) return
  const buffer = await audio.decodeAudioData(await response.arrayBuffer())
  const source = audio.createBufferSource()
  source.buffer = buffer
  source.loop = true
  source.connect(gain)
  source.start()
}

function layerFor(audio: AudioContext, name: string): Layer {
  const existing = layers.get(name)
  if (existing) return existing
  const gain = audio.createGain()
  gain.gain.value = 0
  gain.connect(audio.destination)
  const layer = { gain, started: startLayer(audio, name, gain).catch(() => undefined) }
  layers.set(name, layer)
  return layer
}

function fadeTo(audio: AudioContext, gain: GainNode, value: number) {
  const now = audio.currentTime
  gain.gain.cancelScheduledValues(now)
  gain.gain.setValueAtTime(gain.gain.value, now)
  gain.gain.linearRampToValueAtTime(value, now + FADE_SECONDS)
}

export function playAmbience(targets: Record<string, number>, enabled: boolean) {
  if (!enabled) {
    if (context) for (const layer of layers.values()) fadeTo(context, layer.gain, 0)
    return
  }
  context ??= new AudioContext()
  const audio = context
  void audio.resume()
  for (const [name, layer] of layers) if (!(name in targets)) fadeTo(audio, layer.gain, 0)
  for (const [name, volume] of Object.entries(targets)) fadeTo(audio, layerFor(audio, name).gain, volume)
}
