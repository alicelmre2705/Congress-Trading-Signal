# `data/clean/` — les 4 tables de recherche (LE produit)

| table | dimensions | contenu |
|---|---|---|
| `transactions_brut_2014_2026.csv` | 169 000 × 41 | **la brute** : tout le corpus unique, avec pour chaque ligne écartée son étape et son motif (`exclusion_etape`, `exclusion_motif`) — rien d'écarté en silence |
| `transactions_backtest_2014_2026.csv` | 134 452 × 39 | **la clean** : la table de recherche canonique (celle que `02_recherche_backtest/` consomme) |
| `transactions_gated_2014_2026.csv` | 7 287 × 13 | les scans manuscrits écartés par la politique OCR (`house/ocr.py`), avec leur motif |
| `commissions_membre_congres.csv` | 3 707 × 3 | annexe : texte complet des commissions et sous-commissions par élu × Congrès (jointure `bioguide_id` × `congress`) |

- **Produites par** : `common/backtest_clean.py` (step 7 du pipeline) — les étapes, leur code et
  leurs référentiels : **§7 de `../../RAPPORT_DONNEES.md`**.
- **Consommées par** : la recherche (`02_recherche_backtest/`, dont `tools/donnees.py`) et le
  §7-§8 du rapport.
- **Régénérables hors-ligne** depuis un clone : `python -m common.backtest_clean` ; verrouillées
  par `tests/regression/test_backtest_clean.py` (« ZÉRO ÉCART » attendu, SHA256 au manifest).
