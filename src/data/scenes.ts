import type { Scene } from './schema.ts'

export const scenes: Scene[] = [
  {
    "id": "cannes",
    "title": "Bataille de Cannes",
    "status": "ready",
    "year": -215,
    "lat": 41.2967,
    "lon": 16.1518,
    "summary": "Le 2 août 216 av. J.-C. (calendrier romain), dans la basse vallée de l'Aufide, l'actuel Ofanto. Huit légions et autant d'alliés, environ 86 000 hommes selon Polybe dont 10 000 restés au camp, affrontent les quelque 50 000 hommes d'Hannibal. La maquette suit la restitution de Kromayer (rive droite, en aval de Cannes, Romains face au sud) : l'emplacement exact reste débattu et le tracé antique du fleuve est inconnu. Relief réel (TINITALY), figurines grossies trois fois en vue tactique.",
    "points": [
      {
        "id": "la-traversee",
        "title": "La traversée et le déploiement",
        "text": "Juste après le lever du soleil, Varron, qui a le commandement ce jour-là selon Polybe et Tite-Live, fait passer le fleuve aux troupes du grand camp et les range avec celles du petit camp. Les Romains font face au sud : cavalerie romaine à droite contre le fleuve, infanterie au centre en manipules plus serrés et plus profonds que d'ordinaire, cavalerie alliée à gauche, troupes légères en avant. Hannibal fait passer ses frondeurs baléares et ses lonchophores, puis le reste de l'armée en deux points, et se range face au nord : cavalerie ibère et celte contre le fleuve, Libyens, Celtes et Ibères alternés en croissant, Libyens, Numides. 10 000 Romains restent au grand camp.",
        "sources": [
          "Polybe III, 110, 8 à 11 ; 113, 1 à 9 ; 117, 8",
          "Tite-Live XXII, 45, 5 à 46, 7",
          "Appien, Le livre d'Hannibal, 20 et 25",
          "J. Kromayer et G. Veith, Antike Schlachtfelder III, 1, 1912, p. 322 à 325"
        ]
      },
      {
        "id": "l-escarmouche",
        "title": "L'escarmouche des troupes légères",
        "text": "Les troupes légères engagent le combat sans avantage pour personne : javelots des vélites contre balles des frondeurs baléares et traits des lonchophores. Selon Tite-Live, Paul Émile est grièvement atteint par une balle de fronde dès le début ; Polybe le dit au contraire encore indemne après le combat de cavalerie. Les légers se replient ensuite derrière les lignes, repli supposé par Kromayer d'après la bataille de Zama. Le nom de vélites n'est attesté qu'à partir de 211 av. J.-C. : on parle ici d'infanterie légère.",
        "sources": [
          "Polybe III, 115, 1 et 116, 1",
          "Tite-Live XXII, 47, 1 et 49, 1 ; XXVI, 4",
          "Appien, Le livre d'Hannibal, 25",
          "Kromayer 1912, p. 324, n. 1"
        ]
      },
      {
        "id": "le-choc-des-cavaliers",
        "title": "Le choc des cavaliers au bord de l'Aufide",
        "text": "Sur l'aile romaine droite, coincés entre le fleuve et l'infanterie, les cavaliers ibères et celtes d'Hasdrubal heurtent de front les cavaliers romains. Sans place pour manœuvrer, beaucoup mettent pied à terre et luttent corps à corps. Les Romains sont tués pour la plupart, les autres poursuivis le long du fleuve ; Paul Émile rejoint le centre. Personne ne monte avec des étriers, inconnus en Europe avant la fin du VIe siècle.",
        "sources": [
          "Polybe III, 115, 2 à 4 ; 116, 1 à 4",
          "Tite-Live XXII, 47, 1 à 3 ; 49, 1 à 3",
          "Kromayer 1912, p. 288, n. 1, et p. 295 et 296",
          "A. E. Dien, Ars Orientalis 16, 1986 (étriers)"
        ]
      },
      {
        "id": "la-poussee-romaine",
        "title": "La poussée romaine dans le croissant",
        "text": "L'infanterie lourde s'engage. Les Celtes, torse nu avec leurs longues épées de taille, et les Ibères, en tuniques de lin blanc bordées de pourpre, tiennent un temps, puis cèdent sous le poids des légions : le croissant s'aplatit, puis se creuse. Les Romains, attirés vers le centre, se resserrent et s'enfoncent dans la poche. Paul Émile et Hannibal combattent tous deux dans la mêlée. Tite-Live, Appien et Frontin ajoutent une ruse de faux transfuges que Polybe ignore : elle n'est pas représentée.",
        "sources": [
          "Polybe III, 113, 8 et 9 ; 114, 2 à 4 ; 115, 5 à 8 ; 116, 1 à 4",
          "Tite-Live XXII, 46, 5 à 7 ; 47, 4 à 7 ; 48, 1 à 4",
          "Appien, Le livre d'Hannibal, 20, 22 et 23",
          "Frontin, Stratagèmes II, 3, 7 et II, 5, 27",
          "Kromayer 1912, p. 314 à 316"
        ]
      },
      {
        "id": "la-fuite-de-la-cavalerie-alliee",
        "title": "Les Numides et la fuite de la cavalerie alliée",
        "text": "Sur l'aile gauche romaine, les Numides, sur de petits chevaux montés sans bride, harcèlent la cavalerie alliée de Varron sans engagement décisif. Hasdrubal, vainqueur au bord du fleuve, vient leur prêter main-forte en passant derrière l'armée romaine, selon la restitution de Kromayer : à son approche, la cavalerie alliée s'enfuit. Il lance les Numides à sa poursuite et garde ses escadrons.",
        "sources": [
          "Polybe III, 116, 5 à 7",
          "Tite-Live XXXV, 11, 6 à 8",
          "J. Kromayer et G. Veith, Schlachten-Atlas, 1922, planche 6 et texte",
          "Kromayer 1912, p. 297"
        ]
      },
      {
        "id": "la-tenaille",
        "title": "Les Libyens referment la tenaille",
        "text": "Quand les Romains se sont assez enfoncés, les deux corps de Libyens, armés à la romaine avec les armes prises à la Trébie et à Trasimène, se tournent vers l'intérieur et attaquent les flancs des légions. Les Romains doivent faire face de plusieurs côtés et perdent leur élan. Le détail de la manœuvre (conversion en ligne ou colonnes faisant face) est discuté, comme leur nombre, estimé de 5 000 à 8 500 hommes.",
        "sources": [
          "Polybe III, 114, 1 ; 115, 8 à 12",
          "Tite-Live XXII, 46, 4 ; 47, 8 à 10",
          "M. Samuels, The Reality of Cannae, 1990, p. 18 et 24",
          "Kromayer 1912, p. 326 et 342"
        ]
      },
      {
        "id": "la-charge-d-hasdrubal",
        "title": "Hasdrubal charge le dos des légions",
        "text": "Laissant les Numides poursuivre la cavalerie alliée, Hasdrubal lance ses escadrons contre les derniers rangs romains, par charges répétées en plusieurs points. L'armée romaine est encerclée : Celtes et Ibères devant, Libyens sur les flancs, cavaliers derrière. Tite-Live raconte autrement ce moment : Hasdrubal porterait des Espagnols et des Gaulois au secours des Africains. Cet Hasdrubal n'est pas le frère d'Hannibal, qui combat alors en Espagne.",
        "sources": [
          "Polybe III, 116, 7 et 8",
          "Tite-Live XXII, 48, 5 et 6 ; XXIII, 26 à 29",
          "J. Kromayer et G. Veith, Schlachten-Atlas, 1922, texte de la planche 6"
        ]
      },
      {
        "id": "l-encerclement",
        "title": "L'encerclement et le massacre",
        "text": "Pris dans l'anneau, les Romains combattent sur place et sont tués en masse jusqu'aux deux dernières heures du jour. Paul Émile tombe, comme Cnaeus Servilius Geminus et, selon Tite-Live, l'ancien maître de cavalerie Minucius ; Varron s'enfuit à Venusia. Polybe compte environ 70 000 morts ; Tite-Live, 45 500 fantassins et 2 700 cavaliers. Hannibal perd de 5 700 (Polybe) à 8 000 hommes (Tite-Live). Les 10 000 hommes du grand camp attaquent le camp carthaginois : selon Polybe, 2 000 sont tués et les autres pris ; selon Tite-Live, les deux camps romains capitulent le lendemain.",
        "sources": [
          "Polybe III, 116, 9 à 13 ; 117, 1 à 11",
          "Tite-Live XXII, 49 à 52",
          "Appien, Le livre d'Hannibal, 24 et 25",
          "Plutarque, Fabius, 16, 8"
        ]
      }
    ],
    "ambience": [
      {
        "layer": "wind",
        "volume": 0.5
      },
      {
        "layer": "river",
        "volume": 0.35,
        "points": [
          "la-traversee",
          "le-choc-des-cavaliers"
        ]
      }
    ]
  },
  {
    "id": "pantheon",
    "title": "Panthéon d'Hadrien",
    "status": "ready",
    "year": 129,
    "lat": 41.89861,
    "lon": 12.47683,
    "summary": "Le 21 avril 129, à midi, jour anniversaire de la fondation de Rome. Rebâti sous Trajan et Hadrien sur le temple d'Agrippa, le Panthéon couvre sa rotonde d'une coupole de béton d'environ 43 m de diamètre, aussi haute que large, ouverte au ciel par un oculus de près de 9 m. À midi, la lumière du soleil y découpe une tache qui glisse sur les caissons et les murs.",
    "ambience": [
      {
        "layer": "evening-city",
        "volume": 0.4,
        "points": [
          "vue-d-ensemble",
          "le-porche"
        ]
      },
      {
        "layer": "market",
        "volume": 0.35,
        "points": [
          "vue-d-ensemble",
          "le-porche"
        ]
      },
      {
        "layer": "birds-day",
        "volume": 0.3,
        "points": [
          "vue-d-ensemble",
          "le-porche"
        ]
      },
      {
        "layer": "interior",
        "volume": 0.6,
        "points": [
          "la-rotonde",
          "l-oculus",
          "les-niches"
        ]
      }
    ],
    "points": [
      {
        "id": "le-porche",
        "title": "Granit et bronze : le porche",
        "text": "Seize fûts monolithes de granit égyptien, d'environ 40 pieds romains (près de 12 m) et 50 tonnes chacun, portent le porche : gris du mont Claudien en façade, roses d'Assouan derrière. Bases et chapiteaux sont en marbre du Pentélique, près d'Athènes. Le toit reposait sur une charpente entièrement en bronze, sans doute la plus ancienne charpente métallique connue. Elle a tenu jusqu'en 1625 : le pape Urbain VIII la fit alors démonter, et l'essentiel de son métal, plus de 150 tonnes, fut fondu en canons. Le porche aurait été conçu pour des colonnes encore plus hautes, jamais arrivées : l'hypothèse reste discutée.",
        "sources": [
          "Marder et Wilson Jones 2015, p. 8 et 9 : https://assets.cambridge.org/97805218/09320/excerpt/9780521809320_excerpt.pdf",
          "Wikipédia (en), Pantheon, Rome (fûts de 40 pieds d'après Wilson Jones ; bronze fondu surtout en canons d'après Lanciani et Fea) : https://en.wikipedia.org/wiki/Pantheon,_Rome",
          "Université de Cologne, charpente de bronze (1625 et 1626, 180 t) : https://archaeologie.phil-fak.uni-koeln.de/en/research/research-projects/the-bronze-roof-truss-of-the-vestibule-of-the-pantheon-in-rome",
          "BTU Cottbus (« wohl ältesten metallischen Dachtragwerks ») : https://www.b-tu.de/fg-bautechnikgeschichte/forschung/abgeschlossene-projekte/das-bronzedachwerk-der-vorhalle-des-pantheons-in-rom",
          "Heinzelmann, Heinzelmann et Lorenz, Construction History 33, 2 (2018) (152 t, titre cité par la page de Cologne)",
          "Davies, Hemsoll et Wilson Jones, Art History 10 (1987), p. 133 à 153 (colonnes prévues plus grandes, cité par Marder et Wilson Jones, n. 15)"
        ]
      },
      {
        "id": "la-rotonde",
        "title": "La coupole à caissons",
        "text": "La coupole de béton couvre un cercle d'environ 43,3 m de diamètre, et l'oculus s'ouvre à la même hauteur : une sphère presque parfaite tiendrait dans la salle. Cinq rangées de 28 caissons, de plus en plus petits vers le haut, allègent la voûte. Les bâtisseurs ont aussi allégé le béton en montant, avec de la pierre ponce. Dehors, des tuiles de bronze couvraient la coupole : elles sont attestées en 663, quand l'empereur Constant II les fit enlever. Le décor des caissons est perdu : des rosaces de bronze ont été supposées, sans preuve.",
        "sources": [
          "MiC, 43,30 m de diamètre et de hauteur : https://direzionemuseiroma.cultura.gov.it/en/pantheon/historical-background/",
          "Turismo Roma, cinq rangs de 28 caissons : https://www.turismoroma.it/it/luoghi/pantheon",
          "Fletcher 2019, p. 334 (sphère de 43,98 m du relevé de Berne) : https://doi.org/10.1007/s00004-018-00423-2",
          "Platner et Ashby 1929 (pierre ponce, tuiles enlevées en 663) : https://penelope.uchicago.edu/Thayer/E/Gazetteer/Places/Europe/Italy/Lazio/Roma/Rome/_Texts/PLATOP*/Pantheon.html",
          "Paul Diacre, Histoire des Lombards 5, 11 (traduction citée par Wikipédia en anglais) : https://en.wikipedia.org/wiki/Pantheon,_Rome",
          "F. G. Moore, « The Gilt-Bronze Tiles of the Pantheon », AJA 3 (1899), p. 40 à 43 : https://penelope.uchicago.edu/Thayer/E/Journals/AJA/3/1/Pantheon_Tiles*.html"
        ]
      },
      {
        "id": "l-oculus",
        "title": "L'oculus, cadran solaire géant",
        "text": "Large d'environ 9 m, l'oculus est la seule ouverture de la rotonde vers le ciel. La tache de soleil qu'il découpe tourne au fil des heures, comme sur un cadran solaire. À midi, elle reste sur la coupole en hiver, atteint la naissance de la voûte aux équinoxes et descend sur le sol en été. Vers le 21 avril, anniversaire de la fondation de Rome, elle couvre la porte d'entrée. Robert Hannah et Giulio Magli y voient une mise en scène voulue ; l'hypothèse reste discutée. Les jours de pluie, l'eau tombe dans la salle et s'écoule par 22 trous du dallage.",
        "sources": [
          "Hannah et Magli, Numen 58 (2011), p. 486 à 513 (prépublication, p. 5 et 6) : https://arxiv.org/abs/0910.0128",
          "G. Magli, étude de cas 9.3, ICOMOS et UAI, Heritage Sites of Astronomy and Archaeoastronomy (2010), p. 151 à 154 : https://web.astronomicalheritage.org/images/astronomicalheritage.org/thematic-study/ch09cs3.pdf",
          "K. de Fine Licht, The Rotunda in Rome (1968), p. 295, n. 43, avis contraire cité par Hannah et Magli, n. 5",
          "MiC, oculus d'environ 9 m et 22 trous : https://direzionemuseiroma.cultura.gov.it/en/pantheon/historical-background/",
          "Plutarque, Romulus 12, 1 : https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Plutarch/Lives/Romulus*.html"
        ]
      },
      {
        "id": "les-niches",
        "title": "Niches, édicules et marbres",
        "text": "Sous la coupole, le mur s'ouvre sur sept grandes niches, semi-circulaires ou rectangulaires, précédées ou encadrées de colonnes cannelées, pour la plupart en jaune antique, un marbre jaune d'Afrique du Nord. Entre elles se dressent huit édicules à frontons triangulaires ou cintrés. Porphyre, granit et marbres colorés venus de tout l'Empire couvrent le sol et les parois. Des statues occupaient sans doute ces niches, mais aucune n'a survécu. Dion Cassius cite Mars, Vénus et César divinisé, mais pour le premier Panthéon, celui d'Agrippa. Pour celui d'Hadrien, on ignore quels dieux étaient là : les statues restent donc anonymes.",
        "sources": [
          "Direzione Musei (MiC), sept chapelles et huit édicules : https://direzionemuseiroma.cultura.gov.it/en/pantheon/historical-background/",
          "Fletcher 2019, p. 332 : https://doi.org/10.1007/s00004-018-00423-2",
          "Piranesi, Veduta interna del Panteon (légende : douze colonnes principales de giallo ; essai du projet : marbre de Chemtou, Tunisie) : https://scalar.usc.edu/works/piranesidigitalproject/entirely-ancient",
          "Platner et Ashby 1929 : https://penelope.uchicago.edu/Thayer/E/Gazetteer/Places/Europe/Italy/Lazio/Roma/Rome/_Texts/PLATOP*/Pantheon.html",
          "Dion Cassius 53, 27, 2 et 3 : https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/53*.html",
          "Hannah et Magli, p. 2 (statues non conservées) : https://arxiv.org/abs/0910.0128"
        ]
      }
    ]
  },
  {
    "id": "nimes",
    "title": "Nîmes romaine (Nemausus)",
    "status": "ready",
    "year": 130,
    "lat": 43.8382,
    "lon": 4.3561,
    "summary": "Vers 130, sous Hadrien, un soir de juin. Ancien chef-lieu des Volques Arécomiques devenu colonie, Nemausus s'étend des collines calcaires jusqu'à la plaine, dans une enceinte d'environ 6 km offerte par Auguste. On y trouve le forum et sa Maison Carrée, l'amphithéâtre achevé vers l'an 100, le sanctuaire de la source et l'eau de l'aqueduc venue d'Uzès.",
    "ambience": [
      {
        "layer": "evening-city",
        "volume": 0.35
      },
      {
        "layer": "summer-evening",
        "volume": 0.45
      },
      {
        "layer": "birds-day",
        "volume": 0.3
      },
      {
        "layer": "wind",
        "volume": 0.35,
        "points": [
          "vue-d-ensemble"
        ]
      },
      {
        "layer": "cart",
        "volume": 0.45,
        "points": [
          "porte-d-auguste"
        ]
      },
      {
        "layer": "animals",
        "volume": 0.35,
        "points": [
          "porte-d-auguste",
          "fontaine-tour-magne"
        ]
      },
      {
        "layer": "market",
        "volume": 0.5,
        "points": [
          "maison-carree"
        ]
      },
      {
        "layer": "arena-crowd",
        "volume": 0.5,
        "points": [
          "amphitheatre"
        ]
      },
      {
        "layer": "fountain",
        "volume": 0.6,
        "points": [
          "fontaine-tour-magne",
          "eau-castellum"
        ]
      }
    ],
    "points": [
      {
        "id": "porte-d-auguste",
        "title": "La porte d'Auguste et la voie Domitienne",
        "text": "En 16 ou 15 av. J.-C., Auguste donne à la colonie ses portes et ses murs, rappelle l'inscription de cette porte. Deux grandes arches laissent passer les chariots de la voie Domitienne, venue d'Italie par Ugernum (Beaucaire), deux petites les piétons ; deux tours la flanquaient. L'enceinte, longue d'environ 6 km, enferme près de 220 ha, collines comprises.",
        "sources": [
          "CIL XII 3151",
          "Office de tourisme de Nîmes, La Porte Auguste : https://nimes-tourisme.com/en/explorer/nimes/monuments-et-sites/la-porte-auguste/",
          "APHG et Inrap 2024 : https://www.aphg.fr/IMG/pdf/dossier2_inrap_aphg.pdf"
        ]
      },
      {
        "id": "maison-carree",
        "title": "La Maison Carrée et le forum",
        "text": "Sur le côté sud du forum se dresse un temple corinthien élevé sur un podium. Des lettres de bronze, dont il ne reste que les trous de fixation, le dédiaient à Caius et Lucius César, petits-fils et fils adoptifs d'Auguste, « princes de la jeunesse ». Bâti en calcaire du bois des Lens, il mesure environ 26 m de long et 17 m de haut. Face à lui, au nord, siégeait probablement la curie des décurions.",
        "sources": [
          "Ville de Nîmes, La Maison Carrée de Nîmes, p. 5 à 8 : https://nimes-tourisme.com/app/uploads/2026/03/la-maison-carree-de-nimes.pdf",
          "Musée de la Romanité, dossier pédagogique, p. 8 et 9 : https://museedelaromanite.fr/content/uploads/2021/08/DOSSIER-PEDAGOGIQUE-ARCHI-PUBLIQUE-bd.pdf",
          "CIL XII 3156"
        ]
      },
      {
        "id": "amphitheatre",
        "title": "L'amphithéâtre",
        "text": "Achevé vers l'an 100, l'amphithéâtre mesure 133 m sur 101 m. Deux étages de 60 arcades et un attique portent les consoles des mâts du velum, la toile qui protégeait du soleil 34 rangées de gradins. Environ 22 000 spectateurs, placés selon leur rang, y suivaient chasses, exécutions et combats de gladiateurs. Des places étaient réservées aux bateliers du Rhône et de la Saône.",
        "sources": [
          "Musée de la Romanité, dossier pédagogique, p. 12 et 13",
          "Ville de Nîmes, webdocumentaire des Arènes : https://arenes-webdoc.nimes.fr/en/construction/design/terms-of-the-contract/seating-spectators/"
        ]
      },
      {
        "id": "fontaine-tour-magne",
        "title": "Le sanctuaire de la Fontaine et la tour Magne",
        "text": "Au pied du mont Cavalier jaillit la source du dieu Nemausus, qui a donné son nom à la ville. Dès 25 av. J.-C., on l'entoure d'un nymphée, de portiques, d'un autel du culte impérial, d'un théâtre et d'une salle voûtée, appelée bien plus tard « temple de Diane ». Les notables y font dresser leurs statues. Au sommet, la tour Magne, octogonale, enveloppe une tour gauloise et signale de loin la ville et son sanctuaire.",
        "sources": [
          "Musée de la Romanité, dossier pédagogique, p. 5 et 6",
          "C. Chulsky 2015 : https://books.openedition.org/pccj/2543",
          "Office de tourisme de Nîmes, La Tour Magne : https://nimes-tourisme.com/en/explorer/nimes/monuments-et-sites/la-tour-magne/"
        ]
      },
      {
        "id": "eau-castellum",
        "title": "L'eau d'Uzès : le castellum et le pont du Gard",
        "text": "Construit vers le milieu du Ier siècle, l'aqueduc capte la source d'Eure près d'Uzès et parcourt 50 km avec une pente moyenne de 25 cm par kilomètre. Au pont du Gard, il franchit le Gardon à 48,77 m de hauteur sur trois étages d'arches. À Nîmes, il aboutit au castellum, un bassin circulaire d'environ 6 m de diamètre d'où dix tuyaux de plomb distribuent l'eau aux quartiers.",
        "sources": [
          "Site du Pont du Gard, dossier de presse et mémento : https://pontdugard.fr/sites/default/files/2023-05/lepontdugard.pdf",
          "Musée de la Romanité, dossier pédagogique, p. 10",
          "Notice Mérimée IA30003277 : https://pop.culture.gouv.fr/notice/merimee/IA30003277"
        ]
      }
    ]
  },
  {
    "id": "arles",
    "title": "Arles romaine (Arelate)",
    "status": "ready",
    "year": 160,
    "lat": 43.677616,
    "lon": 4.630799,
    "summary": "Vers 160, à la fin du règne d'Antonin le Pieux. Colonie de vétérans de la VIe légion fondée en 46 av. J.-C., Arelate tient le port fluvial du bas Rhône, entre la Méditerranée et la Gaule. Sur la colline de l'Hauture s'étagent le forum, le théâtre et l'amphithéâtre ; dans la plaine, le cirque est achevé depuis une dizaine d'années, et la ville déborde sur la rive droite, au quartier de Trinquetaille.",
    "ambience": [
      {
        "layer": "evening-city",
        "volume": 0.35
      },
      {
        "layer": "summer-evening",
        "volume": 0.4
      },
      {
        "layer": "birds-day",
        "volume": 0.25
      },
      {
        "layer": "wind",
        "volume": 0.35,
        "points": [
          "vue-d-ensemble"
        ]
      },
      {
        "layer": "market",
        "volume": 0.5,
        "points": [
          "forum"
        ]
      },
      {
        "layer": "arena-crowd",
        "volume": 0.35,
        "points": [
          "theatre"
        ]
      },
      {
        "layer": "arena-crowd",
        "volume": 0.5,
        "points": [
          "amphitheatre",
          "cirque"
        ]
      },
      {
        "layer": "cart",
        "volume": 0.4,
        "points": [
          "port-trinquetaille",
          "cirque"
        ]
      },
      {
        "layer": "harbour",
        "volume": 0.7,
        "points": [
          "port-trinquetaille"
        ]
      }
    ],
    "points": [
      {
        "id": "forum",
        "title": "Le forum et ses cryptoportiques",
        "text": "Sous Auguste, la colonie bâtit son forum sur le flanc ouest de la colline. Pour obtenir une place horizontale, les architectes construisent d'abord un socle de galeries voûtées en fer à cheval, les cryptoportiques, à demi enterrées. Au-dessus s'étend une place dallée d'environ 3 000 m², bordée de portiques, cœur politique, judiciaire et religieux de la cité. On y a retrouvé en 1951 une copie en marbre du bouclier d'honneur décerné à Auguste, datée de 26 av. J.-C.",
        "sources": [
          "MDAA, dossier Urbanisme et romanisation, fiche maquette Le forum d'Arles",
          "AE 1952, 165 ; https://www.livius.org/pictures/france/arles/arelate-clipeus-virtutis-of-augustus/"
        ]
      },
      {
        "id": "theatre",
        "title": "Le théâtre d'Auguste",
        "text": "Premier monument de spectacle de la colonie, le théâtre est élevé au sommet de la colline dans les années 20 à 10 av. J.-C. Sa cavea de 102 m de diamètre compte 33 rangées de gradins, et sa façade trois étages d'arcades. Le mur de scène, orné d'une centaine de colonnes, abritait au-dessus de la porte centrale une statue monumentale d'Auguste. La célèbre Vénus d'Arles, découverte en 1651, appartenait à ce décor.",
        "sources": [
          "MDAA, dossier Urbanisme et romanisation, fiches Le théâtre antique d'Arles et La Vénus d'Arles",
          "MDAA, dossier Golvin 2011, p. 11"
        ]
      },
      {
        "id": "amphitheatre",
        "title": "L'amphithéâtre",
        "text": "Élevé à la fin du Ier siècle sous les Flaviens, l'amphithéâtre mesure 136 m sur 107 m pour 21 m de haut. Ses deux niveaux de 60 arcades associent les styles dorique et corinthien. Sur le podium, une inscription toujours en place rappelle la générosité de Caius Iunius Priscus, flamine augustal : il offrit le podium et ses portes, une statue de Neptune en argent, quatre statues de bronze, deux jours de spectacles scéniques avec une chasse, et des banquets pour les décurions, les corporations du forum et les sévirs augustaux.",
        "sources": [
          "MDAA, dossier Urbanisme et romanisation, fiche maquette L'amphithéâtre d'Arles",
          "CIL XII 697, texte et traduction d'après https://books.openedition.org/pccj/2336"
        ]
      },
      {
        "id": "port-trinquetaille",
        "title": "Le port et le Rhône",
        "text": "Le fleuve est l'artère de la cité. Chalands à fond plat halés depuis la berge, navires de mer des naviculaires d'Arles, qui formeront cinq corporations, entrepôts et docks de Trinquetaille animent les deux rives. À la fin du IVe siècle, le poète Ausone saluera la « petite Rome gauloise » et son pont de bateaux. Mais où passait le pont vers 160 ? La question reste ouverte : les vestiges connus ne datent que du début du IVe siècle.",
        "sources": [
          "Ausone, Ordo urbium nobilium, 10 (Arelas)",
          "CIL III 14165, 8",
          "MDAA, dossier Golvin 2011, p. 20 à 22 et 40",
          "MDAA, dossier de presse Arles-Rhône 3, 2011"
        ]
      },
      {
        "id": "cirque",
        "title": "Le cirque",
        "text": "Hors les murs, au bord du Rhône, s'étire le cirque, long d'environ 450 m pour 101 m de large. Le sol marécageux a imposé plus de 30 000 pieux de bois. Leurs cernes de croissance montrent que les arbres ont été abattus durant l'hiver de 148 à 149 : le cirque a donc été bâti en 149 et 150. Environ 20 000 spectateurs y suivaient les courses de chars.",
        "sources": [
          "MDAA, dossier Urbanisme et romanisation, fiche maquette Le cirque romain d'Arles"
        ]
      }
    ]
  },
  {
    "id": "pont-du-gard",
    "title": "Le pont du Gard",
    "status": "ready",
    "year": 130,
    "lat": 43.94725,
    "lon": 4.53529,
    "summary": "Vers 130, un soir de juin, en basses eaux. Achevé vers le milieu du Ier siècle, le pont porte l'aqueduc de Nîmes au-dessus du Gardon, à 48,77 m de hauteur, sur trois étages d'arches en grand appareil. L'eau captée près d'Uzès coule dans le canal couvert du sommet jusqu'au castellum de Nîmes.",
    "ambience": [
      {
        "layer": "river",
        "volume": 0.65
      },
      {
        "layer": "summer-evening",
        "volume": 0.6
      },
      {
        "layer": "birds-day",
        "volume": 0.3
      },
      {
        "layer": "wind",
        "volume": 0.4
      },
      {
        "layer": "animals",
        "volume": 0.3,
        "points": [
          "vue-d-ensemble",
          "le-pont"
        ]
      },
      {
        "layer": "animals",
        "volume": 0.5,
        "points": [
          "la-carriere"
        ]
      }
    ],
    "points": [
      {
        "id": "le-pont",
        "title": "Trois ponts superposés",
        "text": "Pour franchir le Gardon, l'architecte superpose trois ponts. Le premier étage, haut de 21,87 m, compte six arches ; la plus grande, au-dessus du lit permanent, s'ouvre sur environ 24,5 m. Le deuxième, haut de 19,50 m, en aligne onze. Le troisième, haut de 7,40 m, porte le canal sur 47 petites arches, dont 35 subsistent. L'ensemble culmine à 48,77 m. Côté amont, les piles se terminent en avant-becs qui fendent les crues soudaines du Gardon. Les blocs de calcaire coquillier, jusqu'à 6 t, sont posés à sec, sans mortier.",
        "sources": [
          "Site du Pont du Gard, mémento : https://pontdugard.fr/sites/default/files/2023-05/lepontdugard.pdf",
          "Site du Pont du Gard, dossier de presse, p. 4 et 14 : https://pontdugard.fr/sites/default/files/2023-02/Dossier%20de%20presse%20Pont%20du%20Gard.pdf",
          "Site du Pont du Gard, The monument : https://pontdugard.fr/en/discover/monument",
          "M. Vacca-Goutoulli 2024, p. 35 (avant-becs) : https://doi.org/10.46298/asrm.13671"
        ]
      },
      {
        "id": "la-grande-arche",
        "title": "Les traces du chantier",
        "text": "Les pierres qui dépassent des piles ne sont pas un décor : elles portaient sans doute les planchers des échafaudages et des engins de levage, et furent probablement gardées pour les réparations. Les cintres de bois reposaient sur des voussoirs en saillie. Levés à la louve, les voussoirs portent des repères gravés qui fixaient leur ordre de pose. En septembre 2002, une crue exceptionnelle a mis à nu le rocher en amont et en aval du pont : J.-C. Bessac y a reconnu des traces taillées du chantier romain, dont celles d'engins de levage.",
        "sources": [
          "J.-L. Paillet, Gallia 62, 2005, p. 49 à 68 : https://www.persee.fr/doc/galia_0016-4119_2005_num_62_1_3220",
          "J.-C. Bessac, « Nouvelles traces du chantier romain du Pont du Gard », RAN 36, 2003, p. 177 à 198 : https://www.persee.fr/doc/ran_0557-7705_2003_num_36_1_1120"
        ]
      },
      {
        "id": "le-canal",
        "title": "Le canal sous ses dalles",
        "text": "Au sommet court le canal, large d'environ 1,20 m, fermé par des dalles de 3,61 m de long et 0,34 m d'épaisseur. Ses parois sont enduites de mortier de tuileau et badigeonnées de rouge. Peu après la première mise en eau, l'eau montant plus haut que prévu, on a rehaussé le cuvelage de 0,60 m en glissant une assise de pierre sous les dalles. La pente reste infime, de l'ordre de 7 cm par kilomètre dans les bois voisins de Remoulins. Captée à la source d'Eure, près d'Uzès, l'eau finit sa course au castellum de Nîmes.",
        "sources": [
          "J.-L. Fiches et J.-L. Paillet, CRAI 133-2, 1989, p. 408 à 426 : https://www.persee.fr/doc/crai_0065-0536_1989_num_133_2_14741",
          "J.-L. Paillet, Gallia 62, 2005, p. 49 à 68 : https://www.persee.fr/doc/galia_0016-4119_2005_num_62_1_3220",
          "Site du Pont du Gard, dossier de presse, p. 4 : https://pontdugard.fr/sites/default/files/2023-02/Dossier%20de%20presse%20Pont%20du%20Gard.pdf"
        ]
      },
      {
        "id": "la-carriere",
        "title": "La carrière de l'Estel",
        "text": "À 500 ou 600 m en aval, sur la rive gauche, la carrière de l'Estel a fourni l'essentiel des blocs du pont. Les carriers isolaient chaque bloc par des tranchées étroites, creusées à l'escoude, puis le détachaient avec des coins de fer. Une digue faite de leurs déchets protégeait le chantier des crues, et ils logeaient dans de petites maisons alignées près de la carrière. Selon la dernière étude, les blocs gagnaient le pont par voie de terre. Vers 130, les limons du Gardon recouvrent la carrière abandonnée, où une vingtaine de tombes à incinération ont été installées peu avant.",
        "sources": [
          "M. Vacca-Goutoulli, Archéologies. Sociétés, réseaux, matériaux 2, 2024, p. 9, 20, 21, 29 et 31 : https://doi.org/10.46298/asrm.13671",
          "J.-C. Bessac et M. Vacca-Goutoulli, Gallia 59, 2002, p. 11 à 28 : https://www.persee.fr/doc/galia_0016-4119_2002_num_59_1_3093",
          "Site du Pont du Gard, dossier de presse, p. 6"
        ]
      }
    ]
  },
]
