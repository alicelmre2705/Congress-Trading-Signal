# data/external — collectes tierces de corroboration (§8 du rapport)

Données de collecteurs tiers utilisées **uniquement** pour la vérification croisée
(`common/crosscheck.py`), **jamais réinjectées** dans les tables de production — une source qui
sert à construire ne peut pas servir à vérifier.

- **`house_openset/`** — `hsw_all_transactions.json` (11,4 Mo, **23 675 transactions
  2012-2026**) : l'export **house-stock-watcher**, collecte publique indépendante des mêmes PTR
  officiels. Lu par `crosscheck.load_hsw_lines` → le **« 99,6 % retrouvées à la transaction
  près »** du §8. Détail : [son README](house_openset/README.md).
- **`senate_openset/`** — `ssw_all_daily_summaries.json` (**senate-stock-watcher**, 1 442
  dépôts) → le **« 99,7 % »** du §8 ; + `kadoa_filers.json` (résumé Kadoa, 432 déposants,
  utilisé par `test_crosscheck`). Détail : [son README](senate_openset/README.md).
- `hsw.json` *(optionnel, absent par défaut)* — ancien emplacement attendu par
  `test_crosscheck.py`, qui dégrade proprement s'il manque.

Provenance : instantanés téléchargés en 2026-06/07 (datés dans les README de chaque
sous-dossier) ; l'historique de leur migration vit sur la branche `presentation`.
