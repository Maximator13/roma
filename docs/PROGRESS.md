# Avancement

Le cahier des charges est dans `docs/BRIEF.md`. Ce fichier garde l'état du projet d'une session à l'autre.

## Phase 0 : cadrage (en cours)

### Fait

- Environnement vérifié : Node 24.18, npm 11.16, git 2.55, gh 2.102 (connecté au compte Maximator13), ffmpeg 9.0.1 (avec libx264), Blender 5.2.2 LTS et KTX-Software 4.4.2 (tous deux hors PATH, appelés par leur chemin complet).
- Dépôt initialisé sur la branche `main`, avec une identité de commit masquée.
- Cahier des charges rangé dans `docs/BRIEF.md`.

### Décisions validées (14 octobre 2026)

1. **Dépôt** : dossier `C:\Users\maxim\Projets VSCode\roma`, dépôt public `Maximator13/roma`, site `https://maximator13.github.io/roma/`, donc `base` Vite `/roma/`.
2. **Identité des commits** : `Maximator13 <329881135+Maximator13@users.noreply.github.com>`, l'adresse masquée fournie par GitHub, réglée pour ce dépôt seulement.
3. **Licences** : code sous MIT ; contenus originaux (textes, données, modèles et vidéos produits par les scripts) sous CC BY 4.0 ; données dérivées de sources ODbL ou CC BY-SA rangées dans des fichiers séparés, sous leur propre licence ; GSAP sous sa licence propre (gratuite, non libre), signalée dans `CREDITS.md`.
4. **Assets lourds** : binaires optimisés (`.glb`, `.ktx2`, `.mp4`, tout fichier de plus de 1 Mo) publiés dans des GitHub Releases versionnées ; un manifeste versionné donne pour chacun son chemin, sa taille, son empreinte SHA-256 et sa release ; le workflow de déploiement les télécharge et les met en cache. Scripts `assets:publish` et `assets:pull` écrits en phase 2. Les fichiers `.blend` et les rendus intermédiaires ne sont jamais versionnés : les scripts Blender les régénèrent.
5. **Mesure d'audience** : GoatCounter (gratuit, sans cookie), chargé seulement après consentement explicite (refus par défaut) ; inactif tant que le compte GoatCounter n'est pas créé.
6. **Mentions légales** : éditeur publié sous le pseudonyme Maximator13, hébergeur GitHub, contact par les issues du dépôt.
7. **Référencement** : une page HTML statique par événement générée au build (titre, description et image Open Graph uniques), qui redirige vers la route `#/evenement/<slug>` ; ces pages alimentent `sitemap.xml`, déclaré directement dans la Search Console ; pas de dépôt `Maximator13.github.io`.
8. **Sources** : auteurs antiques, avec des traductions consultables en ligne (Perseus, LacusCurtius, remacle.org), et ouvrages de référence (Oxford Classical Dictionary, Cambridge Ancient History, Oxford Dictionary of Byzantium, manuels universitaires français).
9. **Machine de référence** : i7-1065G7, Intel Iris Plus, 12 Go. Objectif : 60 i/s en qualité automatique sur cette machine. Aucune autre machine signalée ; les temps de rendu Blender seront estimés en phase 2.
10. **Écriture des dates** : « av. J.-C. » une seule fois par intervalle (« de 509 à 27 av. J.-C. ») ; pas de suffixe après notre ère, sauf pour les années 1 à 99 et le Ier siècle (« de 27 av. J.-C. à 14 apr. J.-C. », mais « de 27 av. J.-C. à 235 »).

### Constats de la recherche de cadrage

- GitHub Pages : site publié de 1 Go au plus, déploiement de 10 minutes au plus, bande passante indicative de 100 Go par mois, en-têtes HTTP non configurables (`Cache-Control: max-age=600`, compression gzip seulement, appliquée aussi aux `.glb` et `.wasm`), dépôt public obligatoire sur un compte gratuit.
- Stack du brief conservée en WebGL 2 : le WebGPU n'est pas encore stable avec R3F, drei et le post-traitement.

### Suite

- Proposition d'architecture et plan détaillé de la phase 1, à valider.
