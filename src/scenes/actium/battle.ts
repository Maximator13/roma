import type { Battle, Keyframe, Point, Unit } from '../battle/schema.ts'

interface Part {
  troop: string
  ships: number
  label: string
}

interface Division {
  id: string
  label: string
  side: Unit['side']
  parts: Part[]
  start: { at: Point; facing: number; width: number; depth: number }
  moves: Keyframe[]
}

const DEGREES = Math.PI / 180

function shifted(point: Point, facing: number, across: number): Point {
  const angle = facing * DEGREES
  return [point[0] + Math.cos(angle) * across, point[1] - Math.sin(angle) * across]
}

function split(division: Division): Unit[] {
  const total = division.parts.reduce((sum, part) => sum + part.ships, 0)
  const middle = Math.floor(division.parts.length / 2)
  let before = 0
  return division.parts.map((part, index) => {
    const share = (before + part.ships / 2) / total - 0.5
    const fraction = part.ships / total
    before += part.ships
    let { at, facing, width } = division.start
    const moves = division.moves.map((frame) => {
      at = frame.at ?? at
      facing = frame.facing ?? facing
      width = frame.width ?? width
      const offset = share * width
      return {
        ...frame,
        at: shifted(at, facing, offset),
        ...(frame.via ? { via: frame.via.map((point) => shifted(point, facing, offset)) } : {}),
        ...(frame.width !== undefined ? { width: frame.width * fraction } : {}),
      }
    })
    const start = division.start
    return {
      id: division.parts.slice(0, index).some((other) => other.troop === part.troop) ? `${division.id}-${part.troop}-2` : `${division.id}-${part.troop}`,
      label: index === middle ? division.label : part.label,
      side: division.side,
      troop: part.troop,
      soldiers: part.ships,
      ...(index === middle ? { labelled: true } : {}),
      start: { at: shifted(start.at, start.facing, share * start.width), facing: start.facing, width: start.width * fraction, depth: start.depth },
      moves,
    }
  })
}

const OUT_OF_THE_STRAIT: Point[] = [
  [200, 100],
  [-700, -700],
]

const DIVISIONS: Division[] = [
  {
    id: 'antoine-droite',
    label: 'Aile droite : Antoine et Publicola',
    side: 'enemy',
    parts: [
      { troop: 'decere', ships: 15, label: "Décères et ennères de l'aile droite" },
      { troop: 'hexere', ships: 22, label: "Hexères et heptères de l'aile droite" },
      { troop: 'quinquereme', ships: 19, label: "Quinquérèmes de l'aile droite" },
    ],
    start: { at: [250, 550], facing: 195, width: 220, depth: 600 },
    moves: [
      { phase: 1, via: OUT_OF_THE_STRAIT, at: [-1560, -1250], facing: 275, width: 1050, depth: 240, action: 'march' },
      { phase: 2 },
      { phase: 3, action: 'fight', losses: 0.02 },
      { phase: 4, at: [-1700, -1050], facing: 300, action: 'fight', losses: 0.04 },
      { phase: 5, losses: 0.05 },
      { phase: 6, losses: 0.07 },
      { phase: 7, losses: 0.1 },
      { phase: 8, at: [-1500, -1150], facing: 285, action: 'stand', losses: 0.11 },
    ],
  },
  {
    id: 'antoine-centre',
    label: 'Centre : Marcus Octavius et Marcus Insteius',
    side: 'enemy',
    parts: [
      { troop: 'quinquereme', ships: 10, label: 'Quinquérèmes du centre' },
      { troop: 'hexere', ships: 11, label: 'Hexères et heptères du centre' },
      { troop: 'decere', ships: 14, label: 'Décères et ennères du centre' },
      { troop: 'hexere', ships: 11, label: 'Hexères et heptères du centre' },
      { troop: 'quinquereme', ships: 10, label: 'Quinquérèmes du centre' },
    ],
    start: { at: [700, 1500], facing: 240, width: 220, depth: 600 },
    moves: [
      { phase: 1, via: [[450, 900], [150, 0], [-700, -1200]], at: [-1680, -2330], facing: 275, width: 1050, depth: 240, action: 'march' },
      { phase: 2 },
      { phase: 3, action: 'fight', losses: 0.02 },
      { phase: 4, losses: 0.04 },
      { phase: 5, losses: 0.06 },
      { phase: 6, losses: 0.08 },
      { phase: 7, losses: 0.12 },
      { phase: 8, at: [-1550, -2300], action: 'stand', losses: 0.13 },
    ],
  },
  {
    id: 'antoine-gauche',
    label: 'Aile gauche : Coelius',
    side: 'enemy',
    parts: [
      { troop: 'quinquereme', ships: 20, label: "Quinquérèmes de l'aile gauche" },
      { troop: 'hexere', ships: 22, label: "Hexères et heptères de l'aile gauche" },
      { troop: 'decere', ships: 15, label: "Décères et ennères de l'aile gauche" },
    ],
    start: { at: [1500, 1700], facing: 260, width: 220, depth: 600 },
    moves: [
      { phase: 1, via: [[700, 1150], [250, 500], [100, -200], [-700, -1900]], at: [-1780, -3420], facing: 275, width: 1050, depth: 240, action: 'march' },
      { phase: 2, at: [-2250, -3500], action: 'march' },
      { phase: 3, action: 'fight', losses: 0.02 },
      { phase: 4, losses: 0.04 },
      { phase: 5, losses: 0.05 },
      { phase: 6, losses: 0.07 },
      { phase: 7, losses: 0.1 },
      { phase: 8, at: [-2050, -3450], action: 'stand', losses: 0.11 },
    ],
  },
  {
    id: 'agrippa',
    label: 'Aile gauche : Agrippa',
    side: 'rome',
    parts: [
      { troop: 'liburne', ships: 35, label: "Liburnes d'Agrippa" },
      { troop: 'trireme', ships: 20, label: "Trirèmes d'Agrippa" },
      { troop: 'polyreme', ships: 25, label: "Quadrirèmes à hexères d'Agrippa" },
      { troop: 'trireme', ships: 20, label: "Trirèmes d'Agrippa" },
      { troop: 'liburne', ships: 35, label: "Liburnes d'Agrippa" },
    ],
    start: { at: [-5200, 4000], facing: 190, width: 300, depth: 1200 },
    moves: [
      { phase: 1, via: [[-4200, 1200], [-3700, -400]], at: [-3060, -1100], facing: 95, width: 1500, depth: 260, action: 'march' },
      { phase: 2, at: [-2950, -1050] },
      { phase: 3, at: [-1860, -1180], action: 'fight', losses: 0.01 },
      { phase: 4, at: [-2200, -1000], facing: 115, width: 1000, action: 'fight', losses: 0.02 },
      { phase: 5 },
      { phase: 6 },
      { phase: 7, at: [-2350, -1000], action: 'skirmish', losses: 0.03 },
      { phase: 8, at: [-2000, -1050], facing: 110, action: 'stand' },
    ],
  },
  {
    id: 'arruntius',
    label: 'Centre : Arruntius',
    side: 'rome',
    parts: [
      { troop: 'liburne', ships: 33, label: "Liburnes d'Arruntius" },
      { troop: 'trireme', ships: 20, label: "Trirèmes d'Arruntius" },
      { troop: 'polyreme', ships: 25, label: "Quadrirèmes à hexères d'Arruntius" },
      { troop: 'trireme', ships: 20, label: "Trirèmes d'Arruntius" },
      { troop: 'liburne', ships: 32, label: "Liburnes d'Arruntius" },
    ],
    start: { at: [-4700, 2300], facing: 190, width: 300, depth: 1200 },
    moves: [
      { phase: 1, via: [[-4000, -500]], at: [-3180, -2550], facing: 95, width: 1450, depth: 260, action: 'march' },
      { phase: 2 },
      { phase: 3, at: [-1990, -2400], action: 'fight', losses: 0.01 },
      { phase: 4, at: [-1950, -2380], losses: 0.02 },
      { phase: 5 },
      { phase: 6 },
      { phase: 7, at: [-2200, -2420], action: 'skirmish', losses: 0.03 },
      { phase: 8, at: [-1900, -2400], action: 'stand' },
    ],
  },
  {
    id: 'lurius',
    label: 'Aile droite : Lurius et Octavien',
    side: 'rome',
    parts: [
      { troop: 'liburne', ships: 35, label: 'Liburnes de Lurius' },
      { troop: 'trireme', ships: 20, label: 'Trirèmes de Lurius' },
      { troop: 'polyreme', ships: 25, label: 'Quadrirèmes à hexères de Lurius' },
      { troop: 'trireme', ships: 20, label: 'Trirèmes de Lurius' },
      { troop: 'liburne', ships: 29, label: 'Liburnes de Lurius' },
    ],
    start: { at: [-4200, 600], facing: 190, width: 300, depth: 1200 },
    moves: [
      { phase: 1, via: [[-4100, -1500]], at: [-3320, -4100], facing: 95, width: 1500, depth: 260, action: 'march' },
      { phase: 2, at: [-3750, -4250], action: 'march' },
      { phase: 3, at: [-2520, -3600], action: 'fight', losses: 0.01 },
      { phase: 4, losses: 0.02 },
      { phase: 5 },
      { phase: 6 },
      { phase: 7, at: [-2720, -3620], action: 'skirmish', losses: 0.03 },
      { phase: 8, at: [-2400, -3550], action: 'stand' },
    ],
  },
]

const SINGLE_UNITS: Unit[] = [
  {
    id: 'cleopatre',
    label: 'Cléopâtre (60 navires)',
    side: 'enemy',
    troop: 'egyptien',
    soldiers: 60,
    labelled: true,
    start: { at: [2400, 1700], facing: 265, width: 260, depth: 500 },
    moves: [
      { phase: 1, via: [[900, 1250], [300, 600], [100, -300], [-500, -1700]], at: [-1050, -2050], facing: 275, width: 600, depth: 260, action: 'march' },
      { phase: 2 },
      { phase: 3 },
      { phase: 4 },
      { phase: 5, via: [[-1750, -1700], [-2700, -2000], [-3600, -3500]], at: [-3500, -6200], facing: 190, width: 450, depth: 650, action: 'march' },
      { phase: 6, at: [-3200, -9000], facing: 175, action: 'march' },
      { phase: 7, at: [-3000, -11500] },
      { phase: 8, at: [-2800, -14000], action: 'march' },
    ],
  },
  {
    id: 'navire-d-antoine',
    label: 'Antoine',
    side: 'enemy',
    troop: 'quinquereme',
    soldiers: 1,
    labelled: true,
    start: { at: [350, 850], facing: 195, width: 20, depth: 40 },
    moves: [
      { phase: 1, via: [[200, 150], [-600, -650]], at: [-1350, -1150], facing: 275, action: 'march' },
      { phase: 2 },
      { phase: 3 },
      { phase: 4, at: [-1450, -1000], facing: 300 },
      { phase: 5 },
      { phase: 6, via: [[-1800, -1650], [-2800, -2000], [-3700, -3600], [-3650, -6500]], at: [-3300, -8700], facing: 175, action: 'march' },
      { phase: 7, at: [-3050, -11300] },
      { phase: 8, at: [-2850, -13800], action: 'march' },
    ],
  },
  {
    id: 'liburnes-en-poursuite',
    label: 'Liburnes en poursuite',
    side: 'rome',
    troop: 'liburne',
    soldiers: 6,
    labelled: true,
    start: { at: [-4000, 1300], facing: 190, width: 120, depth: 160 },
    moves: [
      { phase: 1, via: [[-3950, -1500]], at: [-3500, -4600], facing: 95, width: 200, depth: 80, action: 'march' },
      { phase: 2, at: [-3900, -4700], action: 'march' },
      { phase: 3, at: [-2900, -4100] },
      { phase: 4 },
      { phase: 5 },
      { phase: 6, via: [[-3500, -5200]], at: [-3400, -7900], facing: 175, width: 120, depth: 200, action: 'march' },
      { phase: 7, at: [-3000, -4600], facing: 20, action: 'march' },
      { phase: 8, at: [-2700, -4200], facing: 60 },
    ],
  },
  {
    id: 'armee-de-taurus',
    label: 'Armée de terre de Taurus',
    side: 'rome',
    troop: 'armee',
    soldiers: 12,
    labelled: true,
    start: { at: [-2000, 300], facing: 180, width: 900, depth: 200 },
    moves: [],
  },
  {
    id: 'armee-de-canidius',
    label: 'Armée de terre de Canidius',
    side: 'enemy',
    troop: 'armee',
    soldiers: 12,
    labelled: true,
    start: { at: [600, -950], facing: 265, width: 700, depth: 220 },
    moves: [],
  },
]

export const ACTIUM: Battle = {
  scale: 1,
  latitude: 38.95,
  declination: 9.5,
  tacticalScale: 1.5,
  legend: '1 maquette = 1 navire',
  sides: { rome: "Flotte d'Octavien", enemy: "Flotte d'Antoine et de Cléopâtre" },
  phases: [
    {
      id: 'le-face-a-face-du-matin',
      hour: 8.5,
      clock: "de l'aube à 11 h environ",
      seconds: 15,
      focus: [-1500, -1300],
      span: 8200,
      ground: { unit: 'antoine-centre-decere', along: 150, across: 0, look: 400, turn: 180 },
      arrows: [
        { side: 'enemy', kind: 'move', path: [[350, 900], [200, 100], [-700, -800], [-1500, -2200]] },
        { side: 'rome', kind: 'move', path: [[-4700, 2300], [-4000, -500], [-3300, -2400]] },
      ],
      counters: [
        { label: "Navires d'Antoine et de Cléopâtre", from: 0, to: 230 },
        { label: "Navires d'Octavien", from: 0, to: 400 },
      ],
    },
    {
      id: 'le-vent-de-mer',
      hour: 11.5,
      clock: 'vers 11 h à midi (6e heure)',
      seconds: 10,
      focus: [-2700, -2600],
      span: 5200,
      ground: { unit: 'antoine-gauche-decere', along: 200, across: 0, look: 400, turn: 180 },
      arrows: [
        { side: 'enemy', kind: 'move', path: [[-1850, -3420], [-2300, -3520]] },
        { side: 'rome', kind: 'move', path: [[-3350, -4100], [-3800, -4280]] },
        { side: 'rome', kind: 'move', path: [[-3100, -1300], [-2800, -1000]] },
      ],
    },
    {
      id: 'l-assaut-des-citadelles-flottantes',
      hour: 12.5,
      clock: "de midi au début de l'après-midi",
      seconds: 14,
      focus: [-2100, -2400],
      span: 4600,
      ground: { unit: 'arruntius-liburne', along: 150, across: 0, look: 300 },
      arrows: [
        { side: 'rome', kind: 'attack', path: [[-2900, -1250], [-2000, -1200]] },
        { side: 'rome', kind: 'attack', path: [[-3000, -2500], [-2120, -2400]] },
        { side: 'rome', kind: 'attack', path: [[-3300, -3900], [-2660, -3620]] },
        { side: 'enemy', kind: 'attack', path: [[-1700, -2330], [-1900, -2360]] },
      ],
      counters: [{ label: 'Navires engagés', from: 0, to: 570 }],
    },
    {
      id: 'agrippa-deborde-au-nord',
      hour: 13.2,
      clock: "début de l'après-midi (estimation)",
      seconds: 10,
      focus: [-2000, -1500],
      span: 3800,
      ground: { unit: 'agrippa-liburne', along: 150, across: 0, look: 500 },
      arrows: [
        { side: 'rome', kind: 'attack', path: [[-2900, -1500], [-2350, -900], [-1950, -700]] },
        { side: 'enemy', kind: 'move', path: [[-1600, -1350], [-1680, -950]] },
      ],
    },
    {
      id: 'la-percee-de-cleopatre',
      hour: 13.8,
      clock: 'vers 13 h à 14 h (estimation)',
      seconds: 12,
      focus: [-2600, -4300],
      span: 7600,
      ground: { unit: 'cleopatre', along: -380, across: 0, look: 700 },
      arrows: [{ side: 'enemy', kind: 'move', path: [[-1050, -2050], [-1750, -1700], [-2700, -2000], [-3600, -3500], [-3500, -6000]] }],
    },
    {
      id: 'antoine-suit-la-reine',
      hour: 14.3,
      clock: 'aussitôt après (heure non transmise)',
      seconds: 10,
      focus: [-3000, -6800],
      span: 9000,
      ground: { unit: 'navire-d-antoine', along: -120, across: 0, look: 600 },
      arrows: [
        { side: 'enemy', kind: 'flee', path: [[-1400, -1150], [-1800, -1650], [-2800, -2000], [-3700, -3800], [-3350, -8500]] },
        { side: 'rome', kind: 'attack', path: [[-3450, -4800], [-3450, -7600]] },
      ],
    },
    {
      id: 'le-feu',
      hour: 15.2,
      clock: "fin de l'après-midi (heure non transmise)",
      seconds: 10,
      focus: [-2000, -2300],
      span: 4400,
      ground: { unit: 'antoine-centre-decere', along: 150, across: 0, look: 400, turn: 180 },
      arrows: [
        { side: 'rome', kind: 'attack', path: [[-2450, -1050], [-1900, -1100]] },
        { side: 'rome', kind: 'attack', path: [[-2350, -2420], [-1800, -2350]] },
        { side: 'rome', kind: 'attack', path: [[-2850, -3620], [-2350, -3500]] },
      ],
    },
    {
      id: 'la-flotte-cede',
      hour: 16.3,
      clock: 'vers 15 h 15 à 16 h 20 (10e heure), puis le soir',
      seconds: 12,
      focus: [-2000, -2300],
      span: 6000,
      ground: { unit: 'antoine-centre-decere', along: 300, across: 0, look: 800, turn: 180 },
      arrows: [
        { side: 'rome', kind: 'move', path: [[-2300, -2420], [-1950, -2400]] },
        { side: 'rome', kind: 'move', path: [[-2500, -1100], [-2100, -1050]] },
      ],
      counters: [
        { label: "Morts au plus, selon les Mémoires d'Auguste", from: 0, to: 5000 },
        { label: 'Morts selon Orose', from: 0, to: 12000 },
        { label: 'Navires pris sur toute la campagne', from: 0, to: 300 },
      ],
    },
  ],
  units: [...DIVISIONS.flatMap(split), ...SINGLE_UNITS],
}
