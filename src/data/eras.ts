import type { Era } from './schema.ts'

export const eras: Era[] = [
  {
    id: 'royaute',
    name: 'Royauté',
    start: -752,
    end: -508,
    summary:
      "Selon la tradition, Rome est gouvernée par sept rois, de Romulus à Tarquin le Superbe. Les récits de cette période, écrits des siècles plus tard, mêlent légende et souvenirs réels ; l'archéologie confirme l'essor d'une cité latine sous influence étrusque au VIe siècle av. J.-C.",
    boundsNote:
      "Les bornes de 753 et 509 av. J.-C. sont des dates traditionnelles, calculées par les érudits romains (comput de Varron) ; aucune source contemporaine ne les atteste.",
  },
  {
    id: 'republique',
    name: 'République',
    start: -508,
    end: -26,
    summary:
      "Rome est dirigée par des magistrats élus pour un an, d'abord les deux consuls, et par le Sénat. La cité soumet l'Italie puis le bassin méditerranéen, avant que les guerres civiles du Ier siècle av. J.-C. ne ruinent le régime.",
    boundsNote:
      "509 av. J.-C. est la date traditionnelle de l'expulsion du dernier roi. 27 av. J.-C., année où Octavien reçoit le nom d'Auguste, sert de borne conventionnelle au passage à l'Empire.",
  },
  {
    id: 'haut-empire',
    name: 'Haut-Empire',
    start: -26,
    end: 235,
    summary:
      "Auguste fonde le principat, un pouvoir monarchique qui garde les formes de la République. L'Empire atteint sa plus grande extension sous Trajan et connaît deux siècles de paix intérieure relative, la pax Romana.",
    boundsNote:
      "Par convention, le Haut-Empire va de 27 av. J.-C. à la mort de Sévère Alexandre en 235, qui ouvre la crise du IIIe siècle.",
  },
  {
    id: 'crise-du-iiie-siecle',
    name: 'Crise du IIIe siècle',
    start: 235,
    end: 284,
    summary:
      "En un demi-siècle, plus de vingt empereurs se succèdent, souvent proclamés par l'armée. Invasions, défaites face aux Perses, sécessions de l'Empire des Gaules et de Palmyre, épidémies et inflation menacent l'unité de l'Empire.",
    boundsNote:
      "Les bornes de 235 (mort de Sévère Alexandre) et de 284 (avènement de Dioclétien) sont des conventions d'historiens modernes ; l'ampleur même de la « crise » est discutée.",
  },
  {
    id: 'bas-empire',
    name: 'Bas-Empire',
    start: 284,
    end: 476,
    summary:
      "Dioclétien puis Constantin réorganisent l'État, l'armée et la fiscalité ; le christianisme devient religion officielle à la fin du IVe siècle. Après 395, deux cours impériales gouvernent l'Occident et l'Orient, et l'Empire d'Occident disparaît en 476.",
    boundsNote:
      "« Bas-Empire » est une étiquette moderne : beaucoup d'historiens parlent aujourd'hui d'Antiquité tardive. 476, année de la déposition de Romulus Augustule, est une borne conventionnelle.",
  },
  {
    id: 'empire-romain-d-orient',
    name: "Empire romain d'Orient",
    start: 476,
    end: 1453,
    summary:
      "L'Empire se poursuit autour de Constantinople pendant près de mille ans. Ses habitants se disent Romains (Rhômaioi) ; le nom d'« Empire byzantin » a été forgé par des historiens de l'époque moderne.",
    boundsNote:
      "Le début de l'« Empire byzantin » est une convention discutée : 330 (fondation de Constantinople), 395, 476 ou 610 (avènement d'Héraclius). Le site retient 476, fin de l'Empire d'Occident.",
  },
]
