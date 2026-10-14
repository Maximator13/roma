import type { Track } from './schema.ts'

export const tracks: Track[] = [
  {
    id: 'rome',
    name: 'Rome',
    lane: 0,
    spans: [{ start: -752, end: 395 }],
    note: "Piste de l'État romain unique, de la fondation traditionnelle de la ville à la mort de Théodose Ier, le 17 janvier 395. Les gouvernements collégiaux antérieurs (tétrarchie, fils de Constantin, Valentinien et Valens) n'ont pas créé d'États distincts ; la coupure de 395 est une convention, car l'Empire reste juridiquement un.",
  },
  {
    id: 'orient',
    name: "Empire romain d'Orient",
    lane: 0,
    spans: [
      { start: 395, end: 1204 },
      { start: 1261, end: 1453 },
    ],
    note: "Partie orientale de l'Empire à partir de 395, avec Constantinople pour capitale ; ses habitants se disent Romains. La piste est interrompue de la prise de Constantinople par les croisés (12 avril 1204) à sa reprise par Nicée (25 juillet 1261), puis s'achève le 29 mai 1453.",
  },
  {
    id: 'occident',
    name: "Empire romain d'Occident",
    lane: 1,
    spans: [{ start: 395, end: 476 }],
    note: "Partie occidentale de l'Empire, gouvernée par une cour distincte (Milan, puis Ravenne à partir de 402) de 395 à la déposition de Romulus Augustule en 476. La fin en 476 est une convention : Julius Nepos reste reconnu par Constantinople jusqu'à sa mort en 480.",
  },
  {
    id: 'empire-des-gaules',
    name: 'Empire des Gaules',
    lane: 1,
    spans: [{ start: 260, end: 274 }],
    note: "De la proclamation de Postume (260) à la reddition de Tétricus devant Aurélien près de Châlons (début 274). Le nom est moderne : ces empereurs se disaient romains et ne revendiquaient pas l'indépendance de la Gaule.",
  },
  {
    id: 'palmyre',
    name: 'Royaume de Palmyre',
    lane: 2,
    spans: [{ start: 270, end: 273 }],
    note: "De la conquête de l'Égypte par les troupes de Zénobie (270) au sac de Palmyre (273). Avant 270, Odénath puis Zénobie agissent en principe au service de Rome : leur rôle figure sur la piste de Rome.",
  },
  {
    id: 'nicee',
    name: 'Empire de Nicée',
    lane: 0,
    spans: [{ start: 1204, end: 1261 }],
    note: "Théodore Laskaris rassemble les forces romaines d'Asie Mineure dès 1204, prend le titre impérial en 1205 et est couronné en 1208. L'État de Nicée prend fin en 1261, quand Michel VIII s'installe à Constantinople : la piste rejoint alors celle de l'Orient.",
  },
  {
    id: 'empire-latin',
    name: 'Empire latin de Constantinople',
    lane: 1,
    spans: [{ start: 1204, end: 1261 }],
    note: 'Fondé après le sac d\'avril 1204 : Baudouin de Flandre est couronné à Sainte-Sophie le 16 mai 1204. Disparaît avec la reprise de Constantinople par Nicée le 25 juillet 1261.',
  },
  {
    id: 'epire',
    name: "Despotat d'Épire",
    lane: 2,
    spans: [{ start: 1205, end: 1337 }],
    note: "Fondé vers 1205 par Michel Comnène Doukas, avec Arta pour centre. La fin retenue ici est l'annexion par Andronic III en 1337 ; des restes, sous des souverains serbes puis italiens, subsistent jusqu'en 1479.",
  },
  {
    id: 'trebizonde',
    name: 'Empire de Trébizonde',
    lane: 3,
    spans: [{ start: 1204, end: 1453 }],
    note: "Fondé en avril 1204 par Alexis et David Comnène ; pris par Mehmed II le 15 août 1461, après la fin de la période couverte par la frise, qui s'arrête en 1453.",
  },
]
