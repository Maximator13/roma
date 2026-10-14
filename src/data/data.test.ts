import { describe, expect, it } from 'vitest'
import { dataset } from './index.ts'
import { validateDataset } from './validate.ts'

describe('project data', () => {
  it('passes schema, reference and style validation', () => {
    expect(validateDataset(dataset)).toEqual([])
  })
})

describe('validateDataset', () => {
  const valid = structuredClone(dataset)

  it('reports an event outside its era and an inactive track', () => {
    const broken = {
      ...valid,
      events: [
        {
          id: 'evenement-faux',
          title: 'Faux',
          start: 300,
          precision: 'year',
          certainty: 'attested',
          era: 'royaute',
          track: 'occident',
          category: 'politics',
          importance: 3,
          summary: 'Résumé.',
          body: 'Texte.',
          sources: [{ kind: 'modern', author: 'Auteur', work: 'Ouvrage' }],
        },
      ],
    }
    expect(validateDataset(broken)).toEqual([
      'event evenement-faux: start outside era royaute',
      'event evenement-faux: track occident inactive at start',
    ])
  })

  it('reports forbidden dashes anywhere in the data', () => {
    const dash = String.fromCharCode(0x2014)
    const broken = { ...valid, scenes: valid.scenes.map((scene, index) => (index === 0 ? { ...scene, title: `Cannes ${dash} 216` } : scene)) }
    expect(validateDataset(broken)).toEqual(['data.scenes[0].title: em or en dash'])
  })

  it('reports schema problems with the item id', () => {
    const broken = { ...valid, scenes: [{ id: 'Cannes', title: 'Cannes', status: 'planned' }] }
    expect(validateDataset(broken)[0]).toMatch(/^scene Cannes: id /)
  })
})

describe('phase 1 coverage', () => {
  it('has about forty events with at least three in every era', () => {
    expect(dataset.events.length).toBeGreaterThanOrEqual(40)
    for (const era of dataset.eras) {
      expect(dataset.events.filter((event) => event.era === era.id).length).toBeGreaterThanOrEqual(3)
    }
  })
})
