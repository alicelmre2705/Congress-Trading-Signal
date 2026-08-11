# docs/ — qui produit quoi, qui consomme quoi

Deux documents, quatre dossiers. Chaque image du dossier est utilisée par un document vivant —
les orphelines ont été archivées le 2026-08-11 (`../_archive/docs/`, avec les decks qu'elles
servaient).

| entrée | contenu | produit par | consommé par |
|---|---|---|---|
| `SLIDES_DONNEES_S1S2_V2` (.tex + .pdf) | **le deck de la partie données** (141 pages physiques, overlays compris) | compilé par tectonic | — |
| `RAPPORT_QUALITE` (.md + .pdf) | **la certification des chiffres** (couverture, identité, validation Quiver) | `python -m common.quality` | cité par le deck et le README racine |
| `figs_deck/` (63 png) | les figures **fixes** du deck : entonnoirs, schémas, captures annotées | figées (pas de code producteur — extraites des notebooks d'époque ou faites à la main) | le deck (62) ; 6 sont aussi reprises par `RAPPORT_FINAL` et `FICHE_NETTOYAGE_BACKTEST_V2` (branche `presentation`) |
| `quality/` (9 png) | les figures du rapport de qualité | `common/quality.py` (savefig — le dossier = exactement ses 9 sorties) | le rapport (9) + le deck (`top_deposants`) |
| `figs_pop/` (41 png) | population & portraits — la partie II du deck | `02_recherche_backtest/12_Population_et_Portraits.ipynb` (le dossier = exactement ses savefig) | le deck (13 ; le reste = les cartes par membre, même famille) |
| `quiver_validation/` (13 csv) | les verdicts de la validation Quiver, ligne à ligne | `common/quiver_diagnosis.py` | le rapport de qualité (§6) |

Cas particulier : `figs_deck/fig_senat_types.png` a un producteur vivant —
`../Analyse_Types_Rapports_Senat.ipynb` (son `savefig` pointe ici).
