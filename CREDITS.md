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
| Lieux et villes | Pleiades, A Gazetteer of Past Places (R. Bagnall et al., éd.) ; CC BY 3.0 | Pleiades: A Gazetteer of Past Places, https://pleiades.stoa.org, © les contributeurs, CC BY 3.0, données modifiées | Identifiants et coordonnées vérifiés lieu par lieu pour `src/data/places.ts` et `src/data/cities.ts` |

Les autres sources retenues pour la carte (Cliopatria, AWMC, Itiner-e) et leurs obligations sont décrites dans `docs/ARCHITECTURE.md` ; chacune sera ajoutée ici au moment de son intégration.
