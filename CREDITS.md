# Crédits

Toute ressource externe est listée ici au moment où elle entre dans le projet : source, auteur, licence, modifications.

## Polices

| Police | Auteurs | Licence | Source | Modifications |
|---|---|---|---|---|
| Cinzel | The Cinzel Project Authors (Natanael Gama) | SIL Open Font License 1.1 | https://github.com/NDISCOVER/Cinzel, via le paquet npm `@fontsource/cinzel` 5.3.0 | aucune ; seul le sous-ensemble latin (graisses 400 et 600) est servi |
| EB Garamond | The EB Garamond Project Authors (Georg Duffner, Octavio Pardo) | SIL Open Font License 1.1 | https://github.com/octaviopardo/EBGaramond12, via le paquet npm `@fontsource/eb-garamond` 5.3.0 | aucune ; seul le sous-ensemble latin (400, 400 italique, 600) est servi |

## Bibliothèques livrées avec le site

Dépendances npm utilisées sans modification ; leurs licences accompagnent leurs paquets.

| Bibliothèque | Version | Licence | Source |
|---|---|---|---|
| React, React DOM | 19.3.1 | MIT | https://github.com/facebook/react |
| three.js | 0.186.1 | MIT | https://github.com/mrdoob/three.js |
| React Three Fiber | 9.8.2 | MIT | https://github.com/pmndrs/react-three-fiber |
| drei | 10.7.9 | MIT | https://github.com/pmndrs/drei |
| @react-three/postprocessing | 3.2.0 | MIT | https://github.com/pmndrs/react-postprocessing |
| postprocessing | 6.39.5 | zlib | https://github.com/pmndrs/postprocessing |
| troika-three-text (étiquettes 3D, via drei) | 0.52.5 | MIT | https://github.com/protectwise/troika |
| N8AO (occlusion ambiante des scènes) | 2.0.1 | ISC | https://github.com/N8python/n8ao |
| meshoptimizer (décodeur des modèles 3D) | inclus dans three.js | MIT | https://github.com/zeux/meshoptimizer |
| Basis Universal (transcodeur KTX2) | inclus dans three.js | Apache 2.0 | https://github.com/BinomialLLC/basis_universal |
| GSAP | 3.15.0 | GSAP Standard « No Charge » License (gratuite, non libre, propriété de Webflow) | https://gsap.com/standard-license |
| Zustand | 5.0.15 | MIT | https://github.com/pmndrs/zustand |
| marked | 18.1.1 | MIT | https://github.com/markedjs/marked |

## Contenus historiques

Les textes des événements, des époques et des pistes sont rédigés pour le projet (licence CC BY 4.0). Chaque événement cite ses propres sources (auteurs antiques et ouvrages de référence), affichées dans son cartel ; les liens mènent vers des traductions publiées par leurs sites respectifs (remacle.org, LacusCurtius, Perseus, Internet Archive, etc.), qui ne sont pas reproduites ici.

## Données géographiques

| Données | Source et licence | Attribution | Fichiers et modifications |
|---|---|---|---|
| Relief et bathymétrie | NOAA NCEI, ETOPO 2022, version 60 secondes d'arc, altitude de surface ; CC0 1.0 (domaine public des États-Unis) | NOAA National Centers for Environmental Information. 2022: ETOPO 2022 15 Arc-Second Global Relief Model. https://doi.org/10.25921/fd45-gt74 | `public/geo/relief.webp` : extrait régional (13° O à 53° E, 22° à 59° N) moyenné vers 2048 x 1152 px, altitude encodée sur un octet (racine carrée signée) ; script `scripts/geo/relief.ts` |
| Terres et lacs | Natural Earth 1:10m Land et Lakes, v5.1.2 ; domaine public | Made with Natural Earth. Free vector and raster map data @ naturalearthdata.com. | Rastérisés en masque terre et eau sur la grille du relief ; lacs de barrage modernes exclus (anachroniques) |
| Territoires romains | Cliopatria v0.2.1, Seshat Global History Databank ; CC BY 4.0 | J. S. Bennett, E. Mutch, A. Tollefson et al., Cliopatria v0.2.1 (Seshat Global History Databank), https://github.com/Seshat-Global-History-Databank/cliopatria, licence CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) ; article : Bennett et al. 2025, Scientific Data 12:247, doi:10.1038/s41597-025-04516-9 | `public/geo/territories.json` : 12 entités romaines et successeurs extraites, années converties en années astronomiques, tranches alignées sur les pistes de `src/data/tracks.ts`, territoires des sécessions (Gaules, Palmyre) retirés de Rome pendant leurs dates, découpe sur l'emprise de la carte, fusion par entité et période, îles de moins de 100 km² retirées, simplification de Visvalingam (27 km, 8 km pour les petits anneaux), coordonnées arrondies à 0,01°, lacune de la piste d'Orient de 1402 à 1406 comblée par la géométrie identique des années 1395 à 1401 et 1407 à 1414 ; script `scripts/geo/territories.ts` |
| Lieux et villes | Pleiades, A Gazetteer of Past Places (R. Bagnall et al., éd.) ; CC BY 3.0 | Pleiades: A Gazetteer of Past Places, https://pleiades.stoa.org, © les contributeurs, CC BY 3.0, données modifiées | Identifiants et coordonnées vérifiés lieu par lieu pour `src/data/places.ts` et `src/data/cities.ts` |

Les autres sources retenues pour la carte (AWMC, Itiner-e) et leurs obligations sont décrites dans `docs/ARCHITECTURE.md` ; chacune sera ajoutée ici au moment de son intégration.

## Scènes 3D

| Ressource | Source et licence | Attribution | Usage et modifications |
|---|---|---|---|
| Relief de Nîmes | IGN, RGE ALTI 5 m et 50 m, service WMS-R de la Géoplateforme ; Licence Ouverte Etalab 2.0 | IGN, RGE ALTI | Terrain de la scène de Nîmes, reprojeté du Lambert-93 vers le repère local ; fort Vauban et trois remblais modernes effacés (`blender/kit/terrain.py`) |
| Textures de pierre, d'enduit, de sable et de dallage | Poly Haven, Sandstone Blocks 08, Yellow Plaster, Sand 01, Rectangular Paving (1k) ; CC0 1.0 | Rob Tuytel ; Dimitrios Savva (Rectangular Paving) | Teintées et répétées dans la scène de Nîmes (`blender/kit/materials.py`) |
| Textures de marbre, de granit et de travertin du Panthéon et du Colisée | ambientCG, Marble021, Marble014, Granite001A, Travertine009 ; CC0 1.0 | ambientCG (Lennart Demes) | Recolorées en pentélique, jaune antique, pavonazzetto, granit gris et rose, porphyre (`blender/kit/pantheon_materials.py`) |
| Relief, cours d'eau et orthophotographie du pont du Gard et d'Arles | IGN, RGE ALTI 2 m, 5 m, 50 m et 100 m, BD TOPO V3 (surfaces hydrographiques), BD ORTHO, services de la Géoplateforme ; Licence Ouverte Etalab 2.0 | IGN | Terrains des scènes ; l'orthophotographie sert seulement à placer la grande arche du pont du Gard (`blender/kit/pont_terrain.py`, `blender/arles.py`) |
| Textures du pont du Gard, d'Arles et de Nîmes | Poly Haven, Dry Ground Rocks, Old Sandstone 02, Dry Riverbed Rock, Medieval Blocks 02, Brown Planks 03, Monastery Stone Floor ; CC0 1.0 | Poly Haven | Pierre, roche, bois des quais et dallages, teintés et répétés |
| Relief de Cannes | INGV, TINITALY 1.1, modèle numérique de terrain au pas de 10 m, service WCS ; CC BY 4.0 | Tarquini S., Isola I., Favalli M., Battistini A., Dotta G. (2023). TINITALY, a digital elevation model of Italy with a 10 meters cell size (Version 1.1). Istituto Nazionale di Geofisica e Vulcanologia (INGV). https://doi.org/10.13127/tinitaly/1.1 | Extrait de 16 km sur 16 km autour de Canne della Battaglia, reprojeté de l'UTM 32 vers le repère local, rééchantillonné au pas de 25 m ; lit de l'Aufide creusé selon un tracé restitué (le cours de 216 av. J.-C. est inconnu) ; couleurs du sol peintes par le script (`blender/kit/cannes_terrain.py`) |
| Relief de Pompéi et du Vésuve | Copernicus DEM GLO-30, tuile N40 E014 ; licence Copernicus DEM (usage libre avec attribution) | produit à partir de Copernicus WorldDEM-30 © DLR e.V. 2010-2014 et © Airbus Defence and Space GmbH 2014-2018, fourni dans le cadre de COPERNICUS par l'Union européenne et l'ESA ; « The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30 » | Terrain de la scène de Pompéi, retouché pour restituer le Vésuve d'avant 79 (`blender/kit/pompei_terrain.py`) |
| Relief de Rome | TINITALY 1.1, INGV ; CC BY 4.0 | Tarquini S. et al. (2023), TINITALY digital elevation model, version 1.1, doi:10.13127/tinitaly/1.1, modifié | Terrain de la scène du Colisée, vallée et forums nivelés (`blender/colisee.py`) |
| Relief de Constantinople | Copernicus DEM GLO-30, tuiles N40 et N41, E028 et E029 ; licence Copernicus DEM (usage libre avec attribution) | produit à partir de Copernicus WorldDEM-30 © DLR e.V. 2010-2014 et © Airbus Defence and Space GmbH 2014-2018, fourni dans le cadre de COPERNICUS par l'Union européenne et l'ESA | Terrain de la scène de Constantinople, sols bâtis nivelés (`blender/kit/constantinople_terrain.py`) |
| Texture Plastered Wall (alexandrie) | https://polyhaven.com/a/plastered_wall ; CC0 1.0 | Amal Kumar | Matériaux de la scène (Alexandrie) |
| Lettres de bronze des dédicaces | Cinzel (SIL OFL 1.1), déjà livrée avec le site | The Cinzel Project Authors | Converties en volumes pour CIL XII 3156 et CIL XII 3151 |

La frise de rinceaux de la Maison Carrée est générée par le script ; ce n'est pas une copie de la frise conservée.

## Sons d'ambiance

Boucles de 45 s faites pour le projet dans `public/audio/` (mono, recadrées, filtrées, fondu enchaîné à la boucle, volume normalisé à -20 LUFS, Ogg Vorbis et MP3). Coupées par défaut sur le site.

| Fichier | Source | Auteur | Licence |
|---|---|---|---|
| `evening-city` (foule lointaine, filtrée pour rester inintelligible) | https://commons.wikimedia.org/wiki/File:360703_eguobyte_large-crowd-medium-distance-stereo.wav | eguobyte | CC0 1.0 |
| `summer-evening` (cigales) | https://commons.wikimedia.org/wiki/File:Cicada_orni.ogg | DavidDelon | domaine public |
| `summer-evening` (martinets) | https://xeno-canto.org/819689 | Sonothèque ADVL, enregistrement de Léa Lefrou | CC0 1.0 |
| `fountain` | https://commons.wikimedia.org/wiki/File:Fountain_in_toulouse.ogg | aldor | domaine public |
| `river` | https://commons.wikimedia.org/wiki/File:Sanna_river_rapids.ogg | Jarrod Stanley | CC0 1.0 |
| `harbour` (vagues) | https://commons.wikimedia.org/wiki/File:WWS_Smallwaves.ogg | « Smallwaves » par Torsten Nilsson, Work With Sounds | CC BY 4.0, modifié |
| `harbour` (goéland) | https://xeno-canto.org/707075 | Sonothèque ADVL | CC0 1.0 |
| `harbour` (craquements de bois) | https://opengameart.org/content/tree-creaking | AntumDeluge, d'après Department64 | CC0 1.0 |
| `wind` (vent synthétisé) | https://opengameart.org/content/wind1 | Luke.RUSTLTD | CC0 1.0 |
| `arena-crowd` | https://freesound.org/s/342378/ ; https://freesound.org/s/141704/ ; foule d'eguobyte ci-dessus | stefgaz ; felix.blume ; eguobyte | CC0 1.0 |
| `market` | https://freesound.org/s/384052/ ; https://freesound.org/s/159614/ ; https://freesound.org/s/455773/ | emanuele.caro ; lollosound ; kyles | CC0 1.0 |
| `masonry` | https://freesound.org/s/812116/ ; https://freesound.org/s/321571/ | achats57 ; mondofred | CC0 1.0 |
| `animals` | https://freesound.org/s/131925/ ; https://commons.wikimedia.org/wiki/File:157763_felix-blume_a-donkey-is-braying-in-his-enclosure-in-south-of-france.wav ; https://freesound.org/s/453433/ | felix.blume ; Felix Blume ; kyles | CC0 1.0 |
| `cart` | https://freesound.org/s/437078/ ; https://freesound.org/s/538438/ | craigsmith ; bruno.auzet | CC0 1.0 |
| `interior` | https://freesound.org/s/828537/ ; https://freesound.org/s/478545/ | NickTayloe ; LordFluffeh | CC0 1.0 |
| `birds-day` | https://freesound.org/s/404663/ ; https://freesound.org/s/116791/ | straget ; nigelcoop | CC0 1.0 |

