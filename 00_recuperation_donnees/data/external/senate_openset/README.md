# senate_openset — collectes tierces côté Sénat

- **`ssw_all_daily_summaries.json`** (2,6 Mo, 1 442 dépôts) — l'export **senate-stock-watcher** :
  une collecte publique indépendante qui re-lit les mêmes dépôts eFD officiels. Lu par
  `common/crosscheck.py :: load_ssw_lines` — **c'est lui qui produit le « 99,7 % retrouvées à la
  transaction près » du §8 du rapport.** Instantané téléchargé (daté), jamais réinjecté.
- **`kadoa_filers.json`** (432 entrées) — résumé par déposant de l'export Kadoa (liste
  `{full_name, chamber, trade_count…}`), utilisé par `tests/regression/test_crosscheck.py` via
  `crosscheck.load_kadoa_house`. Vestige utile du contrôle de la semaine 1.
