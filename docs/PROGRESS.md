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

Mesure Playwright sur le build : fichiers réellement demandés au premier affichage, taille gzip pour les types que GitHub Pages compresse.

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

Tests : 60 tests unitaires, 12 tests Playwright (6 sur ordinateur, 6 sur mobile), sans aucune erreur console.

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

### Suite

Phase 2, la tranche verticale. Elle commence par un plan de design (palette nommée, typographies, principes, maquette de l'interface), à valider avant toute production.
