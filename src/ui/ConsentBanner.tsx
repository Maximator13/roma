import { useEffect, useState } from 'react'
import { analyticsAvailable, readConsent, startAnalytics, writeConsent, type Consent } from '../core/analytics.ts'
import { UI } from '../data/ui.ts'

export function ConsentBanner() {
  const [consent, setConsent] = useState<Consent>(() => readConsent())
  useEffect(() => {
    if (consent === 'granted') startAnalytics()
  }, [consent])
  if (!analyticsAvailable() || consent !== null) return null
  const choose = (value: 'granted' | 'denied') => {
    writeConsent(value)
    setConsent(value)
  }
  return (
    <div className="consent" role="region" aria-label={UI.consentManage}>
      <p>{UI.consentText}</p>
      <div className="consent__actions">
        <button type="button" className="button" onClick={() => choose('denied')}>
          {UI.consentRefuse}
        </button>
        <button type="button" className="button" onClick={() => choose('granted')}>
          {UI.consentAccept}
        </button>
      </div>
    </div>
  )
}
