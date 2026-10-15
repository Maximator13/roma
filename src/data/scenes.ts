import type { Scene } from './schema.ts'

export const scenes: Scene[] = [
  { id: 'cannes', title: 'Bataille de Cannes', status: 'planned' },
  { id: 'pantheon', title: "Panthéon d'Hadrien", status: 'planned' },
  {
    "id": "nimes",
    "title": "Nîmes romaine (Nemausus)",
    "status": "planned",
    "year": 130,
    "lat": 43.8382,
    "lon": 4.3561,
    "summary": "Vers 130, sous Hadrien, un soir de juin. Ancien chef-lieu des Volques Arécomiques devenu colonie, Nemausus s'étend des collines calcaires jusqu'à la plaine, dans une enceinte d'environ 6 km offerte par Auguste. On y trouve le forum et sa Maison Carrée, l'amphithéâtre achevé vers l'an 100, le sanctuaire de la source et l'eau de l'aqueduc venue d'Uzès.",
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
  { id: 'arles', title: 'Arles romaine (Arelate)', status: 'planned' },
  { id: 'pont-du-gard', title: 'Le pont du Gard', status: 'planned' },
]
