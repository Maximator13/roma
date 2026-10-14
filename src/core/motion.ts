export const EASE = 'power3.inOut'
export const EASE_OUT = 'power3.out'

export function prefersReducedMotion(): boolean {
  return typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function motionDuration(seconds: number): number {
  return prefersReducedMotion() ? 0 : seconds
}
