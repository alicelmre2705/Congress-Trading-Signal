# png/ — les images de la partie données : qui produit quoi, qui consomme quoi

Les deux documents vivent **à la racine du dossier** : `SLIDES_DONNEES.pdf` (le deck) et
`RAPPORT_DONNEES.md` (LE rapport, régénérable : `python -m common.quality`). Ici, uniquement
leurs images — chaque image est utilisée par un document vivant ; les orphelines ont été
archivées le 2026-08-11 (dans `_archive/docs/` de la branche `presentation`, avec les decks
qu'elles servaient).

| dossier | contenu | produit par | consommé par |
|---|---|---|---|
| `figs_deck/` (63) | les figures **fixes** du deck : entonnoirs, schémas, captures annotées | figées (pas de code producteur — extraites des notebooks d'époque ou faites à la main) | le deck (62) ; 6 aussi reprises par `RAPPORT_FINAL` et `FICHE_NETTOYAGE_BACKTEST_V2` |
| `quality/` (9) | les figures du rapport des données | `common/quality.py` (savefig — le dossier = exactement ses 9 sorties, régénérées avec le rapport) | le rapport (9) + le deck (`top_deposants`) |
| `figs_pop/` (41) | population & portraits — la partie II du deck | `02_recherche_backtest/strate_2_copier_les_membres/12_Population_et_Portraits.ipynb` (le dossier = exactement ses savefig) | le deck (13 ; le reste = les cartes par membre, même famille) |

Cas particuliers : `figs_deck/fig_senat_types.png` a un producteur vivant
(`common/quality.py`, §10 du rapport — régénérée à chaque run) ; les CSV de preuve de la
validation Quiver sont dans `../data/quiver_validation/` (produits par
`common/quiver_diagnosis.py`, cités par le rapport).
