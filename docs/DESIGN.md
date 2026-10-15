# Plan de design

Statut : direction en place sur le site, à valider (brief, phase 2, point 1). Les valeurs ci-dessous sont celles du code (`src/styles.css`, `src/stage/grading.ts`, `src/map/terrainMaterial.ts`) ; une modification se fait là, puis ici.

## Palette nommée

| Nom | Valeur | Rôle |
|---|---|---|
| Nuit de Suburre | `#120D0A` | fond de page et des panneaux (à 93 % d'opacité sur la 3D) |
| Papyrus | `#F3EAD8` | texte principal |
| Travertin | `#CBBD9F` | texte secondaire, légendes, aides |
| Or d'Auguste | `#D8B25A` | accent par défaut : filets, bouton principal, année courante |
| Rouge pompéien | `#B83326` | accent de la République, repris par l'itinéraire d'Hannibal |
| Bleu d'Ostie | `#1A4D57` | eaux peu profondes de la carte (valeur du shader avant étalonnage), qui fonce jusqu'à `#040D1C` au large |

Contraste sur Nuit de Suburre : Papyrus 16,2:1, Travertin 10,4:1, Or d'Auguste 9,6:1. L'accent change avec l'époque ; pour le texte, il passe par `readableAccent`, qui l'éclaircit jusqu'à 4,5:1 au moins sur le fond (testé sur toute la frise).

### Accent et étalonnage par époque

Chaque époque a son accent et sa lumière ; la carte et les scènes passent de l'une à l'autre en vingt ans de frise.

| Époque | Accent | Lumière |
|---|---|---|
| Royauté | `#DB803D` terre cuite | aube orangée, soleil rasant, contraste doux |
| République | `#B83326` rouge pompéien | plein jour méditerranéen, ciel bleu franc |
| Haut-Empire | `#D9AD4D` or | fin d'après-midi dorée, saturation pleine |
| Crise du IIIe siècle | `#9E9480` cendre | ciel couvert, couleurs lavées |
| Bas-Empire | `#802E66` pourpre | lumière froide et lilas |
| Empire romain d'Orient | `#D9A842` or byzantin | crépuscule bleu nuit, ors chauds |

## Typographies

- **Cinzel** (SIL OFL 1.1), capitales dessinées d'après les inscriptions lapidaires romaines : titres, noms d'époques, boutons, noms de villes sur la carte. Toujours en capitales, interlettrage de 0,08 à 0,22 em.
- **EB Garamond** (SIL OFL 1.1), Garamond de lecture : textes, cartels, sources ; italique pour les notes, les lieux et les événements sur la carte. Corps de 17 px (16 px sur mobile), interligne 1,55.
- Typographie française appliquée au rendu : espaces insécables fines avant les signes doubles, guillemets « », apostrophes.
- Polices auto-hébergées, sous-ensemble latin seulement.

## Principes

1. **La 3D est le moment fort.** L'interface se tient en bordure : une frise en bas, un cartel sur le côté, rien au centre de l'image.
2. **Des cartels de musée.** Chaque fiche d'événement et chaque point d'intérêt d'une scène est un cartel : titre en capitales, date, certitude, texte court, sources dépliables.
3. **L'exactitude se voit.** Un indicateur de certitude (attesté, traditionnel, légendaire, débattu) accompagne chaque événement ; les doutes vont dans `docs/A_VERIFIER.md`.
4. **Une seule famille de mouvements.** Toutes les animations suivent la même courbe (`power3`) ; la caméra circule sans coupure de la frise à la carte puis à la scène, avec un voile de brume pour la bascule. Avec `prefers-reduced-motion`, les mouvements de caméra deviennent des fondus.
5. **Un seul appel à l'action principal par écran** : « Commencer » à l'accueil, « Point suivant » dans une scène, « Visiter en 3D » dans une fiche liée à une scène.
6. **Mobile d'abord.** Sur téléphone, la frise reste en bas, les fiches couvrent l'écran et le cartel d'une scène devient une feuille basse qui laisse voir la 3D.
7. **Sobriété technique.** Une seule toile WebGL pour tout le site, qualité adaptative (basse, moyenne, haute) et budget de poids par scène.

## Maquette de l'interface

Captures du site déployé, sur ordinateur (1440 x 900) et sur téléphone (Pixel 7), dans `docs/screenshots/phase-2/` :

| Écran | Ordinateur | Téléphone |
|---|---|---|
| Accueil | `01-accueil-bureau.webp` | `01-accueil-mobile.webp` |
| Cannes, 216 av. J.-C., avec l'itinéraire d'Hannibal | `02-cannes-218-av-jc-bureau.webp` | `02-cannes-218-av-jc-mobile.webp` |
| Apogée de 117 | `03-apogee-117-bureau.webp` | `03-apogee-117-mobile.webp` |
| Partage de 395 | `04-partage-395-bureau.webp` | `04-partage-395-mobile.webp` |
| Empire latin, 1204 | `05-empire-latin-1204-bureau.webp` | `05-empire-latin-1204-mobile.webp` |
| Chute de 1453 | `06-chute-1453-bureau.webp` | `06-chute-1453-mobile.webp` |
| Scène de Nîmes (en préparation) | `07-scene-nimes-en-preparation-bureau.webp` | `07-scene-nimes-en-preparation-mobile.webp` |

Les scènes 3D (Nîmes d'abord) auront leurs propres captures dans `docs/screenshots/` au moment de leur validation.

## Points à trancher

- La lumière du Bas-Empire rend les plaines très pâles, presque enneigées (capture du partage de 395) : la garder, ou réchauffer un peu le gain de cette époque.
- Sur la carte, quand un événement a lieu dans une ville, son nom en italique s'affiche au-dessus du nom de la ville en capitales (« Milan » sur « MILAN ») : redondant mais lisible. On peut masquer l'un des deux.
