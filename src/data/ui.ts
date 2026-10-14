import type { PageId } from '../core/route.ts'
import type { Category, Certainty } from './schema.ts'

export const CERTAINTY: Record<Certainty, { label: string; description: string }> = {
  attested: {
    label: 'Attesté',
    description: 'Fait rapporté par des sources contemporaines ou jugées fiables.',
  },
  traditional: {
    label: 'Traditionnel',
    description: 'Transmis par la tradition antique : plausible, mais sans source contemporaine.',
  },
  legendary: {
    label: 'Légendaire',
    description: 'Récit légendaire, sans fondement historique établi.',
  },
  debated: {
    label: 'Débattu',
    description: 'Date ou fait discuté par les historiens.',
  },
}

export const CATEGORY: Record<Category, string> = {
  politics: 'Politique',
  war: 'Guerre',
  building: 'Construction',
  religion: 'Religion',
  society: 'Société',
  culture: 'Culture',
}

export const UI = {
  brand: 'Roma',
  subtitle: 'de Romulus à Constantin XI',
  tagline:
    "Deux mille deux cent cinq ans d'histoire romaine, de la fondation légendaire de Rome à la chute de Constantinople.",
  startCta: 'Commencer en 753 av. J.-C.',
  timelineLabel: 'Frise chronologique',
  timelineHelp:
    'Molette ou pincement : zoom. Glisser ou flèches : déplacement. Page précédente ou suivante : époque. 0 : vue entière.',
  currentYear: 'Année au centre de la frise',
  close: 'Fermer',
  certainty: 'Certitude',
  category: 'Catégorie',
  era: 'Époque',
  place: 'Lieu',
  people: 'Personnes',
  ancientSources: 'Sources antiques',
  modernSources: 'Ouvrages de référence',
  openSource: 'consulter',
  legend: 'Certitude',
  notFoundTitle: 'Page introuvable',
  notFoundText: 'Cette adresse ne correspond à aucun contenu du site.',
  backHome: 'Revenir à la frise',
  footerLabel: 'Informations sur le site',
  consentText:
    "Ce site peut mesurer sa fréquentation avec GoatCounter, sans cookie et de façon anonyme, si vous l'acceptez.",
  consentAccept: 'Accepter',
  consentRefuse: 'Refuser',
  consentManage: "Mesure d'audience",
  webglMissing: "La scène 3D ne peut pas s'afficher sur cet appareil ; la frise reste utilisable.",
} as const

export const PAGE_LINKS: { id: PageId; label: string }[] = [
  { id: 'sources', label: 'Sources et crédits' },
  { id: 'mentions-legales', label: 'Mentions légales' },
  { id: 'confidentialite', label: 'Confidentialité' },
  { id: 'conditions', label: "Conditions d'utilisation" },
]
