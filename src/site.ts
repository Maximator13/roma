export const SITE = {
  origin: 'https://maximator13.github.io',
  base: '/roma/',
  name: 'Roma',
  title: 'Roma, de Romulus à Constantin XI',
  description:
    "Frise chronologique interactive de l'histoire romaine, de la fondation de Rome (753 av. J.-C.) à la chute de Constantinople (1453) : dates, niveau de certitude et sources.",
  repository: 'https://github.com/Maximator13/roma',
  publisher: 'Maximator13',
} as const

export const SITE_URL = `${SITE.origin}${SITE.base}`

export const ANALYTICS: { goatcounterCode: string | null } = {
  goatcounterCode: null,
}
