# `data/quiver_validation/` — les preuves ligne à ligne de la validation Quiver

Les 13 CSV d'annexe du **§6 du rapport** (`../../RAPPORT_DONNEES.md`) : les listes actionnables
derrière chaque agrégat — écarts de ticker, vrais trous (`notre_manque_*`), lignes qu'on a et que
Quiver n'a pas (`on_est_plus_complet_*`), désaccords de champ typés, candidats d'écart de date,
non-coté Quiver.

- **Produits par** : `common/quiver_diagnosis.py`, **réécrits à chaque
  `python -m common.quality`** (step 8) — ce sont des annexes de preuve, pas des tables de
  travail.
- **Hors golden** : régénérables, donc non gelés.
