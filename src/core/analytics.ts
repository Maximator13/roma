import { ANALYTICS } from '../site.ts'

export type Consent = 'granted' | 'denied' | null

const CONSENT_KEY = 'roma.consent.analytics'

export function analyticsAvailable(): boolean {
  return ANALYTICS.goatcounterCode !== null
}

export function readConsent(): Consent {
  try {
    const value = localStorage.getItem(CONSENT_KEY)
    return value === 'granted' || value === 'denied' ? value : null
  } catch {
    return null
  }
}

export function writeConsent(value: 'granted' | 'denied'): boolean {
  try {
    localStorage.setItem(CONSENT_KEY, value)
    return true
  } catch {
    return false
  }
}

interface GoatCounter {
  count: (options: { path: string; title?: string }) => void
}

function countPage() {
  const counter = (window as unknown as { goatcounter?: GoatCounter }).goatcounter
  counter?.count({ path: `${location.pathname}${location.hash}`, title: document.title })
}

export function startAnalytics() {
  const code = ANALYTICS.goatcounterCode
  if (code === null || document.querySelector('script[data-goatcounter]')) return
  const script = document.createElement('script')
  script.async = true
  script.src = 'https://gc.zgo.at/count.js'
  script.dataset.goatcounter = `https://${code}.goatcounter.com/count`
  script.dataset.goatcounterSettings = JSON.stringify({ no_onload: true })
  script.addEventListener('load', countPage)
  document.head.append(script)
  window.addEventListener('hashchange', countPage)
}
