# Tests de non-régression — le filet du dépôt

Deux étages de preuve, tous **hors-ligne** :

1. **Golden octet-à-octet** — toutes les sorties du pipeline (`data/*/tables/`) sont gelées par
   SHA256 : 230 fichiers House + 138 Sénat. Tout mouvement non voulu est détecté.
2. **Reproduction fonction-par-fonction** — chaque transformation (clé naturelle, montants,
   tickers, identité, ancienneté, cache Vision, nettoyage) est recomputée depuis les colonnes
   figées et comparée à la valeur stockée — la preuve isole le code des aléas réseau/OCR.

Depuis que la **source primaire des deux chambres est embarquée** (8 252 PDF House dans
`data/house/pdfs/`, 3 788 pages eFD dans `data/senate/reports/`), la collecte elle-même est
rejouable localement — le filet, lui, n'en a jamais eu besoin : il ne lit que les artefacts
figés.

Lancer toute la suite (depuis `00_recuperation_donnees/`) :

```bash
.venv/bin/python tests/regression/check_golden.py         # golden House  (230 fichiers, sha256)
.venv/bin/python tests/regression/senate_check_golden.py  # golden Sénat  (138 fichiers, sha256)
.venv/bin/python tests/regression/test_backtest_clean.py  # les 4 tables de data/clean/ (sha256)
for t in test_schema test_amounts_tickers test_identity test_tenure test_first_seen test_live_run \
         test_crosscheck test_vision_sha test_incremental test_senate_repro audit_metrics; do
  .venv/bin/python tests/regression/$t.py || echo "ÉCHEC: $t"
done
```

Tout doit dire « ZÉRO ÉCART » / « ✅ ».

## Index

| Fichier | Prouve / sert à |
|------|--------|
| `check_golden.py` / `build_golden.py` | Les 230 sorties House reproduisent le golden (sha256) ; `build_golden.py` (re)gèle l'empreinte. |
| `senate_check_golden.py` / `senate_build_golden.py` | Idem Sénat (138 fichiers). NB : `_scan_census_senat.csv` (139ᵉ CSV, ajouté après le gel) est volontairement hors manifest — le check le signale « en trop », c'est attendu. |
| `test_backtest_clean.py` | **Le step 7 de bout en bout** : reconstruit les 4 tables de `data/clean/` hors-ligne et les compare au manifest (`backtest_clean_manifest.json`, shapes + sha256 + entonnoir). `--build` re-fige. |
| `audit_metrics.py` | Recompte les métriques des FINAL crus et les confronte aux invariants figés (House 152 081 = 58 756 + 93 325 · Sénat 18 839 = 14 813 + 4 026 · identité). |
| `test_schema.py` | `common.schema.natural_key_hash` = drop-in exact des deux moteurs. |
| `test_amounts_tickers.py` | `amount_midpoint` / `infer_asset_type` reproduisent les colonnes figées, sans PDF. |
| `test_identity.py` | Le matcher `house.identity` reproduit les bioguides figés. |
| `test_tenure.py` | `years_in_office` recomputé == valeur figée des 26 FINAL. |
| `test_crosscheck.py` | Statuts de triangulation : un déposant papier sans contrepartie Quiver ressort `ocr_unique` ; Khanna (vu par Quiver) sort `quiver_validable`. |
| `test_vision_sha.py` | Le SHA du prompt OCR == celui des caches (déplacer le code n'invalide pas le cache payé). |
| `test_incremental.py` | 2ᵉ run OCR = 0 appel Vision (cache versionné par `(prompt_sha, model)`). |
| `test_senate_repro.py` | Le pipeline Sénat re-logé reproduit les colonnes des FINAL gelées — **sur les 18 839 lignes 2014-2026** (natural_key_hash, recover_ticker, identité). |
| `test_first_seen.py` | Les invariants du journal d'horodatage (`data/first_seen/first_seen.csv`) : append seul, aucun doc_id réobservé, `first_seen_at` qui ne recule pas, doc_id toujours texte, sources dans le contrat. **Sans réseau.** |
| `test_live_run.py` | Le run en direct produit les 12 champs de la table de référence, et n'écrit **jamais** dans `data/*/tables/` (sha256 des 369 tables, avant/après). Vérifie aussi `signal_date = max(disclosure_date, first_seen_at)`. **Sans réseau.** |

## Couverture, dite honnêtement

- Le golden couvre **tout `data/*/tables/` 2014-2026**, à l'octet.
- `test_backtest_clean` couvre le **step 7 entier** (la chaîne corpus → 4 tables).
- Les tests de reproduction couvrent les transformations unitaires des deux chambres ;
  `test_senate_repro` balaie l'intégralité des lignes Sénat (18 839/18 839).
- Ce qui n'est **pas** couvert : le bout-en-bout réseau (scraping/téléchargement) — par
  construction, le filet est hors-ligne ; la collecte se vérifie par la couverture vs l'index
  officiel (§1 du rapport) et la corroboration externe (§8).
