# Avancement

Le cahier des charges est dans `docs/BRIEF.md`, l'architecture dans `docs/ARCHITECTURE.md`. Ce fichier garde l'état du projet d'une session à l'autre.

## Phase 0 : cadrage (terminée le 15 octobre 2026)

### Fait

- Environnement vérifié : Node 24.18, npm 11.16, git 2.55, gh 2.102 (connecté au compte Maximator13), ffmpeg 9.0.1 (avec libx264), Blender 5.2.2 LTS et KTX-Software 4.4.2 (tous deux hors PATH, appelés par leur chemin complet).
- Dépôt initialisé sur la branche `main`, avec une identité de commit masquée.
- Recherches de cadrage vérifiées : stack, hébergement et assets lourds, licences des sources de données, chaîne Blender.
- Architecture consignée dans `docs/ARCHITECTURE.md`. Le plan de la phase 1 a été exécuté en autonomie, à ta demande du 15 octobre 2026 (« va le plus loin possible en autonomie »).

### Décisions validées (14 octobre 2026)

1. **Dépôt** : dossier `C:\Users\maxim\Projets VSCode\roma`, dépôt public `Maximator13/roma`, site `https://maximator13.github.io/roma/`, donc `base` Vite `/roma/`.
2. **Identité des commits** : `Maximator13 <329881135+Maximator13@users.noreply.github.com>`, l'adresse masquée fournie par GitHub, réglée pour ce dépôt seulement.
3. **Licences** : code sous MIT ; contenus originaux (textes, données, modèles et vidéos produits par les scripts) sous CC BY 4.0 ; données dérivées de sources ODbL ou CC BY-SA rangées dans des fichiers séparés, sous leur propre licence ; GSAP sous sa licence propre (gratuite, non libre), signalée dans `CREDITS.md`.
4. **Assets lourds** : binaires optimisés (`.glb`, `.ktx2`, `.mp4`, tout fichier de plus de 1 Mo) publiés dans des GitHub Releases versionnées ; un manifeste versionné donne pour chacun son chemin, sa taille, son empreinte SHA-256 et sa release ; le workflow de déploiement les télécharge et les met en cache. Scripts `assets:publish` et `assets:pull` écrits en phase 2. Les fichiers `.blend` et les rendus intermédiaires ne sont jamais versionnés : les scripts Blender les régénèrent.
5. **Mesure d'audience** : GoatCounter (gratuit, sans cookie), chargé seulement après consentement explicite (refus par défaut) ; inactif tant que le compte GoatCounter n'est pas créé.
6. **Mentions légales** : éditeur publié sous le pseudonyme Maximator13, hébergeur GitHub, contact par les issues du dépôt.
7. **Référencement** : une page HTML statique par événement générée au build (titre, description et image Open Graph uniques), qui ouvre l'application directement sur l'événement ; ces pages alimentent `sitemap.xml`, à déclarer dans la Search Console ; pas de dépôt `Maximator13.github.io`. Ajustement de la phase 1 : pas de redirection, car Google traite une redirection comme un renvoi vers l'accueil et n'aurait pas indexé chaque événement.
8. **Sources** : auteurs antiques, avec des traductions consultables en ligne (Perseus, LacusCurtius, remacle.org), et ouvrages de référence (Oxford Classical Dictionary, Cambridge Ancient History, Oxford Dictionary of Byzantium, manuels universitaires français).
9. **Machine de référence** : i7-1065G7, Intel Iris Plus, 12 Go. Objectif : 60 i/s en qualité automatique sur cette machine. Aucune autre machine signalée ; les temps de rendu Blender seront estimés en phase 2.
10. **Écriture des dates** : « av. J.-C. » une seule fois par intervalle (« de 509 à 27 av. J.-C. ») ; pas de suffixe après notre ère, sauf pour les années 1 à 99 et le Ier siècle (« de 27 av. J.-C. à 14 apr. J.-C. », mais « de 27 av. J.-C. à 235 »).

## Phase 1 : fondations et déploiement (terminée, en attente de ta validation)

Site en ligne : https://maximator13.github.io/roma/

### Fait

- **Projet** : Vite 8, React 19, TypeScript 6 strict, ESLint, Vitest, Playwright ; versions épinglées.
- **Déploiement** : workflow GitHub Actions vers Pages. Il enchaîne contrôles, build, tests Playwright et déploiement, et chaque push sur `main` est publié.
- **Garde-fous de style** : un script refuse tout commentaire dans le code et tout tiret cadratin ou demi-cadratin dans un fichier du dépôt ; la validation des données refuse aussi ces tirets dans les textes.
- **Module de dates** : années astronomiques, aucun an 0, 2 205 ans de 753 av. J.-C. à 1453, écriture française des dates, des intervalles et des siècles. Couvert par des tests.
- **Données** :
  - schémas zod et validation avant chaque build (références, époques, pistes, lieux, personnes, scènes) ;
  - **58 événements** sur les six époques, chacun avec sa date, son niveau de certitude, ses sources (3 à 8 par événement) et un texte original ;
  - 33 lieux reliés à Pleiades, 124 personnes ;
  - les textes des époques et les bornes des pistes viennent de la même recherche vérifiée.
- **Frise** :
  - six époques, graduations sur des années historiques rondes ;
  - pistes parallèles (Occident et Orient, Empire des Gaules, Palmyre, Nicée, Empire latin, Épire, Trébizonde) ;
  - zoom sémantique selon l'importance, de 2 205 ans à 10 ans ;
  - navigation à la molette, au glisser, au pincement et au clavier ;
  - certitude indiquée par la forme du repère ;
  - cartels d'événements avec sources ;
  - couleur d'accent qui suit l'époque, avec contraste testé.
- **Scène 3D** :
  - `Canvas` unique, chargé après la frise ;
  - portique provisoire en instances ;
  - étalonnage par époque fondu aux frontières (chaud et ambré pour la Royauté, doré pour le Haut-Empire, gris pour la crise, lumière d'hiver pour le Bas-Empire, or et bleu profond pour l'Orient) ;
  - trois paliers de qualité avec adaptation automatique, et HUD de debug (`?debug`).
- **Prérequis web** :
  - pages Mentions légales, Confidentialité, Conditions d'utilisation, Sources et crédits ;
  - 404 personnalisée ; `sitemap.xml` ; balises Open Graph et Twitter ; image de partage ; favicon ;
  - bandeau de consentement prêt mais inactif ;
  - typographie française avec espaces insécables.
- **Documentation** : `docs/ARCHITECTURE.md`, `CREDITS.md`, `LICENSE`, `LICENSE-CONTENT.md`, et `docs/A_VERIFIER.md` (63 points à trancher).

### Poids mesurés et budget

Mesure Playwright des octets réellement transférés au premier affichage : 551,6 Ko sur le build local, **557,3 Ko sur le site en ligne** (le 15 octobre 2026, avec la compression gzip de GitHub Pages). La commande `LIVE_URL=https://maximator13.github.io/roma/ npm run test:e2e` relance les tests de fumée sur le site en ligne.

| Poste | Budget | Mesuré |
|---|---|---|
| Premier écran utile | 5 Mo | **551,6 Ko** (9 fichiers) |
| dont application (React, frise, 58 événements) | | 179,5 Ko |
| dont scène 3D (three.js, R3F, post-traitement) | | 264,5 Ko |
| dont polices (Cinzel, EB Garamond, sous-ensemble latin) | | 103,9 Ko |
| dont HTML et styles | | 3,7 Ko |
| Scène 3D chargée à la demande | 20 Mo par scène | aucune scène en phase 1 |
| Vidéo | 20 Mo par vidéo | aucune vidéo en phase 1 |
| Site complet | 600 Mo | **2,09 Mo** (76 fichiers, dont 58 pages de partage) |

Tests : 60 tests unitaires, 12 tests Playwright (6 sur ordinateur, 6 sur mobile), sans aucune erreur console, en local, en CI et sur le site en ligne. Vérifié en ligne : statut 404 sur une adresse inconnue, redirection HTTP vers HTTPS, balises propres sur les pages de partage, 59 adresses dans `sitemap.xml`.

### Décisions prises en autonomie (à confirmer ou à changer)

- **Molette** : elle zoome autour du curseur, comme une carte. La molette horizontale ou Maj+molette déplace la frise. L'autre choix possible serait de déplacer à la molette et de zoomer avec Ctrl.
- **Contenu** : 58 événements au lieu d'une quarantaine. Les chercheurs en ont ajouté six jugés majeurs (année des quatre empereurs, Abritus, guerre sociale, marche de Sylla, reconquêtes de Justinien, siège arabe de 717) ; chaque ajout figure dans `docs/A_VERIFIER.md` pour que tu le gardes ou le retires.
- **Polices provisoires** : Cinzel pour les titres, EB Garamond pour le texte (OFL). Le choix définitif se fera dans le plan de design de la phase 2.
- **Décor 3D provisoire** : le portique sert à démontrer l'étalonnage et la qualité adaptative ; il sera remplacé par le globe et la carte en phase 2.

### Problèmes connus

- **i/s non mesurés** : en CI et en capture, le WebGL est rendu en logiciel (SwiftShader, 2 à 20 i/s). La mesure se fait sur ta machine (voir plus bas).
- **Plages de jours** : une plage comme le sac de 1204 (du 12 au 15 avril) ne s'exprime pas dans le modèle de données ; seule la date de début s'affiche, et le texte précise la durée.
- **Calendrier** : les dates antérieures à 45 av. J.-C. sont celles du calendrier romain préjulien, sans conversion (point 3 de `docs/A_VERIFIER.md`).
- **Zoom sémantique et clavier** : un événement masqué n'est atteignable au clavier qu'après avoir zoomé ; une liste complète arrivera avec la recherche en phase 3.
- **Batterie** : la scène 3D se redessine en continu ; le rendu à la demande est prévu en phase 2.
- **Rendu logiciel** : la détection du rendu logiciel ne force pas toujours le palier bas sous Chrome headless. Sans effet pour les visiteurs.

### Ce que j'attends de toi

1. **Mesures du HUD** sur ton portable, avec Chrome ou Edge en plein écran 1080p : ouvre https://maximator13.github.io/roma/?debug, puis note FPS, durée d'image, appels de dessin, triangles et qualité dans trois situations :
   - à l'arrivée sur la page ;
   - pendant que tu fais glisser la frise ;
   - avec `?debug&quality=high`.
2. **Relecture de `docs/A_VERIFIER.md`** : 63 points, chacun avec l'hypothèse retenue ; tu tranches.
3. **Search Console**, quand tu veux :
   - crée une propriété « Préfixe d'URL » pour `https://maximator13.github.io/roma/` et choisis la validation par fichier HTML ;
   - donne-moi le nom du fichier : je l'ajoute au site, puis tu déclares `sitemap.xml`.
4. **Facultatif** : un compte GoatCounter, si tu veux la mesure d'audience (donne-moi le code du site).

## Phase 2 : tranche verticale (en cours)

État au 15 octobre 2026, 11 h 30. Site en ligne à jour : https://maximator13.github.io/roma/

### Fait

- **Plan de design** : `docs/DESIGN.md` (palette nommée, accents et lumière par époque, typographies, principes, captures de l'interface dans `docs/screenshots/phase-2/`). À valider.
- **Carte 3D du monde romain**, synchronisée avec la frise :
  - relief ETOPO 2022 et côtes Natural Earth, mer animée, ombres de nuages, brume de bord de carte ;
  - territoire année par année de 753 av. J.-C. à 1453, tiré de Cliopatria v0.2.1 (CC BY 4.0) : 282 tranches, 877 Ko, frontière qui s'étend depuis l'ancien tracé à chaque changement ;
  - 44 villes vérifiées dans Pleiades, épingles des événements de la période, itinéraire d'Hannibal animé (218 av. J.-C.) ;
  - caméra qui cadre le territoire, ou le lieu de l'événement ouvert ; la frise se recale sur l'année de l'événement ou de la scène ouverte par lien.
- **Moteur des scènes 3D** (prêt, en attente du premier modèle) :
  - route `#/scene/<id>` ; module de scène chargé à la demande ;
  - plongée de la caméra de la carte vers la ville, voile de brume pendant la bascule, retour à la carte ;
  - kit glTF commun : chargement compressé (meshopt, KTX2), ciel et brume du soir, soleil avec ombres, rail de caméra entre les points d'intérêt avec regard libre limité ;
  - cartel de musée par point d'intérêt, avec sources, étapes et touches fléchées ; feuille basse sur téléphone ;
  - accès par un anneau doré cliquable sur la ville, par la liste « À visiter en 3D » sous l'époque, et par un bouton dans les fiches liées.
- **Scène de Nîmes vers 130, en ligne** (`#/scene/nimes`) : reconstruite par script (`blender/nimes.py`) sur le relief IGN, avec la Maison Carrée et sa dédicace, le forum, les Arènes, l'enceinte, la porte d'Auguste, la tour Magne, le sanctuaire de la Fontaine, le castellum, 2 267 maisons et boutiques, 724 personnages ; passants animés, fumée et oiseaux dans le site. Modèle optimisé de 6,5 Mo publié dans la release `assets-v1` ; prête en 13 s sur le site en ligne (rendu logiciel de test). Captures dans `docs/screenshots/nimes/`. Environ 1,36 million de triangles affichés : fluidité à mesurer sur ton portable.
- **Nuit du 15 au 16 octobre 2026, en autonomie** (demande de l'utilisateur) : quatre scènes en ligne avec Nîmes.
  - **Panthéon d'Hadrien** (`#/scene/pantheon`, release `assets-v2`, 7,8 Mo) : 21 avril 129 à midi, rayon de l'oculus et tache de soleil calculée, lumière d'ambiance atténuée dans la rotonde.
  - **Arles vers 160** (`#/scene/arles`, `assets-v4`, 6,1 Mo) : forum, théâtre, amphithéâtre, cirque, port et Trinquetaille.
  - **Pont du Gard vers 130** (`#/scene/pont-du-gard`, `assets-v5`, 3,6 Mo) : pont sur relief IGN, canal et dalles, carrière de l'Estel, Gardon.
  - **Nîmes plus réaliste** (`assets-v3`, 7,6 Mo) : personnages détaillés, objets des boutiques, usure ; passants posés sur le sol (correction du site et des trajets).
  - **Son d'ambiance** libre, coupé par défaut ; **ombres de contact** (N8AO) en qualité moyenne et haute ; **6 événements de frise** qui ouvrent les scènes.
  - Captures dans `docs/screenshots/<scène>/`. Restent hors périmètre : vidéos pré-rendues, bataille de Cannes (carte de session proposée), netteté de la carte au zoom (carte de session proposée).
- **Bataille de Cannes, 2 août 216 av. J.-C.** (`#/scene/cannes`, release `assets-v6`, 1,16 Mo), nuit du 19 au 20 octobre 2026, en autonomie :
  - moteur de bataille générique (`src/scenes/battle/`) : données validées par zod, troupes en `InstancedMesh` qui gardent leur formation entre les phases (marche, combat, fuite, chute), emprises colorées par camp, flèches de manœuvre qui se dessinent, étiquettes d'unités, compteurs de pertes ;
  - frise de lecture (lecture, pause, curseur, touche Espace) synchronisée avec les cartels de phase et les flèches gauche et droite ; vue tactique (figurines grossies 3 fois, mention affichée) et vue rasante à hauteur d'homme dans les rangs d'une unité ; avec `prefers-reduced-motion`, pas de lecture automatique, chaque phase s'affiche directement dans son état final et la caméra coupe au lieu de glisser ;
  - terrain réel TINITALY 1.1 (CC BY 4.0) de 9,2 km sur 6,8 km, Aufide restitué au pied de l'escarpement, trois camps et citadelle de Cannes (`blender/cannes.py`) ;
  - 12 figurines low poly faites par script, en deux niveaux de détail (270 à 650 triangles près, 36 à 72 loin) : casque Montefortino à trois plumes, scutum ovale, pila, triaires à la lance, vélites à la rondache, cavaliers sans étriers, Numides sans bride, aucun éléphant ;
  - 6 850 figurines (1 pour 20 soldats, camps compris), 8 phases d'après la proposition vérifiée ; captures dans `docs/screenshots/cannes/`. Hors périmètre : le plan pré-rendu de la charge d'Hasdrubal. Cinq points ajoutés à `docs/A_VERIFIER.md`.
- **Nuit du 19 au 20 octobre 2026, suite, en autonomie** (« fais ce que tu veux », le Vésuve cité en exemple) :
  - **Audit de qualité corrigé** : cartel des scènes qui défile, menu visible sur téléphone, titre `h1`, retour du focus à la fermeture des panneaux, pourcentage de chargement, pages de partage et plan du site pour chaque scène prête.
  - **Son d'ambiance propre à chaque lieu** : 13 nappes libres (CC0), choisies point par point (fontaine, marché, foule de l'arène, chantier, port…).
  - **Passe de détail** sur Nîmes, Arles, le pont du Gard et le Panthéon (releases `assets-v7` à `assets-v10`).
  - **Pompéi et l'éruption du Vésuve** (`#/scene/pompei`, release `assets-v11`, 11,5 Mo) : 24 août 79 vers 14 h (date d'octobre signalée), colonne plinienne dessinée en temps réel au-dessus du Vésuve d'avant 79, chute de ponces et de cendres, ciel voilé, habitants qui fuient avec leurs ballots, boutiques fermées ; forum et Capitole, via dell'Abbondanza, maison à atrium et péristyle, porte et rivage de 79. Relief Copernicus DEM GLO-30 retouché. Ville ajoutée à la carte ; l'événement « Éruption du Vésuve » ouvre la scène.
  - **Le Colisée et le Forum romain vers 107** (`#/scene/colisee`, release `assets-v12`, 8,1 Mo) : jour de jeux pour le triomphe dacique de Trajan, gradins pleins par rang, velum, arène et trappes du sous-sol, Colosse, Meta Sudans, arc de Titus, voie Sacrée, Forum et Palatin. Relief TINITALY 1.1. Accessible depuis Rome sur la carte et par l'événement « Inauguration du Colisée ».
  - Les deux propositions ont été vérifiées par une relecture contradictoire, puis la scène relue par un historien et un chef opérateur avant correction ; elles sont produites **sans ta validation** (`docs/scenes/pompei.md`, `docs/scenes/colisee.md`), et leurs choix de restitution sont dans `docs/A_VERIFIER.md`. Captures dans `docs/screenshots/pompei/` et `docs/screenshots/colisee/`.
- **21 et 22 octobre 2026, en autonomie** (« fais un max d'améliorations sur les graphismes », « je veux voir le phare d'Alexandrie ») :
  - **Carte plus vive** : fond stylisé conservé (teinte par époque, choix de l'utilisateur, qui a écarté un fond Natural Earth II), plaines et collines plus colorées, mer plus profonde, territoires hors de l'Empire moins éteints ; relief à la résolution native d'ETOPO (3 960 x 2 220 px, 2,1 Mo) et maillage plus dense.
  - **Rendu des scènes** : tonemapping neutre au lieu d'ACES, étalonnage plus saturé et plus lumineux dans les scènes, exposition propre à une scène (Pompéi plus sombre), lumière du ciel plus forte dans les ombres, halo léger sur les sources lumineuses, ombres de 4 096 px en qualité haute ; eau animée qui reflète le ciel sur tous les matériaux `water` et `river` ; grain au sol de près.
  - **Alexandrie et son phare** (`#/scene/alexandrie`, 6,9 Mo) : été 130, séjour d'Hadrien ; phare de 107 m à trois étages restitué d'après Thiersch et les monnaies alexandrines, feu allumé au sommet (lueur, lumière et fumée dessinées par le site), Grand Port et ses navires, Heptastade, Césaréum et ses obélisques. Relief restitué à la main d'après la côte antique publiée.
  - **Constantinople et Sainte-Sophie** (`#/scene/constantinople`, 14,2 Mo) : matin du 24 décembre 562, seconde consécration ; Sainte-Sophie avec sa coupole relevée et son intérieur, hippodrome et spina, Mésè et colonne de Justinien, Corne d'Or et ses navires. Relief Copernicus DEM GLO-30.
  - Deux événements ajoutés (Hadrien à Alexandrie, seconde consécration de Sainte-Sophie) ; Alexandrie et Constantinople ouvrent leur scène depuis la carte. Fiches dans `docs/scenes/`, doutes dans `docs/A_VERIFIER.md`, captures dans `docs/screenshots/alexandrie/` et `docs/screenshots/constantinople/`. Produites **sans ta validation**.
  - Restent ouverts : environ 2 millions de triangles affichés pour Constantinople et 330 appels de dessin pour Alexandrie, à mesurer sur ton portable.
- **Apprendre et Rechercher** (22 octobre 2026, porté depuis Hellas) : `#/apprendre` avec quatre jeux (quiz, remets dans l'ordre, situe la date avec av. ou apr. J.-C., où ? sur la carte, de 100 points sous 60 km à 0 au-delà de 900 km), fiches vues et meilleurs scores gardés sur l'appareil (`roma.progress`), `#/recherche` sur les événements, personnes et lieux sans accents ni casse. Sur téléphone, le jeu « Où ? » passe en feuille basse pour laisser la carte cliquable.
- **Propositions de scènes vérifiées** : Nîmes vers 130 (validée, option A2 : le pont du Gard devient une scène à part) et Arles vers 160 (`docs/scenes/arles.md`, à valider).

### En cours

- **Fichiers lourds** : scripts `npm run assets` (optimisation meshopt et KTX2, rapport de poids), `assets:publish` (GitHub Releases, manifeste SHA-256) et `assets:pull`, écrits et en relecture.

### Poids mesurés (site en ligne)

| Poste | Budget | Mesuré |
|---|---|---|
| Premier écran utile | 5 Mo | **1,32 Mo** (13 fichiers) |
| dont application | | 185 Ko |
| dont 3D (three.js, R3F, carte) | | 331 Ko |
| dont polices | | 105 Ko |
| dont relief et territoires | | 694 Ko |
| Site complet | 600 Mo | 5,35 Mo (85 fichiers) |

Tests : 117 tests unitaires et 14 tests Playwright (ordinateur et mobile), verts en local, en CI et sur le site en ligne.

### Décisions prises en autonomie (à confirmer ou à changer)

- **Lacune byzantine de 1402 à 1406** : Cliopatria n'a pas de tranche byzantine ces années-là (elle donne Constantinople aux Ottomans) ; la carte reprend la géométrie identique des années voisines, et l'attribution le précise.
- **Sécessions** : l'Empire des Gaules (de 260 à 274) et Palmyre (de 270 à 273) sont retirés du territoire de Rome pendant leurs dates.
- **Scène de Nîmes** : la frise passe à l'an 130 en entrant dans la scène, pour que l'étalonnage et le territoire correspondent.

### Problèmes connus

- **Netteté de la carte au zoom** (demande du 15 octobre 2026) : le relief à 2048 x 1152 px (environ 3,5 km par pixel) devient flou quand la caméra s'approche d'un lieu ou plonge vers une ville ; à améliorer plus tard (tuiles de relief plus fines chargées près de la caméra, détail procédural).
- **Constantinople** tombe juste hors des polygones de Cliopatria (côte tracée trop au nord) : invisible à l'échelle de la carte, à corriger si la caméra zoome sur la ville.
- **Bas-Empire** : la lumière froide rend les plaines très pâles, presque enneigées (point ouvert dans `docs/DESIGN.md`).
- **Mesure des i/s** toujours à faire sur ta machine (rendu logiciel en CI).

### Ce que j'attends de toi

1. Valider le plan de design (`docs/DESIGN.md`).
2. Regarder Pompéi, le Colisée, Alexandrie et Constantinople, faits sans validation, et me dire ce qui ne va pas. Valider les propositions de scènes vérifiées : Arles (`docs/scenes/arles.md`), pont du Gard (`docs/scenes/pont-du-gard.md`), Panthéon (`docs/scenes/pantheon.md`, une maquette sous licence NC-ND écartée sauf accord) et Cannes (`docs/scenes/cannes.md`).
3. Toujours valables : mesures du HUD, relecture de `docs/A_VERIFIER.md` (165 points désormais), Search Console, GoatCounter (facultatif).

## Collection de cartes (22 octobre 2026, en attente de ta validation)

Page à part, `#/collection`, avec un lien discret « Collection » dans l'en-tête. La frise, la carte et les scènes ne changent pas : la toile 3D se met en pause tant que la page est ouverte.

### Fait

- **Mécanique validée** : un paquet de cinq cartes par jour, tiré de façon déterministe (date et identifiant de joueur), donc impossible à relancer en rechargeant ; 5 raretés (commune 60 %, peu commune 25 %, rare 10 %, épique 4 %, légendaire 1 %) ; au moins une rare par paquet, une épique au plus tard au 10e paquet, une légendaire au plus tard au 30e ; une épique ou une légendaire tirée est toujours une carte nouvelle tant qu'il en reste.
- **Économie** : doublons changés en deniers (5 à 500 selon la rareté), fabrication d'une carte choisie (20 à 2 000 deniers). Première visite d'une scène 3D : la carte du lieu. Fiche d'événement lue : 5 deniers. Série complète (6 époques, 4 types) : un paquet bonus.
- **142 cartes** générées à partir des données (personnes, villes, lieux, scènes) ou créées pour les reliques et les unités, validées par zod au build : 51 personnages, 30 lieux, 20 reliques et objets, 20 armées et unités, 21 dieux ; 9 légendaires, 20 épiques, 32 rares, 40 peu communes, 41 communes. Caligula ajouté à ta demande (épique ; personne ajoutée aux données, texte qui sépare les faits attestés de la tradition hostile). Chaque carte a un texte court et au moins une source.
- **Dieux de Rome** (à ta demande) : 21 dieux à part, avec leur onglet, leur série et un cadre céleste (filet d'or, halo bleu, étoiles) : triade capitoline, grands dieux, Janus et Quirinus sans équivalent grec, César et Auguste divinisés, cultes venus d'ailleurs (Isis, Cybèle, Mithra, Sol Invictus), chacun avec sa date d'arrivée ou de premier temple à Rome et ses sources (Tite-Live, Ovide, Cicéron, Varron, Denys d'Halicarnasse). Les rapprochements grecs sont donnés comme tels (« rapproché de Zeus »).
- **Illustrations (option A + B)** : 129 œuvres du domaine public et photos sous CC0, CC BY ou CC BY-SA (Wikimedia Commons, Met), vérifiées une à une ; 13 rendus Blender du projet (8 scènes et 5 cartes de Cannes, `blender/cards.py`). WebP 640 et 320 px, 13,6 Mo en tout, chargés seulement quand une carte est affichée. Crédits sur chaque carte, dans `CREDITS.md` et sur la page Sources.
- **Design** : cadre par rareté (bronze, argent, lapis, pourpre, or), reflet holographique et inclinaison au survol pour les rares et au-delà, paquet scellé qui tremble puis éclate, cartes distribuées puis retournées une à une, rayons derrière les épiques et les légendaires. Avec le mouvement réduit, l'ouverture devient un simple fondu. Tout se joue au clavier (fenêtres modales natives, focus guidé).
- **Tests** : 25 tests Vitest (tirage, probabilités sur 200 000 tirages, garanties, sauvegarde, catalogue) ; 2 tests Playwright (ouverture au clavier, rechargement, Échap ; mouvement réduit), sur ordinateur et mobile.
- Points incertains (identifications de bustes, illustrations approchées, rareté) : section « Collection de cartes » de `docs/A_VERIFIER.md`.

### Ce que j'attends de toi

1. Ouvrir ton paquet du jour et dire si les effets et les couleurs sont assez spectaculaires.
2. Juger les illustrations les plus ternes (moulages de la colonne Trajane, strigile, gladius) et les rendus Blender de Cannes, à refaire si tu veux.
3. Trancher les points de `docs/A_VERIFIER.md` (rareté, portraits discutés).
