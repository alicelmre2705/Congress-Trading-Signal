# Congress Trading Signal — Recherche stratégie (Semaines 3-4)

**Toute la recherche tient dans un seul notebook autonome : [`Congress_Trading_Signal_Recherche.ipynb`](Congress_Trading_Signal_Recherche.ipynb).**

On le lit de haut en bas et on comprend tout — **aucun fichier `.py` à ouvrir** : la **Partie 0** définit
l'intégralité du moteur (chargement, prix, event-study, portefeuille, métriques, sélection) en cellules
courtes et expliquées ; les **Parties I-IX** racontent la recherche (contexte → données → event-study →
chasse au signal → backtest générique → stratégie Ramify V1 actions → V2 ETF → approfondissement →
littérature → verdict). Déjà exécuté (sorties + graphiques sauvegardés), relançable sur le kernel
*S3S4 (.venv)*.

- **Seules dépendances** : `numpy / pandas / scipy / scikit-learn / matplotlib / pyyaml` (aucun module maison).
- **Données** (lecture seule) : caches Quiver + tables FINAL du dépôt, et les prix dans `cache/` (gitignoré).
- **Recherche ISOLÉE** : écriture uniquement dans ce dossier ; rien du travail finalisé n'est touché.

**Verdict** : alpha actions positif mais non significatif (V1), dilué en ETF (V2), aucune version ne bat SPY
en risque-ajusté → produit thématique livrable (à la NANC/KRUZ), pas un générateur d'alpha.

*Les versions antérieures (notebooks séparés, modules `.py`, notes) sont conservées dans `_archive/`.*
