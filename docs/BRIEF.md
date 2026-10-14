# Roma, de Romulus à Constantin XI

Cahier des charges du projet. Le travail se mène sur plusieurs sessions : ce fichier décrit le but et la méthode, `docs/PROGRESS.md` garde l'avancement. Titre de travail, modifiable.

## 1. Vision

Un site web statique, publié sur GitHub Pages, pour étudier l'histoire romaine de la fondation de Rome (753 av. J.-C., date traditionnelle) à la chute de Constantinople (1453). La frise chronologique est la colonne vertébrale : on la parcourt, et chaque événement important ouvre une scène 3D cinématique : la carte du monde romain qui s'étend puis se rétracte, l'intérieur de monuments et de palais, des batailles en mouvement.

Le site sert deux publics à la fois : moi, pour apprendre la chronologie (dates fiables, sources, jeux de révision), et les visiteurs de mon GitHub, qui doivent être saisis dès les premières secondes.

Critères de réussite :
- Tout événement se retrouve en trois interactions au plus, avec sa date, son niveau de certitude et ses sources.
- Les trente premières secondes (intro → carte → frise) donnent envie de continuer.
- 60 images/s visées sur un ordinateur portable récent sans carte graphique dédiée ; ailleurs, la qualité s'adapte automatiquement.

## 2. Contraintes

**GitHub Pages**
- Site 100 % statique, déployé par un workflow GitHub Actions.
- Limites de GitHub : site publié ≤ 1 Go, fichier ≤ 100 Mo, déploiement ≤ 10 min. Budget interne : site complet ≤ 600 Mo.
- Le site vit sous `/<nom-du-dépôt>/` : la `base` de Vite, les chemins des décodeurs (Draco, Meshopt, KTX2) et de tous les assets en tiennent compte.
- Routage par hash : chaque événement et chaque scène a une URL partageable qui survit au rechargement (`#/evenement/bataille-de-cannes`).
- Chaque nouvelle version d'une vidéo ou d'un `.glb` alourdit définitivement l'historique Git. Propose en phase 0 une stratégie pour les assets lourds (ne versionner que les versions finales, ou les stocker dans une GitHub Release que le workflow télécharge au build, etc.).

**Budget de performance** (mesuré et reporté dans PROGRESS à chaque phase)
- Premier écran utile : ≤ 5 Mo téléchargés.
- Chaque scène 3D, chargée à la demande : ≤ 20 Mo hors vidéo. Chaque vidéo : ≤ 20 Mo.
- Géométrie compressée (Meshopt ou Draco), textures KTX2, instanciation pour tout ce qui se répète (colonnes, soldats).
- Qualité adaptative (résolution, ombres, post-traitement) et mode léger pour mobile : frise, carte simplifiée, vidéos.

**Licences**
- Uniquement des ressources gratuites, aucune API payante.
- Par ordre de préférence : ce qu'on crée dans Blender, puis CC0 et domaine public, puis CC BY, polices OFL. CC BY-SA et ODbL acceptées en documentant l'obligation de partage à l'identique. Toute ressource NC ou ND : demande-moi d'abord.
- Chaque ressource externe entre dans `CREDITS.md` (source, auteur, licence, modifications) au moment où tu l'ajoutes.

**Langue et style**
- Interface et contenus en français ; code, types et commits en anglais. Les identifiants de contenu sont des slugs français, réutilisés dans les URL. Tous les textes vivent dans les fichiers de données.
- Aucun tiret cadratin ni demi-cadratin, nulle part (site, documentation, commits) : des virgules, des deux-points ou des parenthèses à la place, et « de 509 à 27 av. J.-C. » pour les intervalles.
- Le code ne contient aucun commentaire : des noms explicites et des fonctions courtes portent le sens.
- Rien de ce qui est publié ne mentionne l'outil qui a servi à produire le projet : ni le code, ni la documentation, ni le site, ni l'historique Git (aucune ligne de co-auteur, de session ou de signature automatique dans les commits).

## 3. Stack

Vite, TypeScript strict, React, React Three Fiber, drei, @react-three/postprocessing, rendu WebGL 2. GSAP pour le motion design et les mouvements de caméra, Zustand pour l'état global, zod pour valider les données au build, Vitest pour la logique, Playwright pour les tests de fumée et les captures. Si tu as une raison forte de choisir autrement, argumente-la en phase 0.

## 4. Production 3D avec Blender

- Blender est l'usine à assets. Chaque scène a son script Python dans `blender/`, qui la reconstruit entièrement, exporte le glTF et lance les rendus (`blender --background --python blender/<scene>.py`). Le script est la source de vérité de l'asset. L'exécutable de Blender n'est pas toujours dans le PATH : trouve-le.
- Si une skill ou un serveur MCP Blender est disponible dans ta session, sers-t'en pour itérer et prévisualiser, puis reporte le résultat dans le script.
- Architecture : un kit modulaire (ordres toscan, ionique et corinthien, arcs, voûtes, coupoles à caissons, tuiles), formes simplifiées, proportions fidèles.
- Intérieurs : éclairage et occlusion précalculés dans Blender (lightmaps), pour une lumière de cinéma à faible coût en temps réel.
- Soldats : figurines low-poly stylisées modélisées par script, animations simples (marche, charge, combat, chute) précalculées en vertex animation textures ou sur un squelette léger, affichées en `InstancedMesh`.
- Caméras : animées dans Blender et exportées dans le glTF, ou tracées en courbes GSAP ; choisis scène par scène.
- Plans cinématiques pré-rendus : EEVEE (Cycles si nécessaire), 1920×1080, 24 i/s, 8 à 15 s, encodés en MP4 H.264 avec ffmpeg, plus une image d'affiche. Avant tout rendu de plus de 10 minutes, donne-moi une estimation et attends mon accord.
- Optimisation automatisée (`npm run assets`, par exemple avec gltf-transform) : compression, KTX2, LOD, et un rapport de poids par scène.
- Ressources externes : Poly Haven et ambientCG (textures, HDRI, CC0) ; Sketchfab seulement pour des modèles téléchargeables dont la licence est vérifiée un par un.

## 5. Direction artistique : réalisme stylisé, éclairé comme un film

- Formes simplifiées ; proportions et matériaux fidèles : marbres, bronze, terre cuite, porphyre, mosaïques dorées. Lumière méditerranéenne chaude, ombres bleutées, brume atmosphérique, faisceaux volumétriques, profondeur de champ sur les plans rapprochés. Référence d'ambiance : les tableaux de Lawrence Alma-Tadema (domaine public).
- Un étalonnage par époque, qui glisse de l'un à l'autre quand on parcourt la frise :
  - Royauté : bois, terre cuite, lumière de feu.
  - République : tuf, ocre, rouge pompéien, lumière franche de midi.
  - Haut-Empire : marbre blanc, or, bleu de Méditerranée, fin d'après-midi dorée.
  - Crise du IIIe siècle : couleurs éteintes, fumée, ciel d'orage.
  - Bas-Empire : pourpre impériale, porphyre, lumière d'hiver.
  - Empire romain d'Orient : or des mosaïques, lapis-lazuli, pénombre des cierges.
- La 3D est le moment fort ; l'interface reste sobre autour d'elle. Les fiches d'événements sont des cartels de musée. Titres en capitales inspirées des inscriptions lapidaires romaines, texte en sérif de lecture, polices OFL auto-hébergées.
- Mouvement : une seule famille de courbes d'accélération ; la caméra circule en continu entre frise, carte et scènes ; les vidéos s'enchaînent en fondu ; chaque cinématique peut être passée ; avec `prefers-reduced-motion`, les mouvements de caméra deviennent des fondus.
- Pour l'interface 2D, utilise une skill de design frontend si tu en as une (par exemple frontend-design).

## 6. L'expérience

- **Intro**, passable : le globe terrestre, la plongée vers la Méditerranée, Rome, le titre.
- **Frise** : bande toujours présente, navigable à la molette, au glisser, au clavier et au toucher. Zoom sémantique, des 2 205 ans d'un coup d'œil jusqu'à la décennie, les événements apparaissant selon leur importance. Pistes parallèles quand plusieurs pouvoirs coexistent (de 395 à 476 : Occident et Orient ; crise du IIIe siècle : Empire des Gaules, Palmyre ; de 1204 à 1261 : Empire latin, Nicée, Épire, Trébizonde). Un indicateur de certitude sur chaque événement. Une recherche (événements, personnes, lieux).
- **Carte** : relief stylisé du monde romain, de l'Atlantique à la Mésopotamie, synchronisé avec l'année affichée par la frise : territoire, provinces, villes, routes, itinéraires de campagnes animés.
- **Monuments et palais** : caméra guidée sur un rail entre des points d'intérêt, regard libre limité autour de chacun, cartels sur les détails.
- **Batailles**, temps réel et vidéo mêlés : une maquette tactique 3D (terrain, unités en formation, 1 figurine = N soldats avec l'échelle affichée, phases scriptées, lecture, pause et défilement, flèches de manœuvre, vue tactique et vue rasante), ponctuée d'un ou deux plans cinématiques pré-rendus aux moments décisifs.
- **Apprendre en jouant** : un quiz par époque ; « Remets dans l'ordre » (glisser des événements) ; « Situe la date » (score selon l'écart) ; « Où ? » (cliquer le lieu sur la carte) ; des fiches d'empereurs, de batailles et de monuments débloquées en explorant ; progression sauvegardée en `localStorage`.

## 7. Contenu historique

Époques (bornes conventionnelles, que le site explique) :

| Époque | Dates |
|---|---|
| Royauté | de 753 à 509 av. J.-C. (dates traditionnelles) |
| République | de 509 à 27 av. J.-C. |
| Haut-Empire | de 27 av. J.-C. à 235 |
| Crise du IIIe siècle | de 235 à 284 |
| Bas-Empire | de 284 à 476 (piste Orient dès 395) |
| Empire romain d'Orient | de 476 à 1453 (le début de l'« Empire byzantin » est une convention discutée : 330, 395, 476 ou 610) |

Modèle de données : un fichier par type dans `src/data/`, validé par zod au build.

```ts
type Year = number;
type Certainty = "attested" | "traditional" | "legendary" | "debated";

interface HistoricalEvent {
  id: string;
  title: string;
  start: Year;
  end?: Year;
  precision: "day" | "month" | "year" | "decade" | "century";
  certainty: Certainty;
  era: EraId;
  track: TrackId;
  category: "politics" | "war" | "building" | "religion" | "society" | "culture";
  importance: 1 | 2 | 3;
  placeId?: string;
  summary: string;
  body: string;
  sources: Source[];
  people?: string[];
  scene?: string;
}
```

Sens des champs :
- `Year` est une année astronomique : 1 av. J.-C. = 0, 753 av. J.-C. = -752.
- `id` est un slug français (`bataille-de-cannes`) ; `track` désigne la piste (`rome`, `occident`, `orient`, `empire-des-gaules`…).
- `importance` pilote le zoom sémantique.
- `placeId` renvoie aux lieux (coordonnées et identifiant Pleiades), `people` aux personnes, `scene` à une scène 3D.
- `summary` tient en deux ou trois phrases ; `body` est en markdown.
- `sources` contient au moins une entrée : auteur antique ou ouvrage de référence.

Exactitude, priorité absolue :
- Il n'y a pas d'an 0. Toutes les dates passent par un module de conversion unique, couvert par des tests (753 av. J.-C. → -752 ; de 753 av. J.-C. à 1453 : 2 205 ans).
- Légende, tradition et faits attestés sont distingués (Romulus, les sept rois…). Les dates débattues et les chiffres incertains (effectifs, pertes) sont signalés, avec une fourchette.
- Chaque fait s'appuie sur une source vérifiable. Ce dont tu n'es pas sûr va dans `docs/A_VERIFIER.md`, avec ta meilleure hypothèse et tes sources : je tranche.
- Les « Byzantins » se disaient Romains : le site le dit.
- En 3D, équipement, architecture et tactique correspondent à la date. Exemple, Cannes (216 av. J.-C.) : légion manipulaire (vélites, hastati, principes, triarii), pilum, scutum ovale, casques de type Montefortino ; la lorica segmentata n'apparaît qu'au Ier siècle apr. J.-C. ; la cavalerie monte sans étriers ; Hannibal n'a plus d'éléphants.

Sources de données à évaluer (licence et précision à vérifier avant usage) :
- Itiner-e : routes romaines, CC BY 4.0.
- AWMC (Ancient World Mapping Center) : côtes antiques, provinces, emprise de l'empire à plusieurs dates. GeoJSON sous ODbL dans le dépôt actuel ; certaines versions anciennes étaient en CC BY-NC.
- Pleiades : lieux antiques et coordonnées.
- historical-basemaps : frontières par année, utile pour Byzance ; précision et licence à vérifier.
- Natural Earth (domaine public) pour les côtes ; un modèle numérique de terrain du domaine public (par exemple ETOPO, de la NOAA) pour le relief.
- Là où les données manquent, trace des polygones approximatifs, cite tes sources et montre l'imprécision à l'écran (bords flous).

## 8. Méthode de travail

Règles valables pour toutes les phases :
- Une phase à la fois. À la fin de chacune : mets à jour `docs/PROGRESS.md` (fait, décisions, problèmes connus, suite), commit, push, vérifie que le site déployé fonctionne, puis arrête-toi et attends ma validation.
- Commits petits et fréquents, à chaque étape cohérente.
- Chaque changement visuel se vérifie sur des captures Playwright que tu regardes toi-même avant de le dire terminé. En headless, le WebGL est souvent rendu en logiciel : les FPS se mesurent chez moi, grâce à un HUD de debug activable (`?debug` : FPS, draw calls, triangles, mémoire). Demande-moi ces chiffres à la fin de chaque phase visuelle.
- Quand une limite (performance, poids, licence, exactitude) impose un compromis, présente deux ou trois options chiffrées avec ta recommandation, et laisse-moi choisir.
- Chaque scène est un module autonome (`src/scenes/<id>/` + `blender/<id>.py`) chargé à la demande : ajouter une scène, c'est ajouter un dossier et une entrée de données, sans toucher au cœur.
- Confie la recherche historique et la vérification des licences à des sous-agents quand c'est possible.

### Phase 0 : cadrage (aucun code produit)
1. Vérifie l'environnement : node, git, gh (et sa connexion), Blender, ffmpeg. Pour chaque manque, donne la commande d'installation adaptée à mon système et attends.
2. Initialise le dépôt Git, puis, avant tout commit, garde l'historique propre : désactive l'attribution automatique dans tes réglages locaux (aujourd'hui la clé `attribution`, avec `commit` et `pr` vides) ; installe un hook `commit-msg` local qui retire toute ligne de co-auteur, de session ou de signature ajoutée par l'outil ; exclus tes fichiers de mémoire et de réglages via `.git/info/exclude`, qui reste local, pour que même le `.gitignore` publié n'en garde pas trace.
3. Pose-moi tes questions sur ce qui reste ambigu.
4. Propose l'architecture (modules, flux de données, chargement des scènes), la stratégie pour les assets lourds, les licences du dépôt (code et contenus) et le plan détaillé de la phase 1.
5. Range ce brief dans `docs/BRIEF.md` et crée ton fichier de mémoire de projet, celui que tu relis automatiquement à chaque session : court (commandes, conventions), il renvoie vers `docs/BRIEF.md` et `docs/PROGRESS.md` sans les importer. Fais le premier commit et montre-moi son message complet.

Terminé quand : le message du premier commit ne contient que le texte voulu et j'ai validé le plan.

### Phase 1 : fondations et déploiement
- Projet initialisé ; workflow GitHub Actions vers Pages ; base et routage par hash. Si `gh` est connecté, crée le dépôt distant et active Pages ; sinon, guide-moi pas à pas.
- Module de dates et schémas de données, avec leurs tests.
- Une quarantaine d'événements clés, sourcés, couvrant les six époques.
- La frise dans toute sa mécanique : époques, pistes parallèles, zoom sémantique, navigation, étalonnage qui suit l'époque.
- Canvas 3D avec qualité adaptative et HUD de debug.

Terminé quand : le site est en ligne ; build, tests et validation des données passent ; le test Playwright ne relève aucune erreur console ; PROGRESS compare les poids mesurés au budget.

### Phase 2 : tranche verticale (la phase décisive)
But : prouver toute la chaîne de bout en bout et valider la direction artistique avant de produire en série.
1. D'abord un plan de design : palette nommée (4 à 6 couleurs), typographies, principes, maquette de l'interface. Je valide avant la suite.
2. Carte : globe puis Méditerranée, relief stylisé, territoire romain à au moins cinq dates (dont 218 av. J.-C. et l'apogée de 117) avec des transitions animées synchronisées avec la frise, grandes villes, itinéraire d'Hannibal animé (218 av. J.-C.).
3. Monument : le Panthéon d'Hadrien, modélisé par script, éclairage précalculé, faisceau de lumière de l'oculus, trois à cinq points d'intérêt.
4. Bataille : Cannes (216 av. J.-C.) en maquette tactique temps réel, avec un plan cinématique pré-rendu intégré.
5. Transitions continues frise ↔ carte ↔ scène, sans rechargement.

Terminé quand : le parcours frise → Cannes → frise → Panthéon → frise fonctionne en ligne ; chaque scène tient son budget ; les captures de chaque étape sont dans `docs/screenshots/` ; j'ai testé sur ma machine et validé le rendu.

### Phase 3 : tout le contenu, et l'apprentissage
- Environ 200 événements ; tous les souverains (rois, empereurs d'Occident et d'Orient, co-empereurs et usurpateurs marqués comme tels) ; lieux reliés à Pleiades.
- Le territoire pour toutes les époques, jusqu'en 1453.
- Recherche, quiz, mini-jeux, fiches et progression.

Terminé quand : chaque événement passe la validation (source, certitude, époque, piste) ; chaque époque a son quiz ; `docs/A_VERIFIER.md` est à jour et je l'ai relu.

### Phase 4 : les scènes, une par une
Pour chaque scène : proposition (références historiques, plan de caméra, budget) → ma validation → production → captures → ma validation.

Ordre de départ, modifiable : Alésia (52 av. J.-C.), le Colisée et le Forum, Actium (31 av. J.-C., bataille navale), la Domus Aurea, le palais de Dioclétien à Split, Sainte-Sophie, et le siège de Constantinople (1453) en finale. En réserve : Zama, Pharsale, Teutobourg, le pont Milvius, Andrinople, les champs Catalauniques, le Yarmouk, Mantzikert, le palais du Palatin, la villa d'Hadrien, le Grand Palais de Constantinople.

### Phase 5 : finitions
Intro cinématique définitive, son d'ambiance sous licence libre (coupé par défaut), accessibilité (clavier, contrastes, sous-titres, mouvement réduit), mode mobile, README avec captures et GIF, `CREDITS.md` complet.

Terminé quand : un audit Lighthouse (performance, accessibilité) est noté dans PROGRESS et `CREDITS.md` couvre toutes les ressources externes.
