# data/external — jeux externes de triangulation (crosscheck)

Données d'agrégateurs tiers utilisées **uniquement** pour la vérification croisée (`common.crosscheck`),
jamais réinjectées dans les tables de production.

- `senate_openset/` — export **Kadoa** (open dataset). `kadoa_filers.json` = résumé par déposant
  (nom → nombre de trades), consommé par `tests/regression/test_crosscheck.py` via
  `crosscheck.load_kadoa_house`. Les autres JSON = détail par sénateur.
- `hsw.json` *(optionnel, absent par défaut)* — miroir House/Senate Stock Watcher ; le test dégrade
  proprement s'il manque (`if HSW.exists()`).

Provenance : migré depuis l'ancien `_archive/semaine 1/data/external/` lors de la consolidation
(2026-06-26), pour rendre le dépôt autonome sans dépendre des dossiers archivés.
