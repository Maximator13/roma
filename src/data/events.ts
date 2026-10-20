import type { HistoricalEvent } from './schema.ts'

export const events: HistoricalEvent[] = [
  {
    "id": "enlevement-des-sabines",
    "title": "Enlèvement des Sabines",
    "start": -752,
    "precision": "year",
    "certainty": "legendary",
    "certaintyNote": "Récit légendaire ; Plutarque le place quatre mois après la fondation, d'après Fabius Pictor, et le rattache à la fête des Consualia.",
    "era": "royaute",
    "track": "rome",
    "category": "society",
    "importance": 3,
    "placeId": "rome",
    "people": [
      "romulus",
      "titus-tatius"
    ],
    "summary": "Pour peupler sa ville, Romulus invite les Sabins voisins à des jeux et fait enlever leurs filles. La guerre qui suit s'achève par la réconciliation des deux peuples, que Romulus et le roi sabin Titus Tatius gouvernent ensemble. Cette légende explique après coup la fusion de populations diverses à Rome.",
    "body": "**Le récit.** Selon Tite-Live et Plutarque, la jeune Rome manque de femmes et ses voisins refusent de lui accorder des épouses. Romulus organise une fête en l'honneur du dieu Consus et y convie les peuples des environs ; à un signal, les jeunes Romains enlèvent les jeunes filles sabines. Plutarque place l'épisode quatre mois après la fondation, le jour des Consualia (18 août).\n\n**La réconciliation.** Les Sabins, menés par leur roi Titus Tatius, attaquent Rome et s'emparent de la citadelle grâce à la trahison de Tarpéia. Au cœur de la bataille, les Sabines s'interposent entre leurs pères et leurs maris. Les deux peuples s'unissent et Titus Tatius partage la royauté avec Romulus.\n\n**Comment le lire.** Ce récit relève de la légende. Les historiens y voient une explication, construite bien plus tard, de la présence d'éléments sabins dans la population et la religion romaines, ainsi que de certains rites du mariage romain.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Tite-Live",
        "work": "Histoire romaine",
        "locus": "I, 9 à 13",
        "url": "https://bcs.fltr.ucl.ac.be/LIV/I.html"
      },
      {
        "kind": "ancient",
        "author": "Plutarque",
        "work": "Vie de Romulus",
        "locus": "14 à 19",
        "url": "https://remacle.org/bloodwolf/historiens/Plutarque/romuluspierron.htm"
      },
      {
        "kind": "modern",
        "author": "Alexandre Grandazzi",
        "work": "La Fondation de Rome. Réflexion sur l'histoire, Paris, Les Belles Lettres, 1991"
      },
      {
        "kind": "modern",
        "author": "A. Momigliano",
        "work": "The origins of Rome, dans The Cambridge Ancient History, 2e éd., vol. VII, 2, 1989",
        "locus": "chap. 3"
      }
    ]
  },
  {
    "id": "fondation-de-rome",
    "title": "Fondation de Rome",
    "start": -752,
    "month": 4,
    "day": 21,
    "precision": "day",
    "certainty": "legendary",
    "certaintyNote": "Date calculée au Ier siècle av. J.-C. par Varron ; les auteurs antiques cités par Denys d'Halicarnasse plaçaient la fondation entre 814 et 728 av. J.-C.",
    "era": "royaute",
    "track": "rome",
    "category": "politics",
    "importance": 1,
    "placeId": "rome",
    "people": [
      "romulus",
      "remus"
    ],
    "summary": "Selon la légende, Romulus fonde Rome sur le Palatin le 21 avril 753 av. J.-C., après avoir tué son jumeau Rémus. Cette date, fixée tardivement par Varron, est une construction savante : le site était habité bien avant, et la ville est née peu à peu du regroupement de villages.",
    "body": "**La légende.** Tite-Live et Plutarque racontent l'histoire des jumeaux Romulus et Rémus, fils du dieu Mars et de Rhéa Silvia, abandonnés sur le Tibre puis nourris par une louve. Devenus adultes, ils décident de fonder une ville. Une querelle sur le présage des oiseaux tourne au drame : Romulus tue son frère et trace seul l'enceinte sacrée du Palatin.\n\n**La date.** Le 21 avril est le jour de la fête des Parilia, que les Romains célébraient comme l'anniversaire de leur ville. L'année 753 av. J.-C. est celle que retient Varron au Ier siècle av. J.-C. ; d'autres auteurs antiques, cités par Denys d'Halicarnasse, proposaient des années comprises entre 814 et 728 av. J.-C. C'est une convention, non un fait attesté.\n\n**Ce que dit l'archéologie.** Des cabanes de l'âge du fer sont attestées sur le Palatin et les collines voisines bien avant le milieu du VIIIe siècle av. J.-C. Des fouilles menées dans les années 1980 au pied du Palatin ont mis au jour un mur du VIIIe siècle av. J.-C., dont la datation et le lien avec la légende restent discutés. Rome n'a pas été fondée en un jour : elle est le fruit d'un lent regroupement de villages.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Tite-Live",
        "work": "Histoire romaine",
        "locus": "I, 4 à 7",
        "url": "https://bcs.fltr.ucl.ac.be/LIV/I.html"
      },
      {
        "kind": "ancient",
        "author": "Plutarque",
        "work": "Vie de Romulus",
        "locus": "3 à 12",
        "url": "https://remacle.org/bloodwolf/historiens/Plutarque/romuluspierron.htm"
      },
      {
        "kind": "ancient",
        "author": "Denys d'Halicarnasse",
        "work": "Antiquités romaines",
        "locus": "I, 74",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Dionysius_of_Halicarnassus/1D*.html"
      },
      {
        "kind": "modern",
        "author": "Alexandre Grandazzi",
        "work": "La Fondation de Rome. Réflexion sur l'histoire, Paris, Les Belles Lettres, 1991"
      },
      {
        "kind": "modern",
        "author": "T. J. Cornell",
        "work": "The Beginnings of Rome, Londres, Routledge, 1995",
        "locus": "chap. 3, The Origins of Rome"
      }
    ]
  },
  {
    "id": "regne-de-servius-tullius",
    "title": "Règne de Servius Tullius",
    "start": -577,
    "end": -534,
    "precision": "year",
    "certainty": "traditional",
    "certaintyNote": "Dates de la tradition annalistique ; le rempart dit servien date pour l'essentiel du IVe siècle av. J.-C.",
    "era": "royaute",
    "track": "rome",
    "category": "politics",
    "importance": 2,
    "placeId": "rome",
    "people": [
      "servius-tullius"
    ],
    "summary": "Sixième roi selon la tradition, Servius Tullius aurait créé le recensement des citoyens et réparti ceux-ci en classes selon leur fortune, base de l'organisation militaire et politique. Ses dates sont traditionnelles, et le rempart qui porte son nom date en réalité du IVe siècle av. J.-C.",
    "body": "**Un roi de tradition.** Tite-Live fait de Servius Tullius le successeur de Tarquin l'Ancien et lui attribue un règne de 44 ans, de 578 à 535 av. J.-C. selon la chronologie traditionnelle. Ses origines sont entourées de récits merveilleux, et une tradition étrusque, rapportée par l'empereur Claude, l'identifiait à un chef de guerre nommé Mastarna.\n\n**Le cens et les classes.** On lui attribue le premier recensement : chaque citoyen déclare ses biens et se voit classé selon sa fortune, ce qui fixe son équipement militaire et le poids de son vote. Tite-Live rapporte, d'après Fabius Pictor, 80 000 citoyens en âge de porter les armes, chiffre que les historiens jugent très exagéré. Le système des 193 centuries décrit par les auteurs anciens reflète sans doute un état plus tardif, mais beaucoup d'historiens admettent une réforme militaire au VIe siècle av. J.-C. et la création de tribus territoriales.\n\n**Le « mur servien ».** Tite-Live écrit que Servius entoura la ville d'un rempart. Les vestiges conservés sous ce nom, en blocs de tuf extraits près de Véies, datent pour l'essentiel du IVe siècle av. J.-C., après le sac gaulois ; Tite-Live mentionne d'ailleurs un marché public pour un mur de pierre en 378 av. J.-C.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Tite-Live",
        "work": "Histoire romaine",
        "locus": "I, 39 à 48",
        "url": "https://bcs.fltr.ucl.ac.be/LIV/I.html"
      },
      {
        "kind": "ancient",
        "author": "Tite-Live",
        "work": "Histoire romaine",
        "locus": "VI, 32, 1",
        "url": "https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.02.0026:book=6:chapter=32"
      },
      {
        "kind": "modern",
        "author": "T. J. Cornell",
        "work": "The Beginnings of Rome, Londres, Routledge, 1995",
        "locus": "chap. 7, The Reforms of Servius Tullius"
      }
    ]
  },
  {
    "id": "expulsion-de-tarquin-le-superbe",
    "title": "Expulsion de Tarquin le Superbe",
    "start": -508,
    "precision": "year",
    "certainty": "traditional",
    "certaintyNote": "Date traditionnelle ; Polybe place les premiers consuls 28 ans avant le passage de Xerxès en Grèce, soit en 508 ou 507 av. J.-C.",
    "era": "royaute",
    "track": "rome",
    "category": "politics",
    "importance": 2,
    "placeId": "rome",
    "people": [
      "tarquin-le-superbe",
      "lucrece",
      "lucius-junius-brutus"
    ],
    "summary": "Selon la tradition, le viol de Lucrèce par le fils du roi provoque une révolte menée par Lucius Junius Brutus, qui chasse Tarquin le Superbe, septième et dernier roi de Rome. Ce récit très dramatisé cache une transition sans doute plus lente, à une époque où l'influence étrusque recule dans le Latium.",
    "body": "**Le récit traditionnel.** Tite-Live raconte que Sextus Tarquin, fils du roi, viole Lucrèce, épouse de Collatin. Elle révèle le crime à son père et à son mari, puis se donne la mort. Lucius Junius Brutus brandit le poignard et fait jurer aux Romains de chasser les rois ; Tarquin, alors en campagne, trouve les portes de Rome fermées et s'exile à Caeré, en Étrurie.\n\n**Après l'exil.** Le roi déchu tente de reprendre le pouvoir avec l'appui de cités étrusques puis latines, sans succès. Selon Tite-Live, il meurt à Cumes en 495 av. J.-C., réfugié auprès du tyran Aristodème.\n\n**Ce qu'en pensent les historiens.** L'existence des derniers rois d'origine étrusque est plausible, mais les détails du récit sont légendaires et s'inspirent en partie de modèles grecs de chute des tyrans. La date de 509 av. J.-C. vient de la tradition romaine ; Polybe, qui cite le premier traité entre Rome et Carthage, la place un ou deux ans plus tard.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Tite-Live",
        "work": "Histoire romaine",
        "locus": "I, 57 à 60",
        "url": "https://bcs.fltr.ucl.ac.be/LIV/I.html"
      },
      {
        "kind": "ancient",
        "author": "Tite-Live",
        "work": "Histoire romaine",
        "locus": "II, 21, 5",
        "url": "https://bcs.fltr.ucl.ac.be/LIV/II.html"
      },
      {
        "kind": "ancient",
        "author": "Polybe",
        "work": "Histoires",
        "locus": "III, 22",
        "url": "https://remacle.org/bloodwolf/historiens/polybe/livre3.htm"
      },
      {
        "kind": "modern",
        "author": "T. J. Cornell",
        "work": "The Beginnings of Rome, Londres, Routledge, 1995",
        "locus": "chap. 9, The Beginnings of the Roman Republic"
      }
    ]
  },
  {
    "id": "instauration-de-la-republique",
    "title": "Instauration de la République",
    "start": -508,
    "precision": "year",
    "certainty": "traditional",
    "certaintyNote": "Date traditionnelle ; Polybe place les premiers consuls en 508 ou 507 av. J.-C., et les listes de magistrats des premières années sont incertaines.",
    "era": "republique",
    "track": "rome",
    "category": "politics",
    "importance": 1,
    "placeId": "rome",
    "people": [
      "lucius-junius-brutus",
      "collatin"
    ],
    "summary": "Après la chute de la monarchie, le pouvoir passe selon la tradition à deux magistrats élus pour un an, les consuls. Le Sénat conseille, le peuple vote dans ses assemblées : c'est la res publica, la « chose publique ». Les historiens pensent que ces institutions se sont mises en place par étapes.",
    "body": "**Un pouvoir partagé et limité.** Pour empêcher le retour d'un roi, les Romains confient l'autorité suprême, l'imperium, à deux magistrats élus chaque année, qui peuvent s'opposer l'un à l'autre. Tite-Live ouvre son livre II sur cette liberté nouvelle, fondée sur des magistrats annuels et sur l'autorité des lois plutôt que sur celle des hommes.\n\n**Les premiers consuls.** Selon Tite-Live, les comices centuriates élisent Lucius Junius Brutus et Lucius Tarquin Collatin, le mari de Lucrèce. Polybe, lui, nomme Brutus et Marcus Horatius comme premiers consuls : les listes des premières années sont incertaines.\n\n**Une naissance progressive.** Les historiens modernes pensent que les institutions républicaines se sont construites au cours du Ve siècle av. J.-C. Le titre de consul n'est peut-être pas le plus ancien (les premiers magistrats ont pu s'appeler préteurs), et le long conflit entre patriciens et plébéiens a profondément façonné le régime.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Tite-Live",
        "work": "Histoire romaine",
        "locus": "I, 60 et II, 1",
        "url": "https://bcs.fltr.ucl.ac.be/LIV/II.html"
      },
      {
        "kind": "ancient",
        "author": "Polybe",
        "work": "Histoires",
        "locus": "III, 22",
        "url": "https://remacle.org/bloodwolf/historiens/polybe/livre3.htm"
      },
      {
        "kind": "modern",
        "author": "T. J. Cornell",
        "work": "The Beginnings of Rome, Londres, Routledge, 1995",
        "locus": "chap. 9, The Beginnings of the Roman Republic"
      },
      {
        "kind": "modern",
        "author": "A. Drummond",
        "work": "Appendice : Early Roman chronology, dans The Cambridge Ancient History, 2e éd., vol. VII, 2, 1989",
        "locus": "appendice, section 1"
      }
    ]
  },
  {
    "id": "loi-des-douze-tables",
    "title": "Loi des Douze Tables",
    "start": -450,
    "end": -449,
    "precision": "year",
    "certainty": "traditional",
    "certaintyNote": "Dates de la tradition annalistique ; l'existence du code est sûre, mais son texte n'est connu que par des citations d'auteurs plus tardifs.",
    "era": "republique",
    "track": "rome",
    "category": "society",
    "importance": 2,
    "placeId": "rome",
    "people": [
      "appius-claudius-decemvir"
    ],
    "summary": "Sous la pression des plébéiens, Rome confie à dix magistrats, les décemvirs, la rédaction d'un code de lois écrit et public. Dix tables sont adoptées en 451, deux autres en 450 av. J.-C. Ce texte, socle du droit romain, n'est connu que par des fragments cités par des auteurs plus tardifs.",
    "body": "**Pourquoi écrire la loi ?** Au début de la République, le droit est coutumier et interprété par des prêtres patriciens. Les plébéiens réclament des règles connues de tous. Selon Tite-Live, une commission de dix hommes, les décemvirs, reçoit en 451 av. J.-C. tous les pouvoirs pour rédiger les lois ; dix tables sont votées, puis deux autres l'année suivante.\n\n**Le contenu.** Les fragments conservés portent sur la procédure en justice, les dettes, la famille, l'héritage, la propriété, les funérailles et certains délits. Certaines dispositions sont très dures, comme le droit pour le créancier de saisir le débiteur insolvable. Selon Tite-Live, les lois sont exposées en public, gravées sur du bronze.\n\n**Entre tradition et histoire.** Le récit du second décemvirat, devenu tyrannique sous Appius Claudius, est très romancé. Mais l'existence d'un code archaïque est certaine : Cicéron rappelle qu'enfant, il apprenait encore les Douze Tables par cœur, et les juristes les ont commentées pendant des siècles.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Tite-Live",
        "work": "Histoire romaine",
        "locus": "III, 32 à 37 et III, 57, 10",
        "url": "https://bcs.fltr.ucl.ac.be/LIV/III.html"
      },
      {
        "kind": "ancient",
        "author": "Cicéron",
        "work": "Des lois (De legibus)",
        "locus": "II, 59",
        "url": "https://www.thelatinlibrary.com/cicero/leg2.shtml"
      },
      {
        "kind": "modern",
        "author": "Michel Humbert",
        "work": "La loi des XII Tables. Édition et commentaire, Rome, École française de Rome, coll. Sources et documents, 2018"
      },
      {
        "kind": "modern",
        "author": "T. J. Cornell",
        "work": "The Beginnings of Rome, Londres, Routledge, 1995",
        "locus": "chap. 11, The Twelve Tables"
      }
    ]
  },
  {
    "id": "sac-de-rome-par-les-gaulois",
    "title": "Sac de Rome par les Gaulois",
    "start": -389,
    "precision": "year",
    "certainty": "debated",
    "certaintyNote": "390 av. J.-C. selon la chronologie varronienne, 387 ou 386 av. J.-C. selon Polybe, date que préfèrent beaucoup d'historiens.",
    "era": "republique",
    "track": "rome",
    "category": "war",
    "importance": 2,
    "placeId": "rome",
    "people": [
      "brennus",
      "camille"
    ],
    "summary": "Une armée gauloise venue d'Italie du Nord écrase les Romains sur l'Allia, puis prend et pille Rome, à l'exception du Capitole. Les envahisseurs repartent après un accord. L'événement, daté de 390 ou de 387 av. J.-C. selon les chronologies, marque durablement la mémoire romaine.",
    "body": "**L'événement.** Des Gaulois Sénons, installés sur la côte adriatique, descendent vers l'Italie centrale. Un 18 juillet, jour resté néfaste dans le calendrier romain, ils mettent en déroute l'armée romaine près de la rivière Allia, à quelques kilomètres au nord de Rome, puis entrent dans la ville. Polybe, auteur du plus ancien récit conservé, dit qu'ils l'occupèrent sauf le Capitole et repartirent après un accord, rappelés chez eux par une attaque des Vénètes.\n\n**Légendes et embellissements.** Tite-Live ajoute des épisodes célèbres : les oies sacrées qui donnent l'alerte sur le Capitole, le chef gaulois Brennus jetant son épée dans la balance de la rançon en lançant « Malheur aux vaincus », et le dictateur Camille qui surgit pour sauver l'honneur romain. Ces récits relèvent largement de la légende patriotique.\n\n**La date et les traces.** La chronologie de Varron, suivie par Tite-Live, donne 390 av. J.-C. ; Polybe fait coïncider le sac avec la paix d'Antalcidas, soit 387 ou 386 av. J.-C. L'archéologie n'a pas trouvé de traces nettes d'une destruction générale. Après le désastre, Rome se dote d'une puissante enceinte de pierre, le rempart dit servien.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Polybe",
        "work": "Histoires",
        "locus": "I, 6",
        "url": "https://remacle.org/bloodwolf/historiens/polybe/livre1.htm"
      },
      {
        "kind": "ancient",
        "author": "Polybe",
        "work": "Histoires",
        "locus": "II, 18",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Polybius/2*.html"
      },
      {
        "kind": "ancient",
        "author": "Tite-Live",
        "work": "Histoire romaine",
        "locus": "V, 35 à 55",
        "url": "https://bcs.fltr.ucl.ac.be/LIV/V.html"
      },
      {
        "kind": "ancient",
        "author": "Tite-Live",
        "work": "Histoire romaine",
        "locus": "VI, 1, 11",
        "url": "https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.02.0026:book=6:chapter=1"
      },
      {
        "kind": "ancient",
        "author": "Plutarque",
        "work": "Vie de Camille",
        "locus": "18 à 30",
        "url": "https://remacle.org/bloodwolf/historiens/Plutarque/camillepierron.htm"
      },
      {
        "kind": "modern",
        "author": "T. J. Cornell",
        "work": "Rome and Latium to 390 B.C., dans The Cambridge Ancient History, 2e éd., vol. VII, 2, 1989",
        "locus": "chap. 6"
      },
      {
        "kind": "modern",
        "author": "T. J. Cornell",
        "work": "The Beginnings of Rome, Londres, Routledge, 1995",
        "locus": "chap. 12, Wars and External Relations, 509-345 BC"
      }
    ]
  },
  {
    "id": "premiere-guerre-punique",
    "title": "Première guerre punique",
    "start": -263,
    "end": -240,
    "precision": "year",
    "certainty": "attested",
    "era": "republique",
    "track": "rome",
    "category": "war",
    "importance": 2,
    "placeId": "sicile",
    "people": [
      "hamilcar-barca",
      "caius-lutatius-catulus"
    ],
    "summary": "Rome et Carthage s'affrontent pendant près d'un quart de siècle pour le contrôle de la Sicile. Puissance terrestre, Rome se dote d'une flotte de guerre et l'emporte sur mer aux îles Égates en 241 av. J.-C. Carthage évacue la Sicile, qui passe sous domination romaine, et paie une lourde indemnité.",
    "body": "**Les causes.** En 264 av. J.-C., Rome intervient à Messine, en Sicile, à l'appel de mercenaires campaniens, les Mamertins, menacés par Syracuse et par Carthage. C'est la première fois que les légions quittent la péninsule italienne. Le conflit s'étend vite à toute l'île, où Carthage possède depuis longtemps des cités et des comptoirs.\n\n**Une guerre navale.** Rome construit des flottes de quinquérèmes et remporte en 260 av. J.-C. la bataille de Mylae, grâce à une passerelle d'abordage, le « corbeau ». Elle perd aussi des flottes entières dans des tempêtes, et l'expédition de Regulus en Afrique tourne au désastre. En Sicile, Hamilcar Barca tient tête aux Romains pendant des années.\n\n**La paix de 241 av. J.-C.** Après la victoire navale de Lutatius Catulus aux îles Égates, Carthage traite. Selon Polybe, elle évacue la Sicile, rend les prisonniers sans rançon et paie 3 200 talents en dix ans. La Sicile, hors du royaume allié de Syracuse, passe sous l'autorité de Rome et devient sa première province ; un préteur n'y est envoyé chaque année qu'à partir de 227 av. J.-C. Polybe, notre source principale, écrit un siècle plus tard en s'appuyant sur des historiens favorables à l'un ou l'autre camp.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Polybe",
        "work": "Histoires",
        "locus": "I, 10 à 63",
        "url": "https://remacle.org/bloodwolf/historiens/polybe/livre1.htm"
      },
      {
        "kind": "modern",
        "author": "H. H. Scullard",
        "work": "Carthage and Rome, dans The Cambridge Ancient History, 2e éd., vol. VII, 2, 1989",
        "locus": "chap. 11"
      },
      {
        "kind": "modern",
        "author": "J. F. Lazenby",
        "work": "The First Punic War. A Military History, Londres, UCL Press, 1996"
      }
    ]
  },
  {
    "id": "bataille-de-cannes",
    "title": "Bataille de Cannes",
    "start": -215,
    "month": 8,
    "day": 2,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Polybe donne environ 86 000 Romains et alliés et 70 000 morts, Tite-Live jusqu'à 87 200 hommes et environ 48 000 morts, chiffres discutés par les historiens ; la date suit le calendrier romain d'alors, dont l'équivalence julienne est incertaine.",
    "era": "republique",
    "track": "rome",
    "category": "war",
    "importance": 1,
    "placeId": "cannes",
    "people": [
      "hannibal",
      "lucius-aemilius-paullus",
      "caius-terentius-varron"
    ],
    "summary": "En Apulie, Hannibal encercle et anéantit la plus grande armée jamais levée par la République, commandée par les consuls Paul Émile et Varron. Les pertes romaines, d'environ 48 000 à 70 000 morts selon les sources, en font l'une des pires défaites de l'histoire de Rome, mais la cité refuse de capituler.",
    "body": "**Le contexte.** Deux ans après avoir franchi les Alpes, Hannibal a battu les Romains à la Trébie puis au lac Trasimène. En 216 av. J.-C., Rome lève une armée exceptionnelle, confiée aux consuls Lucius Aemilius Paullus (Paul Émile) et Caius Terentius Varron. Hannibal s'empare du dépôt de vivres de Cannes, en Apulie, et attend l'ennemi dans la plaine de l'Aufide, l'actuel Ofanto.\n\n**La bataille.** Les légions manipulaires alignent des vélites, fantassins légers armés de javelots, puis trois lignes d'infanterie lourde : hastati et principes armés du pilum et d'une épée, triarii armés d'une lance, tous protégés par le grand bouclier ovale (scutum) et coiffés pour beaucoup de casques de type Montefortino. Elles se massent en profondeur au centre pour enfoncer la ligne adverse. Hannibal dispose ses Gaulois et ses Ibères en arc de cercle, qui recule sous la poussée, tandis que ses fantassins africains se rabattent sur les flancs. Sa cavalerie, qui monte sans étriers comme toutes celles de l'époque, chasse les cavaliers romains puis prend l'infanterie à revers : l'armée romaine est encerclée. Hannibal n'a plus d'éléphants : selon Polybe, un seul avait survécu à l'hiver qui suivit la Trébie.\n\n**Un bilan très discuté.** Polybe parle de 80 000 fantassins et de plus de 6 000 cavaliers romains et alliés, dont environ 70 000 tués ; Tite-Live compte 45 500 fantassins et 2 700 cavaliers tués, et hésite lui-même sur l'effectif engagé. Le consul Paul Émile meurt dans la bataille. Hannibal, qui disposait d'environ 40 000 fantassins et 10 000 cavaliers, aurait perdu de 5 700 à 8 000 hommes selon les sources.\n\n**Une bataille modèle.** L'encerclement de Cannes est resté un cas d'école de la tactique militaire. Pourtant Rome refuse de négocier, lève de nouvelles légions et finit par gagner la guerre.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Polybe",
        "work": "Histoires",
        "locus": "III, 107 à 117",
        "url": "https://remacle.org/bloodwolf/historiens/polybe/livre3.htm"
      },
      {
        "kind": "ancient",
        "author": "Tite-Live",
        "work": "Histoire romaine",
        "locus": "XXII, 36 et 44 à 52",
        "url": "https://bcs.fltr.ucl.ac.be/LIV/XXII.html"
      },
      {
        "kind": "ancient",
        "author": "Aulu-Gelle",
        "work": "Nuits attiques",
        "locus": "V, 17, 5",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Gellius/5*.html"
      },
      {
        "kind": "modern",
        "author": "Adrian Goldsworthy",
        "work": "Cannae, Londres, Cassell, 2001"
      },
      {
        "kind": "modern",
        "author": "Gregory Daly",
        "work": "Cannae. The Experience of Battle in the Second Punic War, Londres, Routledge, 2002"
      },
      {
        "kind": "modern",
        "author": "John Briscoe",
        "work": "The Second Punic War, dans The Cambridge Ancient History, 2e éd., vol. VIII, 1989",
        "locus": "chap. 3"
      }
    ],
    "scene": "cannes"
  },
  {
    "id": "bataille-de-zama",
    "title": "Bataille de Zama",
    "start": -201,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "Le jour (souvent fixé au 19 octobre d'après une éclipse) et l'emplacement exact du champ de bataille restent incertains.",
    "era": "republique",
    "track": "rome",
    "category": "war",
    "importance": 2,
    "placeId": "zama",
    "people": [
      "scipion-l-africain",
      "hannibal",
      "massinissa"
    ],
    "summary": "En Afrique, Scipion bat Hannibal, rappelé d'Italie pour défendre Carthage. Grâce notamment à la cavalerie numide de Massinissa, cette victoire met fin à la deuxième guerre punique. Carthage perd sa flotte et ses possessions hors d'Afrique et doit verser un lourd tribut.",
    "body": "**Le contexte.** Après quinze ans de guerre en Italie, Hannibal est rappelé en Afrique, où Publius Cornelius Scipion a débarqué en 204 av. J.-C. et s'est allié au prince numide Massinissa. Les deux généraux se rencontrent avant la bataille, sans parvenir à un accord.\n\n**La bataille.** Selon Polybe, Hannibal place en tête plus de 80 éléphants, puis trois lignes d'infanterie. Scipion ménage des couloirs entre ses manipules pour laisser passer les éléphants affolés. La cavalerie romaine et numide, victorieuse sur les ailes, revient frapper l'arrière de l'armée carthaginoise. Polybe compte 20 000 morts carthaginois et presque autant de prisonniers, contre un peu plus de 1 500 morts romains.\n\n**Lieu, date et conséquences.** Le nom de Zama vient d'une ville près de laquelle Hannibal campa ; Tite-Live place le camp de Scipion près de Naraggara, et le champ de bataille n'a jamais été identifié avec certitude. Le jour précis est également discuté. La paix de 201 av. J.-C. réduit Carthage au rang de puissance africaine, et Scipion reçoit le surnom d'Africain.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Polybe",
        "work": "Histoires",
        "locus": "XV, 5 à 16",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Polybius/15*.html"
      },
      {
        "kind": "ancient",
        "author": "Tite-Live",
        "work": "Histoire romaine",
        "locus": "XXX, 29 à 35",
        "url": "https://bcs.fltr.ucl.ac.be/LIV/XXX.html"
      },
      {
        "kind": "modern",
        "author": "John Briscoe",
        "work": "The Second Punic War, dans The Cambridge Ancient History, 2e éd., vol. VIII, 1989",
        "locus": "chap. 3"
      },
      {
        "kind": "modern",
        "author": "Serge Lancel",
        "work": "Hannibal, Paris, Fayard, 1995"
      }
    ]
  },
  {
    "id": "destruction-de-carthage",
    "title": "Destruction de Carthage",
    "start": -145,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "Le chiffre de 50 000 survivants donné par Appien est invérifiable ; le sel répandu sur les ruines est un mythe moderne.",
    "era": "republique",
    "track": "rome",
    "category": "war",
    "importance": 2,
    "placeId": "carthage",
    "people": [
      "scipion-emilien",
      "hasdrubal-le-boetharque",
      "polybe"
    ],
    "summary": "Au printemps 146 av. J.-C., après trois ans de siège, Scipion Émilien prend Carthage d'assaut. La ville est incendiée et rasée, ses habitants survivants vendus comme esclaves, et son territoire devient la province romaine d'Afrique. L'idée d'un sol couvert de sel est une invention moderne.",
    "body": "**La troisième guerre punique.** Carthage a payé son tribut et retrouvé sa prospérité. À Rome, Caton l'Ancien réclame sa destruction. En 149 av. J.-C., Rome prend prétexte d'une guerre entre Carthage et le roi numide Massinissa pour exiger que les Carthaginois abandonnent leur ville et s'installent loin de la mer. Ils refusent et soutiennent un long siège.\n\n**La prise de la ville.** Selon Appien, Scipion Émilien force le port au printemps 146 av. J.-C. ; les combats de rue durent six jours et six nuits jusqu'à la citadelle de Byrsa, d'où sortent environ 50 000 survivants. Le général carthaginois Hasdrubal se rend, tandis que sa femme tue leurs enfants et se jette avec eux dans les flammes.\n\n**Après la chute.** Polybe, présent aux côtés de Scipion, rapporte que le vainqueur, devant la ville en feu, lui confia sa crainte qu'un jour Rome connaisse le même sort ; Appien, qui le cite, ajoute que Scipion pleura. Le Sénat ordonne de raser ce qui reste et interdit d'y habiter. Aucune source antique ne dit en revanche que le sol fut semé de sel : cette image n'apparaît qu'à l'époque moderne. Une colonie romaine, projetée par César, sera fondée sur le site sous Auguste.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Appien",
        "work": "Livre africain (Libyca)",
        "locus": "127 à 130",
        "url": "https://www.livius.org/sources/content/appian/appian-the-punic-wars/appian-the-punic-wars-26/"
      },
      {
        "kind": "ancient",
        "author": "Appien",
        "work": "Livre africain (Libyca)",
        "locus": "131 à 135",
        "url": "https://www.livius.org/sources/content/appian/appian-the-punic-wars/appian-the-punic-wars-27/"
      },
      {
        "kind": "ancient",
        "author": "Polybe",
        "work": "Histoires",
        "locus": "XXXVIII, 19 à 21",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Polybius/38*.html"
      },
      {
        "kind": "modern",
        "author": "Serge Lancel",
        "work": "Carthage, Paris, Fayard, 1992"
      },
      {
        "kind": "modern",
        "author": "R. T. Ridley",
        "work": "To Be Taken with a Pinch of Salt: The Destruction of Carthage, Classical Philology, 81, 2, 1986",
        "url": "https://www.journals.uchicago.edu/doi/10.1086/366973"
      }
    ]
  },
  {
    "id": "assassinat-de-tiberius-gracchus",
    "title": "Assassinat de Tiberius Gracchus",
    "start": -132,
    "precision": "year",
    "certainty": "attested",
    "era": "republique",
    "track": "rome",
    "category": "politics",
    "importance": 2,
    "placeId": "rome",
    "people": [
      "tiberius-gracchus",
      "scipion-nasica"
    ],
    "summary": "Tribun de la plèbe, Tiberius Gracchus fait voter une loi agraire pour distribuer des terres publiques aux citoyens pauvres. Alors qu'il brigue un second mandat, des sénateurs menés par Scipion Nasica le tuent avec plus de 300 de ses partisans. Pour la première fois depuis la fin des rois, un conflit politique s'achève dans le sang.",
    "body": "**La réforme.** Les guerres de conquête ont enrichi les grands propriétaires, qui occupent une large part des terres publiques (l'ager publicus), tandis que les petits paysans, réservoir des légions, s'appauvrissent. Tribun de la plèbe en 133 av. J.-C., Tiberius Sempronius Gracchus fait voter une loi qui limite ces occupations et redistribue l'excédent en petits lots.\n\n**L'escalade.** Pour faire passer sa loi, il fait destituer un autre tribun, Octavius, qui y opposait son veto, puis propose d'utiliser le trésor légué à Rome par le roi Attale III de Pergame. Ses adversaires l'accusent de viser la royauté. Lorsqu'il se présente pour un second tribunat, ce qui est contraire à l'usage, le grand pontife Scipion Nasica entraîne des sénateurs et leurs partisans vers le Capitole.\n\n**Le massacre.** Tiberius est assommé à coups de bancs et de bâtons ; selon Plutarque, plus de 300 de ses partisans périssent et leurs corps sont jetés dans le Tibre. Les historiens voient dans cet épisode le début de la crise de la République, désormais marquée par la violence entre factions.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Plutarque",
        "work": "Vie de Tiberius Gracchus",
        "locus": "8 à 20",
        "url": "https://remacle.org/bloodwolf/historiens/Plutarque/gracquespierron.htm"
      },
      {
        "kind": "ancient",
        "author": "Appien",
        "work": "Guerres civiles",
        "locus": "I, 14 à 17",
        "url": "https://remacle.org/bloodwolf/historiens/appien/combes3.htm"
      },
      {
        "kind": "modern",
        "author": "Claude Nicolet",
        "work": "Les Gracques. Crise agraire et révolution à Rome, Paris, Julliard, coll. Archives, 1967"
      },
      {
        "kind": "modern",
        "author": "Andrew Lintott",
        "work": "Political history, 146-95 B.C., dans The Cambridge Ancient History, 2e éd., vol. IX, 1994",
        "locus": "chap. 3"
      }
    ]
  },
  {
    "id": "guerre-sociale",
    "title": "Guerre sociale",
    "start": -90,
    "end": -87,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "Velleius Paterculus parle de plus de 300 000 morts, chiffre sans doute très exagéré.",
    "era": "republique",
    "track": "rome",
    "category": "war",
    "importance": 2,
    "placeId": "corfinium",
    "people": [
      "marcus-livius-drusus",
      "marius",
      "sylla"
    ],
    "summary": "Les alliés italiens de Rome, qui fournissent une grande part de ses soldats sans avoir la citoyenneté, se soulèvent après l'assassinat du tribun Livius Drusus. Rome l'emporte militairement, mais doit accorder la citoyenneté romaine à presque toute l'Italie au sud du Pô.",
    "body": "**Les causes.** Depuis des générations, les peuples italiens combattent aux côtés de Rome sans bénéficier des droits des citoyens. En 91 av. J.-C., le tribun Marcus Livius Drusus propose de leur accorder la citoyenneté ; il est assassiné. Les Marses, les Samnites et d'autres peuples prennent les armes et créent leur propre État, avec pour capitale Corfinium, rebaptisée Italia ou Italica selon les auteurs.\n\n**Une guerre très dure.** Les combats opposent des armées organisées et équipées de la même manière, souvent d'anciens compagnons d'armes. Deux consuls romains sont tués en deux ans. Marius, Sylla et Pompée Strabon, père du grand Pompée, commandent les forces romaines.\n\n**L'issue.** Pour diviser ses adversaires, Rome accorde la citoyenneté aux alliés restés fidèles, puis à ceux qui déposent les armes, par des lois votées en 90 et 89 av. J.-C. À la fin de la guerre, presque tous les Italiens libres au sud du Pô sont citoyens romains : la cité de Rome s'étend désormais à l'Italie.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Appien",
        "work": "Guerres civiles",
        "locus": "I, 34 à 53",
        "url": "https://remacle.org/bloodwolf/historiens/appien/combes6.htm"
      },
      {
        "kind": "ancient",
        "author": "Velleius Paterculus",
        "work": "Histoire romaine",
        "locus": "II, 15 à 17",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Velleius_Paterculus/2A*.html"
      },
      {
        "kind": "modern",
        "author": "Emilio Gabba",
        "work": "Rome and Italy: the Social War, dans The Cambridge Ancient History, 2e éd., vol. IX, 1994",
        "locus": "chap. 4"
      }
    ]
  },
  {
    "id": "marche-de-sylla-sur-rome",
    "title": "Sylla marche sur Rome",
    "start": -87,
    "precision": "year",
    "certainty": "attested",
    "era": "republique",
    "track": "rome",
    "category": "politics",
    "importance": 2,
    "placeId": "rome",
    "people": [
      "sylla",
      "marius",
      "publius-sulpicius-rufus"
    ],
    "summary": "Privé par une loi du commandement de la guerre contre Mithridate au profit de Marius, le consul Sylla marche sur Rome avec six légions et s'en empare. Pour la première fois, une armée de citoyens prend la ville par la force : un précédent que César suivra en 49 av. J.-C.",
    "body": "**L'enjeu.** En 88 av. J.-C., le consul Lucius Cornelius Sulla, dit Sylla, reçoit le commandement de la guerre contre Mithridate VI, roi du Pont, qui vient de faire massacrer des milliers d'Italiens en Asie Mineure. Le tribun Publius Sulpicius Rufus fait voter le transfert de ce commandement au vieux Marius.\n\n**La marche.** Sylla, qui se trouve avec son armée en Campanie, convainc ses soldats de le suivre et marche sur Rome avec six légions ; selon Appien, tous ses officiers sauf un questeur refusent de l'accompagner. Il prend la ville après des combats de rue, fait déclarer Marius, Sulpicius et leurs partisans ennemis publics, puis part pour l'Orient. Sulpicius est tué ; Marius s'enfuit en Afrique.\n\n**Un tournant.** Appien souligne qu'à partir de ce moment, les querelles politiques se règlent par les armes. Sylla reviendra en 83 av. J.-C., gagnera une nouvelle guerre civile, se fera nommer dictateur et organisera les proscriptions, listes d'opposants que chacun pouvait tuer contre récompense.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Appien",
        "work": "Guerres civiles",
        "locus": "I, 55 à 60",
        "url": "https://remacle.org/bloodwolf/historiens/appien/combes8.htm"
      },
      {
        "kind": "ancient",
        "author": "Plutarque",
        "work": "Vie de Sylla",
        "locus": "7 à 10",
        "url": "https://remacle.org/bloodwolf/historiens/Plutarque/syllapierron.htm"
      },
      {
        "kind": "modern",
        "author": "Robin Seager",
        "work": "Sulla, dans The Cambridge Ancient History, 2e éd., vol. IX, 1994",
        "locus": "chap. 6"
      },
      {
        "kind": "modern",
        "author": "François Hinard",
        "work": "Sylla, Paris, Fayard, 1985"
      }
    ]
  },
  {
    "id": "siege-d-alesia",
    "title": "Siège d'Alésia",
    "start": -51,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "Les effectifs donnés par César (80 000 assiégés, 8 000 cavaliers et environ 250 000 fantassins dans l'armée de secours) sont jugés très exagérés.",
    "era": "republique",
    "track": "rome",
    "category": "war",
    "importance": 2,
    "placeId": "alesia",
    "people": [
      "jules-cesar",
      "vercingetorix"
    ],
    "summary": "Réfugié dans l'oppidum d'Alésia avec son armée, l'Arverne Vercingétorix est assiégé par César, qui l'entoure de deux lignes de fortifications. L'armée de secours gauloise échoue et Vercingétorix se rend. La victoire scelle la conquête de la Gaule par Rome.",
    "body": "**La révolte de 52 av. J.-C.** Après six ans de campagnes de César en Gaule, de nombreux peuples se soulèvent sous la direction de Vercingétorix. Repoussé devant Gergovie, César reprend l'initiative ; Vercingétorix se retranche avec son armée dans Alésia, oppidum des Mandubiens.\n\n**Un double siège.** César fait creuser une ligne de fortifications tournée vers la ville et une seconde tournée vers l'extérieur, avec fossés, pièges et tours. Une immense armée de secours gauloise attaque à plusieurs reprises ; César, à la fois assiégeant et assiégé, résiste. À court de vivres, Vercingétorix se livre au vainqueur. Il sera exhibé lors du triomphe de César en 46 av. J.-C., puis exécuté.\n\n**Le site et les chiffres.** La localisation à Alise-Sainte-Reine, en Côte-d'Or, a été confirmée par les fouilles franco-allemandes des années 1990, qui ont retrouvé les fortifications romaines ; d'autres hypothèses subsistent sans convaincre la majorité des archéologues. Les chiffres de César, notre principale source, servent sa gloire et sont jugés très exagérés.",
    "sources": [
      {
        "kind": "ancient",
        "author": "César",
        "work": "Guerre des Gaules",
        "locus": "VII, 68 à 74",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Caesar/Gallic_War/7F*.html"
      },
      {
        "kind": "ancient",
        "author": "César",
        "work": "Guerre des Gaules",
        "locus": "VII, 75 à 90",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Caesar/Gallic_War/7G*.html"
      },
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "XL, 39 à 41",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/40*.html"
      },
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "XLIII, 19, 4",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/43*.html"
      },
      {
        "kind": "modern",
        "author": "Michel Reddé",
        "work": "Alésia. L'archéologie face à l'imaginaire, Paris, Errance, 2003"
      }
    ]
  },
  {
    "id": "franchissement-du-rubicon",
    "title": "Franchissement du Rubicon",
    "start": -48,
    "month": 1,
    "precision": "month",
    "certainty": "attested",
    "certaintyNote": "Le jour exact est inconnu (on cite souvent le 10 janvier), et le calendrier romain d'alors était décalé par rapport aux saisons.",
    "era": "republique",
    "track": "rome",
    "category": "politics",
    "importance": 2,
    "placeId": "rubicon",
    "people": [
      "jules-cesar",
      "pompee"
    ],
    "summary": "En janvier 49 av. J.-C., César franchit avec ses troupes le Rubicon, petit fleuve qui sépare sa province de Gaule cisalpine de l'Italie. Entrer en armes en Italie sans l'accord du Sénat est un acte de guerre : c'est le début de la guerre civile contre Pompée et les partisans du Sénat.",
    "body": "**L'impasse politique.** Proconsul des Gaules depuis 58 av. J.-C., César veut passer directement de son commandement à un second consulat, pour échapper aux procès que lui promettent ses adversaires. Le Sénat, appuyé sur Pompée, exige qu'il licencie son armée ; les tribuns favorables à César, menacés, s'enfuient de Rome.\n\n**Le passage.** Selon Plutarque, César n'a avec lui que 300 cavaliers et 5 000 légionnaires. Il hésite au bord du Rubicon, puis passe et s'empare d'Ariminum (Rimini) avant l'aube. Suétone lui prête la formule « le sort en est jeté » (iacta alea est), que Plutarque dit prononcée en grec. César lui-même, dans sa Guerre civile, ne mentionne pas le fleuve.\n\n**Incertitudes.** Le jour exact n'est pas connu, et le calendrier romain, mal tenu, était alors décalé par rapport aux saisons. Le cours des rivières a changé depuis l'Antiquité : l'identification du Rubicon reste discutée, et le fleuve qui porte aujourd'hui ce nom, l'ancien Fiumicino, ne l'a reçu officiellement qu'en 1933.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Suétone",
        "work": "Vie de César",
        "locus": "31 à 33",
        "url": "https://remacle.org/bloodwolf/historiens/suetone/cesar.htm"
      },
      {
        "kind": "ancient",
        "author": "Plutarque",
        "work": "Vie de César",
        "locus": "32",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Plutarch/Lives/Caesar*.html"
      },
      {
        "kind": "ancient",
        "author": "Plutarque",
        "work": "Vie de Pompée",
        "locus": "60",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Plutarch/Lives/Pompey*.html"
      },
      {
        "kind": "modern",
        "author": "Elizabeth Rawson",
        "work": "Caesar: civil war and dictatorship, dans The Cambridge Ancient History, 2e éd., vol. IX, 1994",
        "locus": "chap. 11"
      }
    ]
  },
  {
    "id": "fondation-colonie-arles",
    "title": "Fondation de la colonie d'Arles",
    "start": -45,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "46 av. J.-C. est l'année retenue par le musée départemental Arles antique ; d'autres auteurs placent la fondation en 45 av. J.-C. Suétone, qui rapporte le rôle de Tiberius Claudius Nero, ne donne pas l'année.",
    "era": "republique",
    "track": "rome",
    "category": "politics",
    "importance": 3,
    "placeId": "arles",
    "people": [
      "jules-cesar"
    ],
    "summary": "Sur l'ordre de César, Tiberius Claudius Nero, père du futur empereur Tibère, établit à Arles une colonie de citoyens romains pour les vétérans de la VIe légion, d'où son surnom de Sextanorum. Bâtie au sommet du delta du Rhône, la ville devient un grand port entre la Méditerranée et l'intérieur de la Gaule.",
    "body": "Le rocher de l'Hauture, qui domine le sommet du delta du Rhône, porte une agglomération commerçante dès les premières décennies du VIe siècle av. J.-C. ; le poète Aviénus rapporte qu'elle s'appelait Theline au temps où des Grecs y vivaient. En 49 av. J.-C., pendant la guerre civile, **César** y fait construire douze navires de guerre pour le siège de Marseille : selon son propre récit, ils sont armés trente jours après la coupe du bois.\n\nQuelques années plus tard, **Tiberius Claudius Nero**, envoyé par César, y installe des vétérans, comme le rapporte Suétone dans sa *Vie de Tibère*, dont il est le père. Pline l'Ancien et Pomponius Mela désignent la colonie par le nom de la légion d'origine de ses colons, la VIe : Arelate Sextanorum, la ville « des hommes de la Sixième ».\n\nL'année exacte reste incertaine : 46 av. J.-C. selon le musée départemental Arles antique, 45 selon d'autres auteurs. L'identité précise de la légion, souvent rapprochée de la VI Ferrata, est elle aussi discutée. Placée à la jonction du fleuve et de la mer, la colonie devient l'un des ports majeurs de la future province de Narbonnaise.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Suétone",
        "work": "Vie de Tibère",
        "locus": "4, 1"
      },
      {
        "kind": "ancient",
        "author": "Pline l'Ancien",
        "work": "Histoire naturelle",
        "locus": "III, 36"
      },
      {
        "kind": "ancient",
        "author": "Pomponius Mela",
        "work": "Chorographie",
        "locus": "II, 75"
      },
      {
        "kind": "ancient",
        "author": "César",
        "work": "Guerre civile",
        "locus": "I, 36"
      },
      {
        "kind": "ancient",
        "author": "Aviénus",
        "work": "Ora maritima",
        "locus": "v. 689 à 691"
      },
      {
        "kind": "modern",
        "author": "Musée départemental Arles antique",
        "work": "Dossier enseignant Jean-Claude Golvin, 2011",
        "url": "https://www.arretetonchar.fr/wp-content/uploads/2024/10/Arles-MDAA-13-Dossier-enseignant-Jean-Claude-Golvin-2011.pdf"
      }
    ],
    "scene": "arles"
  },
  {
    "id": "assassinat-de-cesar",
    "title": "Assassinat de César",
    "start": -43,
    "month": 3,
    "day": 15,
    "precision": "day",
    "certainty": "attested",
    "era": "republique",
    "track": "rome",
    "category": "politics",
    "importance": 1,
    "placeId": "curie-de-pompee",
    "people": [
      "jules-cesar",
      "marcus-junius-brutus",
      "caius-cassius-longinus"
    ],
    "summary": "Aux ides de mars 44 av. J.-C., Jules César, dictateur à vie depuis quelques semaines, est poignardé en pleine séance du Sénat, dans la curie de Pompée. Les conjurés, menés par Brutus et Cassius, veulent sauver la République ; leur geste ouvre au contraire une nouvelle série de guerres civiles.",
    "body": "**Un pouvoir sans précédent.** Vainqueur de Pompée et de ses partisans, César accumule les honneurs et se fait nommer dictateur à vie au début de 44 av. J.-C. Pour une partie de l'aristocratie, attachée au partage du pouvoir entre magistrats élus, c'est une royauté déguisée.\n\n**Le meurtre.** Selon Suétone, plus de 60 hommes participent à la conjuration, menée par Caius Cassius, Marcus Brutus et Decimus Brutus. Le 15 mars, jour des ides, le Sénat se réunit dans la curie attenante au théâtre de Pompée, sur le Champ de Mars, la curie du Forum étant en reconstruction. César reçoit 23 coups de poignard et s'effondre, selon certains auteurs cités par Plutarque, au pied d'une statue de Pompée. Les mots « Toi aussi, mon fils ? », qu'il aurait dits en grec à Brutus, ne sont rapportés par Suétone que d'après « quelques écrivains ».\n\n**Les conséquences.** Les conjurés n'avaient rien prévu pour la suite. Marc Antoine soulève la foule lors des funérailles, et le jeune Octavien, fils adoptif de César, entre en scène. La République ne s'en relèvera pas.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Suétone",
        "work": "Vie de César",
        "locus": "80 à 82",
        "url": "https://remacle.org/bloodwolf/historiens/suetone/cesar.htm"
      },
      {
        "kind": "ancient",
        "author": "Plutarque",
        "work": "Vie de César",
        "locus": "60 à 67",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Plutarch/Lives/Caesar*.html"
      },
      {
        "kind": "modern",
        "author": "Robert Étienne",
        "work": "Les Ides de mars. L'assassinat de César ou de la dictature ?, Paris, Gallimard et Julliard, coll. Archives, 1973"
      },
      {
        "kind": "modern",
        "author": "Elizabeth Rawson",
        "work": "Caesar: civil war and dictatorship, dans The Cambridge Ancient History, 2e éd., vol. IX, 1994",
        "locus": "chap. 11"
      }
    ]
  },
  {
    "id": "bataille-d-actium",
    "title": "Bataille d'Actium",
    "start": -30,
    "month": 9,
    "day": 2,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Le nombre de navires réellement engagés et les intentions d'Antoine pendant la bataille restent discutés.",
    "era": "republique",
    "track": "rome",
    "category": "war",
    "importance": 2,
    "placeId": "actium",
    "people": [
      "auguste",
      "marc-antoine",
      "cleopatre",
      "agrippa"
    ],
    "summary": "Au large du promontoire d'Actium, en Grèce, la flotte d'Octavien commandée par Agrippa bat celle de Marc Antoine et de Cléopâtre VII, reine d'Égypte. Antoine et Cléopâtre s'enfuient en Égypte, où ils se donnent la mort l'année suivante. Octavien reste seul maître du monde romain.",
    "body": "**La rupture.** Après le partage du monde romain entre les triumvirs, Marc Antoine gouverne l'Orient en lien étroit avec Cléopâtre. Octavien présente le conflit comme une lutte contre une reine étrangère : en 32 av. J.-C., le Sénat déclare la guerre à Cléopâtre, et non à Antoine.\n\n**La campagne.** Antoine et Cléopâtre concentrent leurs forces dans le golfe d'Ambracie, sur la côte ouest de la Grèce. Agrippa coupe leur ravitaillement par mer, tandis que maladies et désertions affaiblissent leur armée. Plutarque attribue à Antoine plus de 500 navires de guerre au début de la campagne, et 250 à Octavien ; faute d'équipages, Antoine brûle une partie de sa flotte avant la bataille, et le nombre de navires engagés le 2 septembre reste discuté.\n\n**La bataille.** Antoine tente de forcer le blocus. Pendant le combat, l'escadre de Cléopâtre prend le large et Antoine la suit avec quelques navires ; le reste de sa flotte se rend, puis son armée de terre une semaine plus tard. Les historiens discutent encore pour savoir si Antoine cherchait la victoire ou seulement à percer le blocus. L'historien Dion Cassius fait commencer à cette date le pouvoir d'Octavien seul.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "L, 4 à 6 et 31 à 35",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/50*.html"
      },
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "LI, 1, 1 et 2",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/51*.html"
      },
      {
        "kind": "ancient",
        "author": "Plutarque",
        "work": "Vie d'Antoine",
        "locus": "60 à 68",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Plutarch/Lives/Antony*.html"
      },
      {
        "kind": "modern",
        "author": "Christopher Pelling",
        "work": "The triumviral period, dans The Cambridge Ancient History, 2e éd., vol. X, 1996",
        "locus": "chap. 1"
      },
      {
        "kind": "modern",
        "author": "Carsten Hjort Lange",
        "work": "The Battle of Actium: A Reconsideration, Classical Quarterly, 61, 2, 2011",
        "url": "https://www.cambridge.org/core/journals/classical-quarterly/article/battle-of-actium-a-reconsideration/0DD01E5FBBCA2198FB105C20014F9662"
      }
    ]
  },
  {
    "id": "auguste-princeps",
    "title": "Octavien devient Auguste",
    "start": -26,
    "month": 1,
    "day": 16,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Les calendriers de Préneste et de Cumes donnent le 16 janvier pour le nom d'Auguste, mais Ovide rattache ce nom aux ides (13 janvier), jour de la restitution de l'État et des provinces.",
    "era": "haut-empire",
    "track": "rome",
    "category": "politics",
    "importance": 1,
    "placeId": "rome",
    "people": [
      "auguste"
    ],
    "summary": "Le 16 janvier 27 av. J.-C., le Sénat confère à Octavien, vainqueur des guerres civiles, le nom d'Auguste. Trois jours plus tôt, il avait solennellement « rendu » l'État au Sénat et au peuple romain. Ces séances fondent le principat, un pouvoir monarchique présenté comme une restauration de la République.",
    "body": "Le 13 janvier 27 av. J.-C., Octavien annonce au Sénat qu'il remet l'État entre les mains du Sénat et du peuple romain. En retour, les sénateurs lui confient pour dix ans les provinces où stationnent la plupart des légions, puis, le 16 janvier, lui décernent le nom d'*Augustus*, « le vénérable », un terme à forte résonance religieuse. Suétone attribue la proposition à Munatius Plancus ; selon Dion Cassius, Octavien aurait d'abord songé au nom de Romulus, jugé trop royal.\n\nDans ses *Res Gestae* (chapitre 34), Auguste affirme qu'il l'emporta dès lors sur tous par son autorité (*auctoritas*, leçon de la copie d'Antioche de Pisidie), sans avoir plus de pouvoir légal que ses collègues magistrats. En réalité, il contrôle l'armée, une large part des finances et les nominations. Les historiens appellent ce régime le « principat », d'après le titre informel de *princeps*, le premier des citoyens.\n\nFaire commencer l'Empire en 27 av. J.-C. est une convention : le régime se construit par étapes, de la victoire d'Actium (31 av. J.-C.) aux réaménagements de 23 av. J.-C.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Auguste",
        "work": "Res Gestae Divi Augusti",
        "locus": "34",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Augustus/Res_Gestae/6*.html"
      },
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "LIII, 2 à 16",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/53*.html"
      },
      {
        "kind": "ancient",
        "author": "Suétone",
        "work": "Vie d'Auguste",
        "locus": "7, 2",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Suetonius/12Caesars/Augustus*.html"
      },
      {
        "kind": "ancient",
        "author": "Calendriers épigraphiques",
        "work": "Fastes de Préneste et férial de Cumes (trad. anglaise Ehrenberg et Jones)",
        "locus": "13 et 16 janvier",
        "url": "https://www.attalus.org/docs/ej_fasti.html"
      },
      {
        "kind": "ancient",
        "author": "Ovide",
        "work": "Fastes",
        "locus": "I, 587 à 616",
        "url": "https://www.thelatinlibrary.com/ovid/ovid.fasti1.shtml"
      },
      {
        "kind": "modern",
        "author": "John Scheid",
        "work": "Res Gestae Divi Augusti. Hauts faits du divin Auguste (Les Belles Lettres, Collection des Universités de France, 2007)",
        "locus": "chapitre 34"
      },
      {
        "kind": "modern",
        "author": "Bowman, Champlin et Lintott (dir.)",
        "work": "The Cambridge Ancient History, vol. X : The Augustan Empire (2e éd., 1996)"
      },
      {
        "kind": "modern",
        "author": "Le Glay, Voisin et Le Bohec",
        "work": "Histoire romaine (PUF)"
      }
    ]
  },
  {
    "id": "enceinte-de-nemausus",
    "title": "Auguste donne portes et murs à Nemausus",
    "start": -15,
    "end": -14,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "L'inscription de la porte d'Auguste date le don de la huitième puissance tribunicienne d'Auguste, soit 16 ou 15 av. J.-C. Le chantier de l'enceinte se prolonge bien après, sans doute jusque vers 25 ou 30 apr. J.-C. selon les fouilles récentes.",
    "era": "haut-empire",
    "track": "rome",
    "category": "building",
    "importance": 3,
    "placeId": "nimes",
    "people": [
      "auguste"
    ],
    "summary": "En 16 ou 15 av. J.-C., Auguste offre à la colonie de Nemausus ses portes et ses murs, comme le rappelle l'inscription de la porte d'Auguste. Longue d'environ 6 km et flanquée de plus de 80 tours, l'enceinte enferme près de 220 hectares : c'est l'une des plus vastes de la Gaule romaine.",
    "body": "Ancien chef-lieu des Volques Arécomiques, Nemausus est devenue une colonie qui porte le nom d'**Auguste**. Sur la porte qui ouvre la ville vers l'est, là où arrive la voie Domitienne, une inscription placée au-dessus des arches rappelle que l'empereur, consul pour la onzième fois et revêtu de sa huitième puissance tribunicienne, donne à la colonie ses portes et ses murs. Cette titulature situe le don en 16 ou 15 av. J.-C.\n\nLe rempart court sur environ 6 km et englobe près de 220 hectares, y compris les collines du nord, mont Cavalier, Montaury et Canteduc, restées peu bâties. La courtine, haute d'environ 9 mètres et bordée d'un chemin de ronde crénelé, est rythmée par plus de 80 tours aux plans variés, rondes, octogonales ou rectangulaires, et percée d'une dizaine de portes. La pierre vient surtout de la carrière de Roquemaillère.\n\nLa dédicace ne marque pas la fin des travaux. Les fouilles de Montaury, menées de 2014 à 2019, et l'étude des monnaies montrent un chantier étalé sur plusieurs décennies, jusque vers 25 ou 30 apr. J.-C. selon R. Pellé (Inrap). Parmi les portes, seules la porte d'Auguste et la porte de France subsistent aujourd'hui, avec la tour Magne et plusieurs tronçons de mur.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Inscription de la porte d'Auguste à Nîmes",
        "work": "Corpus Inscriptionum Latinarum, XII",
        "locus": "3151"
      },
      {
        "kind": "modern",
        "author": "Office de tourisme de Nîmes",
        "work": "L'enceinte romaine",
        "url": "https://nimes-tourisme.com/en/explorer/nimes/monuments-et-sites/lenceinte-romaine/"
      },
      {
        "kind": "modern",
        "author": "APHG et Inrap",
        "work": "Dossier pédagogique sur Nîmes, 2024",
        "locus": "p. 3",
        "url": "https://www.aphg.fr/IMG/pdf/dossier2_inrap_aphg.pdf"
      },
      {
        "kind": "modern",
        "author": "F. Cabane",
        "work": "Résumé de communication, Académie de Nîmes, 2024",
        "url": "https://www.academiedenimes.org/site/wp-content/uploads/Resume-F-Cabane-22-mars.pdf"
      },
      {
        "kind": "modern",
        "author": "Objectif Gard",
        "work": "Nîmes : sixième campagne de fouille et énième bonne surprise, 29 août 2019",
        "url": "http://www.objectifsud.fr/a-la-une/nimes-sixieme-campagne-de-fouille-et-enieme-bonne-surprise-30523.php"
      }
    ],
    "scene": "nimes"
  },
  {
    "id": "dedicace-maison-carree",
    "title": "Dédicace de la Maison Carrée à Caius et Lucius César",
    "start": 2,
    "end": 5,
    "precision": "year",
    "certainty": "debated",
    "certaintyNote": "Le Musée de la Romanité donne deux fourchettes, de 2 à 4 et 4 ou 5 apr. J.-C., la Ville de Nîmes une construction entre 10 av. J.-C. et le début du Ier siècle. J. C. Anderson (2001) voit dans le temple une reconstruction du IIe siècle, hypothèse minoritaire.",
    "era": "haut-empire",
    "track": "rome",
    "category": "building",
    "importance": 3,
    "placeId": "nimes",
    "people": [
      "auguste"
    ],
    "summary": "Au forum de Nemausus, un temple corinthien élevé sur un podium est dédié à Caius et Lucius César, petits-fils et héritiers d'Auguste, tous deux morts jeunes. Construit entre 10 av. J.-C. et le début du Ier siècle apr. J.-C., il reçoit sa dédicace entre 2 et 5 apr. J.-C. Presque intact, il est inscrit au patrimoine mondial depuis 2023.",
    "body": "La Maison Carrée occupe le côté sud du forum, sa façade principale tournée vers le nord. C'est un temple pseudo-périptère : six colonnes corinthiennes en façade, un porche à colonnes libres, puis des colonnes à demi engagées dans les murs de la cella, soit trente colonnes cannelées d'environ 9 mètres. Un escalier de quinze marches conduit au podium ; l'édifice mesure environ 26 mètres de long, 15 de large et 17 de haut.\n\nSon plan reprend celui du temple d'Apollon *in Circo* à Rome, et son décor s'inspire du temple de Mars Ultor et de l'Ara Pacis : denticules, modillons et frise de rinceaux d'acanthe peuplée d'oiseaux courent sur trois côtés. La dédicace était faite de lettres de bronze fixées sur la frise et l'architrave de la façade. Les lettres ont disparu, mais l'érudit J.-F. Séguier en a restitué le texte au milieu du XVIIIe siècle d'après les trous de fixation.\n\nLa date fine reste discutée : le Musée de la Romanité place la dédicace entre 2 et 5 apr. J.-C., et une dédicace faite après la mort des deux princes, en 4 ou 5, n'est pas exclue. En 2001, J. C. Anderson a proposé d'y voir un temple reconstruit dans la première moitié du IIe siècle, hypothèse restée minoritaire. Restaurée de 2006 à 2010, la Maison Carrée nous est parvenue presque intacte.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Dédicace de la Maison Carrée",
        "work": "Corpus Inscriptionum Latinarum, XII",
        "locus": "3156"
      },
      {
        "kind": "modern",
        "author": "Ville de Nîmes",
        "work": "La Maison Carrée de Nîmes, patrimoine mondial de l'UNESCO",
        "locus": "p. 5 à 10",
        "url": "https://nimes-tourisme.com/app/uploads/2026/03/la-maison-carree-de-nimes.pdf"
      },
      {
        "kind": "modern",
        "author": "Musée de la Romanité",
        "work": "Dossier pédagogique sur l'architecture publique",
        "locus": "p. 4, 8 et 9",
        "url": "https://museedelaromanite.fr/content/uploads/2021/08/DOSSIER-PEDAGOGIQUE-ARCHI-PUBLIQUE-bd.pdf"
      },
      {
        "kind": "modern",
        "author": "J. C. Anderson Jr.",
        "work": "Anachronism in the Roman Architecture of Gaul: The Date of the Maison Carrée at Nîmes, Journal of the Society of Architectural Historians 60, 1, 2001",
        "locus": "p. 68 à 79"
      }
    ],
    "scene": "nimes"
  },
  {
    "id": "desastre-de-varus",
    "title": "Le désastre de Varus",
    "start": 9,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "Aucune source antique ne donne le mois : on place la bataille à la fin de l'été ou au début de l'automne, souvent en septembre. Les pertes (de 15 000 à 20 000 soldats environ) sont une estimation moderne, et le lieu exact reste discuté.",
    "era": "haut-empire",
    "track": "rome",
    "category": "war",
    "importance": 2,
    "placeId": "kalkriese",
    "people": [
      "quinctilius-varus",
      "arminius"
    ],
    "summary": "En 9 apr. J.-C., trois légions commandées par Publius Quinctilius Varus sont anéanties en Germanie dans une embuscade tendue par le Chérusque Arminius. Le désastre met fin au projet d'une province de Germanie jusqu'à l'Elbe. Le site de Kalkriese, en Basse-Saxe, est souvent identifié au champ de bataille, sans certitude absolue.",
    "body": "Légat d'Auguste dans une Germanie en cours d'organisation, Varus regagne ses quartiers d'hiver quand Arminius, chef chérusque, citoyen romain et ancien officier des troupes auxiliaires, l'attire dans un piège. Pendant plusieurs jours, la colonne étirée dans des terrains boisés et marécageux est harcelée puis détruite. Velleius Paterculus compte trois légions, trois ailes de cavalerie et six cohortes, sans doute de 15 000 à 20 000 soldats sans compter les non-combattants, mais aucune source antique ne donne d'effectif. Varus se donne la mort.\n\nVelleius, un contemporain, écrit que la nouvelle parvint moins de cinq jours après la fin de la guerre de Pannonie et de Dalmatie, et Dion Cassius montre Varus en route vers ses quartiers d'hiver : d'où la date de la fin de l'été ou du début de l'automne retenue par les modernes, aucun texte ne donnant le mois. Suétone rapporte le désespoir d'Auguste, qui aurait crié : « Quinctilius Varus, rends-moi mes légions ! ». Ces légions, sans doute les XVIIe, XVIIIe et XIXe, ne furent jamais reconstituées sous leurs numéros.\n\nDepuis la découverte de monnaies romaines en 1987, les fouilles de Kalkriese, près d'Osnabrück, ont livré armes, monnaies et ossements d'un combat de l'époque d'Auguste. La plupart des chercheurs y voient un lieu de la bataille ; d'autres l'attribuent aux campagnes de Germanicus, en 15 et 16 apr. J.-C. Tacite raconte justement comment Germanicus visita en 15 apr. J.-C. le champ de bataille, dans le *saltus Teutoburgiensis*, et y fit enterrer les restes des soldats.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Velleius Paterculus",
        "work": "Histoire romaine",
        "locus": "II, 117 à 119",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Velleius_Paterculus/2D*.html"
      },
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "LVI, 18 à 24",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/56*.html"
      },
      {
        "kind": "ancient",
        "author": "Tacite",
        "work": "Annales",
        "locus": "I, 60 à 62",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Tacitus/Annals/1D*.html"
      },
      {
        "kind": "ancient",
        "author": "Suétone",
        "work": "Vie d'Auguste",
        "locus": "23",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Suetonius/12Caesars/Augustus*.html"
      },
      {
        "kind": "modern",
        "author": "Peter S. Wells",
        "work": "The Battle That Stopped Rome (Norton, 2003)"
      },
      {
        "kind": "modern",
        "author": "Museum und Park Kalkriese",
        "work": "The Varus Battle",
        "url": "https://www.kalkriese-varusschlacht.de/en/the-varus-battle.html"
      }
    ]
  },
  {
    "id": "construction-du-pont-du-gard",
    "title": "Construction de l'aqueduc de Nîmes et du pont du Gard",
    "start": 40,
    "end": 60,
    "precision": "decade",
    "certainty": "attested",
    "certaintyNote": "Sans inscription de construction, l'ouvrage est daté par l'archéologie : céramique des couches de chantier, postérieure à l'époque augustéenne, et phases de la carrière de l'Estel. L'attribution traditionnelle à Agrippa, vers 19 av. J.-C., est abandonnée.",
    "era": "haut-empire",
    "track": "rome",
    "category": "building",
    "importance": 2,
    "placeId": "pont-du-gard",
    "summary": "Vers le milieu du Ier siècle apr. J.-C., Nemausus capte la source d'Eure, près d'Uzès, et l'amène jusqu'à la ville par un aqueduc d'environ 50 km. Pour franchir le Gardon, les bâtisseurs élèvent en quelques années le pont du Gard, trois rangs d'arches superposés hauts de 48,77 mètres.",
    "body": "Le chantier de l'aqueduc dure près de quinze ans, de 40 à 60 environ selon le site du Pont du Gard. Le canal maçonné et couvert, enterré sur 90 % de son parcours, suit le relief avec une pente moyenne de 24 à 25 centimètres par kilomètre : entre la source d'Eure et le bassin de distribution (castellum) de Nîmes, il ne descend que d'un peu plus de 12 mètres. Il franchit les vallées par dix-sept ouvrages aériens et passe par trois tunnels.\n\nLe pont du Gard, bâti en cinq ans environ, superpose trois ponts de grand appareil posé presque entièrement à sec : six arches au premier étage, dont la plus grande s'ouvre sur 24,50 mètres, onze au deuxième et quarante-sept petites arches au troisième, qui portent le canal couvert de dalles. Le calcaire coquillier vient de la carrière de l'Estel, quelques centaines de mètres en aval, et certains blocs pèsent jusqu'à 6 tonnes ; des pierres laissées en saillie servaient d'appui aux échafaudages.\n\nAucune inscription ne commémore les travaux : la date repose sur la céramique des couches de chantier et sur l'étude de la carrière. L'ancienne attribution à **Agrippa**, gendre d'Auguste, vers 19 av. J.-C., est aujourd'hui abandonnée. L'aqueduc livre en moyenne environ 20 000 mètres cubes d'eau par jour ; mal entretenu à partir du IIIe siècle, il est abandonné au début du VIe.",
    "sources": [
      {
        "kind": "modern",
        "author": "Site du Pont du Gard",
        "work": "Dossier de presse",
        "locus": "p. 4 à 6 et 14",
        "url": "https://pontdugard.fr/sites/default/files/2023-02/Dossier%20de%20presse%20Pont%20du%20Gard.pdf"
      },
      {
        "kind": "modern",
        "author": "Site du Pont du Gard",
        "work": "Le Pont du Gard (mémento)",
        "url": "https://pontdugard.fr/sites/default/files/2023-05/lepontdugard.pdf"
      },
      {
        "kind": "modern",
        "author": "Site du Pont du Gard",
        "work": "The monument",
        "url": "https://pontdugard.fr/en/discover/monument"
      },
      {
        "kind": "modern",
        "author": "M. Vacca-Goutoulli",
        "work": "Étude archéologique diachronique de la carrière de l'Estel sud, Archéologies. Sociétés, réseaux, matériaux 2, 2024",
        "url": "https://doi.org/10.46298/asrm.13671"
      }
    ],
    "scene": "pont-du-gard"
  },
  {
    "id": "incendie-de-rome",
    "title": "Le grand incendie de Rome",
    "start": 64,
    "month": 7,
    "day": 19,
    "precision": "day",
    "certainty": "attested",
    "era": "haut-empire",
    "track": "rome",
    "category": "society",
    "importance": 2,
    "placeId": "rome",
    "people": [
      "neron"
    ],
    "summary": "Le 19 juillet 64 apr. J.-C., un incendie éclate près du Grand Cirque et ravage Rome pendant six jours, puis reprend ailleurs. Sur les quatorze régions de la ville, trois sont rasées et sept presque entièrement détruites. Néron accuse les chrétiens et profite des terrains libérés pour bâtir la Domus Aurea.",
    "body": "Selon Tacite, le feu part de boutiques remplies de marchandises inflammables, dans la partie du Grand Cirque voisine du Palatin et du Caelius. Poussé par le vent, il progresse pendant six jours avant d'être arrêté au pied de l'Esquilin, puis repart dans d'autres quartiers. Des quatorze régions de Rome, quatre seulement restent intactes. Aucune source ne donne le nombre des victimes.\n\nNéron, alors à Antium, rentre à Rome et organise des secours. Mais la rumeur l'accuse d'avoir voulu l'incendie pour rebâtir la ville à sa gloire. Suétone et Dion Cassius reprennent cette accusation, tandis que Tacite laisse la question ouverte. Les historiens modernes y croient peu : les incendies étaient fréquents dans une ville dense, construite en partie en bois.\n\nSelon Tacite, Néron, pour détourner les soupçons, fait arrêter et supplicier des chrétiens : c'est traditionnellement la première persécution à Rome. Tacite est pourtant le seul à lier ces supplices à l'incendie, et certains historiens doutent que les victimes aient été visées en tant que chrétiens. Néron élève sur les terrains dévastés un immense palais, la Domus Aurea, et impose de nouvelles règles de construction : rues plus larges, portiques, matériaux moins inflammables.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Tacite",
        "work": "Annales",
        "locus": "XV, 38 à 44",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Tacitus/Annals/15B*.html"
      },
      {
        "kind": "ancient",
        "author": "Suétone",
        "work": "Vie de Néron",
        "locus": "38",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Suetonius/12Caesars/Nero*.html"
      },
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "LXII, 16 à 18",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/62*.html"
      },
      {
        "kind": "modern",
        "author": "Anthony A. Barrett",
        "work": "Rome Is Burning. Nero and the Fire That Ended a Dynasty (Princeton University Press, 2020)"
      },
      {
        "kind": "modern",
        "author": "Edward Champlin",
        "work": "Nero (Harvard University Press, 2003)"
      },
      {
        "kind": "modern",
        "author": "Brent D. Shaw",
        "work": "« The Myth of the Neronian Persecution », Journal of Roman Studies, 105 (2015)"
      }
    ]
  },
  {
    "id": "annee-des-quatre-empereurs",
    "title": "L'année des quatre empereurs",
    "start": 69,
    "precision": "year",
    "certainty": "attested",
    "era": "haut-empire",
    "track": "rome",
    "category": "politics",
    "importance": 2,
    "placeId": "rome",
    "people": [
      "galba",
      "othon",
      "vitellius",
      "vespasien"
    ],
    "summary": "Après le suicide de Néron en juin 68 apr. J.-C., quatre empereurs se succèdent en 69 apr. J.-C. : Galba, Othon, Vitellius et Vespasien, chacun porté par des armées. Cette guerre civile révèle, selon Tacite, qu'un empereur peut être fait ailleurs qu'à Rome. Vespasien, vainqueur, fonde la dynastie flavienne.",
    "body": "La mort de Néron éteint la dynastie julio-claudienne. Galba, proclamé en Hispanie, est tué à Rome le 15 janvier 69 apr. J.-C. par les prétoriens ralliés à Othon. Les légions de Germanie ont déjà acclamé leur légat Vitellius ; vaincu à Bédriac, Othon se suicide en avril.\n\nLe 1er juillet, les légions d'Égypte, puis celles de Judée et de Syrie, proclament Vespasien, qui mène alors la guerre contre la révolte juive. Ses partisans des armées du Danube battent les vitelliens près de Crémone, puis prennent Rome, où Vitellius est tué en décembre. Le temple de Jupiter Capitolin brûle pendant les combats.\n\nTacite, dont les *Histoires* sont la source principale, tire la leçon de l'année : le pouvoir impérial dépend désormais des armées provinciales. Vespasien rétablit l'ordre et les finances, et sa dynastie règne jusqu'en 96 apr. J.-C.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Tacite",
        "work": "Histoires",
        "locus": "I, 4 et I, 27",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Tacitus/Histories/1A*.html"
      },
      {
        "kind": "ancient",
        "author": "Suétone",
        "work": "Vie de Galba",
        "locus": "19 et 20",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Suetonius/12Caesars/Galba*.html"
      },
      {
        "kind": "ancient",
        "author": "Suétone",
        "work": "Vie de Vespasien",
        "locus": "6",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Suetonius/12Caesars/Vespasian*.html"
      },
      {
        "kind": "modern",
        "author": "Gwyn Morgan",
        "work": "69 A.D. The Year of Four Emperors (Oxford University Press, 2006)"
      },
      {
        "kind": "modern",
        "author": "Bowman, Champlin et Lintott (dir.)",
        "work": "The Cambridge Ancient History, vol. X : The Augustan Empire (2e éd., 1996)",
        "locus": "chap. 6, T. Wiedemann, « From Nero to Vespasian »"
      }
    ]
  },
  {
    "id": "eruption-du-vesuve",
    "title": "L'éruption du Vésuve",
    "start": 79,
    "precision": "year",
    "certainty": "debated",
    "certaintyNote": "Le 24 août, transmis par la plupart des manuscrits de Pline le Jeune, est contesté au profit de la fin octobre 79 apr. J.-C. (vers le 24 octobre), sans preuve décisive à ce jour.",
    "era": "haut-empire",
    "track": "rome",
    "category": "society",
    "importance": 2,
    "placeId": "pompei",
    "people": [
      "pline-l-ancien",
      "pline-le-jeune",
      "titus"
    ],
    "summary": "En 79 apr. J.-C., le Vésuve entre en éruption et ensevelit Pompéi, Herculanum, Stabies et d'autres localités de Campanie. Pline le Jeune en a laissé le seul récit de témoin oculaire. La date traditionnelle du 24 août est aujourd'hui discutée, de nombreux chercheurs préférant la fin octobre.",
    "body": "Le volcan, endormi depuis des siècles malgré un fort séisme en 62 ou 63 apr. J.-C., projette d'abord une haute colonne de cendres et de ponces, puis des nuées ardentes dévalent ses pentes. Pompéi disparaît sous plusieurs mètres de dépôts, Herculanum sous une couche bien plus épaisse. Les fouilles ont livré les restes de plus d'un millier de victimes à Pompéi et de plus de 300 à Herculanum, mais le bilan total reste inconnu.\n\nPline l'Ancien, naturaliste et commandant de la flotte de Misène, part par mer porter secours et meurt sur le rivage de Stabies. Son neveu Pline le Jeune, alors âgé de 17 ans, raconte l'événement des années plus tard dans deux lettres à Tacite. L'empereur Titus envoie des commissaires pour aider la Campanie sinistrée.\n\nLa date pose problème. La plupart des manuscrits de Pline donnent le 24 août, mais la tradition manuscrite varie, et Dion Cassius, qui écrit plus d'un siècle après, place l'éruption à la toute fin de l'été. En 2018, une inscription au charbon datée du 17 octobre, découverte à Pompéi dans une maison en travaux, a renforcé l'hypothèse d'une éruption vers le 24 octobre, déjà suggérée par des indices saisonniers (fruits d'automne, vin déjà mis en jarres). L'inscription ne porte pas d'année : le débat reste ouvert.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Pline le Jeune",
        "work": "Lettres",
        "locus": "VI, 16 et VI, 20",
        "url": "https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.02.0139:book=6:letter=16"
      },
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "LXVI, 21 à 24",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/66*.html"
      },
      {
        "kind": "ancient",
        "author": "Suétone",
        "work": "Vie de Titus",
        "locus": "8, 3 et 4",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Suetonius/12Caesars/Titus*.html"
      },
      {
        "kind": "modern",
        "author": "Domenico M. Doronzo et al.",
        "work": "« The 79 CE eruption of Vesuvius: A lesson from the past and the need of a multidisciplinary approach for developments in volcanology », Earth-Science Reviews, 231 (2022)",
        "url": "https://ingv.it/en/urp-press/Press-office/Press-releases/vesuvio-revealed-ancient-mysteries-of-the-eruption-of-79-dc"
      }
    ],
    "scene": "pompei"
  },
  {
    "id": "inauguration-du-colisee",
    "title": "Inauguration du Colisée",
    "start": 80,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "La capacité de l'amphithéâtre est incertaine : environ 50 000 spectateurs selon les estimations courantes, certaines allant plus haut.",
    "era": "haut-empire",
    "track": "rome",
    "category": "building",
    "importance": 2,
    "placeId": "colisee",
    "people": [
      "titus",
      "vespasien"
    ],
    "summary": "En 80 apr. J.-C., Titus inaugure par des jeux de cent jours l'amphithéâtre flavien, que l'on appellera plus tard Colisée. Commencé par son père Vespasien sur l'emplacement du bassin de la Domus Aurea de Néron, il peut accueillir sans doute environ 50 000 spectateurs. Domitien en achève l'aménagement.",
    "body": "Vespasien lance le chantier entre 70 et 72 apr. J.-C. environ, sur le site du bassin artificiel de la Domus Aurea, rendant au peuple un espace que Néron s'était réservé. Une inscription restituée indique que la construction fut financée par le butin de la guerre de Judée. L'édifice elliptique, d'environ 188 mètres sur 156, associe travertin, tuf, brique et béton romain.\n\nTitus l'inaugure en 80 apr. J.-C. Suétone parle de 5 000 bêtes sauvages montrées en un seul jour ; Dion Cassius, de 9 000 animaux tués et de cent jours de spectacles, dont des combats navals. Ces chiffres, typiques des sources antiques, sont sans doute gonflés. Domitien complète ensuite le monument, notamment les souterrains de l'arène.\n\nLe nom de « Colisée » n'apparaît qu'au Moyen Âge, probablement d'après la statue colossale de Néron qui se dressait tout près. Les Romains disaient simplement *amphitheatrum*.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Suétone",
        "work": "Vie de Titus",
        "locus": "7, 3",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Suetonius/12Caesars/Titus*.html"
      },
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "LXVI, 25",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/66*.html"
      },
      {
        "kind": "modern",
        "author": "Keith Hopkins et Mary Beard",
        "work": "The Colosseum (Profile Books, 2005)"
      },
      {
        "kind": "modern",
        "author": "Bowman, Garnsey et Rathbone (dir.)",
        "work": "The Cambridge Ancient History, vol. XI : The High Empire (2e éd., 2000)"
      }
    ],
    "scene": "colisee"
  },
  {
    "id": "amphitheatre-de-nimes",
    "title": "Construction de l'amphithéâtre de Nîmes",
    "start": 100,
    "precision": "decade",
    "certainty": "debated",
    "certaintyNote": "Une monnaie probablement frappée en 88 ou 89, retrouvée dans les fondations, et la datation radiocarbone des queues d'aronde placent le chantier entre les années 90 et 130 ; selon la Ville de Nîmes, Nerva (de 96 à 98) ne l'a pas vu achevé.",
    "era": "haut-empire",
    "track": "rome",
    "category": "building",
    "importance": 3,
    "placeId": "nimes",
    "summary": "Vers 100 apr. J.-C., une vingtaine d'années après le Colisée, Nemausus se dote d'un amphithéâtre elliptique de 133 mètres sur 101, prévu pour environ 22 000 spectateurs. Bien conservé, il accueille encore aujourd'hui des spectacles.",
    "body": "L'édifice suit le modèle du Colisée : une façade de 21 mètres de haut, faite de deux étages de soixante arcades et d'un attique, enveloppe trente-quatre rangées de gradins réparties en quatre zones (*maeniana*). Galeries, escaliers et vomitoires distribuent un public placé selon son rang social ; au sommet, des consoles recevaient les mâts du *velum*, la toile tendue au-dessus des gradins. Sous la piste, longue de 68 mètres et large de 38, s'étendent des galeries et une salle en forme de croix.\n\nLe chantier est daté par l'archéologie. Une monnaie probablement frappée en 88 ou 89, sans doute perdue au début des années 90, a été retrouvée dans les fondations, et la datation radiocarbone des doubles queues d'aronde montre que la construction est antérieure à 130. Selon la Ville de Nîmes, l'empereur Nerva, qui règne de 96 à 98, ne l'a pas vu achevé.\n\nDes inscriptions du podium réservaient des places à des corporations, dont quarante aux bateliers du Rhône et de la Saône. À l'époque wisigothique, l'amphithéâtre devient une forteresse, puis un village fortifié qui compte jusqu'à 150 maisons ; son dégagement, décidé en 1786, commence en 1809. Sa capacité, estimée à 22 000 places par le Musée de la Romanité, varie selon les sources.",
    "sources": [
      {
        "kind": "modern",
        "author": "Musée de la Romanité",
        "work": "Dossier pédagogique sur l'architecture publique",
        "locus": "p. 12 à 15",
        "url": "https://museedelaromanite.fr/content/uploads/2021/08/DOSSIER-PEDAGOGIQUE-ARCHI-PUBLIQUE-bd.pdf"
      },
      {
        "kind": "modern",
        "author": "Ville de Nîmes",
        "work": "Webdocumentaire des Arènes : When was the amphitheater built?",
        "url": "https://arenes-webdoc.nimes.fr/en/construction/build/in-all-its-splendor/when-was-the-amphitheater-built"
      },
      {
        "kind": "modern",
        "author": "Ville de Nîmes",
        "work": "Webdocumentaire des Arènes : Seating spectators",
        "url": "https://arenes-webdoc.nimes.fr/en/construction/design/terms-of-the-contract/seating-spectators/"
      },
      {
        "kind": "modern",
        "author": "Ministère de la Culture et Inrap",
        "work": "Communiqué de presse sur la fouille de la salle cruciforme, 5 mars 2020",
        "url": "https://www.culture.gouv.fr/Media/Medias-creation-rapide/Communique-de-presse5"
      }
    ],
    "scene": "nimes"
  },
  {
    "id": "pantheon-d-hadrien",
    "title": "Le Panthéon d'Hadrien",
    "start": 113,
    "end": 125,
    "precision": "decade",
    "certainty": "debated",
    "certaintyNote": "Les estampilles des briques suggèrent un début des travaux sous Trajan, entre 113 et 118 environ, et un achèvement sous Hadrien, entre 125 et 128 environ.",
    "era": "haut-empire",
    "track": "rome",
    "category": "building",
    "importance": 2,
    "placeId": "pantheon",
    "people": [
      "hadrien",
      "trajan"
    ],
    "summary": "Le Panthéon actuel remplace le temple élevé par Agrippa entre 27 et 25 av. J.-C., endommagé par des incendies. Commencé sans doute sous Trajan et achevé sous Hadrien vers 125, il est couvert d'une coupole de béton d'environ 43 mètres de diamètre, percée d'un oculus. Hadrien y fit réinscrire le nom d'Agrippa.",
    "body": "Le premier Panthéon fut construit par Marcus Agrippa, gendre d'Auguste, entre 27 et 25 av. J.-C. Endommagé par des incendies, notamment celui de 80 apr. J.-C., il est entièrement rebâti au début du IIe siècle. La plupart des estampilles de briques datent de la fin du règne de Trajan, ce qui fait penser que le chantier commença sous lui ; l'édifice est achevé et dédié sous Hadrien, entre 125 et 128 environ. Selon l'*Histoire Auguste*, Hadrien restaurait les monuments au nom de leurs premiers bâtisseurs : la façade porte toujours M. AGRIPPA L. F. COS. TERTIVM FECIT.\n\nLe bâtiment associe un porche à colonnes monolithes de granit égyptien et une rotonde couverte d'une coupole hémisphérique en béton de 150 pieds romains, soit environ 43 mètres de diamètre, autant que la hauteur intérieure. Les constructeurs ont allégé le béton vers le sommet (pierre ponce, tuf) et creusé des caissons. L'oculus, large d'environ 9 mètres, est la seule source de lumière.\n\nSa fonction exacte reste discutée : temple de tous les dieux, lieu de culte dynastique, salle d'audience (Dion Cassius rapporte qu'Hadrien y rendait la justice). Dion lui-même hésite sur l'origine de son nom. Transformé en église en 609, c'est l'un des monuments antiques les mieux conservés de Rome.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "LIII, 27, 2 et 3",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/53*.html"
      },
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "LXVI, 24, 2",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/66*.html"
      },
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "LXIX, 7, 1",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/69*.html"
      },
      {
        "kind": "ancient",
        "author": "Histoire Auguste",
        "work": "Vie d'Hadrien",
        "locus": "19, 9 et 10",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Historia_Augusta/Hadrian/2*.html"
      },
      {
        "kind": "modern",
        "author": "Lise M. Hetland",
        "work": "« Dating the Pantheon », Journal of Roman Archaeology, 20 (2007)"
      },
      {
        "kind": "modern",
        "author": "Tod A. Marder et Mark Wilson Jones (dir.)",
        "work": "The Pantheon. From Antiquity to the Present (Cambridge University Press, 2015)",
        "locus": "chapitre de L. M. Hetland, « New Perspectives on the Dating of the Pantheon »"
      }
    ],
    "scene": "pantheon"
  },
  {
    "id": "apogee-de-l-empire",
    "title": "Mort de Trajan : l'Empire à son apogée",
    "start": 117,
    "month": 8,
    "precision": "month",
    "certainty": "attested",
    "certaintyNote": "Le jour exact de la mort de Trajan est discuté (du 7 au 9 août selon les historiens), et l'extension maximale de 116 et 117 fut éphémère en Mésopotamie.",
    "era": "haut-empire",
    "track": "rome",
    "category": "politics",
    "importance": 1,
    "placeId": "selinonte-de-cilicie",
    "people": [
      "trajan",
      "hadrien"
    ],
    "summary": "Trajan meurt en août 117 à Sélinonte de Cilicie, au retour de sa guerre contre les Parthes. Avec la Dacie, l'Arabie, l'Arménie et la Mésopotamie, l'Empire atteint alors sa plus grande extension. Son successeur Hadrien abandonne aussitôt les conquêtes orientales, jugées intenables, et fixe la frontière sur l'Euphrate.",
    "body": "Empereur depuis 98 apr. J.-C., Trajan a conquis la Dacie en deux guerres (achevées en 106) et annexé la même année l'Arabie nabatéenne. De 114 à 116, il occupe l'Arménie puis la Mésopotamie, prend Ctésiphon, la capitale parthe, et atteint le golfe Persique. Eutrope affirme qu'il créa trois provinces : Arménie, Assyrie et Mésopotamie.\n\nCes conquêtes restent fragiles : la Mésopotamie se soulève, et des révoltes juives éclatent en Égypte, en Cyrénaïque et à Chypre (de 115 à 117). Malade, Trajan reprend la route de l'Italie et meurt à Sélinonte, en Cilicie, selon Dion Cassius (Eutrope parle de Séleucie d'Isaurie). D'après l'*Histoire Auguste*, Hadrien, gouverneur de Syrie, apprend son adoption le 9 août et la mort de Trajan le 11 août, et se fait aussitôt reconnaître empereur.\n\nHadrien renonce à l'Arménie, à l'Assyrie et à la Mésopotamie. L'extension maximale de 117 fut donc brève ; l'idée d'« apogée » de l'Empire, au sens d'une paix et d'une prospérité durables, s'applique plutôt à l'ensemble du IIe siècle, celui des Antonins.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "LXVIII, 17 à 33",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/68*.html"
      },
      {
        "kind": "ancient",
        "author": "Eutrope",
        "work": "Abrégé d'histoire romaine",
        "locus": "VIII, 3 à 6",
        "url": "https://www.thelatinlibrary.com/eutropius/eutropius8.shtml"
      },
      {
        "kind": "ancient",
        "author": "Histoire Auguste",
        "work": "Vie d'Hadrien",
        "locus": "4, 6 et 7",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Historia_Augusta/Hadrian/1*.html"
      },
      {
        "kind": "modern",
        "author": "Julian Bennett",
        "work": "Trajan. Optimus Princeps (Routledge, 1997)"
      },
      {
        "kind": "modern",
        "author": "Dietmar Kienast, Werner Eck et Matthäus Heil",
        "work": "Römische Kaisertabelle (6e éd., 2017)",
        "locus": "Traianus"
      },
      {
        "kind": "modern",
        "author": "Herbert W. Benario",
        "work": "De Imperatoribus Romanis, notice « Trajan »",
        "url": "https://roman-emperors.sites.luc.edu/trajan.htm"
      }
    ]
  },
  {
    "id": "construction-cirque-arles",
    "title": "Construction du cirque d'Arles",
    "start": 149,
    "end": 150,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "Date établie par la dendrochronologie des pieux de fondation, dont les arbres ont été abattus durant l'hiver de 148 à 149.",
    "era": "haut-empire",
    "track": "rome",
    "category": "building",
    "importance": 3,
    "placeId": "arles",
    "summary": "En 149 et 150, sous Antonin le Pieux, Arles se dote hors de ses murs, au bord du Rhône, d'un cirque d'environ 450 mètres de long pour les courses de chars. Ses fondations reposent sur plus de 30 000 pieux, taillés dans des arbres abattus durant l'hiver de 148 à 149.",
    "body": "Le cirque s'élève au sud-ouest de la ville, hors les murs, sur un terrain marécageux en bordure du fleuve. Pour l'asseoir, les bâtisseurs creusent des tranchées de fondation de 2,60 mètres sur 1,20 et y plantent plus de 30 000 pieux de chêne et de résineux, longs de 2 à 3,5 mètres, associés à du gravier et à un blocage.\n\nL'étude des cernes de ce bois, la dendrochronologie, date le chantier avec une rare précision : les arbres ont été abattus durant l'hiver de 148 à 149, et la construction se place en 149 et 150. L'édifice mesure environ 450 mètres sur 101 et peut accueillir environ 20 000 spectateurs. Ses gradins reposent sur des voûtes ouvertes vers l'extérieur par des arcades ; au milieu de la piste, la *spina*, ornée de statues et de bassins, se termine à chaque extrémité par des bornes (*metae*).\n\nLe monument est remanié au IVe siècle, époque où la *spina* reçoit aussi un placage de marbre et un obélisque, puis démantelé vers le milieu du VIe siècle. Une partie des fondations est visible devant le musée départemental Arles antique ; l'extrémité de la piste et les stalles de départ, jamais fouillées, se trouvent sous l'autoroute et le quartier de la Roquette.",
    "sources": [
      {
        "kind": "modern",
        "author": "Musée départemental Arles antique",
        "work": "Dossier pédagogique Urbanisme et romanisation, fiche Le cirque romain d'Arles"
      },
      {
        "kind": "modern",
        "author": "Musée départemental Arles antique",
        "work": "Dossier enseignant Jean-Claude Golvin, 2011",
        "locus": "p. 13",
        "url": "https://www.arretetonchar.fr/wp-content/uploads/2024/10/Arles-MDAA-13-Dossier-enseignant-Jean-Claude-Golvin-2011.pdf"
      },
      {
        "kind": "modern",
        "author": "Ministère de la Culture",
        "work": "Base Mérimée, notice PA00081516 : Cirque romain de la presqu'île",
        "url": "https://pop.culture.gouv.fr/notice/merimee/PA00081516"
      },
      {
        "kind": "modern",
        "author": "Site régional du tourisme Provence-Alpes-Côte d'Azur",
        "work": "Le cirque romain, Arles",
        "url": "https://provence-alpes-cotedazur.com/que-faire/culture-et-patrimoine/lieux/le-cirque-romain-arles-fr-2890827/"
      }
    ],
    "scene": "arles"
  },
  {
    "id": "edit-de-caracalla",
    "title": "L'édit de Caracalla",
    "start": 212,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "L'année 212 est la plus probable (premier semestre selon A. Besson, 11 juillet selon une lecture du papyrus de Giessen par P. van Minnen), mais quelques historiens ont jugé cette date moins sûre et envisagé une date un peu plus tardive.",
    "era": "haut-empire",
    "track": "rome",
    "category": "society",
    "importance": 2,
    "placeId": "rome",
    "people": [
      "caracalla"
    ],
    "summary": "En 212, l'empereur Caracalla accorde la citoyenneté romaine à presque tous les habitants libres de l'Empire par la Constitution antonine. Dion Cassius y voit surtout un moyen d'augmenter les impôts payés par les seuls citoyens. La mesure efface une distinction juridique séculaire entre citoyens et pérégrins.",
    "body": "La décision est connue par une brève mention de Dion Cassius, par une phrase du juriste Ulpien conservée dans le *Digeste* (ceux qui vivent dans le monde romain sont devenus citoyens par une constitution de l'empereur Antonin) et par un papyrus grec mutilé conservé à Giessen, qui en garde sans doute le texte. Caracalla portait officiellement le nom de Marc Aurèle Antonin, d'où le nom de « Constitution antonine ».\n\nDion Cassius, hostile à l'empereur, y voit une manœuvre fiscale : seuls les citoyens payaient les taxes sur les successions et les affranchissements, que Caracalla avait portées de 5 à 10 %. Les historiens avancent aussi d'autres motifs : piété envers les dieux, volonté d'unifier l'Empire, besoins de l'armée.\n\nLes effets se lisent dans les inscriptions et les papyrus, où les nouveaux citoyens prennent en masse le nom d'Aurelius. Le texte exclut une catégorie, les *dediticii*, dont l'identité reste débattue. La citoyenneté perd peu à peu sa valeur de privilège, au profit d'autres distinctions sociales, entre *honestiores* et *humiliores*.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Dion Cassius",
        "work": "Histoire romaine",
        "locus": "LXXVIII, 9, 4 et 5 (numérotation Loeb ; LXXVII, 9 dans l'édition Boissevain)",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Cassius_Dio/78*.html"
      },
      {
        "kind": "ancient",
        "author": "Ulpien",
        "work": "Digeste",
        "locus": "I, 5, 17",
        "url": "https://www.thelatinlibrary.com/justinian/digest1.shtml"
      },
      {
        "kind": "modern",
        "author": "Arnaud Besson",
        "work": "Constitutio Antoniniana. L'universalisation de la citoyenneté romaine au 3e siècle (Schwabe, 2020)"
      },
      {
        "kind": "modern",
        "author": "Le Glay, Voisin et Le Bohec",
        "work": "Histoire romaine (PUF)"
      }
    ]
  },
  {
    "id": "assassinat-de-severe-alexandre",
    "title": "Assassinat de Sévère Alexandre",
    "start": 235,
    "month": 3,
    "precision": "month",
    "certainty": "attested",
    "certaintyNote": "Le mois de mars 235 est admis, mais le jour exact et le lieu précis, près de Mayence, restent incertains.",
    "era": "crise-du-iiie-siecle",
    "track": "rome",
    "category": "politics",
    "importance": 2,
    "placeId": "mayence",
    "people": [
      "severe-alexandre",
      "julia-mamaea",
      "maximin-le-thrace"
    ],
    "summary": "En mars 235, près de Mayence, des soldats tuent l'empereur Sévère Alexandre et sa mère Julia Mamaea, et proclament Maximin le Thrace. La mort du dernier des Sévères ouvre un demi-siècle de guerres sur plusieurs frontières et de successions rapides, appelé « crise du IIIe siècle ».",
    "body": "Empereur à 13 ans en 222, Sévère Alexandre gouverne sous l'influence de sa mère, Julia Mamaea. Après une campagne coûteuse et peu concluante contre les Perses sassanides, il rejoint le Rhin, menacé par des peuples germaniques. Son choix de négocier et d'acheter la paix plutôt que de combattre mécontente les soldats.\n\nSelon Hérodien, les recrues proclament empereur Maximin, un officier d'origine thrace sorti du rang, puis des émissaires tuent Alexandre et sa mère dans leurs quartiers. L'*Histoire Auguste* et Aurelius Victor placent la scène dans un village nommé Sicilia, qu'ils situent en Bretagne : sans doute une confusion, car tout indique les environs de Mayence (Mogontiacum).\n\nMaximin, un simple chevalier, ne vient jamais à Rome pendant son règne. Les historiens font commencer ici la « crise du IIIe siècle », parfois appelée « anarchie militaire » : de 235 à 284, plus d'une vingtaine d'empereurs reconnus se succèdent, sans compter les usurpateurs, et la plupart meurent de mort violente.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Hérodien",
        "work": "Histoire des empereurs romains",
        "locus": "VI, 8 et 9",
        "url": "https://remacle.org/bloodwolf/historiens/herodien/livre6.htm"
      },
      {
        "kind": "ancient",
        "author": "Histoire Auguste",
        "work": "Vie de Sévère Alexandre",
        "locus": "59 à 61",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Historia_Augusta/Severus_Alexander/3*.html"
      },
      {
        "kind": "ancient",
        "author": "Aurelius Victor",
        "work": "Livre des Césars",
        "locus": "24, 4",
        "url": "https://www.thelatinlibrary.com/victor.caes.html"
      },
      {
        "kind": "modern",
        "author": "Michel Christol",
        "work": "L'Empire romain du IIIe siècle. Histoire politique (Errance, 1997)"
      },
      {
        "kind": "modern",
        "author": "Bowman, Garnsey et Cameron (dir.)",
        "work": "The Cambridge Ancient History, vol. XII : The Crisis of Empire (2e éd., 2005)"
      }
    ]
  },
  {
    "id": "bataille-d-abritus",
    "title": "Abritus : un empereur tué par les Goths",
    "start": 251,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "La bataille a lieu à l'été 251, en juin ou au début de juillet selon les chronologies modernes ; les effectifs et les pertes ne sont pas connus.",
    "era": "crise-du-iiie-siecle",
    "track": "rome",
    "category": "war",
    "importance": 2,
    "placeId": "abritus",
    "people": [
      "dece",
      "cniva"
    ],
    "summary": "En 251, près d'Abritus, en Mésie inférieure (actuelle Bulgarie), l'empereur Dèce et son fils Herennius Etruscus périssent face aux Goths de Cniva. C'est la première mort certaine d'un empereur romain au combat contre un ennemi extérieur. La défaite montre la pression nouvelle des peuples installés au nord du Danube.",
    "body": "Dèce, empereur depuis 249, connu aussi pour avoir exigé de tous les habitants un sacrifice aux dieux, ce qui frappa durement les chrétiens, affronte des Goths qui ravagent les Balkans sous la conduite de Cniva. Après plusieurs revers, dont la prise de Philippopolis par les Goths, il tente d'intercepter les envahisseurs qui repartent chargés de butin.\n\nSelon Zosime, l'armée romaine est attirée dans un marais où les Goths l'enveloppent, et Trébonien Galle, qui succède à Dèce, aurait trahi l'empereur. Jordanès raconte que le fils de Dèce tombe d'abord, frappé d'une flèche, puis que l'empereur, cerné par les Goths près d'Abritus, cité de Mésie, y trouve la mort. Aurelius Victor parle lui aussi d'une trahison. Lactance, qui nomme les Carpes et non les Goths, affirme que le corps de l'empereur resta sans sépulture.\n\nEn 2016, des archéologues bulgares ont localisé un champ de bataille probable près du village de Dryanovets, à une quinzaine de kilomètres de Razgrad, l'antique Abritus, grâce à des armes et des monnaies. La mort de Gordien III face aux Perses, en 244, reste discutée, car les sources romaines parlent d'un meurtre : Dèce est donc le premier empereur dont la mort au combat contre un ennemi extérieur est certaine.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Zosime",
        "work": "Histoire nouvelle",
        "locus": "I, 23",
        "url": "https://www.livius.org/sources/content/zosimus/zosimus-new-history-1/zosimus-new-history-1.23/"
      },
      {
        "kind": "ancient",
        "author": "Jordanès",
        "work": "Getica",
        "locus": "XVIII, 101 à 103",
        "url": "https://www.thelatinlibrary.com/iordanes1.html"
      },
      {
        "kind": "ancient",
        "author": "Aurelius Victor",
        "work": "Livre des Césars",
        "locus": "29, 4 et 5",
        "url": "https://www.thelatinlibrary.com/victor.caes.html"
      },
      {
        "kind": "ancient",
        "author": "Lactance",
        "work": "De la mort des persécuteurs",
        "locus": "4",
        "url": "https://remacle.org/bloodwolf/eglise/lactance/persecuteurs.htm"
      },
      {
        "kind": "modern",
        "author": "David S. Potter",
        "work": "The Roman Empire at Bay (Routledge, 2004)"
      },
      {
        "kind": "modern",
        "author": "Michel Christol",
        "work": "L'Empire romain du IIIe siècle. Histoire politique (Errance, 1997)"
      },
      {
        "kind": "modern",
        "author": "BNT (télévision nationale bulgare)",
        "work": "« Bulgarian archaeologists found the site of a Roman Empire historic battle » (10 août 2016)",
        "url": "https://bntnews.bg/news/bulgarian-archaeologists-found-the-site-of-a-roman-empire-historic-battle-1315001news.html"
      }
    ]
  },
  {
    "id": "capture-de-valerien",
    "title": "Valérien capturé par Shapur Ier",
    "start": 260,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "La capture date de 260 (printemps ou été) pour la plupart des historiens, quelques-uns ayant proposé 259.",
    "era": "crise-du-iiie-siecle",
    "track": "rome",
    "category": "war",
    "importance": 1,
    "placeId": "edesse",
    "people": [
      "valerien",
      "shapur-ier",
      "gallien"
    ],
    "summary": "En 260, près d'Édesse, l'empereur Valérien est vaincu et fait prisonnier par le roi perse Shapur Ier : pour la première fois, un empereur romain tombe vivant aux mains d'un ennemi. Il meurt en captivité. Le choc ouvre la voie aux sécessions de la Gaule et de l'Orient palmyrénien.",
    "body": "Valérien règne depuis 253 avec son fils Gallien, à qui il a confié l'Occident, tandis que lui-même défend l'Orient contre la Perse sassanide. Son armée est affaiblie par une épidémie. Près d'Édesse, en Mésopotamie, il est capturé : au cours d'une grande bataille livrée au-delà de Carrhes et d'Édesse selon l'inscription de Shapur, lors d'une entrevue destinée à négocier selon Zosime.\n\nShapur Ier célèbre sa victoire dans une longue inscription trilingue (moyen-perse, parthe et grec) gravée sur la Ka'ba-ye Zardosht, à Naqsh-e Rostam, et dans des reliefs rupestres où l'empereur romain apparaît soumis. De nombreux prisonniers romains sont déportés et installés en Perse.\n\nLa fin de Valérien a nourri des récits invérifiables : l'auteur chrétien Lactance, qui y voit un châtiment divin pour ses persécutions, raconte que Shapur se servait de lui comme marchepied et fit exposer sa peau après sa mort. La date et les circonstances réelles de sa mort sont inconnues.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Shapur Ier",
        "work": "Res Gestae Divi Saporis (inscription trilingue de la Ka'ba-ye Zardosht, Naqsh-e Rostam), trad. anglaise de R. N. Frye",
        "locus": "récit de la troisième campagne (lignes 9 à 11 de la traduction)",
        "url": "http://web.archive.org/web/20180830174154/https://www.colorado.edu/classics/clas4091/Text/Shapur.htm"
      },
      {
        "kind": "ancient",
        "author": "Zosime",
        "work": "Histoire nouvelle",
        "locus": "I, 36",
        "url": "https://www.livius.org/sources/content/zosimus/zosimus-new-history-1/zosimus-new-history-1.36/"
      },
      {
        "kind": "ancient",
        "author": "Lactance",
        "work": "De la mort des persécuteurs",
        "locus": "5",
        "url": "https://remacle.org/bloodwolf/eglise/lactance/persecuteurs.htm"
      },
      {
        "kind": "ancient",
        "author": "Eutrope",
        "work": "Abrégé d'histoire romaine",
        "locus": "IX, 7",
        "url": "https://www.thelatinlibrary.com/eutropius/eutropius9.shtml"
      },
      {
        "kind": "modern",
        "author": "David S. Potter",
        "work": "The Roman Empire at Bay (Routledge, 2004)"
      },
      {
        "kind": "modern",
        "author": "Bowman, Garnsey et Cameron (dir.)",
        "work": "The Cambridge Ancient History, vol. XII : The Crisis of Empire (2e éd., 2005)"
      }
    ]
  },
  {
    "id": "empire-des-gaules",
    "title": "Postume fonde l'Empire des Gaules",
    "start": 260,
    "end": 274,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "La proclamation de Postume date sans doute de l'été ou de l'automne 260, et la fin de l'Empire des Gaules du début de 274.",
    "era": "crise-du-iiie-siecle",
    "track": "empire-des-gaules",
    "category": "politics",
    "importance": 2,
    "placeId": "cologne",
    "people": [
      "postume",
      "gallien",
      "tetricus-ier"
    ],
    "summary": "En 260, après la capture de Valérien, le gouverneur Postume est proclamé empereur par l'armée du Rhin et fait tuer à Cologne Saloninus, fils de Gallien. Il règne sur la Gaule et les Germanies, puis sur la Bretagne et l'Hispanie. Cet « Empire des Gaules » dure jusqu'à la reddition de Tétricus devant Aurélien, en 274.",
    "body": "Postume commande les troupes du Rhin quand, selon Zonaras, une querelle sur le partage d'un butin le pousse à la rébellion. Ses soldats le proclament Auguste ; il assiège Cologne, où résident le jeune César Saloninus et son tuteur Silvanus, obtient qu'on les lui livre et les fait mettre à mort. L'Hispanie et la Bretagne le reconnaissent dès 261.\n\nCe n'est pas un État gaulois indépendantiste : Postume se présente comme un empereur romain, avec ses propres consuls et sa monnaie, mais il ne marche pas sur Rome et se consacre à la défense du Rhin. L'expression « Empire des Gaules » est moderne ; les sources antiques, écrites du point de vue de Rome, parlent d'usurpateurs.\n\nPostume est tué par ses soldats à Mayence en 269. Lui succèdent Marius, Victorin, puis Tétricus, sans doute établi à Trèves. En 274, Aurélien affronte l'armée de Tétricus près de Châlons ; selon Eutrope, Tétricus trahit ses propres troupes et se rend. Il figure au triomphe d'Aurélien, puis reçoit un poste d'administrateur en Italie du Sud.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Zosime",
        "work": "Histoire nouvelle",
        "locus": "I, 38, 2",
        "url": "https://www.livius.org/sources/content/zosimus/zosimus-new-history-1/zosimus-new-history-1.38/"
      },
      {
        "kind": "ancient",
        "author": "Eutrope",
        "work": "Abrégé d'histoire romaine",
        "locus": "IX, 9 à 13",
        "url": "https://www.thelatinlibrary.com/eutropius/eutropius9.shtml"
      },
      {
        "kind": "ancient",
        "author": "Aurelius Victor",
        "work": "Livre des Césars",
        "locus": "33, 8 et 35, 3 à 5",
        "url": "https://www.thelatinlibrary.com/victor.caes.html"
      },
      {
        "kind": "ancient",
        "author": "Histoire Auguste",
        "work": "Les Trente Tyrans",
        "locus": "3",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Historia_Augusta/Tyranni_XXX*.html"
      },
      {
        "kind": "modern",
        "author": "John F. Drinkwater",
        "work": "The Gallic Empire (Historia Einzelschriften 52, Steiner, 1987)"
      },
      {
        "kind": "modern",
        "author": "Michel Polfer",
        "work": "De Imperatoribus Romanis, notice « Postumus »",
        "url": "https://roman-emperors.sites.luc.edu/postumus.htm"
      }
    ]
  },
  {
    "id": "royaume-de-palmyre",
    "title": "Zénobie et le royaume de Palmyre",
    "start": 270,
    "end": 273,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "L'invasion de l'Égypte se place en 270 (parfois 269) et la prise des titres impériaux en 271 ou 272.",
    "era": "crise-du-iiie-siecle",
    "track": "palmyre",
    "category": "politics",
    "importance": 2,
    "placeId": "palmyre",
    "people": [
      "zenobie",
      "odenath",
      "vaballath",
      "aurelien"
    ],
    "summary": "Veuve d'Odénath, Zénobie gouverne Palmyre au nom de son fils Vaballath et étend son pouvoir à l'Égypte, à l'Arabie et à une partie de l'Asie Mineure à partir de 270. Aurélien reprend ces territoires en 272 et capture la reine. Une nouvelle révolte, en 273, entraîne le sac de Palmyre.",
    "body": "Palmyre, riche cité caravanière de Syrie, prend une importance militaire avec Odénath, un notable palmyrénien devenu sénateur romain. Après la capture de Valérien en 260, il bat les Perses et sert Gallien, qui lui confie un commandement sur l'Orient ; il prend aussi le titre de « roi des rois ». Il est assassiné en 267 ou 268.\n\nSa veuve Zénobie exerce alors le pouvoir au nom de leur fils Vaballath. En 270, ses troupes conquièrent l'Égypte, puis une partie de l'Asie Mineure. D'abord prudente, elle fait frapper des monnaies associant Vaballath à l'empereur Aurélien ; puis, vers 272, Vaballath prend le titre d'Auguste et Zénobie celui d'Augusta, ce qui marque une rupture ouverte avec Rome.\n\nAurélien bat les Palmyréniens près d'Antioche puis devant Émèse, et assiège Palmyre en 272. Zénobie, en fuite vers la Perse, est capturée au bord de l'Euphrate. Une nouvelle révolte éclate en 273 ; Aurélien revient et la ville est saccagée. Les récits romains sur Zénobie, surtout dans l'*Histoire Auguste*, mêlent faits et inventions romanesques.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Zosime",
        "work": "Histoire nouvelle",
        "locus": "I, 39 et I, 44 à 61",
        "url": "https://www.livius.org/sources/content/zosimus/zosimus-new-history-1/zosimus-new-history-1.44/"
      },
      {
        "kind": "ancient",
        "author": "Histoire Auguste",
        "work": "Vie d'Aurélien",
        "locus": "22 à 31",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Historia_Augusta/Aurelian/2*.html"
      },
      {
        "kind": "ancient",
        "author": "Eutrope",
        "work": "Abrégé d'histoire romaine",
        "locus": "IX, 13",
        "url": "https://www.thelatinlibrary.com/eutropius/eutropius9.shtml"
      },
      {
        "kind": "modern",
        "author": "Udo Hartmann",
        "work": "Das palmyrenische Teilreich (Steiner, 2001)"
      },
      {
        "kind": "modern",
        "author": "Jacqueline F. Long",
        "work": "De Imperatoribus Romanis, notice « Zenobia »",
        "url": "https://roman-emperors.sites.luc.edu/zenobia.htm"
      },
      {
        "kind": "modern",
        "author": "Alaric Watson",
        "work": "Aurelian and the Third Century (Routledge, 1999)"
      }
    ]
  },
  {
    "id": "mur-d-aurelien",
    "title": "Le mur d'Aurélien",
    "start": 271,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "Le chantier commence en 271, ou pendant l'hiver de 271 à 272, et s'achève sous Probus (de 276 à 282) selon Zosime ; la date exacte de la fin des travaux est inconnue.",
    "era": "crise-du-iiie-siecle",
    "track": "rome",
    "category": "building",
    "importance": 2,
    "placeId": "rome",
    "people": [
      "aurelien",
      "probus"
    ],
    "summary": "En 271, après une invasion germanique qui a atteint l'Italie, Aurélien fait entourer Rome d'une nouvelle enceinte, la première depuis des siècles. Longue d'environ 19 kilomètres, elle est achevée sous Probus. Renforcée à plusieurs reprises, elle subsiste aujourd'hui sur une grande partie de son tracé.",
    "body": "Rome n'avait plus de véritable muraille : l'enceinte du IVe siècle av. J.-C., attribuée par la tradition au roi Servius Tullius, avait depuis longtemps été dépassée par la ville. Vers 270 et 271, des peuples germaniques (Juthunges, Alamans ou Marcomans selon les sources) pénètrent en Italie et battent Aurélien près de Plaisance avant d'être repoussés. L'empereur décide alors de protéger la capitale.\n\nLe mur, en béton parementé de briques, court sur environ 19 kilomètres. Haut à l'origine de 6 à 8 mètres environ, il est flanqué de tours carrées à intervalles réguliers et percé de portes sur les grandes voies. Pour aller vite, on y intègre des constructions existantes, comme la pyramide de Cestius.\n\nAurélien meurt en 275 avant la fin des travaux, que Zosime attribue à Probus. L'*Histoire Auguste* prête au circuit une longueur de près de 50 milles, un chiffre impossible. L'enceinte est surélevée et renforcée par la suite, notamment sous Honorius, au début du Ve siècle.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Zosime",
        "work": "Histoire nouvelle",
        "locus": "I, 49, 2",
        "url": "https://www.livius.org/sources/content/zosimus/zosimus-new-history-1/zosimus-new-history-1.49"
      },
      {
        "kind": "ancient",
        "author": "Aurelius Victor",
        "work": "Livre des Césars",
        "locus": "35, 7",
        "url": "https://www.thelatinlibrary.com/victor.caes.html"
      },
      {
        "kind": "ancient",
        "author": "Histoire Auguste",
        "work": "Vie d'Aurélien",
        "locus": "21, 9",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Historia_Augusta/Aurelian/2*.html"
      },
      {
        "kind": "ancient",
        "author": "Histoire Auguste",
        "work": "Vie d'Aurélien",
        "locus": "39, 2",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Historia_Augusta/Aurelian/3*.html"
      },
      {
        "kind": "ancient",
        "author": "Eutrope",
        "work": "Abrégé d'histoire romaine",
        "locus": "IX, 15",
        "url": "https://www.thelatinlibrary.com/eutropius/eutropius9.shtml"
      },
      {
        "kind": "modern",
        "author": "Hendrik W. Dey",
        "work": "The Aurelian Wall and the Refashioning of Imperial Rome (Cambridge University Press, 2011)"
      },
      {
        "kind": "modern",
        "author": "Christian Körner",
        "work": "De Imperatoribus Romanis, notice « Aurelian »",
        "url": "https://roman-emperors.sites.luc.edu/aurelian.htm"
      }
    ]
  },
  {
    "id": "avenement-de-diocletien",
    "title": "Avènement de Dioclétien",
    "start": 284,
    "month": 11,
    "day": 20,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Le jour se déduit des vicennales, fêtées le 20 novembre 303 selon Lactance ; le lieu de la proclamation, près de Nicomédie, est une reconstruction moderne.",
    "era": "bas-empire",
    "track": "rome",
    "category": "politics",
    "importance": 1,
    "placeId": "nicomedie",
    "people": [
      "diocletien",
      "numerien"
    ],
    "summary": "Le 20 novembre 284, l'armée revenue de la campagne contre les Perses proclame empereur Dioclès, un officier d'origine dalmate, qui prend le nom de Dioclétien. Vainqueur de Carin en 285, il règne jusqu'en 305 et engage les réformes qui ouvrent la période dite du Bas-Empire.",
    "body": "Au retour de l'expédition contre les Perses, le jeune empereur Numérien meurt dans des circonstances obscures ; on accuse son beau-père, le préfet du prétoire Aper. Réunis, semble-t-il, près de Nicomédie, en Bithynie, les généraux et les tribuns choisissent Dioclès, qui commande la garde rapprochée de l'empereur. Selon Aurélius Victor et Eutrope, il jure devant les soldats n'être pour rien dans la mort de Numérien, puis tue Aper de sa propre main.\n\nLa date se déduit de Lactance, qui fixe au 20 novembre (303) la fête des vingt ans de règne. Le nouvel empereur doit encore battre Carin, frère de Numérien, près de Margum, au confluent de la Morava et du Danube, en 285 pour rester seul maître de l'Empire.\n\nDioclétien gouverne plus de vingt ans, une durée exceptionnelle après les crises du IIIe siècle. Il associe d'autres empereurs au pouvoir, multiplie les provinces, renforce l'armée et l'administration, puis déclenche en 303 la dernière grande persécution contre les chrétiens. Il abdique le 1er mai 305.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Lactance",
        "work": "De la mort des persécuteurs",
        "locus": "17, 1 (date des vicennales)",
        "url": "https://remacle.org/bloodwolf/eglise/lactance/persecuteurs.htm"
      },
      {
        "kind": "ancient",
        "author": "Aurélius Victor",
        "work": "Livre des Césars",
        "locus": "39, 1 et 11 à 13",
        "url": "https://remacle.org/bloodwolf/historiens/aurelvictor/cesars.htm"
      },
      {
        "kind": "ancient",
        "author": "Eutrope",
        "work": "Abrégé d'histoire romaine",
        "locus": "IX, 19 et 20",
        "url": "https://remacle.org/bloodwolf/historiens/eutrope/livre9.htm"
      },
      {
        "kind": "modern",
        "author": "Timothy D. Barnes",
        "work": "Constantine and Eusebius (Harvard University Press, 1981)",
        "locus": "chap. 1, Diocletian and Maximian"
      },
      {
        "kind": "modern",
        "author": "Alan K. Bowman",
        "work": "The Cambridge Ancient History, vol. XII : The Crisis of Empire (2e éd., Cambridge University Press, 2005)",
        "locus": "chap. 3, Diocletian and the first tetrarchy",
        "url": "https://www.cambridge.org/core/books/cambridge-ancient-history/diocletian-and-the-first-tetrarchy-ad-284305/9C09DBBB93CC6D3FB4BE2F8E6FDDA96B"
      },
      {
        "kind": "modern",
        "author": "Monica Hellström",
        "work": "Oxford Classical Dictionary (édition numérique, Oxford University Press)",
        "locus": "entrée Diocletian",
        "url": "https://doi.org/10.1093/acrefore/9780199381135.013.2187"
      }
    ]
  },
  {
    "id": "tetrarchie",
    "title": "Naissance de la tétrarchie",
    "start": 293,
    "month": 3,
    "day": 1,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Le 1er mars est la date officielle de l'avènement des deux Césars (Panégyrique latin de 297, Lactance) ; certains historiens ont proposé une investiture effective plus tardive pour Galère, peut-être le 21 mai 293.",
    "era": "bas-empire",
    "track": "rome",
    "category": "politics",
    "importance": 2,
    "people": [
      "diocletien",
      "maximien",
      "galere",
      "constance-chlore"
    ],
    "summary": "Le 1er mars 293, Dioclétien et Maximien, les deux Augustes, se donnent chacun un César : Galère en Orient, Constance (dit Chlore) en Occident. Ce gouvernement à quatre, que les modernes appellent tétrarchie, doit défendre toutes les frontières à la fois sans diviser l'Empire.",
    "body": "Dès 285, Dioclétien a fait de Maximien son César, puis son égal avec le titre d'Auguste en 286. En 293, chaque Auguste reçoit un adjoint et successeur désigné : Galère auprès de Dioclétien, Constance auprès de Maximien. Selon Eutrope et Aurélius Victor, des mariages scellent le système : Constance épouse Théodora, belle-fille de Maximien, et Galère épouse Valeria, fille de Dioclétien (le mariage de Constance pourrait être antérieur à 293).\n\nLe mot « tétrarchie » est moderne. Ce n'est pas un partage juridique : lois et monnaies sont émises au nom des quatre princes, mais chacun a la charge d'une région et réside près des frontières qu'il protège, dans des villes comme Trèves, Milan, Sirmium ou Nicomédie. Lactance, hostile à Dioclétien, y voit surtout une multiplication des armées et des impôts.\n\nLe système tient tant que Dioclétien le domine. Après l'abdication des deux Augustes en 305, les fils écartés de la succession, Constantin (fils de Constance) et Maxence (fils de Maximien), le font éclater, et les guerres civiles ne s'achèvent qu'en 324.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Lactance",
        "work": "De la mort des persécuteurs",
        "locus": "7 ; 35, 4 (vicennales de Galère prévues un 1er mars)",
        "url": "https://remacle.org/bloodwolf/eglise/lactance/persecuteurs.htm"
      },
      {
        "kind": "ancient",
        "author": "Aurélius Victor",
        "work": "Livre des Césars",
        "locus": "39, 24 à 30",
        "url": "https://remacle.org/bloodwolf/historiens/aurelvictor/cesars.htm"
      },
      {
        "kind": "ancient",
        "author": "Eutrope",
        "work": "Abrégé d'histoire romaine",
        "locus": "IX, 22",
        "url": "https://remacle.org/bloodwolf/historiens/eutrope/livre9.htm"
      },
      {
        "kind": "modern",
        "author": "Alan K. Bowman",
        "work": "The Cambridge Ancient History, vol. XII : The Crisis of Empire (2e éd., Cambridge University Press, 2005)",
        "locus": "chap. 3, Diocletian and the first tetrarchy",
        "url": "https://www.cambridge.org/core/books/cambridge-ancient-history/diocletian-and-the-first-tetrarchy-ad-284305/9C09DBBB93CC6D3FB4BE2F8E6FDDA96B"
      },
      {
        "kind": "modern",
        "author": "Timothy D. Barnes",
        "work": "The New Empire of Diocletian and Constantine (Harvard University Press, 1982)"
      }
    ]
  },
  {
    "id": "bataille-du-pont-milvius",
    "title": "Bataille du pont Milvius",
    "start": 312,
    "month": 10,
    "day": 28,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Le 28 octobre est donné par le calendrier de 354 (evictio tyranni) ; Lactance rattache la bataille à l'anniversaire de l'avènement de Maxence, qu'il place le 27 octobre.",
    "era": "bas-empire",
    "track": "rome",
    "category": "war",
    "importance": 2,
    "placeId": "pont-milvius",
    "people": [
      "constantin-ier",
      "maxence"
    ],
    "summary": "Le 28 octobre 312, Constantin, venu de Gaule, bat Maxence au nord de Rome ; Maxence se noie dans le Tibre pendant la retraite. Constantin devient seul maître de l'Occident, et les auteurs chrétiens attribuent sa victoire à la protection du Dieu des chrétiens.",
    "body": "Fils de Constance, acclamé par ses troupes à York en 306, Constantin franchit les Alpes en 312 contre Maxence, maître de Rome et de l'Italie. Plutôt que de soutenir un siège, Maxence fait passer son armée sur la rive droite du Tibre. Aurélius Victor situe le combat aux Saxa Rubra, à neuf milles de la ville. Repoussées vers le fleuve, ses troupes s'entassent sur un pont provisoire qui cède (pont de bateaux selon Eusèbe, pont démontable selon Zosime), et Maxence se noie.\n\nLes effectifs sont inconnus : Zosime prête près de 190 000 hommes à Maxence et moins de 100 000 à Constantin, des chiffres jugés très exagérés par les historiens.\n\nDeux récits chrétiens ont fait la célébrité de la bataille. Lactance, qui écrit peu après, rapporte qu'un songe aurait ordonné à Constantin de faire peindre sur les boucliers un signe du Christ. Eusèbe de Césarée, des années plus tard, décrit une croix lumineuse apparue dans le ciel avec une inscription invitant à vaincre par ce signe, d'après ce que l'empereur lui aurait confié. Ces récits relèvent de la tradition et de la propagande ; l'historien constate surtout que Constantin favorise ensuite le christianisme.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Lactance",
        "work": "De la mort des persécuteurs",
        "locus": "44",
        "url": "https://remacle.org/bloodwolf/eglise/lactance/persecuteurs.htm"
      },
      {
        "kind": "ancient",
        "author": "Eusèbe de Césarée",
        "work": "Histoire ecclésiastique",
        "locus": "IX, 9",
        "url": "https://remacle.org/bloodwolf/historiens/eusebe/histoire9.htm"
      },
      {
        "kind": "ancient",
        "author": "Eusèbe de Césarée",
        "work": "Vie de Constantin",
        "locus": "I, 28 à 38",
        "url": "https://remacle.org/bloodwolf/historiens/eusebe/constantin1.htm"
      },
      {
        "kind": "ancient",
        "author": "Zosime",
        "work": "Histoire nouvelle",
        "locus": "II, 15 et 16",
        "url": "https://remacle.org/bloodwolf/historiens/zosime/livre2.htm"
      },
      {
        "kind": "ancient",
        "author": "Aurélius Victor",
        "work": "Livre des Césars",
        "locus": "40, 23",
        "url": "https://remacle.org/bloodwolf/historiens/aurelvictor/cesars.htm"
      },
      {
        "kind": "ancient",
        "author": "Furius Dionysius Filocalus",
        "work": "Calendrier de 354 (Chronographe de 354)",
        "locus": "28 octobre (V des calendes de novembre) : evictio tyranni",
        "url": "https://www.tertullian.org/fathers/chronography_of_354_06_calendar.htm"
      },
      {
        "kind": "modern",
        "author": "Averil Cameron",
        "work": "The Cambridge Ancient History, vol. XII : The Crisis of Empire (2e éd., Cambridge University Press, 2005)",
        "locus": "chap. 4, The reign of Constantine"
      },
      {
        "kind": "modern",
        "author": "Raymond Davis",
        "work": "Oxford Classical Dictionary (édition numérique, Oxford University Press)",
        "locus": "entrée Constantine I",
        "url": "https://doi.org/10.1093/acrefore/9780199381135.013.1786"
      }
    ]
  },
  {
    "id": "edit-de-milan",
    "title": "« Édit » de Milan",
    "start": 313,
    "precision": "year",
    "certainty": "debated",
    "certaintyNote": "La rencontre de Milan et la lettre de 313 sont attestées ; c'est la qualification d'« édit de Milan » qui est discutée, car le texte conservé est une lettre de Licinius publiée à Nicomédie le 13 juin 313.",
    "era": "bas-empire",
    "track": "rome",
    "category": "religion",
    "importance": 2,
    "placeId": "milan",
    "people": [
      "constantin-ier",
      "licinius"
    ],
    "summary": "En 313, Constantin et Licinius, réunis à Milan, s'accordent pour garantir à tous, et d'abord aux chrétiens, la liberté de culte et la restitution des biens confisqués. Le texte connu est une lettre de Licinius affichée à Nicomédie le 13 juin 313 : parler d'« édit de Milan » est une commodité discutée.",
    "body": "Après le pont Milvius, Constantin rencontre à Milan, au début de 313, Licinius, Auguste des provinces danubiennes, qui y épouse sa demi-sœur Constantia. Les deux empereurs arrêtent une politique religieuse commune : chacun peut suivre le culte de son choix, et les communautés chrétiennes doivent récupérer les lieux de réunion et les biens saisis pendant la persécution.\n\nAucun édit signé à Milan ne nous est parvenu. Lactance donne le texte latin d'une lettre adressée au gouverneur de Bithynie, que Licinius, vainqueur de Maximin Daïa, fait afficher à Nicomédie le 13 juin 313 ; Eusèbe de Césarée en conserve une version grecque. Depuis l'historien allemand Otto Seeck (1891), beaucoup préfèrent parler d'un accord ou d'un rescrit plutôt que d'un édit.\n\nCe texte prolonge l'édit de tolérance de Galère (avril 311). Il ne fait pas du christianisme la religion officielle, mais il met fin aux persécutions et ouvre la voie au soutien impérial dont l'Église bénéficie sous Constantin.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Lactance",
        "work": "De la mort des persécuteurs",
        "locus": "45 (mariage de Milan) et 48 (texte de la lettre)",
        "url": "https://remacle.org/bloodwolf/eglise/lactance/persecuteurs.htm"
      },
      {
        "kind": "ancient",
        "author": "Eusèbe de Césarée",
        "work": "Histoire ecclésiastique",
        "locus": "X, 5",
        "url": "https://remacle.org/bloodwolf/historiens/eusebe/histoire10.htm"
      },
      {
        "kind": "modern",
        "author": "Otto Seeck",
        "work": "« Das sogenannte Edikt von Mailand », Zeitschrift für Kirchengeschichte, 12 (1891)"
      },
      {
        "kind": "modern",
        "author": "Averil Cameron",
        "work": "The Cambridge Ancient History, vol. XII : The Crisis of Empire (2e éd., Cambridge University Press, 2005)",
        "locus": "chap. 4, The reign of Constantine"
      },
      {
        "kind": "modern",
        "author": "Julia Hillner",
        "work": "Oxford Classical Dictionary (édition numérique, Oxford University Press)",
        "locus": "entrée Constantia, half-sister of Constantine and wife of Licinius",
        "url": "https://doi.org/10.1093/acrefore/9780199381135.013.8065"
      }
    ]
  },
  {
    "id": "concile-de-nicee",
    "title": "Concile de Nicée",
    "start": 325,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "L'ouverture le 20 mai suit Socrate ; d'autres sources, plus tardives, donnent le 19 juin. Le nombre d'évêques va de plus de 250 (Eusèbe) à 318 (chiffre symbolique de la tradition).",
    "era": "bas-empire",
    "track": "rome",
    "category": "religion",
    "importance": 2,
    "placeId": "nicee",
    "people": [
      "constantin-ier",
      "arius"
    ],
    "summary": "En 325, Constantin réunit à Nicée, en Bithynie, plusieurs centaines d'évêques pour trancher la querelle soulevée par le prêtre Arius sur la nature du Christ. Le concile adopte une profession de foi qui déclare le Fils « consubstantiel » au Père et devient le modèle des conciles œcuméniques.",
    "body": "Vers 320, Arius, prêtre d'Alexandrie, enseigne que le Fils, engendré par le Père, lui est subordonné. Condamné par son évêque, il trouve des appuis en Orient, et la dispute divise les Églises au moment où Constantin, vainqueur de Licinius en 324, devient seul empereur.\n\nConstantin convoque une assemblée générale des évêques à Nicée, non loin de Nicomédie, et y assiste en personne. Selon Socrate, le concile s'ouvre le 20 mai 325. Eusèbe de Césarée, qui y participe, compte plus de 250 évêques ; la tradition retiendra le chiffre symbolique de 318. Presque tous viennent d'Orient.\n\nLe symbole de Nicée affirme que le Fils est de même substance (*homoousios*) que le Père ; Arius et les deux évêques qui refusent de signer sont exilés. Le concile règle aussi la question de la date de Pâques et la discipline du clergé. La querelle n'est pas close pour autant : elle se poursuit pendant tout le IVe siècle.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Eusèbe de Césarée",
        "work": "Vie de Constantin",
        "locus": "III, 6 à 14 (plus de 250 évêques en III, 8)",
        "url": "https://www.newadvent.org/fathers/25023.htm"
      },
      {
        "kind": "ancient",
        "author": "Socrate le Scolastique",
        "work": "Histoire ecclésiastique",
        "locus": "I, 8 et 13 (date d'ouverture à la fin du chap. 13)",
        "url": "https://remacle.org/bloodwolf/eglise/socrate/eglise1.htm"
      },
      {
        "kind": "modern",
        "author": "Averil Cameron",
        "work": "The Cambridge Ancient History, vol. XII : The Crisis of Empire (2e éd., Cambridge University Press, 2005)",
        "locus": "chap. 4, The reign of Constantine"
      },
      {
        "kind": "modern",
        "author": "Timothy D. Barnes",
        "work": "Constantine and Eusebius (Harvard University Press, 1981)",
        "locus": "chap. The council of Nicaea"
      },
      {
        "kind": "modern",
        "author": "J. N. D. Kelly et David M. Gwynn",
        "work": "Oxford Classical Dictionary (édition numérique, Oxford University Press)",
        "locus": "entrée Arius",
        "url": "https://doi.org/10.1093/acrefore/9780199381135.013.774"
      }
    ]
  },
  {
    "id": "fondation-de-constantinople",
    "title": "Inauguration de Constantinople",
    "start": 330,
    "month": 5,
    "day": 11,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Le 11 mai est donné par des chroniques plus tardives (Chronique pascale, Malalas, Hésychios de Milet) mais il est généralement accepté.",
    "era": "bas-empire",
    "track": "rome",
    "category": "building",
    "importance": 1,
    "placeId": "constantinople",
    "people": [
      "constantin-ier"
    ],
    "summary": "Le 11 mai 330, Constantin inaugure sur le site de l'ancienne Byzance une ville qui porte son nom. Dotée d'un sénat et de distributions de blé, Constantinople devient la grande capitale de l'Orient romain et le reste jusqu'en 1453, sauf de 1204 à 1261.",
    "body": "Byzance, vieille cité grecque sur le Bosphore, commande le passage entre l'Europe et l'Asie. Après sa victoire sur Licinius en 324, Constantin décide de la refonder à une échelle bien plus vaste ; les travaux durent six ans. Selon la Chronique pascale, la ville est consacrée le 11 mai 330 au milieu de grandes fêtes, et ce jour reste celui de son anniversaire officiel.\n\nConstantin y crée un sénat (Anonyme de Valois), y loge des sénateurs venus de Rome et offre au peuple des distributions de blé (Zosime). Cette « nouvelle Rome » n'éclipse pas tout de suite l'ancienne, mais elle devient la résidence ordinaire des empereurs d'Orient à partir de la fin du IVe siècle.\n\nLes historiens, comme Gilbert Dagron, ont montré que l'image d'une fondation entièrement chrétienne a été construite après coup. Jusqu'en 1453, les habitants de la ville se disent Romains (*Rhomaioi*) ; l'adjectif « byzantin » est une étiquette moderne.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Zosime",
        "work": "Histoire nouvelle",
        "locus": "II, 30 à 32",
        "url": "https://remacle.org/bloodwolf/historiens/zosime/livre2.htm"
      },
      {
        "kind": "ancient",
        "author": "Anonyme de Valois",
        "work": "Excerpta Valesiana, première partie (Origo Constantini)",
        "locus": "6, 30",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Excerpta_Valesiana/1*.html"
      },
      {
        "kind": "ancient",
        "author": "Socrate le Scolastique",
        "work": "Histoire ecclésiastique",
        "locus": "I, 16",
        "url": "https://remacle.org/bloodwolf/eglise/socrate/eglise1.htm"
      },
      {
        "kind": "ancient",
        "author": "Anonyme",
        "work": "Chronique pascale",
        "locus": "année 330 (éd. de Bonn, p. 527 et suiv.)"
      },
      {
        "kind": "modern",
        "author": "Gilbert Dagron",
        "work": "Naissance d'une capitale. Constantinople et ses institutions de 330 à 451 (Presses universitaires de France, 1974)"
      },
      {
        "kind": "modern",
        "author": "Eugen Oberhummer",
        "work": "« Constantinopolis », Paulys Realencyclopädie der classischen Altertumswissenschaft, IV, 1 (1900)",
        "locus": "section Gründung",
        "url": "https://de.wikisource.org/wiki/RE:Constantinopolis"
      },
      {
        "kind": "modern",
        "author": "Alan Cameron",
        "work": "Oxford Classical Dictionary (édition numérique, Oxford University Press)",
        "locus": "entrée Constantinople",
        "url": "https://doi.org/10.1093/acrefore/9780199381135.013.1789"
      }
    ]
  },
  {
    "id": "bataille-d-andrinople",
    "title": "Bataille d'Andrinople",
    "start": 378,
    "month": 8,
    "day": 9,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Effectifs incertains : de 15 000 à 30 000 Romains environ selon les estimations modernes, avec des pertes de 10 000 à 20 000 hommes ; Ammien affirme qu'à peine un tiers de l'armée s'échappa.",
    "era": "bas-empire",
    "track": "rome",
    "category": "war",
    "importance": 2,
    "placeId": "andrinople",
    "people": [
      "valens",
      "fritigern",
      "gratien"
    ],
    "summary": "Le 9 août 378, près d'Andrinople en Thrace, l'armée de l'empereur d'Orient Valens est écrasée par les Goths de Fritigern. Valens est tué et environ deux tiers des soldats romains périssent : Ammien Marcellin compare ce désastre à celui de Cannes.",
    "body": "En 376, chassés par la poussée des Huns, des Goths obtiennent de Valens le droit de franchir le Danube. Maltraités et affamés par les officiers romains chargés de les accueillir, ils se révoltent et ravagent la Thrace. Valens revient d'Antioche et, sans attendre l'armée de son neveu Gratien, empereur d'Occident, décide d'attaquer.\n\nD'après Ammien Marcellin, seul récit détaillé, l'armée marche plusieurs heures sous la chaleur avant d'atteindre le cercle de chariots des Goths. Le retour inattendu de la cavalerie gothique prend les Romains de flanc ; l'infanterie, serrée et épuisée, est massacrée. Le corps de Valens n'est jamais retrouvé, et le lieu exact du combat, à quelques heures de marche de la ville, n'est pas localisé.\n\nLes historiens modernes estiment l'armée romaine entre 15 000 et 30 000 hommes environ, dont près des deux tiers auraient péri. On a longtemps vu dans cette bataille le triomphe de la cavalerie sur l'infanterie ; l'idée est aujourd'hui abandonnée, et les cavaliers des deux camps montent encore sans étriers. En 382, Théodose doit traiter avec les Goths et les installer dans l'Empire.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Ammien Marcellin",
        "work": "Histoires",
        "locus": "XXXI, 12 et 13 (date en 12, 10 ; pertes en 13, 18 et 19)",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Ammian/31*.html"
      },
      {
        "kind": "modern",
        "author": "John Curran",
        "work": "The Cambridge Ancient History, vol. XIII : The Late Empire (Cambridge University Press, 1998)",
        "locus": "chap. 3, From Jovian to Theodosius",
        "url": "https://www.cambridge.org/core/books/cambridge-ancient-history/from-jovian-to-theodosius/72B66E68410074D5EC9FD9E3FD5EAA20"
      },
      {
        "kind": "modern",
        "author": "Noel Lenski",
        "work": "Failure of Empire: Valens and the Roman State in the Fourth Century A.D. (University of California Press, 2002)"
      }
    ]
  },
  {
    "id": "edit-de-thessalonique",
    "title": "Édit de Thessalonique",
    "start": 380,
    "month": 2,
    "day": 27,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Le Code date la loi du III des calendes de mars, converti en 27 février par l'usage courant ; 380 étant bissextile, certains auteurs donnent le 28 février.",
    "era": "bas-empire",
    "track": "rome",
    "category": "religion",
    "importance": 2,
    "placeId": "thessalonique",
    "people": [
      "theodose-ier",
      "gratien",
      "valentinien-ii"
    ],
    "summary": "Le 27 février 380, à Thessalonique, Théodose Ier, au nom aussi de Gratien et de Valentinien II, ordonne à tous les peuples de l'Empire de suivre la foi trinitaire de Nicée, celle des évêques Damase de Rome et Pierre d'Alexandrie. Ses fidèles seuls sont dits chrétiens catholiques ; les autres sont déclarés hérétiques.",
    "body": "Proclamé Auguste par Gratien en 379 pour faire face à la crise gothique, Théodose réside alors à Thessalonique, dont l'évêque Ascholius, fidèle à Nicée, le baptise lors d'une grave maladie (Sozomène ; la date exacte de ce baptême, avant ou après la loi, est discutée). Le 27 février 380, une constitution adressée au peuple de Constantinople, conservée dans le Code théodosien et appelée d'après ses premiers mots *Cunctos populos*, fixe la foi que tous doivent suivre.\n\nLe texte vise d'abord les querelles entre chrétiens : il impose la doctrine de Nicée sur la Trinité, contre les ariens encore puissants à Constantinople. On le présente souvent comme l'acte qui fait du christianisme la religion d'État ; c'est juste pour la définition de l'orthodoxie, mais les cultes païens ne sont interdits que par les lois de 391 et 392.\n\nL'année suivante, le concile de Constantinople (381) confirme et précise le credo de Nicée.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Code théodosien",
        "work": "Livre XVI (texte de Mommsen, trad. J. Rougé, introduction et notes de R. Delmaire, Sources chrétiennes 497, Cerf, 2005)",
        "locus": "XVI, 1, 2",
        "url": "https://droitromain.univ-grenoble-alpes.fr/Constitutiones/CTh16.html"
      },
      {
        "kind": "ancient",
        "author": "Sozomène",
        "work": "Histoire ecclésiastique",
        "locus": "VII, 4",
        "url": "https://www.newadvent.org/fathers/26027.htm"
      },
      {
        "kind": "modern",
        "author": "John Curran",
        "work": "The Cambridge Ancient History, vol. XIII : The Late Empire (Cambridge University Press, 1998)",
        "locus": "chap. 3, From Jovian to Theodosius",
        "url": "https://www.cambridge.org/core/books/cambridge-ancient-history/from-jovian-to-theodosius/72B66E68410074D5EC9FD9E3FD5EAA20"
      },
      {
        "kind": "modern",
        "author": "John F. Matthews",
        "work": "Oxford Classical Dictionary (édition numérique, Oxford University Press)",
        "locus": "entrée Theodosius (2) I",
        "url": "https://doi.org/10.1093/acrefore/9780199381135.013.6355"
      }
    ]
  },
  {
    "id": "partage-de-l-empire",
    "title": "Mort de Théodose et partage de l'Empire",
    "start": 395,
    "month": 1,
    "day": 17,
    "precision": "day",
    "certainty": "attested",
    "era": "bas-empire",
    "track": "rome",
    "category": "politics",
    "importance": 1,
    "placeId": "milan",
    "people": [
      "theodose-ier",
      "arcadius",
      "honorius",
      "stilicon"
    ],
    "summary": "Le 17 janvier 395, Théodose Ier meurt à Milan. Ses fils Arcadius, à Constantinople, et Honorius, en Occident, gouvernent chacun une partie de l'Empire, qui reste en droit un seul État : c'est la date conventionnelle de la naissance de l'Empire romain d'Orient.",
    "body": "Vainqueur de l'usurpateur Eugène à la bataille de la rivière Froide (septembre 394), Théodose est le dernier empereur à exercer, brièvement, l'autorité sur l'ensemble du monde romain. Il meurt à Milan dans la nuit du 16 au 17 janvier 395. Arcadius, Auguste depuis 383, règne en Orient ; Honorius, âgé de dix ans, règne en Occident sous la tutelle du général Stilicon.\n\nCe n'est pas la première fois que l'Empire a deux souverains : Valentinien Ier et Valens se l'étaient déjà réparti en 364. En droit, il n'existe toujours qu'un Empire romain, avec deux cours ; les lois sont promulguées au nom des deux Augustes, et le chroniqueur Marcellin le Comte écrit que les deux frères se mirent à gouverner les deux parties de l'Empire en séparant seulement leurs résidences. Mais les deux cours mènent bientôt des politiques distinctes, parfois rivales, et l'unité devient surtout un principe.\n\nLa partie orientale, centrée sur Constantinople, durera jusqu'en 1453. Ses habitants se sont toujours appelés Romains (*Rhomaioi*) ; l'expression « Empire byzantin » a été forgée par les historiens modernes.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Socrate le Scolastique",
        "work": "Histoire ecclésiastique",
        "locus": "V, 26",
        "url": "https://remacle.org/bloodwolf/eglise/socrate/eglise5.htm"
      },
      {
        "kind": "ancient",
        "author": "Zosime",
        "work": "Histoire nouvelle",
        "locus": "V, 1 (en IV, 59, Zosime fait mourir Théodose à tort sur la route de Constantinople)",
        "url": "https://remacle.org/bloodwolf/historiens/zosime/livre5.htm"
      },
      {
        "kind": "ancient",
        "author": "Marcellin le Comte",
        "work": "Chronique",
        "locus": "année 395, 1 à 3",
        "url": "https://remacle.org/bloodwolf/historiens/marcellin/chronique1.htm"
      },
      {
        "kind": "modern",
        "author": "R. C. Blockley",
        "work": "The Cambridge Ancient History, vol. XIII : The Late Empire (Cambridge University Press, 1998)",
        "locus": "chap. 4, The dynasty of Theodosius",
        "url": "https://www.cambridge.org/core/books/cambridge-ancient-history/dynasty-of-theodosius/13877E996427028C87E955CCD1948F9C"
      },
      {
        "kind": "modern",
        "author": "John F. Matthews",
        "work": "Oxford Classical Dictionary (édition numérique, Oxford University Press)",
        "locus": "entrée Theodosius (2) I",
        "url": "https://doi.org/10.1093/acrefore/9780199381135.013.6355"
      }
    ]
  },
  {
    "id": "sac-de-rome-par-alaric",
    "title": "Sac de Rome par Alaric",
    "start": 410,
    "month": 8,
    "day": 24,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Le jour d'entrée est celui que retiennent les historiens modernes, sans source antique vérifiée ici ; les Goths quittent la ville le troisième jour selon Orose, le sixième selon Marcellin le Comte.",
    "era": "bas-empire",
    "track": "occident",
    "category": "war",
    "importance": 2,
    "placeId": "rome",
    "people": [
      "alaric-ier",
      "honorius"
    ],
    "summary": "Le 24 août 410, les Goths d'Alaric entrent dans Rome et la pillent pendant plusieurs jours. Pour la première fois depuis l'attaque gauloise du IVe siècle av. J.-C., la Ville tombe aux mains d'un ennemi, et le choc moral est immense dans tout le monde romain.",
    "body": "Chef des Goths installés dans l'Empire, Alaric réclame depuis des années des terres, du ravitaillement et un commandement officiel. L'empereur Honorius, retranché à Ravenne, refuse de traiter. Alaric assiège Rome en 408 puis en 409, y fait même proclamer un empereur docile, Priscus Attale, avant de s'emparer de la ville en 410.\n\nSelon Procope, qui rapporte deux versions, la porte Salaria est ouverte de l'intérieur, par ruse ou par trahison. Les Goths repartent le troisième jour selon Orose, le sixième selon Marcellin le Comte. Chrétiens, ils épargnent en partie les basiliques et ceux qui s'y réfugient, mais incendient des quartiers et emmènent Galla Placidia, sœur de l'empereur. Le nombre des victimes est inconnu.\n\nRome n'est plus la capitale politique, mais sa chute frappe les esprits : Jérôme se lamente depuis Bethléem, et Augustin entreprend *La Cité de Dieu* pour répondre aux païens qui accusent l'abandon des anciens dieux. Alaric meurt peu après dans le Bruttium (l'actuelle Calabre), près de Cosenza.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Orose",
        "work": "Histoires contre les païens",
        "locus": "VII, 39 et 40 (départ le troisième jour en 39, 15)",
        "url": "https://www.thelatinlibrary.com/orosius/orosius7.shtml"
      },
      {
        "kind": "ancient",
        "author": "Procope de Césarée",
        "work": "Guerre des Vandales",
        "locus": "I, 2 (Guerres, III, 2)",
        "url": "https://remacle.org/bloodwolf/historiens/procope/vandales.htm"
      },
      {
        "kind": "ancient",
        "author": "Marcellin le Comte",
        "work": "Chronique",
        "locus": "année 410",
        "url": "https://remacle.org/bloodwolf/historiens/marcellin/chronique1.htm"
      },
      {
        "kind": "ancient",
        "author": "Jordanès",
        "work": "Histoire des Goths (Getica)",
        "locus": "30",
        "url": "https://remacle.org/bloodwolf/historiens/jornandes/gothsfr.htm"
      },
      {
        "kind": "ancient",
        "author": "Jérôme",
        "work": "Lettres",
        "locus": "127, 12",
        "url": "https://www.newadvent.org/fathers/3001127.htm"
      },
      {
        "kind": "modern",
        "author": "R. C. Blockley",
        "work": "The Cambridge Ancient History, vol. XIII : The Late Empire (Cambridge University Press, 1998)",
        "locus": "chap. 4, The dynasty of Theodosius",
        "url": "https://www.cambridge.org/core/books/cambridge-ancient-history/dynasty-of-theodosius/13877E996427028C87E955CCD1948F9C"
      },
      {
        "kind": "modern",
        "author": "Peter Heather",
        "work": "Oxford Classical Dictionary (édition numérique, Oxford University Press)",
        "locus": "entrée Alaric",
        "url": "https://doi.org/10.1093/acrefore/9780199381135.013.237"
      }
    ]
  },
  {
    "id": "deposition-de-romulus-augustule",
    "title": "Déposition de Romulus Augustule",
    "start": 476,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "L'année est sûre ; le jour exact de la déposition n'est pas transmis directement (on avance souvent le 4 septembre, date de la mort de Paul près de Ravenne).",
    "era": "bas-empire",
    "track": "occident",
    "category": "politics",
    "importance": 1,
    "placeId": "ravenne",
    "people": [
      "romulus-augustule",
      "oreste",
      "odoacre",
      "julius-nepos",
      "zenon"
    ],
    "summary": "En 476, le chef militaire Odoacre tue le patrice Oreste et dépose son fils, le jeune empereur Romulus Augustule, à Ravenne. Il renvoie les insignes impériaux à Constantinople et gouverne l'Italie comme roi : cette date marque, par convention, la fin de l'Empire romain d'Occident.",
    "body": "En 475, le patrice Oreste chasse l'empereur Julius Nepos et fait proclamer à Ravenne son propre fils Romulus, encore enfant, que l'on surnomme Augustule, « le petit Auguste ». L'année suivante, les soldats barbares au service de l'Italie réclament des terres (le tiers du sol, selon Procope) ; Oreste refuse. Ils se donnent pour chef Odoacre, qui tue Oreste à Plaisance puis son frère Paul près de Ravenne, à la fin d'août ou au début de septembre 476.\n\nOdoacre épargne Romulus en raison de son jeune âge, lui accorde un revenu de 6 000 sous d'or et l'envoie vivre en Campanie (Anonyme de Valois), au château de Lucullus près de Naples (Marcellin le Comte, Jordanès). Il ne prend pas le titre d'empereur : une ambassade du Sénat, connue par l'historien Malchus, renvoie les insignes impériaux à Zénon, empereur à Constantinople, et Odoacre règne en Italie comme roi.\n\n476 est une date conventionnelle. Sur le moment, rien ne semble finir : Julius Nepos, réfugié en Dalmatie, reste l'empereur légitime aux yeux de Constantinople jusqu'à sa mort en 480, et le Sénat comme le consulat subsistent. C'est à Constantinople, vers 518, que le chroniqueur Marcellin le Comte écrit que l'empire d'Occident « périt avec cet Augustule », idée reprise ensuite par la tradition. L'Empire romain, lui, continue en Orient jusqu'en 1453.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Marcellin le Comte",
        "work": "Chronique",
        "locus": "année 476, 2",
        "url": "https://remacle.org/bloodwolf/historiens/marcellin/chronique2.htm"
      },
      {
        "kind": "ancient",
        "author": "Anonyme de Valois",
        "work": "Excerpta Valesiana, seconde partie",
        "locus": "8, 37 et 38",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Excerpta_Valesiana/2*.html"
      },
      {
        "kind": "ancient",
        "author": "Jordanès",
        "work": "Histoire des Goths (Getica)",
        "locus": "45 et 46",
        "url": "https://remacle.org/bloodwolf/historiens/jornandes/gothsfr.htm"
      },
      {
        "kind": "ancient",
        "author": "Procope de Césarée",
        "work": "Guerre des Goths",
        "locus": "I, 1 (Guerres, V, 1)",
        "url": "https://remacle.org/bloodwolf/historiens/procope/goth1.htm"
      },
      {
        "kind": "modern",
        "author": "Brian Croke",
        "work": "« A.D. 476: The Manufacture of a Turning Point », Chiron, 13 (1983)",
        "url": "https://publications.dainst.org/journals/chiron/article/view/1273"
      },
      {
        "kind": "modern",
        "author": "Peter Heather",
        "work": "The Cambridge Ancient History, vol. XIV : Late Antiquity, Empire and Successors (Cambridge University Press, 2000)",
        "locus": "chap. 1, The western empire",
        "url": "https://www.cambridge.org/core/books/cambridge-ancient-history/western-empire-42576/F370F583E4336A965470D048BD346924"
      },
      {
        "kind": "modern",
        "author": "Peter Heather",
        "work": "Oxford Classical Dictionary (édition numérique, Oxford University Press)",
        "locus": "entrée Romulus Augustulus",
        "url": "https://doi.org/10.1093/acrefore/9780199381135.013.5611"
      },
      {
        "kind": "modern",
        "author": "Peter Heather",
        "work": "Oxford Classical Dictionary (édition numérique, Oxford University Press)",
        "locus": "entrée Odoacer",
        "url": "https://doi.org/10.1093/acrefore/9780199381135.013.4514"
      }
    ]
  },
  {
    "id": "code-de-justinien",
    "title": "Le Code de Justinien",
    "start": 529,
    "end": 534,
    "precision": "year",
    "certainty": "attested",
    "era": "empire-romain-d-orient",
    "track": "orient",
    "category": "politics",
    "importance": 1,
    "placeId": "constantinople",
    "people": [
      "justinien",
      "tribonien"
    ],
    "summary": "De 529 à 534, l'empereur Justinien fait rassembler et mettre en ordre le droit romain : un Code des lois impériales, le Digeste (extraits des grands juristes) et les Institutes, un manuel pour les étudiants. Cet ensemble, appelé bien plus tard « Corpus iuris civilis », est la principale voie par laquelle le droit romain nous est parvenu.",
    "body": "Dès 528, Justinien confie à une commission la révision des lois impériales. Un premier **Code** est promulgué en avril 529 : il réunit les constitutions des empereurs encore en vigueur, depuis Hadrien. Sous la direction du juriste **Tribonien**, une autre commission dépouille ensuite les écrits des grands juristes des IIe et IIIe siècles pour composer le **Digeste** (ou Pandectes), publié à la fin de 533 en même temps que les **Institutes**, un manuel destiné aux étudiants en droit.\n\nUne seconde édition du Code, mise à jour, est promulguée en novembre 534. C'est elle qui nous est parvenue : la première édition est perdue. Les lois nouvelles de Justinien, les **Novelles**, rédigées pour la plupart en grec, viennent ensuite s'y ajouter.\n\nLe nom de « Corpus iuris civilis » n'est pas d'époque : il s'impose chez les juristes humanistes du XVIe siècle. Redécouvert en Occident à la fin du XIe siècle, notamment à Bologne, ce corpus a profondément marqué le droit des pays européens.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Justinien",
        "work": "Code de Justinien, constitutions préliminaires Haec (528), Summa (529) et Cordi (534)",
        "locus": "en tête du livre I (trad. angl. F. H. Blume, édition numérique de l'université du Wyoming)",
        "url": "https://www.uwyo.edu/lawlib/blume-justinian/ajc-edition-2/books/book1/Book%201-ConcerningCode.pdf"
      },
      {
        "kind": "ancient",
        "author": "Justinien",
        "work": "Institutes",
        "locus": "constitution Imperatoriam (préambule, 21 novembre 533 ; trad. angl. J. B. Moyle)",
        "url": "https://www.gutenberg.org/ebooks/5983"
      },
      {
        "kind": "modern",
        "author": "Tony Honoré",
        "work": "Tribonian (Duckworth, 1978)"
      },
      {
        "kind": "modern",
        "author": "Cécile Morrisson (dir.)",
        "work": "Le Monde byzantin, t. I : L'Empire romain d'Orient (330-641), PUF, Nouvelle Clio, 2004"
      }
    ]
  },
  {
    "id": "reconquetes-de-justinien",
    "title": "Reconquêtes de Justinien en Occident",
    "start": 533,
    "end": 554,
    "precision": "year",
    "certainty": "attested",
    "certaintyNote": "Les effectifs donnés par Procope (environ 15 000 soldats pour l'expédition d'Afrique) sont plausibles mais invérifiables.",
    "era": "empire-romain-d-orient",
    "track": "orient",
    "category": "war",
    "importance": 2,
    "people": [
      "justinien",
      "belisaire",
      "narses"
    ],
    "summary": "De 533 à 554, les armées de Justinien, menées par Bélisaire puis par Narsès, reprennent l'Afrique aux Vandales, l'Italie aux Ostrogoths et une partie du sud de l'Espagne aux Wisigoths. Ces conquêtes rendent à l'empire une partie de l'Occident, au prix de guerres longues et ruineuses, surtout en Italie.",
    "body": "En 533, **Bélisaire** débarque en Afrique avec une armée assez modeste (environ 15 000 soldats selon Procope) et défait le roi vandale Gélimer à Ad Decimum, près de Carthage, puis à Tricamarum. Le royaume vandale disparaît en 534, mais la pacification de l'Afrique, face aux révoltes des tribus maures, dure jusqu'en 548.\n\nEn 535, Bélisaire attaque le royaume ostrogoth d'Italie. Il prend Rome puis Ravenne (540), mais la guerre reprend sous le roi Totila et ravage la péninsule pendant plus de dix ans. L'eunuque **Narsès** y met fin par ses victoires de 552, notamment à Taginae (Busta Gallorum), et Justinien réorganise l'Italie par la Pragmatique Sanction de 554. Vers 552, une expédition prend aussi pied dans le sud-est de l'Espagne.\n\nProcope de Césarée, secrétaire de Bélisaire, raconte ces guerres en témoin. Les historiens soulignent leur coût humain et financier : l'Italie, épuisée, est en grande partie envahie par les Lombards dès 568.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Procope de Césarée",
        "work": "Histoire des guerres (Guerre contre les Vandales, livres III et IV ; Guerre contre les Goths, livres V à VIII)",
        "locus": "III, 11, 2 (effectifs : 10 000 fantassins et 5 000 cavaliers) ; III, 18 et 19 (Ad Decimum) ; VIII, 29 à 32 (Taginae) ; trad. angl. H. B. Dewing, qui numérote aussi la Guerre des Vandales en livres I et II",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Procopius/Wars/home.html"
      },
      {
        "kind": "modern",
        "author": "Peter Heather",
        "work": "Rome Resurgent: War and Empire in the Age of Justinian (Oxford University Press, 2018)"
      },
      {
        "kind": "modern",
        "author": "Cécile Morrisson (dir.)",
        "work": "Le Monde byzantin, t. I : L'Empire romain d'Orient (330-641), PUF, Nouvelle Clio, 2004"
      }
    ]
  },
  {
    "id": "consecration-de-sainte-sophie",
    "title": "Consécration de Sainte-Sophie",
    "start": 537,
    "month": 12,
    "day": 27,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Le jour exact vient de Théophane ; Jean Malalas mentionne la dédicace sans donner le jour, à une date qui correspond plutôt à 538.",
    "era": "empire-romain-d-orient",
    "track": "orient",
    "category": "building",
    "importance": 2,
    "placeId": "sainte-sophie",
    "people": [
      "justinien",
      "anthemius-de-tralles",
      "isidore-de-milet"
    ],
    "summary": "Le 27 décembre 537, l'empereur Justinien et le patriarche Ménas inaugurent la nouvelle église Sainte-Sophie de Constantinople, rebâtie en moins de six ans après l'incendie de la sédition Nika (532). Sa coupole, conçue par Anthémius de Tralles et Isidore de Milet, en fait l'une des plus vastes églises de la chrétienté pendant des siècles.",
    "body": "L'ancienne basilique, dédiée à la Sagesse divine (Hagia Sophia), brûle en janvier 532 pendant la sédition **Nika**, une émeute qui faillit renverser Justinien. L'empereur la fait aussitôt reconstruire sur un plan nouveau, confié à deux savants, **Anthémius de Tralles** et **Isidore de Milet** : une immense salle couverte d'une coupole posée sur quatre grands arcs et prolongée par deux demi-coupoles.\n\nLe jour de la dédicace, le 27 décembre 537, est donné par la chronique de Théophane. Jean Malalas mentionne aussi la cérémonie, mais sans le jour, et son comput la place plutôt en 538. Procope de Césarée, contemporain, décrit l'édifice avec admiration dans son traité *Sur les édifices*, sans donner de date. La phrase prêtée à Justinien ce jour-là (« Salomon, je t'ai vaincu ») provient d'un récit légendaire bien plus tardif.\n\nLa première coupole, trop plate, s'effondre en partie en 558 après une série de séismes. Isidore le Jeune, neveu d'Isidore de Milet, la reconstruit plus haute, et l'église est consacrée une seconde fois le 24 décembre 562. Transformée en mosquée après 1453, Sainte-Sophie conserve l'essentiel de la structure voulue par Justinien.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Procope de Césarée",
        "work": "Sur les édifices (De aedificiis)",
        "locus": "I, 1, 20 à 78 (trad. angl. H. B. Dewing, Loeb)",
        "url": "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Procopius/Buildings/1A*.html"
      },
      {
        "kind": "ancient",
        "author": "Jean Malalas",
        "work": "Chronographie",
        "locus": "XVIII, 86 (trad. angl. E. Jeffreys, M. Jeffreys et R. Scott, 1986)"
      },
      {
        "kind": "ancient",
        "author": "Théophane le Confesseur",
        "work": "Chronographie",
        "locus": "AM 6030 (éd. de Boor, p. 217 ; trad. angl. C. Mango et R. Scott, 1997)"
      },
      {
        "kind": "modern",
        "author": "Rowland J. Mainstone",
        "work": "Hagia Sophia: Architecture, Structure and Liturgy of Justinian's Great Church (Thames and Hudson, 1988)"
      }
    ]
  },
  {
    "id": "bataille-du-yarmouk",
    "title": "Bataille du Yarmouk",
    "start": 636,
    "month": 8,
    "precision": "month",
    "certainty": "attested",
    "certaintyNote": "Le mois d'août 636 est retenu par la plupart des historiens, mais une tradition arabe place la bataille en 634 ; les effectifs sont inconnus, de 15 000 à 40 000 hommes environ par armée selon la plupart des estimations modernes.",
    "era": "empire-romain-d-orient",
    "track": "orient",
    "category": "war",
    "importance": 2,
    "placeId": "yarmouk",
    "people": [
      "heraclius",
      "vahan",
      "khalid-ibn-al-walid"
    ],
    "summary": "En août 636, près de la rivière Yarmouk, à l'est du lac de Tibériade, l'armée arabe musulmane écrase l'armée romaine envoyée par l'empereur Héraclius. Cette défaite entraîne la perte durable de la Syrie et de la Palestine, puis ouvre la voie à la conquête de l'Égypte.",
    "body": "Après les premières victoires arabes en Palestine (634) et la prise de Damas, Héraclius réunit depuis Antioche une grande armée de troupes romaines, arméniennes et d'alliés arabes chrétiens (les Ghassanides). Placée sous le commandement de **Vahan**, un général arménien, elle affronte l'armée du califat, dirigée sur le terrain par **Khalid ibn al-Walid**, sur les plateaux que borde le Yarmouk, un affluent du Jourdain.\n\nLes combats, étalés sur plusieurs jours (six selon une tradition), s'achèvent par une déroute romaine : une partie de l'armée est acculée aux ravins du Yarmouk et de son affluent. Les chiffres des sources sont très exagérés (environ 200 000 hommes du côté impérial selon al-Baladhuri) ; les historiens modernes estiment chaque armée à quelques dizaines de milliers d'hommes au plus et divergent beaucoup.\n\nHéraclius renonce alors à défendre la Syrie. Jérusalem capitule en 637 ou 638 et l'Égypte est conquise de 639 à 642. Réduit à l'Asie Mineure, à une partie des Balkans, à l'Afrique et à des territoires en Italie, l'empire entre dans une longue période de transformation.",
    "sources": [
      {
        "kind": "ancient",
        "author": "al-Baladhuri",
        "work": "Futuh al-buldan (Le Livre des conquêtes des pays)",
        "locus": "chapitre sur la bataille du Yarmouk (trad. angl. P. K. Hitti, The Origins of the Islamic State, 1916)",
        "url": "https://sourcebooks.fordham.edu/source/yarmuk.asp"
      },
      {
        "kind": "ancient",
        "author": "Théophane le Confesseur",
        "work": "Chronographie",
        "locus": "AM 6126 (trad. angl. C. Mango et R. Scott, 1997)"
      },
      {
        "kind": "modern",
        "author": "Walter E. Kaegi",
        "work": "Byzantium and the Early Islamic Conquests (Cambridge University Press, 1992)"
      },
      {
        "kind": "modern",
        "author": "Cécile Morrisson (dir.)",
        "work": "Le Monde byzantin, t. I : L'Empire romain d'Orient (330-641), PUF, Nouvelle Clio, 2004"
      }
    ]
  },
  {
    "id": "siege-arabe-de-constantinople",
    "title": "Siège arabe de Constantinople",
    "start": 717,
    "end": 718,
    "month": 8,
    "precision": "month",
    "certainty": "attested",
    "certaintyNote": "Le siège terrestre commence à la mi-juillet ou à la mi-août 717 selon les sources, et les effectifs arabes donnés (1 800 navires selon Théophane, 120 000 hommes selon al-Masudi) sont sans doute très exagérés.",
    "era": "empire-romain-d-orient",
    "track": "orient",
    "category": "war",
    "importance": 2,
    "placeId": "constantinople",
    "people": [
      "leon-iii-l-isaurien",
      "maslama-ibn-abd-al-malik"
    ],
    "summary": "D'août 717 à août 718, une grande armée et une flotte du califat omeyyade, commandées par Maslama, assiègent Constantinople par terre et par mer. Le nouvel empereur Léon III résiste grâce aux murailles, au feu grégeois et à l'aide des Bulgares ; l'échec du siège met fin aux grandes offensives arabes contre la capitale.",
    "body": "Après des décennies de conquêtes, le calife omeyyade Sulayman lance une offensive majeure contre la capitale romaine. Son frère **Maslama ibn Abd al-Malik** traverse l'Asie Mineure, passe en Thrace et assiège la ville par terre à partir de l'été 717 (mi-juillet ou mi-août selon les sources), tandis qu'une grande flotte, arrivée le 1er septembre, tente de la bloquer par mer. Quelques mois plus tôt, en mars 717, le général **Léon**, stratège des Anatoliques, s'était emparé du trône sous le nom de Léon III.\n\nLes murailles terrestres tiennent. La flotte impériale détruit une partie des navires arabes avec le **feu grégeois**, un liquide incendiaire projeté par des siphons, et la ville reste ravitaillée par la mer Noire. L'hiver qui suit, très rude, décime les assiégeants, et les Bulgares du khan Tervel, alliés de l'empire, attaquent leur camp ; l'importance exacte de leur rôle est discutée.\n\nLe 15 août 718, Maslama lève le siège sur ordre du nouveau calife Umar II ; une partie de la flotte est détruite par une tempête au retour. Les raids arabes en Asie Mineure continuent, mais Constantinople n'est plus jamais menacée de cette façon par le califat.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Théophane le Confesseur",
        "work": "Chronographie",
        "locus": "AM 6209 et AM 6210 (trad. angl. C. Mango et R. Scott, 1997)"
      },
      {
        "kind": "modern",
        "author": "E. W. Brooks",
        "work": "« The Campaign of 716-718, from Arabic Sources », Journal of Hellenic Studies 19 (1899)"
      },
      {
        "kind": "modern",
        "author": "Leslie Brubaker et John Haldon",
        "work": "Byzantium in the Iconoclast Era, c. 680-850: A History (Cambridge University Press, 2011)"
      }
    ]
  },
  {
    "id": "crise-iconoclaste",
    "title": "La querelle des images",
    "start": 726,
    "end": 843,
    "precision": "year",
    "certainty": "debated",
    "certaintyNote": "Le début est discuté : 726 selon Théophane, mais beaucoup d'historiens placent les premières mesures officielles en 730 et jugent le rôle de Léon III grossi par les sources favorables aux images.",
    "era": "empire-romain-d-orient",
    "track": "orient",
    "category": "religion",
    "importance": 2,
    "placeId": "constantinople",
    "people": [
      "leon-iii-l-isaurien",
      "constantin-v",
      "irene-l-athenienne",
      "theodora-epouse-de-theophile"
    ],
    "summary": "De 726 ou 730 à 843, l'Empire romain d'Orient se déchire sur la question des images religieuses (icônes). Les empereurs iconoclastes en interdisent la vénération, jugée idolâtre, avant que l'impératrice Théodora ne la rétablisse définitivement en 843, victoire célébrée depuis comme le « triomphe de l'Orthodoxie ».",
    "body": "Selon le chroniqueur Théophane, l'empereur **Léon III** commence à combattre le culte des icônes en 726, après une éruption volcanique à Théra (Santorin) interprétée comme un signe de la colère divine. En 730, le patriarche Germain, hostile à cette politique, est remplacé. Les recherches récentes (Brubaker et Haldon) invitent à la prudence : les sources, presque toutes écrites par les vainqueurs favorables aux images, ont noirci et peut-être avancé dans le temps l'action de Léon III.\n\nSon fils **Constantin V** fait condamner la vénération des images au concile de Hiéreia (754) et s'en prend aux moines qui les défendent. Le deuxième concile de Nicée, réuni en 787 sous l'impératrice **Irène**, rétablit les icônes. Une seconde période iconoclaste s'ouvre en 815, sous Léon V.\n\nEn 843, après la mort de l'empereur Théophile, sa veuve **Théodora**, régente, fait rétablir le culte des images par un synode. Cette décision, fêtée chaque année par l'Église orthodoxe (dimanche de l'Orthodoxie), clôt la crise. L'ampleur réelle des destructions d'icônes reste discutée.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Théophane le Confesseur",
        "work": "Chronographie",
        "locus": "AM 6218 et AM 6221 (trad. angl. C. Mango et R. Scott, 1997)"
      },
      {
        "kind": "modern",
        "author": "Leslie Brubaker et John Haldon",
        "work": "Byzantium in the Iconoclast Era, c. 680-850: A History (Cambridge University Press, 2011)"
      },
      {
        "kind": "modern",
        "author": "Jean-Claude Cheynet (dir.)",
        "work": "Le Monde byzantin, t. II : L'Empire byzantin (641-1204), PUF, Nouvelle Clio, 2006"
      }
    ]
  },
  {
    "id": "schisme-de-1054",
    "title": "Le schisme de 1054",
    "start": 1054,
    "month": 7,
    "day": 16,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "La date des excommunications est sûre, mais leur portée est débattue : la séparation entre Églises d'Orient et d'Occident s'est faite progressivement et ne devient profonde qu'après 1204.",
    "era": "empire-romain-d-orient",
    "track": "orient",
    "category": "religion",
    "importance": 2,
    "placeId": "sainte-sophie",
    "people": [
      "humbert-de-moyenmoutier",
      "michel-cerulaire",
      "leon-ix"
    ],
    "summary": "Le 16 juillet 1054, des légats du pape conduits par le cardinal Humbert déposent sur l'autel de Sainte-Sophie une bulle excommuniant le patriarche Michel Cérulaire, qui les excommunie à son tour quelques jours plus tard. L'épisode est devenu le symbole de la séparation entre catholiques et orthodoxes, mais la rupture fut en réalité lente.",
    "body": "Au milieu du XIe siècle, Rome et Constantinople s'opposent sur l'autorité du pape, sur l'usage du pain sans levain (azyme) dans l'eucharistie et sur l'ajout du *Filioque* au Credo par les Latins. Le pape **Léon IX** envoie à Constantinople une légation dirigée par le cardinal **Humbert de Moyenmoutier**, alors que l'empereur Constantin IX cherche une alliance avec la papauté contre les Normands d'Italie du Sud.\n\nLes discussions échouent. Le 16 juillet 1054, les légats déposent sur l'autel de Sainte-Sophie une bulle d'excommunication visant le patriarche **Michel Cérulaire** et ses partisans, puis quittent la ville. Le patriarche réunit un synode qui anathématise à son tour les légats (édit lu le 24 juillet). Léon IX était mort depuis le mois d'avril, ce qui rendait la mission des légats juridiquement fragile.\n\nSur le moment, ces excommunications visent des personnes, non des Églises entières, et les contemporains n'y voient pas une rupture définitive. Le fossé se creuse surtout avec les croisades et le sac de Constantinople en 1204. Les excommunications de 1054 ont été levées le 7 décembre 1965 par le pape Paul VI et le patriarche Athénagoras.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Michel Cérulaire",
        "work": "Lettre à Pierre d'Antioche (juin ou juillet 1054)",
        "locus": "extraits, § 9 à 15 (trad. angl. T. M. Kolbaba, 2019, Internet Medieval Sourcebook)",
        "url": "https://sourcebooks.fordham.edu/halsall/source/1054michael-kerularious-to-peter-of-antioch1.asp"
      },
      {
        "kind": "ancient",
        "author": "Humbert de Moyenmoutier",
        "work": "Brevis et succincta commemoratio",
        "locus": "éd. C. Will, Acta et scripta quae de controversiis ecclesiae graecae et latinae saeculo undecimo composita extant, 1861"
      },
      {
        "kind": "modern",
        "author": "Henry Chadwick",
        "work": "East and West: The Making of a Rift in the Church. From Apostolic Times until the Council of Florence (Oxford University Press, 2003)"
      },
      {
        "kind": "modern",
        "author": "Jean-Claude Cheynet (dir.)",
        "work": "Le Monde byzantin, t. II : L'Empire byzantin (641-1204), PUF, Nouvelle Clio, 2006"
      }
    ]
  },
  {
    "id": "bataille-de-mantzikert",
    "title": "Bataille de Mantzikert",
    "start": 1071,
    "month": 8,
    "day": 26,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Les effectifs restent inconnus : les chroniqueurs donnent des chiffres invérifiables et les estimations modernes, très variables, se comptent en dizaines de milliers d'hommes ; les pertes romaines semblent avoir été plus limitées que ne le dit la tradition.",
    "era": "empire-romain-d-orient",
    "track": "orient",
    "category": "war",
    "importance": 2,
    "placeId": "mantzikert",
    "people": [
      "romain-iv-diogene",
      "alp-arslan",
      "andronic-doukas"
    ],
    "summary": "Le 26 août 1071, près de Mantzikert, en Arménie, l'empereur Romain IV Diogène est vaincu et capturé par le sultan seldjoukide Alp Arslan. Plus que la bataille elle-même, ce sont les guerres civiles qui suivent qui livrent une grande partie de l'Asie Mineure aux Turcs.",
    "body": "Pour arrêter les raids turcs en Arménie et en Asie Mineure, **Romain IV Diogène** mène en 1071 une grande expédition vers l'est. Son armée, qui mêle troupes impériales et mercenaires (Normands, Petchénègues, Turcs Oghouzes), est divisée avant la bataille : une partie, envoyée vers Akhlat, ne participe pas aux combats.\n\nLe 26 août, près de Mantzikert, au nord du lac de Van, l'empereur affronte le sultan **Alp Arslan**. Lors d'un repli en fin de journée, l'arrière-garde commandée par **Andronic Doukas**, membre d'une famille hostile à l'empereur, se retire au lieu de soutenir le centre. Romain IV est fait prisonnier, ce qui n'était plus arrivé à un empereur romain depuis Valérien, capturé par les Perses en 260. Le sultan le libère quelques jours plus tard contre un traité.\n\nMichel Attaleiatès, présent dans l'armée, et Michel Psellos, proche des Doukas, en donnent des récits opposés. Depuis les travaux de Jean-Claude Cheynet, les historiens estiment que les pertes furent limitées : la catastrophe vient surtout de la guerre civile qui suit, Romain IV étant déposé puis aveuglé en 1072, pendant que les Turcs s'installent en Asie Mineure.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Michel Attaleiatès",
        "work": "Histoire",
        "locus": "récit de la campagne et de la bataille de 1071 (trad. angl. A. Kaldellis et D. Krallis, Dumbarton Oaks Medieval Library 16, 2012)"
      },
      {
        "kind": "ancient",
        "author": "Michel Psellos",
        "work": "Chronographie",
        "locus": "livre VII, règne de Romain IV (trad. angl. E. R. A. Sewter, 1953)",
        "url": "https://sourcebooks.fordham.edu/basis/psellus-chrono07.asp"
      },
      {
        "kind": "modern",
        "author": "Jean-Claude Cheynet",
        "work": "« Mantzikert : un désastre militaire ? », Byzantion 50 (1980)"
      },
      {
        "kind": "modern",
        "author": "Carole Hillenbrand",
        "work": "Turkish Myth and Muslim Symbol: The Battle of Manzikert (Edinburgh University Press, 2007)"
      }
    ]
  },
  {
    "id": "fondation-de-l-empire-de-trebizonde",
    "title": "Fondation de l'Empire de Trébizonde",
    "start": 1204,
    "month": 4,
    "precision": "month",
    "certainty": "attested",
    "certaintyNote": "Le mois d'avril 1204 vient de la chronique de Michel Panarétos ; on ignore si la prise de Trébizonde précède ou suit de quelques jours celle de Constantinople.",
    "era": "empire-romain-d-orient",
    "track": "trebizonde",
    "category": "politics",
    "importance": 3,
    "placeId": "trebizonde",
    "people": [
      "alexis-ier-de-trebizonde",
      "david-comnene",
      "tamar-de-georgie"
    ],
    "summary": "En avril 1204, Alexis et David Comnène, petits-fils de l'empereur Andronic Ier, s'emparent de Trébizonde, sur la mer Noire, avec l'aide de leur parente la reine Tamar de Géorgie. Leur État, gouverné par les « Grands Comnènes », survit jusqu'en 1461, huit ans après la chute de Constantinople.",
    "body": "Après le renversement et la mort d'Andronic Ier Comnène en 1185, ses petits-fils **Alexis** et **David** trouvent refuge en Géorgie, auprès de la reine **Tamar**, qui leur est apparentée. En avril 1204, avec des troupes géorgiennes, ils prennent Trébizonde et la région du Pont. Cette conquête, presque contemporaine de la prise de Constantinople par les croisés, avait été préparée avant elle et indépendamment d'elle.\n\nDavid pousse vers l'ouest le long de la côte de la mer Noire, mais il se heurte à Théodore Laskaris, le souverain de Nicée. L'État de Trébizonde reste dès lors limité à une bande côtière du Pont, enrichie par le commerce avec l'Orient.\n\nSes souverains, qui se disent empereurs des Romains, portent le nom de « Grands Comnènes ». À la fin du XIIIe siècle, après le retour des Paléologues à Constantinople, ils abandonnent ce titre pour celui d'« empereur de tout l'Orient ». Trébizonde est prise par le sultan Mehmed II le 15 août 1461.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Michel Panarétos",
        "work": "Chronique des empereurs de Trébizonde",
        "locus": "première notice, année 1204 (trad. angl. S. Kennedy, Two Works on Trebizond, Dumbarton Oaks Medieval Library 52, 2019)"
      },
      {
        "kind": "modern",
        "author": "Alexander A. Vasiliev",
        "work": "« The Foundation of the Empire of Trebizond (1204-1222) », Speculum 11 (1936)"
      },
      {
        "kind": "modern",
        "author": "Anthony Bryer",
        "work": "The Empire of Trebizond and the Pontos (Variorum, 1980)"
      }
    ]
  },
  {
    "id": "sac-de-constantinople-1204",
    "title": "Sac de Constantinople par les croisés",
    "start": 1204,
    "month": 4,
    "day": 12,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Villehardouin estime la part du butin mise en commun à 400 000 marcs d'argent (500 000 selon une autre leçon du texte) ; la valeur réelle du pillage est inconnue.",
    "era": "empire-romain-d-orient",
    "track": "orient",
    "category": "war",
    "importance": 1,
    "placeId": "constantinople",
    "people": [
      "alexis-v-doukas",
      "boniface-de-montferrat",
      "baudouin-de-flandre",
      "enrico-dandolo",
      "nicetas-choniates"
    ],
    "summary": "Le 12 avril 1204, les armées de la quatrième croisade, détournée vers Constantinople avec l'appui de Venise, prennent la ville d'assaut ; le pillage commence le 13 avril et dure trois jours. Les croisés fondent un Empire latin, tandis que des princes grecs créent des États rivaux à Nicée, en Épire et à Trébizonde.",
    "body": "Partie pour l'Égypte, la quatrième croisade, endettée envers Venise, est détournée vers Constantinople pour rétablir sur le trône le prince Alexis Ange, qui avait promis argent et renforts. Après sa chute et son assassinat, le nouvel empereur **Alexis V Doukas**, surnommé Murzuphle, refuse d'honorer ces promesses. Croisés et Vénitiens, conduits notamment par **Boniface de Montferrat**, **Baudouin de Flandre** et le doge **Enrico Dandolo**, décident alors de prendre la ville pour eux-mêmes.\n\nUn premier assaut échoue le 9 avril 1204. Le 12 avril, des navires vénitiens poussés par le vent atteignent les tours de la muraille maritime de la Corne d'Or, et les assaillants entrent dans la ville. Murzuphle s'enfuit dans la nuit, pendant qu'un incendie ravage plusieurs quartiers. Le 13 avril commence un pillage de trois jours : églises, palais et maisons sont dévastés, et l'historien **Nicétas Choniatès**, témoin, en laisse un récit indigné. De nombreuses reliques et œuvres d'art partent vers l'Occident, comme les chevaux de bronze aujourd'hui à Saint-Marc de Venise.\n\nBaudouin de Flandre est couronné empereur à Sainte-Sophie le 16 mai 1204 : c'est le début de l'**Empire latin de Constantinople**. Le pouvoir romain d'Orient survit dans des États grecs successeurs, dont l'Empire de Nicée, qui reprendra la ville en 1261. Le sac de 1204 a durablement nourri l'hostilité des Grecs envers les Latins.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Geoffroi de Villehardouin",
        "work": "La Conquête de Constantinople",
        "locus": "ch. 124 à 139 de l'édition en ligne (assaut, pillage, partage du butin, élection et couronnement de Baudouin)",
        "url": "https://remacle.org/bloodwolf/francais/villehardouin/memoires3.htm"
      },
      {
        "kind": "ancient",
        "author": "Nicétas Choniatès",
        "work": "Histoire",
        "locus": "récit du sac de 1204 (extrait, trad. angl. D. C. Munro, 1912)",
        "url": "https://sourcebooks.fordham.edu/source/choniates1.asp"
      },
      {
        "kind": "modern",
        "author": "Jonathan Phillips",
        "work": "The Fourth Crusade and the Sack of Constantinople (Jonathan Cape, 2004)"
      },
      {
        "kind": "modern",
        "author": "Michael Angold",
        "work": "The Fourth Crusade: Event and Context (Longman, 2003)"
      }
    ]
  },
  {
    "id": "despotat-d-epire",
    "title": "Naissance du « despotat » d'Épire",
    "start": 1205,
    "precision": "decade",
    "certainty": "debated",
    "certaintyNote": "La date exacte est inconnue (1204 ou 1205) ; le nom de « despotat » est une appellation moderne, les premiers souverains ne portant pas ce titre.",
    "era": "empire-romain-d-orient",
    "track": "epire",
    "category": "politics",
    "importance": 3,
    "placeId": "arta",
    "people": [
      "michel-ier-doukas",
      "theodore-comnene-doukas"
    ],
    "summary": "Vers 1205, Michel Comnène Doukas, cousin des empereurs Ange, prend le contrôle de l'Épire, dans l'ouest de la Grèce, avec Arta pour centre. Cet État grec, appelé plus tard « despotat d'Épire », dispute à Nicée l'héritage de l'empire, et son souverain Théodore se fait même couronner empereur à Thessalonique.",
    "body": "**Michel Comnène Doukas**, cousin des empereurs Isaac II et Alexis III Ange, suit d'abord le croisé Boniface de Montferrat après 1204, puis le quitte pour s'établir dans l'ouest de la Grèce. Villehardouin raconte qu'il épousa la fille d'un notable grec et prit le contrôle de sa région ; les sources grecques et latines divergent sur les détails, et la date exacte (1204 ou 1205) reste discutée.\n\nDepuis Arta, Michel puis son demi-frère **Théodore** étendent leur domination vers le nord et vers la Thessalie. Théodore prend Thessalonique aux Latins en 1224 et s'y fait couronner empereur, défiant Nicée. Sa défaite face aux Bulgares à Klokotnitsa, en 1230, met fin à ces ambitions impériales.\n\nLe terme de « despotat » est une commodité des historiens : le titre de despote, dignité de la cour impériale, n'est porté par les souverains d'Épire qu'à partir de Michel II, dans les années 1230. L'Épire reste un État grec indépendant jusqu'à son annexion par l'empereur Andronic III, de 1337 à 1340 ; ses derniers restes, passés sous des souverains serbes puis italiens, tombent aux mains des Ottomans entre 1430 et 1479.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Geoffroi de Villehardouin",
        "work": "La Conquête de Constantinople",
        "locus": "ch. 160 de l'édition en ligne (Michel quitte Boniface de Montferrat et épouse la fille d'un riche Grec)",
        "url": "https://remacle.org/bloodwolf/francais/villehardouin/memoires3.htm"
      },
      {
        "kind": "modern",
        "author": "Donald M. Nicol",
        "work": "The Despotate of Epiros (Blackwell, 1957)"
      },
      {
        "kind": "modern",
        "author": "Donald M. Nicol",
        "work": "The Despotate of Epiros 1267-1479: A Contribution to the History of Greece in the Middle Ages (Cambridge University Press, 1984)"
      }
    ]
  },
  {
    "id": "empire-de-nicee",
    "title": "Théodore Laskaris, empereur à Nicée",
    "start": 1205,
    "precision": "year",
    "certainty": "debated",
    "certaintyNote": "Laskaris organise la résistance dès 1204, prend le titre impérial en 1205 et n'est couronné par un patriarche qu'en 1208 : selon les ouvrages, l'Empire de Nicée commence en 1204, 1205 ou 1208.",
    "era": "empire-romain-d-orient",
    "track": "nicee",
    "category": "politics",
    "importance": 2,
    "placeId": "nicee",
    "people": [
      "theodore-ier-laskaris"
    ],
    "summary": "Après la chute de Constantinople, Théodore Laskaris, gendre de l'empereur Alexis III, rassemble les forces romaines d'Asie Mineure autour de Nicée. Proclamé empereur en 1205 et couronné en 1208, il fonde l'État qui apparaît comme le principal héritier de l'empire et qui reprendra Constantinople en 1261.",
    "body": "Gendre de l'empereur Alexis III Ange, **Théodore Laskaris** passe en Asie Mineure au moment de la chute de la capitale. Il doit y affronter à la fois les croisés, qui cherchent à conquérir la Bithynie, et des seigneurs grecs rivaux. En 1205, il prend le titre impérial ; la même année, la lourde défaite des Latins face aux Bulgares à Andrinople desserre l'étau.\n\nLe jour de Pâques 1208, un nouveau patriarche élu à Nicée, Michel Autôreianos, le couronne et l'oint empereur. La présence du patriarche donne à Nicée une légitimité que ses rivaux d'Épire et de Trébizonde n'ont pas au même degré. La ville, où s'étaient tenus deux conciles œcuméniques, devient la capitale d'un État solidement administré.\n\nSous Jean III Vatatzès (de 1221 à 1254), l'Empire de Nicée reprend une grande partie de la Thrace et de la Macédoine. Michel VIII Paléologue, qui écarte du pouvoir le jeune Jean IV Laskaris, reprend Constantinople en 1261.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Georges Akropolitès",
        "work": "Histoire",
        "locus": "récit du règne de Théodore Ier Laskaris (trad. angl. R. Macrides, George Akropolites: The History, Oxford, 2007)"
      },
      {
        "kind": "modern",
        "author": "Michael Angold",
        "work": "A Byzantine Government in Exile: Government and Society under the Laskarids of Nicaea (1204-1261) (Oxford University Press, 1975)"
      },
      {
        "kind": "modern",
        "author": "Angeliki Laiou et Cécile Morrisson (dir.)",
        "work": "Le Monde byzantin, t. III : Byzance et ses voisins (1204-1453), PUF, Nouvelle Clio, 2011"
      }
    ]
  },
  {
    "id": "reprise-de-constantinople",
    "title": "Reprise de Constantinople par Nicée",
    "start": 1261,
    "month": 7,
    "day": 25,
    "precision": "day",
    "certainty": "attested",
    "era": "empire-romain-d-orient",
    "track": "nicee",
    "category": "war",
    "importance": 2,
    "placeId": "constantinople",
    "people": [
      "alexis-strategopoulos",
      "baudouin-ii",
      "michel-viii-paleologue"
    ],
    "summary": "Le 25 juillet 1261, une petite troupe de l'Empire de Nicée commandée par Alexis Stratègopoulos entre par surprise dans Constantinople, en l'absence de la flotte vénitienne. L'empereur latin Baudouin II s'enfuit et Michel VIII Paléologue fait son entrée solennelle le 15 août : l'empire retrouve sa capitale.",
    "body": "En juillet 1261, le césar **Alexis Stratègopoulos** est envoyé en Thrace avec une petite troupe (environ 800 hommes, en majorité des Coumans) pour surveiller les Bulgares et sonder les défenses latines. Il apprend que la garnison et la flotte vénitienne sont parties attaquer l'île de Daphnousia, dans la mer Noire.\n\nDans la nuit du 24 au 25 juillet, guidés par des habitants, ses hommes franchissent la muraille près de la porte de la Source (Pègè) et ouvrent la ville à leurs compagnons. Constantinople est prise presque sans combat. L'empereur latin **Baudouin II** s'enfuit, et la flotte vénitienne, revenue trop tard, ne peut qu'évacuer une partie des Latins.\n\n**Michel VIII Paléologue** entre dans la ville par la Porte d'Or le 15 août 1261, jour de la Dormition, et se fait couronner à Sainte-Sophie. L'Empire romain d'Orient retrouve sa capitale, mais il reste affaibli, entouré de rivaux, tandis que Venise et Gênes dominent de plus en plus ses mers.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Georges Pachymère",
        "work": "Histoire (Relations historiques)",
        "locus": "II, 26 à 31 (trad. L. Cousin)",
        "url": "https://remacle.org/bloodwolf/erudits/pachymere/histoire2a.htm"
      },
      {
        "kind": "modern",
        "author": "Deno J. Geanakoplos",
        "work": "Emperor Michael Palaeologus and the West, 1258-1282 (Harvard University Press, 1959)"
      },
      {
        "kind": "modern",
        "author": "Donald M. Nicol",
        "work": "The Last Centuries of Byzantium, 1261-1453 (Cambridge University Press, 2e éd., 1993)"
      }
    ]
  },
  {
    "id": "chute-de-constantinople",
    "title": "Chute de Constantinople",
    "start": 1453,
    "month": 5,
    "day": 29,
    "precision": "day",
    "certainty": "attested",
    "certaintyNote": "Effectifs incertains : environ 7 000 à 8 000 défenseurs selon les estimations modernes, contre 50 000 à 80 000 soldats environ pour l'armée ottomane (les témoins occidentaux donnent de 160 000 à 300 000 hommes).",
    "era": "empire-romain-d-orient",
    "track": "orient",
    "category": "war",
    "importance": 1,
    "placeId": "constantinople",
    "people": [
      "mehmed-ii",
      "constantin-xi",
      "giovanni-giustiniani"
    ],
    "summary": "Le 29 mai 1453, après un siège de près de deux mois, l'armée du sultan ottoman Mehmed II prend Constantinople d'assaut. Le dernier empereur, Constantin XI Paléologue, meurt dans les combats : c'est la fin de l'Empire romain d'Orient, plus de onze siècles après l'inauguration de la ville par Constantin, en 330.",
    "body": "Au milieu du XVe siècle, l'empire ne contrôle plus guère que Constantinople, quelques îles et la Morée. Le jeune sultan **Mehmed II** fait construire en 1452 la forteresse de Rumeli Hisar sur le Bosphore, puis met le siège devant la ville au début d'avril 1453 avec une puissante artillerie, dont un canon géant fondu par l'ingénieur Urbain (Orban).\n\nLes défenseurs sont commandés par l'empereur **Constantin XI** et par le Génois **Giovanni Giustiniani Longo**, venu avec 700 hommes. Sphrantzès, chargé du recensement, compte 4 773 Grecs en état de combattre et seulement 200 étrangers environ, chiffre sans doute trop bas pour ces derniers ; les historiens estiment l'ensemble des défenseurs à 7 000 ou 8 000 hommes. L'armée ottomane, bien plus nombreuse, fait passer le 22 avril une partie de sa flotte par voie de terre jusque dans la Corne d'Or.\n\nAvant l'aube du 29 mai, après l'échec des premières vagues d'assaut, les janissaires percent la muraille terrestre ; Giustiniani, blessé, est évacué et la défense cède. Constantin XI meurt dans les combats, et son corps n'a jamais été identifié avec certitude. La ville est livrée au pillage, Sainte-Sophie devient une mosquée et Constantinople la capitale ottomane. Des États romains d'Orient survivent encore quelques années : la Morée jusqu'en 1460, Trébizonde jusqu'en 1461.",
    "sources": [
      {
        "kind": "ancient",
        "author": "Georges Sphrantzès",
        "work": "Chronique (Chronicon minus)",
        "locus": "XXXV, 6 et 9 (trad. angl. M. Philippides, 1980)",
        "url": "https://deremilitari.org/2016/08/the-siege-of-constantinople-in-1453-according-to-george-sphrantzes/"
      },
      {
        "kind": "ancient",
        "author": "Kritoboulos",
        "work": "Histoire de Mehmed le Conquérant",
        "locus": "I, 117 à 257 (trad. angl. C. T. Riggs, 1954)",
        "url": "https://deremilitari.org/2016/08/the-siege-of-constantinople-in-1453-according-to-kritovoulos/"
      },
      {
        "kind": "modern",
        "author": "Steven Runciman",
        "work": "The Fall of Constantinople 1453 (Cambridge University Press, 1965)"
      },
      {
        "kind": "modern",
        "author": "Angeliki Laiou et Cécile Morrisson (dir.)",
        "work": "Le Monde byzantin, t. III : Byzance et ses voisins (1204-1453), PUF, Nouvelle Clio, 2011"
      }
    ]
  }
]
