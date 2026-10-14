import type { Era } from './schema.ts'

export const eras: Era[] = [
  {
    id: 'royaute',
    name: 'Royauté',
    start: -752,
    end: -508,
    summary:
      "Selon la tradition, Rome est gouvernée par sept rois, de sa fondation en 753 à l'expulsion de Tarquin le Superbe en 509 av. J.-C. Les premiers règnes relèvent de la légende, mais l'archéologie montre qu'aux VIIe et VIe siècles av. J.-C. les villages du Palatin et des collines voisines deviennent une véritable cité, ouverte aux influences étrusques et grecques.",
    boundsNote:
      "753 av. J.-C. est la date calculée au Ier siècle av. J.-C. par Varron, parmi d'autres proposées dans l'Antiquité, alors que le site est habité bien plus tôt. 509 av. J.-C. est la date traditionnelle de la chute de la monarchie : Polybe place les premiers consuls un ou deux ans plus tard, et le passage à la République fut sans doute progressif.",
  },
  {
    id: 'republique',
    name: 'République',
    start: -508,
    end: -26,
    summary:
      "De 509 à 27 av. J.-C., Rome est dirigée par des magistrats élus pour un an, au premier rang desquels deux consuls, sous l'autorité du Sénat et avec le vote des assemblées du peuple. La cité conquiert l'Italie puis le pourtour de la Méditerranée, mais au Ier siècle av. J.-C. les rivalités entre chefs militaires provoquent des guerres civiles qui aboutissent au pouvoir d'un seul homme.",
    boundsNote:
      "Le début reprend la date traditionnelle de l'expulsion des rois (509 av. J.-C.). La fin est fixée en janvier 27 av. J.-C., quand Octavien reçoit le nom d'Auguste ; d'autres historiens retiennent Actium (31 av. J.-C.) ou la mort de César, car le passage au principat fut progressif.",
  },
  {
    id: 'haut-empire',
    name: 'Haut-Empire',
    start: -26,
    end: 235,
    summary:
      "Du principat d'Auguste à la mort de Sévère Alexandre, le pouvoir impérial s'installe et l'Empire atteint sa plus grande extension sous Trajan. Malgré des guerres civiles de succession (en 68 et 69 apr. J.-C., puis en 193), la paix romaine favorise l'essor des villes, la diffusion de la citoyenneté et l'intégration des provinces.",
    boundsNote:
      "Les bornes sont conventionnelles : 27 av. J.-C. retient le jour où Octavien reçoit le nom d'Auguste, alors que le régime se met en place de 31 à 23 av. J.-C., et 235 l'assassinat de Sévère Alexandre, dernier des Sévères. Certains manuels arrêtent le Haut-Empire en 192, à la mort de Commode.",
  },
  {
    id: 'crise-du-iiie-siecle',
    name: 'Crise du IIIe siècle',
    start: 235,
    end: 284,
    summary:
      "De 235 à 284, l'Empire affronte à la fois la Perse sassanide, les peuples germaniques et des guerres civiles incessantes : plus d'une vingtaine d'empereurs se succèdent, souvent proclamés par leurs troupes. L'Empire des Gaules fait sécession de 260 à 274, et Palmyre rompt avec Rome de 270 à 273, avant qu'Aurélien ne rétablisse l'unité.",
    boundsNote:
      "Les deux dates sont des repères commodes : 235, assassinat de Sévère Alexandre, et 284, avènement de Dioclétien. Les historiens discutent aujourd'hui la notion même de « crise », car les difficultés ont beaucoup varié selon les régions et les décennies.",
  },
  {
    id: 'bas-empire',
    name: 'Bas-Empire',
    start: 284,
    end: 476,
    summary:
      "Dioclétien puis Constantin réorganisent l'État, l'armée et la fiscalité, et Constantinople devient une seconde capitale. Persécuté jusqu'en 311, le christianisme devient sous Constantin la religion soutenue par l'empereur, puis sous Théodose la seule foi autorisée en principe. Après 395, deux cours gouvernent l'Empire, et l'Occident se fragmente en royaumes barbares.",
    boundsNote:
      "Bornes conventionnelles : 284 marque la fin de la crise avec un règne enfin durable ; 476, déposition du dernier empereur résidant en Italie, n'a été érigée en tournant qu'après coup. « Bas-Empire » est une étiquette française : on parle aujourd'hui volontiers d'Antiquité tardive.",
  },
  {
    id: 'empire-romain-d-orient',
    name: "Empire romain d'Orient",
    start: 476,
    end: 1453,
    summary:
      "L'Empire se poursuit autour de Constantinople pendant près de mille ans. Ses habitants se disent Romains (Rhômaioi) et appellent leur État l'empire des Romains : le mot « byzantin » est une étiquette apparue chez des érudits du XVIe siècle et généralisée au XIXe.",
    boundsNote:
      "Le début de l'« Empire byzantin » est une convention discutée : 330 (fondation de Constantinople), 395, 476 ou 610 (avènement d'Héraclius). Le site retient 476, fin de l'Empire d'Occident. La fin, le 29 mai 1453, vaut pour la capitale : la Morée tient jusqu'en 1460 et Trébizonde jusqu'en 1461.",
  },
]
