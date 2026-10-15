import type { PageId } from '../core/route.ts'

export interface Page {
  id: PageId
  title: string
  description: string
  body: string
}

export const pages: Page[] = [
  {
    id: 'mentions-legales',
    title: 'Mentions légales',
    description: 'Éditeur, hébergeur et propriété intellectuelle du site Roma.',
    body: `## Éditeur

Ce site est édité à titre personnel et non commercial par **Maximator13** (pseudonyme).

Contact : par les [issues du dépôt GitHub](https://github.com/Maximator13/roma/issues).

## Hébergeur

GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis ([github.com](https://github.com)), via le service GitHub Pages.

## Propriété intellectuelle

Le code source est publié sous licence MIT. Les contenus originaux (textes, données, modèles 3D et vidéos produits pour le projet) sont publiés sous licence [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/deed.fr). Les ressources de tiers gardent leur propre licence : voir la page Sources et crédits.`,
  },
  {
    id: 'confidentialite',
    title: 'Confidentialité',
    description: "Données personnelles, stockage local et mesure d'audience sur le site Roma.",
    body: `## En bref

Ce site ne dépose aucun cookie et ne vous demande aucune donnée personnelle. Toutes ses ressources (code, polices, images, modèles 3D) sont servies par le site lui-même : votre navigateur ne contacte aucun service tiers.

## Stockage dans votre navigateur

Le site peut enregistrer dans votre navigateur (\`localStorage\`) vos préférences, votre choix sur la mesure d'audience et, plus tard, votre progression dans les jeux de révision. Ces données restent sur votre appareil ; vous pouvez les effacer à tout moment depuis les réglages de votre navigateur.

## Mesure d'audience

Aucune mesure d'audience n'est active pour l'instant. Si elle est activée, elle reposera sur GoatCounter, un outil sans cookie qui ne conserve pas votre adresse IP, et ne se chargera qu'après votre accord explicite. Vous pourrez retirer cet accord à tout moment.

## Hébergement

L'hébergeur, GitHub, peut journaliser les adresses IP des visiteurs pour assurer la sécurité de son service. Voir la [déclaration de confidentialité de GitHub](https://docs.github.com/fr/site-policy/privacy-policies/github-general-privacy-statement).`,
  },
  {
    id: 'conditions',
    title: "Conditions d'utilisation",
    description: "Conditions d'utilisation du site Roma : accès, contenus, licences et responsabilité.",
    body: `## Objet

Roma est un site éducatif gratuit, consacré à l'histoire romaine de 753 av. J.-C. à 1453. Il est accessible sans inscription.

## Contenus

Les contenus sont rédigés avec soin et appuyés sur des sources citées pour chaque événement. Les dates traditionnelles, légendaires ou débattues sont signalées comme telles. Le site est fourni en l'état, sans garantie d'exactitude ni d'exhaustivité. Pour signaler une erreur, ouvrez une [issue sur le dépôt](https://github.com/Maximator13/roma/issues).

## Réutilisation

Vous pouvez réutiliser les contenus originaux selon la licence CC BY 4.0, en citant « Roma, de Romulus à Constantin XI, par Maximator13 » et l'adresse du dépôt. Le code est sous licence MIT. Les ressources de tiers suivent leur propre licence.

## Liens externes

Les liens vers d'autres sites (traductions de sources antiques, ouvrages, bases de données) sont fournis pour information ; l'éditeur n'est pas responsable de leur contenu.

## Évolution

Ces conditions peuvent évoluer avec le site. Elles sont régies par le droit français.`,
  },
  {
    id: 'sources',
    title: 'Sources et crédits',
    description: 'Méthode, conventions de dates, sources et crédits du site Roma.',
    body: `## Méthode

Chaque événement indique sa date, son niveau de certitude et au moins une source : un auteur antique, avec la référence du passage, ou un ouvrage de référence moderne.

- **Attesté** : fait rapporté par des sources contemporaines ou jugées fiables.
- **Traditionnel** : transmis par la tradition antique, plausible mais sans source contemporaine (la plupart des dates de la royauté et des débuts de la République).
- **Légendaire** : récit légendaire, sans fondement historique établi.
- **Débattu** : date ou fait discuté par les historiens ; la fourchette est indiquée.

## Dates

Il n'y a pas d'an 0 : l'an 1 av. J.-C. est suivi de l'an 1 apr. J.-C. De 753 av. J.-C. à 1453, la frise couvre donc 2 205 ans. Les dates antérieures à notre ère portent la mention « av. J.-C. » ; les autres n'ont pas de mention, sauf entre l'an 1 et l'an 99.

Les bornes des époques sont des conventions d'historiens, expliquées pour chacune d'elles. Les habitants de l'Empire d'Orient se disaient Romains : le nom d'« Empire byzantin » est une invention moderne.

## Crédits

- Polices : Cinzel (Natanael Gama) et EB Garamond (Georg Duffner et Octavio Pardo), sous licence SIL Open Font License 1.1.
- Bibliothèques : React, three.js, React Three Fiber, drei, Zustand et marked (licence MIT), postprocessing (licence zlib), GSAP (licence gratuite propre à Webflow).
- Relief et fonds marins : NOAA NCEI, ETOPO 2022 (domaine public), [doi:10.25921/fd45-gt74](https://doi.org/10.25921/fd45-gt74).
- Traits de côte et lacs : Made with Natural Earth (domaine public).
- Lieux antiques : [Pleiades](https://pleiades.stoa.org), © les contributeurs, CC BY 3.0.
- Territoires romains année par année : J. S. Bennett, E. Mutch, A. Tollefson et al., [Cliopatria v0.2.1](https://github.com/Seshat-Global-History-Databank/cliopatria) (Seshat Global History Databank), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) ; données modifiées (extraction des entités romaines, simplification, dates alignées sur le projet, lacune byzantine de 1402 à 1406 comblée par la géométrie identique des années voisines).

La liste complète des ressources, avec leurs auteurs, licences et modifications, est tenue à jour dans le fichier [CREDITS.md](https://github.com/Maximator13/roma/blob/main/CREDITS.md) du dépôt.`,
  },
]
