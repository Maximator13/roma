# Architecture

Ce document décrit comment le site est construit et pourquoi. Il complète `docs/BRIEF.md` (le but) et `docs/PROGRESS.md` (l'avancement). Il a été établi en phase 0 à partir de recherches vérifiées (stack, hébergement, licences, chaîne 3D) et de deux propositions d'architecture indépendantes, l'une centrée sur la performance, l'autre sur la simplicité.

## 1. Vue d'ensemble

- Une application monopage statique (Vite, React, TypeScript strict), servie par GitHub Pages sous `/roma/`.
- **Un seul `Canvas` WebGL 2**, monté une fois et jamais démonté, derrière l'interface. La carte et les scènes (phases 2 et 4) s'y succèdent : les ressources GPU ne se partagent pas entre contextes WebGL, les navigateurs limitent le nombre de contextes, et seule une caméra unique permet de circuler en continu.
- **La frise est en DOM**, pas en WebGL : chaque événement est un bouton accessible au clavier et aux lecteurs d'écran, avec un vrai texte.
- **Routage par hash** (`#/evenement/<slug>`), complété par une page statique par événement (`/roma/evenement/<slug>/`) pour les moteurs de recherche et les réseaux sociaux (section 8).
- Les données sont des fichiers TypeScript validés par zod avant chaque build ; zod n'est pas envoyé au navigateur.

## 2. Arborescence

```
.github/workflows/deploy.yml   contrôles, build, tests Playwright, déploiement Pages
docs/                          BRIEF, PROGRESS, ARCHITECTURE, A_VERIFIER
public/                        favicon, image de partage
scripts/
  check-style.ts               aucun commentaire dans le code, aucun tiret cadratin ni demi-cadratin
  validate-data.ts             validation zod et références croisées, avant chaque build
  postbuild.ts                 pages de partage, sitemap.xml, 404.html, budget du site
src/
  core/      dates.ts (module de dates unique), route.ts, motion.ts, analytics.ts
  data/      schema.ts (zod), eras, tracks, events, places, people, scenes, pages, ui
  timeline/  viewport, ticks, layout (zoom sémantique), lanes, keys, Timeline.tsx
  stage/     Stage.tsx (Canvas), Backdrop, GradingEffect, grading, quality, DebugHud
  ui/        panels (cartels), Markdown, ConsentBanner
  scenes/    une scène par dossier, à partir de la phase 2
blender/     un script par scène, à partir de la phase 2
tests/       smoke.spec.ts (fumée et poids du premier écran), look.spec.ts (captures)
```

## 3. Données

1. **Saisie** : un fichier par type dans `src/data/`, typé par `z.infer` depuis `schema.ts` (import de type, effacé à la compilation).
2. **Validation** (`npm run validate`, lancé par `npm run build` et par les tests) :
   - schémas zod (slugs, années dans le domaine, précision cohérente avec mois et jour, au moins une source) ;
   - identifiants uniques ;
   - début de l'événement dans son époque (une année frontière appartient aux deux époques voisines) ;
   - piste active à la date de l'événement ;
   - lieux, personnes et scènes référencés existants ;
   - époques contiguës de 753 av. J.-C. à 1453 ;
   - aucun tiret cadratin ni demi-cadratin dans aucun texte.
3. **Exécution** : l'application importe les données directement. Le markdown des corps de texte est rendu par `marked` à l'ouverture d'un cartel.

Les scripts du dossier `scripts/` sont exécutés par Node 24 sans compilation (suppression native des types). D'où les règles du `tsconfig` : imports relatifs avec extension `.ts`, `erasableSyntaxOnly`, `verbatimModuleSyntax`.

## 4. Dates

Toutes les dates passent par `src/core/dates.ts`, couvert par des tests :

- années astronomiques : 1 av. J.-C. = 0, 753 av. J.-C. = -752 ; de 753 av. J.-C. à 1453, 2 205 ans ;
- écriture française : « av. J.-C. » une fois par intervalle ; « apr. J.-C. » seulement de l'an 1 à l'an 99 et pour le Ier siècle ;
- précisions jour, mois, année, décennie (« vers 120 ») et siècle (« IIIe siècle av. J.-C. ») ;
- les jours et les mois sont ceux que donnent les sources : calendrier romain préjulien avant la réforme de César (45 av. J.-C.), calendrier julien ensuite, sans conversion (voir `docs/A_VERIFIER.md`).

Les graduations de la frise tombent sur des années historiques rondes des deux côtés de l'ère, sans jamais afficher d'an 0.

## 5. Frise

- **Géométrie** : une fenêtre `{center, span}` en années, entre 10 ans et 2 205 ans plus une marge. Le zoom garde fixe l'année sous le curseur.
- **Zoom sémantique** : importance 1 visible partout, 2 sous 700 ans de fenêtre, 3 sous 160 ans. Placement glouton des étiquettes sur trois rangées pour la piste principale ; un événement sans place reste un repère cliquable sur la ligne de base.
- **Pistes parallèles** : chaque piste a une rangée et ses périodes d'activité. Rome jusqu'en 395, puis Orient et Occident ; Empire des Gaules et Palmyre pendant la crise du IIIe siècle ; Nicée, Empire latin, Épire et Trébizonde à partir de 1204. Les rangées secondaires n'apparaissent que si une de leurs pistes est visible.
- **Navigation** :
  - molette : zoom autour du curseur ;
  - molette horizontale ou Maj+molette : déplacement ;
  - glisser : déplacement ; pincement : zoom ;
  - clavier : flèches, + et -, Début et Fin, Page précédente et Page suivante pour changer d'époque, 0 pour la vue entière ;
  - Échap ferme un cartel.

  Toutes les animations utilisent une seule famille de courbes (GSAP `power3`) ; avec `prefers-reduced-motion`, elles deviennent instantanées.
- **Certitude** : forme du repère, jamais la couleur seule (plein : attesté, anneau : traditionnel, pointillés : légendaire, demi : débattu), répétée dans le nom accessible.
- **Étalonnage de l'interface** : la couleur d'accent suit l'époque au centre de la frise. Un test garantit un contraste d'au moins 4,5:1 sur toute la frise.

## 6. Scène 3D, qualité adaptative et HUD

- **Chargement** : le module `Stage` (three.js, R3F, post-traitement) est un chunk séparé, demandé après le premier affichage. La frise est utilisable avant.
- **Étalonnage par époque** : un effet de post-traitement maison (exposition, contraste, saturation, lift et gain), fusionné dans la même passe que le tone mapping ACES et le vignettage. Les réglages par époque sont dans `src/stage/grading.ts` et se fondent sur 20 ans de part et d'autre de chaque frontière. Ils sont lus à chaque image depuis l'état, sans rendu React.
- **Paliers de qualité** :

| Palier | Densité de pixels | Tampon d'image | Anticrénelage | Ombres |
|---|---|---|---|---|
| bas | 1 | 8 bits | aucun | non |
| moyen | jusqu'à 1,25 | demi-flottant | 2x | oui |
| haut | jusqu'à 2 | demi-flottant | 4x | oui |

  - Palier initial : bas sur écran tactile, sur 4 cœurs ou moins, ou si le navigateur signale un rendu logiciel (`failIfMajorPerformanceCaveat`) ; moyen sinon.
  - `PerformanceMonitor` de drei monte ou descend ensuite d'un palier selon la fréquence mesurée.
  - Pour forcer un palier : `?quality=low`, `?quality=medium` ou `?quality=high`.
- **HUD** (`?debug`) : i/s, durée d'image, appels de dessin, triangles, géométries, textures, programmes, mémoire JS, palier, densité de pixels et nom du GPU. Les compteurs couvrent toutes les passes de l'image.
- **Mesures** : les i/s ne se mesurent pas en CI, où le rendu est logiciel ; elles se mesurent sur la machine de référence.

## 7. Scènes (contrat pour les phases 2 et 4)

- Une scène = un dossier `src/scenes/<id>/index.tsx`, découvert par `import.meta.glob` (chargement différé, un chunk par scène), plus une entrée dans `src/data/scenes.ts` et un script `blender/<id>.py`. La validation échoue si l'un des deux côtés manque.
- Le module exporte un composant rendu dans le `Canvas` persistant, une pose de caméra d'entrée et la liste de ses fichiers.
- Cycle de vie :
  1. préchargement quand l'événement est survolé ou centré (sauf mode économie de données) ;
  2. chargement avec indicateur de progression fondé sur les tailles du manifeste d'assets ;
  3. compilation des shaders (`compileAsync`) avant l'affichage ;
  4. entrée par la caméra ;
  5. libération des ressources à la sortie.
- Passage carte vers scène : la caméra plonge vers le lieu, un voile de brume monte pendant 300 à 500 ms, la scène remplace la carte avec une pose qui prolonge le mouvement, puis le voile retombe. Carte et scène gardent chacune leur origine (précision des flottants). Avec `prefers-reduced-motion`, il ne reste que le fondu.
- Budget par scène : le code de la scène hors premier écran, plus ses fichiers (gzip pour les types que Pages compresse, taille brute pour KTX2, MP4, WebP).

### Implémentation (phase 2)

- **Données** : une scène de `src/data/scenes.ts` passe au statut `ready` seulement avec sa date (`year`), son lieu (`lat`, `lon`), son résumé et ses points d'intérêt (`points` : identifiant, titre, cartel, sources). `npm run validate` refuse une scène prête sans `src/scenes/<id>/index.tsx` ni `blender/<id>.py`, et tout dossier de scène sans entrée de données.
- **Registre** : `src/scenes/registry.ts` découvre les modules par `import.meta.glob('./*/index.tsx')` ; `isPlayable` exige le statut `ready` et le module.
- **Bascule** : `src/stage/useSceneSwap.ts` attend la plongée de la carte (1,3 s, zéro en mouvement réduit) et le module, lève le voile (0,45 s), monte la scène, attend `compileAsync` (4 s au plus), puis baisse le voile (0,9 s). Un échec de chargement ramène à la carte et l'affiche dans le cartel.
- **Kit glTF** (`src/scenes/kit/`) : `useSceneModel` charge `assets/<chemin>.glb` avec meshopt et KTX2 et repère les nœuds vides `poi_<id>` ; `Atmosphere` pose ciel, brume, lumière d'ambiance et soleil (ombres qui suivent la caméra) ; `GuidedRail` déplace la caméra entre la vue d'ensemble et les points d'intérêt sur une courbe en arc (2,4 à 6,5 s), avec un regard libre limité (environ 26° de côté, 13° en hauteur). Une scène simple tient en une configuration (`ModelScene`) : modèle, soleil, brume, vue d'ensemble.
- **Repères dans Blender** : un nœud vide `poi_<id>` par point d'intérêt, placé à la position de la caméra et orienté vers le sujet (axe -Z local après export glTF, +Y en haut). L'optimisation garde ces nœuds (`prune` avec `keepLeaves`).
- **Fichiers** : `npm run assets` optimise `.cache/scenes/<id>/<id>.glb` vers `.cache/build/scenes/<id>/<id>.glb` ; `npm run assets:publish` les publie ; `npm run assets:pull` les place dans `public/assets/` (ignoré par git), en CI avant le build.

## 8. Routage, état et pages de partage

- **Routes** : `#/`, `#/evenement/<slug>`, `#/mentions-legales`, `#/confidentialite`, `#/conditions`, `#/sources` ; toute autre adresse affiche « Page introuvable ». Le titre du document suit la route.
- **Navigation interne** : `history.pushState`. Un écouteur global intercepte les liens internes, y compris ceux des textes markdown. Retour, avance et rechargement conservent l'état.
- **Pages de partage** : le post-build copie `index.html` pour chaque événement dans `/roma/evenement/<slug>/`, avec un titre, une description, une URL canonique et une carte Open Graph et Twitter propres, plus un cartel statique dans `#root` pour les robots. Le visiteur arrive directement sur l'événement dans l'application, sans redirection. Contrairement à une redirection, cela permet aux moteurs d'indexer chaque événement.
- **État** : un magasin Zustand (`route`, `view`, `quality`). La fenêtre de la frise, modifiée à chaque image pendant un geste, est lue directement par la scène 3D sans passer par React.

## 9. Build, CI et budgets

- `npm run check` : style (commentaires, tirets), ESLint, typage, tests unitaires Vitest.
- `npm run build` : validation des données, build Vite, post-build. Le post-build échoue au-delà de 600 Mo pour le site ou 100 Mo pour un fichier.
- `npm run test:e2e` (Playwright, ordinateur et mobile) :
  - aucune erreur console ;
  - navigation au clavier, pages légales, page introuvable, HUD, ouverture, rechargement et page de partage d'un événement ;
  - **poids du premier écran** : somme des fichiers réellement demandés, gzip pour les types que Pages compresse, au plus 5 Mo. Le relevé est écrit dans `reports/`.
- **CI GitHub Actions** : contrôles, build, Playwright, puis déploiement Pages. Les versions des actions sont les majeures actuelles (checkout v7, setup-node v7, configure-pages v6, upload-pages-artifact v5, deploy-pages v5).

## 10. Assets lourds

Décision validée en phase 0 : **GitHub Releases versionnées et manifeste versionné**.

- **Dans git** : les sources (scripts Blender, données, code) et les petits fichiers de moins de 1 Mo.
- **Jamais versionné ni publié** : les fichiers `.blend`, les rendus intermédiaires et les glTF non optimisés. Les scripts les régénèrent.
- **Dans des releases `assets-vN`** : chaque `.glb`, `.ktx2`, `.mp4` et tout fichier de plus de 1 Mo. Les noms sont adressés par contenu, et une release ne contient que les fichiers modifiés.
- **Manifeste versionné** : chemin, taille, SHA-256 et release de chaque fichier.
- **Récupération** : `npm run assets:pull` télécharge, vérifie l'empreinte et échoue au moindre écart. La CI met ce dossier en cache, avec le manifeste comme clé.
- **Pourquoi pas les autres options** : versionner les binaires ferait passer l'historique au-delà de 1 Go sans retour possible ; Git LFS consommerait le quota de 10 Gio/mois à chaque clone de visiteur.
- **Calendrier** : ces scripts arrivent en phase 2, avec le premier `.glb`.
- **Décodeurs** (Draco, Basis pour KTX2) : copiés depuis `node_modules/three` et servis par le site. drei les chargerait sinon depuis des CDN tiers.
- **Compression** : on préfère Meshopt à Draco, parce que GitHub Pages recompresse les `.glb` en gzip, ce qui profite à Meshopt.

## 11. Licences

### Le dépôt

- Code : MIT (`LICENSE`).
- Contenus originaux (textes, données, modèles, vidéos) : CC BY 4.0 (`LICENSE-CONTENT.md`).
- Polices Cinzel et EB Garamond : SIL OFL 1.1.
- GSAP : licence gratuite propre à Webflow, non libre, utilisée comme dépendance npm sans modification.

### Sources de données géographiques (contre-vérifiées)

| Source | Licence | Usage prévu |
|---|---|---|
| Cliopatria (Seshat) v0.2.1 | CC BY 4.0 | territoire année par année de 753 av. J.-C. à 1453 ; dates à corriger d'après nos événements (par exemple l'Empire latin y commence en 1206) |
| AWMC geodata (commit postérieur au 21 juin 2016) | ODbL 1.0 | étendues de 60 av. J.-C., 117 et 200, côtes antiques ; fichiers dérivés isolés sous ODbL, mention « © OpenStreetMap contributors » |
| Itiner-e (Zenodo, 2024) | CC BY 4.0 | routes ; réseau valable de 312 av. J.-C. à 400 environ, filtré par époque, certitude affichée |
| Pleiades v4.1 (doi:10.5281/zenodo.15540082) | CC BY 3.0 | identifiants et coordonnées des lieux |
| OpenHistoricalMap | CC0 par défaut | recoupement des provinces, entité par entité |
| Natural Earth | domaine public | côtes actuelles |
| NOAA ETOPO 2022 | CC0 | relief, cuit en textures |
| Wikidata | CC0 | identifiants et liens, jamais seule source d'une date |

Écartées :

- **historical-basemaps** : GPL-3.0, hors de la liste acceptée, licence floue pour des données. Cliopatria couvre mieux le besoin.
- **DARE** : CC BY-SA 3.0, qui s'étendrait aux rendus vidéo.
- **DARMC** : licence NC.
- **klokantech/roman-empire** : aucune licence.

Règle : une source ODbL ou BY-SA ne partage jamais un fichier avec une autre source. Chaque dossier de données dérivées porte son `LICENSE` et la méthode de dérivation, et `CREDITS.md` est complété au moment de l'ajout.

## 12. Prérequis web

| Prérequis | Réponse |
|---|---|
| HTTPS | servi et forcé par GitHub Pages (`https_enforced: true`) |
| Clés d'API | aucune |
| Anti-spam | aucun formulaire ; un honeypot si un formulaire apparaît |
| Sauvegardes | git sur GitHub et le clone local ; assets dans des releases immuables |
| Cookies et consentement | aucun cookie ; GoatCounter (sans cookie) chargé seulement après accord, bandeau inactif tant que le compte n'existe pas |
| Mentions légales, confidentialité, CGU | pages `#/mentions-legales`, `#/confidentialite`, `#/conditions`, plus `#/sources` |
| Mobile first, contraste | mise en page testée à 375 px et à 1 440 px ; contraste de l'accent testé |
| Images | WebP et chargement différé dès qu'il y aura des images (aucune en phase 1) |
| Page 404 | `404.html` statique (`noindex`) et panneau « Page introuvable » dans l'application |
| Titre et description uniques | une page de partage par événement |
| `robots.txt` | sans effet sur un site de projet : seul celui de `maximator13.github.io/robots.txt` est lu ; balises `robots` par page à la place |
| `sitemap.xml` | `/roma/sitemap.xml`, à déclarer dans une propriété Search Console de préfixe `https://maximator13.github.io/roma/` |
| Open Graph et Twitter Cards | sur l'accueil et chaque page de partage |
| CTA principal unique | accueil : « Commencer en 753 av. J.-C. » ; page de partage : « Voir dans la frise chronologique » |
| Favicon | SVG |

## 13. Reporté volontairement

- Phase 2 :
  - carte, globe, intro ;
  - registre des scènes et directeur de caméra ;
  - chargeurs glTF et décodeurs ;
  - scripts d'assets et de releases ;
  - image de partage par époque ;
  - politique de rendu à la demande (`frameloop="demand"`) pour économiser la batterie quand rien ne bouge.
- Phase 3 :
  - recherche, quiz et jeux ;
  - liste accessible de tous les événements, pour atteindre au clavier ceux que le zoom sémantique masque ;
  - vérification planifiée des liens des sources.
- Phase 5 : audit Lighthouse, accessibilité complète, mode mobile léger.
- Seulement si les mesures le justifient :
  - service worker : Pages impose `max-age=600` ;
  - LUT 3D pour l'étalonnage, si l'approche paramétrique ne suffit pas à la direction artistique ;
  - WebGPU, quand R3F 10 et drei 11 seront stables.
