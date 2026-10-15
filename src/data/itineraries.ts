import type { Itinerary } from './schema.ts'

export const itineraries: Itinerary[] = [
  {
    "id": "itineraire-d-hannibal",
    "title": "Itinéraire d'Hannibal, de Carthagène à Cannes",
    "summary": "Parti de Carthagène au printemps 218 av. J.-C., Hannibal franchit l'Èbre, les Pyrénées, le Rhône et les Alpes en cinq mois avant de déboucher dans la plaine du Pô. Il écrase ensuite les armées romaines à la Trébie, au lac Trasimène puis à Cannes, le 2 août 216 av. J.-C.",
    "from": -217,
    "to": -215,
    "waypoints": [
      {
        "lon": -0.988,
        "lat": 37.6028,
        "label": "Départ de Carthagène",
        "year": -217,
        "month": 5,
        "certainty": "attested",
        "note": "Hannibal quitte ses quartiers d'hiver au début du printemps 218 av. J.-C. avec environ 90 000 fantassins et 12 000 cavaliers (Polybe III, 34, 6 et 35, 1 ; Tite-Live XXI, 21 à 23), mois approximatif."
      },
      {
        "lon": 0.52,
        "lat": 40.81,
        "label": "Passage de l'Èbre",
        "year": -217,
        "month": 6,
        "certainty": "traditional",
        "note": "Traversée de l'Èbre (Polybe III, 35, 2), en trois colonnes selon Tite-Live (XXI, 23, 1), en un point du cours inférieur que les sources ne précisent pas."
      },
      {
        "lon": 2.8619,
        "lat": 42.4636,
        "label": "Franchissement des Pyrénées",
        "year": -217,
        "month": 8,
        "certainty": "traditional",
        "note": "Passage par l'est de la chaîne vers Iliberris (Elne) et Ruscino (Tite-Live XXI, 23 et 24), placé par la tradition au col du Perthus ou au col de Panissars voisin."
      },
      {
        "lon": 3.22,
        "lat": 43.35,
        "label": "Traversée du Languedoc",
        "year": -217,
        "month": 8,
        "certainty": "traditional",
        "note": "Marche le long de la côte, la mer à main droite (Polybe III, 41, 7), à travers le pays des Volques (Tite-Live XXI, 26, 6) ; tracé exact inconnu."
      },
      {
        "lon": 4.78,
        "lat": 44.05,
        "label": "Passage du Rhône",
        "year": -217,
        "month": 9,
        "certainty": "debated",
        "note": "Franchissement à quatre jours de marche de la mer (Polybe III, 42, 1 ; Tite-Live XXI, 26 à 28) ; le lieu est discuté de Fourques à Roquemaure, cette dernière hypothèse est retenue ici."
      },
      {
        "lon": 4.86,
        "lat": 44.98,
        "label": "L'Île, au confluent de l'Isère",
        "year": -217,
        "month": 10,
        "certainty": "debated",
        "note": "Région nommée l'Île, atteinte en quatre jours depuis le passage du fleuve, au confluent du Rhône et d'une rivière généralement identifiée à l'Isère (Polybe III, 49, 5 à 13 ; Tite-Live XXI, 31), certains proposant l'Aygues."
      },
      {
        "lon": 6.9228,
        "lat": 45.1675,
        "label": "Col des Alpes (col du Clapier)",
        "year": -217,
        "month": 10,
        "certainty": "debated",
        "note": "Col débattu dès l'Antiquité (Tite-Live XXI, 38) : le col du Clapier, défendu par Lavis-Trafford, Lazenby et Hunt, est retenu, mais le col de la Traversette (de Beer, Mahaney 2017, Berti et Vollrath 2026), le Montgenèvre, le Mont-Cenis et le Petit-Saint-Bernard ont leurs partisans ; sommet atteint peu avant le coucher des Pléiades (Polybe III, 54, 1)."
      },
      {
        "lon": 7.686,
        "lat": 45.0718,
        "label": "Prise de la ville des Taurins",
        "year": -217,
        "month": 11,
        "certainty": "traditional",
        "note": "Après quinze jours dans les Alpes et cinq mois depuis Carthagène (Polybe III, 56, 3 ; Tite-Live XXI, 38, 1), Hannibal prend en trois jours la principale ville des Taurins (Polybe III, 60, 8 à 10 ; Tite-Live XXI, 39), identifiée à Turin."
      },
      {
        "lon": 8.9,
        "lat": 45.25,
        "label": "Bataille du Tessin",
        "year": -217,
        "month": 11,
        "certainty": "debated",
        "note": "Combat de cavalerie où le consul Scipion est blessé, près du Tessin (Polybe III, 64 à 66 ; Tite-Live XXI, 45 à 47), en un lieu discuté de la rive droite."
      },
      {
        "lon": 9.57,
        "lat": 45,
        "label": "Bataille de la Trébie",
        "year": -217,
        "month": 12,
        "certainty": "attested",
        "note": "Victoire d'Hannibal vers le solstice d'hiver (Polybe III, 72, 3 et 73 à 74 ; Tite-Live XXI, 52 à 56), près de Plaisance, sur la rive gauche (ouest) de la Trébie selon la reconstruction la plus suivie, la rive exacte restant discutée."
      },
      {
        "lon": 10.95,
        "lat": 43.8,
        "label": "Marais de l'Arno",
        "year": -216,
        "month": 5,
        "certainty": "debated",
        "note": "Après la traversée de l'Apennin au printemps 217 av. J.-C., marche dans les marais inondés où Hannibal perd un œil : trois jours et trois nuits selon Polybe (III, 78 et 79), quatre jours et trois nuits selon Tite-Live (XXII, 2) ; col et emplacement discutés, mois approximatif."
      },
      {
        "lon": 12.07,
        "lat": 43.205,
        "label": "Bataille du lac Trasimène",
        "year": -216,
        "month": 6,
        "certainty": "attested",
        "note": "Embuscade sur la rive nord du lac où périt le consul Flaminius (Polybe III, 83 et 84 ; Tite-Live XXII, 4 à 7), le dixième jour avant les calendes de juillet selon Ovide (Fastes VI, 767 et 768), soit le 21 juin 217 av. J.-C. du calendrier républicain (le 22 juin dans le calendrier julien d'Ovide)."
      },
      {
        "lon": 13.98,
        "lat": 42.58,
        "label": "Côte adriatique (Hadria)",
        "year": -216,
        "month": 7,
        "certainty": "traditional",
        "note": "Marche par l'Ombrie et le Picenum jusqu'à l'Adriatique, atteinte le dixième jour ; l'armée se refait près de la côte, dans le Picenum selon Tite-Live, puis traverse le territoire d'Hadria (Polybe III, 86, 8 à 88, 3 ; Tite-Live XXII, 9)."
      },
      {
        "lon": 16.1518,
        "lat": 41.2967,
        "label": "Bataille de Cannes",
        "year": -215,
        "month": 8,
        "certainty": "attested",
        "note": "Après la prise de la citadelle de Cannes (Polybe III, 107, 2 et 3), écrasement de l'armée de Paul Émile et Varron sur l'Aufide (Polybe III, 110 à 117 ; Tite-Live XXII, 43 à 50), le 2 août 216 av. J.-C. du calendrier romain (Aulu-Gelle V, 17, 5)."
      }
    ],
    "sources": [
      "Polybe, Histoires III, 33 à 118 (trad. W. R. Paton, LacusCurtius) : https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Polybius/3*.html",
      "Tite-Live, Histoire romaine XXI, 21 à 56 (texte latin) : https://www.thelatinlibrary.com/livy/liv.21.shtml",
      "Tite-Live, Histoire romaine XXII, 2 à 9 et 43 à 50 (texte latin) : https://www.thelatinlibrary.com/livy/liv.22.shtml",
      "Aulu-Gelle, Nuits attiques V, 17, 5 (date de Cannes) : https://www.thelatinlibrary.com/gellius/gellius5.shtml",
      "Ovide, Fastes VI, 765 à 768 (date de Trasimène) : https://www.thelatinlibrary.com/ovid/ovid.fasti6.shtml",
      "J. F. Lazenby, Hannibal's War. A Military History of the Second Punic War, Warminster, Aris and Phillips, 1978",
      "Serge Lancel, Hannibal, Paris, Fayard, 1995",
      "W. C. Mahaney et al., Biostratigraphic evidence relating to the age-old question of Hannibal's invasion of Italy, I: history and geological reconstruction, Archaeometry 59 (1), 2017, p. 164 à 178, doi:10.1111/arcm.12231",
      "E. Berti et F. Vollrath, Energy costs of Hannibal's alpine crossing, PNAS 123 (28), 2026, e2612764123, doi:10.1073/pnas.2612764123 (présentation : https://www.archaeology.wiki/blog/2026/07/22/energy-costs-of-hannibals-alpine-crossing/)",
      "Col du Clapier, coordonnées : https://en.wikipedia.org/wiki/Col_de_Clapier"
    ]
  }
]
