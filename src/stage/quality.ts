export const QUALITY_TIERS = ['low', 'medium', 'high'] as const

export type QualityTier = (typeof QUALITY_TIERS)[number]

export interface QualitySettings {
  maxDpr: number
  multisampling: number
  halfFloat: boolean
  shadows: boolean
  shadowMapSize: number
}

export const QUALITY: Record<QualityTier, QualitySettings> = {
  low: { maxDpr: 1, multisampling: 0, halfFloat: false, shadows: false, shadowMapSize: 1024 },
  medium: { maxDpr: 1.25, multisampling: 2, halfFloat: true, shadows: true, shadowMapSize: 2048 },
  high: { maxDpr: 2, multisampling: 4, halfFloat: true, shadows: true, shadowMapSize: 4096 },
}

function isQualityTier(value: string | null): value is QualityTier {
  return value !== null && (QUALITY_TIERS as readonly string[]).includes(value)
}

function hasHardwareWebGl(): boolean {
  try {
    const canvas = document.createElement('canvas')
    const context = canvas.getContext('webgl2', { failIfMajorPerformanceCaveat: true })
    context?.getExtension('WEBGL_lose_context')?.loseContext()
    return context !== null
  } catch {
    return false
  }
}

export function initialQuality(search = location.search, device = navigator): QualityTier {
  const requested = new URLSearchParams(search).get('quality')
  if (isQualityTier(requested)) return requested
  const coarsePointer = typeof matchMedia === 'function' && matchMedia('(pointer: coarse)').matches
  if (coarsePointer || device.hardwareConcurrency <= 4 || !hasHardwareWebGl()) return 'low'
  return 'medium'
}

export function stepQuality(tier: QualityTier, direction: 1 | -1): QualityTier {
  const index = QUALITY_TIERS.indexOf(tier) + direction
  return QUALITY_TIERS[Math.min(QUALITY_TIERS.length - 1, Math.max(0, index))]!
}

export function isDebug(search = location.search): boolean {
  return new URLSearchParams(search).has('debug')
}
