import { describe, expect, it } from 'vitest'
import type { Scene } from '../data/schema.ts'
import { ambienceTargets, pointIdAt } from './ambience.ts'

const scene: Scene = {
  id: 'essai',
  title: 'Essai',
  status: 'ready',
  points: [{ id: 'fontaine', title: 'Fontaine', text: 'Texte.', sources: ['Source'] }],
  ambience: [
    { layer: 'evening-city', volume: 0.5 },
    { layer: 'fountain', volume: 0.6, points: ['fontaine'] },
  ],
}

describe('ambience', () => {
  it('names the overview and the points of interest', () => {
    expect(pointIdAt(scene, 0)).toBe('vue-d-ensemble')
    expect(pointIdAt(scene, 1)).toBe('fontaine')
  })

  it('mutes the layers tied to other points', () => {
    expect(ambienceTargets(scene, 'vue-d-ensemble')).toEqual({ 'evening-city': 0.5, fountain: 0 })
    expect(ambienceTargets(scene, 'fontaine')).toEqual({ 'evening-city': 0.5, fountain: 0.6 })
  })
})
