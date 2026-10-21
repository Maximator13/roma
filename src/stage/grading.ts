import type { Era, EraId } from '../data/schema.ts'

export type Rgb = [number, number, number]

export interface Grading {
  exposure: number
  contrast: number
  saturation: number
  lift: Rgb
  gain: Rgb
  skyTop: Rgb
  skyHorizon: Rgb
  fog: Rgb
  sun: Rgb
  sunElevation: number
  accent: Rgb
}

export const ERA_GRADING: Record<EraId, Grading> = {
  royaute: {
    exposure: 0.92,
    contrast: 1.06,
    saturation: 1.05,
    lift: [0.05, 0.02, 0.0],
    gain: [1.1, 0.96, 0.82],
    skyTop: [0.16, 0.1, 0.12],
    skyHorizon: [0.86, 0.46, 0.22],
    fog: [0.5, 0.3, 0.18],
    sun: [1.0, 0.62, 0.32],
    sunElevation: 0.06,
    accent: [0.86, 0.5, 0.24],
  },
  republique: {
    exposure: 1.04,
    contrast: 1.1,
    saturation: 1.14,
    lift: [0.03, 0.01, 0.0],
    gain: [1.04, 1.0, 0.93],
    skyTop: [0.3, 0.5, 0.78],
    skyHorizon: [0.86, 0.82, 0.74],
    fog: [0.78, 0.72, 0.62],
    sun: [1.0, 0.96, 0.88],
    sunElevation: 0.7,
    accent: [0.72, 0.2, 0.15],
  },
  'haut-empire': {
    exposure: 1.02,
    contrast: 1.08,
    saturation: 1.2,
    lift: [0.02, 0.02, 0.05],
    gain: [1.1, 1.0, 0.84],
    skyTop: [0.2, 0.42, 0.72],
    skyHorizon: [0.98, 0.8, 0.52],
    fog: [0.86, 0.72, 0.52],
    sun: [1.0, 0.82, 0.55],
    sunElevation: 0.22,
    accent: [0.85, 0.68, 0.3],
  },
  'crise-du-iiie-siecle': {
    exposure: 0.82,
    contrast: 1.16,
    saturation: 0.72,
    lift: [0.03, 0.03, 0.03],
    gain: [0.95, 0.98, 1.0],
    skyTop: [0.14, 0.15, 0.17],
    skyHorizon: [0.42, 0.42, 0.4],
    fog: [0.36, 0.35, 0.33],
    sun: [0.7, 0.68, 0.62],
    sunElevation: 0.3,
    accent: [0.62, 0.58, 0.5],
  },
  'bas-empire': {
    exposure: 0.9,
    contrast: 1.08,
    saturation: 1.1,
    lift: [0.03, 0.01, 0.05],
    gain: [0.98, 0.95, 1.03],
    skyTop: [0.2, 0.22, 0.32],
    skyHorizon: [0.7, 0.68, 0.74],
    fog: [0.6, 0.58, 0.64],
    sun: [0.86, 0.88, 1.0],
    sunElevation: 0.14,
    accent: [0.5, 0.18, 0.4],
  },
  'empire-romain-d-orient': {
    exposure: 0.8,
    contrast: 1.14,
    saturation: 1.15,
    lift: [0.0, 0.02, 0.07],
    gain: [1.14, 0.98, 0.76],
    skyTop: [0.04, 0.07, 0.2],
    skyHorizon: [0.42, 0.3, 0.2],
    fog: [0.18, 0.15, 0.16],
    sun: [1.0, 0.74, 0.4],
    sunElevation: 0.03,
    accent: [0.85, 0.66, 0.26],
  },
}

export const SCENE_LOOK = { exposure: 1 }

const TRANSITION_YEARS = 20

function mix(a: number, b: number, t: number): number {
  return a * (1 - t) + b * t
}

function mixRgb(a: Rgb, b: Rgb, t: number): Rgb {
  return [mix(a[0], b[0], t), mix(a[1], b[1], t), mix(a[2], b[2], t)]
}

export function mixGrading(a: Grading, b: Grading, t: number): Grading {
  return {
    exposure: mix(a.exposure, b.exposure, t),
    contrast: mix(a.contrast, b.contrast, t),
    saturation: mix(a.saturation, b.saturation, t),
    lift: mixRgb(a.lift, b.lift, t),
    gain: mixRgb(a.gain, b.gain, t),
    skyTop: mixRgb(a.skyTop, b.skyTop, t),
    skyHorizon: mixRgb(a.skyHorizon, b.skyHorizon, t),
    fog: mixRgb(a.fog, b.fog, t),
    sun: mixRgb(a.sun, b.sun, t),
    sunElevation: mix(a.sunElevation, b.sunElevation, t),
    accent: mixRgb(a.accent, b.accent, t),
  }
}

function smoothstep(edge0: number, edge1: number, value: number): number {
  const t = Math.min(1, Math.max(0, (value - edge0) / (edge1 - edge0)))
  return t * t * (3 - 2 * t)
}

export function gradingAt(year: number, eras: Era[]): Grading {
  const ordered = [...eras].sort((a, b) => a.start - b.start)
  let grading = ERA_GRADING[ordered[0]!.id]
  for (const era of ordered.slice(1)) {
    const window = Math.min(TRANSITION_YEARS, (era.end - era.start) / 4)
    const t = smoothstep(era.start - window, era.start + window, year)
    grading = mixGrading(grading, ERA_GRADING[era.id], t)
  }
  return grading
}

export function rgbToCss([r, g, b]: Rgb): string {
  const channel = (value: number) => Math.round(Math.min(1, Math.max(0, value)) * 255)
  return `rgb(${channel(r)} ${channel(g)} ${channel(b)})`
}

export const BACKGROUND: Rgb = [0.07, 0.05, 0.04]

function relativeLuminance([r, g, b]: Rgb): number {
  const linear = (value: number) => (value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4)
  return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)
}

export function contrastRatio(a: Rgb, b: Rgb): number {
  const [light, dark] = [relativeLuminance(a), relativeLuminance(b)].sort((x, y) => y - x)
  return (light! + 0.05) / (dark! + 0.05)
}

export function readableAccent(accent: Rgb): Rgb {
  return mixRgb(accent, [1, 1, 1], 0.4)
}
