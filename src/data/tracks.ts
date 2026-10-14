import type { Track } from './schema.ts'

export const tracks: Track[] = [
  { id: 'rome', name: 'Rome', lane: 0, spans: [{ start: -752, end: 395 }] },
  { id: 'orient', name: "Empire romain d'Orient", lane: 0, spans: [{ start: 395, end: 1204 }, { start: 1261, end: 1453 }] },
  { id: 'occident', name: "Empire d'Occident", lane: 1, spans: [{ start: 395, end: 476 }] },
  { id: 'empire-des-gaules', name: 'Empire des Gaules', lane: 1, spans: [{ start: 260, end: 274 }] },
  { id: 'palmyre', name: 'Palmyre', lane: 2, spans: [{ start: 270, end: 273 }] },
  { id: 'nicee', name: 'Empire de Nicée', lane: 0, spans: [{ start: 1204, end: 1261 }] },
  { id: 'empire-latin', name: 'Empire latin', lane: 1, spans: [{ start: 1204, end: 1261 }] },
  { id: 'epire', name: "Despotat d'Épire", lane: 2, spans: [{ start: 1205, end: 1261 }] },
  { id: 'trebizonde', name: 'Empire de Trébizonde', lane: 3, spans: [{ start: 1204, end: 1453 }] },
]
