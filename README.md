# Roma, de Romulus à Constantin XI

Un site pour étudier l'histoire romaine, de la fondation de Rome (753 av. J.-C., date traditionnelle) à la chute de Constantinople (1453). La frise chronologique en est la colonne vertébrale ; chaque grand événement ouvre une scène 3D.

Site : https://maximator13.github.io/roma/ (en construction)

## Développement

Il faut Node 24 ou plus récent.

```bash
npm install
npm run dev
```

| Commande | Rôle |
|---|---|
| `npm run dev` | serveur de développement |
| `npm run check` | style, lint, typage et tests unitaires |
| `npm run build` | validation des données puis build de production dans `dist/` |
| `npm run test:e2e` | tests de fumée Playwright sur le build |

## Licences

Code sous licence MIT (`LICENSE`). Contenus originaux sous licence CC BY 4.0 (`LICENSE-CONTENT.md`). Ressources de tiers : voir `CREDITS.md`.
