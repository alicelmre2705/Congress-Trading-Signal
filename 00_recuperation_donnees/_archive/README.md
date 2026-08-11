# _archive/ — supplanté du dossier `00_recuperation_donnees/`

Rien n'est supprimé : ce qui est remplacé est déplacé ici (`git mv`). Les documents de référence
à jour vivent à la racine du dossier : `RAPPORT_DONNEES.md` (LE rapport, régénérable) et
`SLIDES_DONNEES.pdf` (le deck) — plus, sur cette branche seulement, AUDIT_DONNEES_2014_2026,
RAPPORT_FINAL, FICHE_NETTOYAGE_BACKTEST_V2 et les 2 ANALYSE_*.

```
docs/            rapports et decks supplantés (RAPPORT_COMPLET, RAPPORT_V2_*, ARCHITECTURE,
                 SLIDES_DONNEES_S1S2 (26/06) · SLIDES_DONNEES_S1S2_20260714 (14/07, rapatrié du
                 dossier 01 le 2026-08-11 — graphicspath réparé, figures figs/ copiées, compile) ·
                 SLIDES_BACKTEST · FICHE_NETTOYAGE_BACKTEST v1 · FICHE_RESUME · plans de slides)
data_external/   senate_openset (kadoa, ssw) — remplacé par ../data/external/ (README y documente
                 la migration)
house/ tools/ congress_core/   scripts et notebooks des refontes successives
(_archive/ interne — DÉMÉNAGÉ le 2026-08-11 : les notebooks RAMIFY_V1/V2, SUPP_*, le moteur
                 backtest .py et PATCHS_S3S4_A_APPLIQUER.md étaient du matériel de recherche S3/S4 ;
                 ils vivent désormais dans 02_recherche_backtest/_archive/recherche_v0/)
```

⚠️ Collision de nom assumée : `docs/RAPPORT_FINAL.*` (ici, version du 26/06) ≠
`../docs/RAPPORT_FINAL.*` (la version courante du 04/07) — même nom, contenus différents.

## 2026-08-11 (soir) — le notebook de nettoyage archivé

Le nettoyage vit désormais dans **`common/backtest_clean.py`** (step 7 du pipeline, testé par
`tests/regression/test_backtest_clean.py`) et se lit au **§7 de `../RAPPORT_DONNEES.md`** — les
étapes et leur code, sans notebook, comme le reste du pipeline (le recensement intermédiaire
`NETTOYAGE.md` du 11/08 est archivé ici : `NETTOYAGE_20260811.md`).
`Nettoyage_Backtest_2014_2026_vitrine.ipynb`
(ex-vitrine du module, et avant elle le notebook qui portait toute la logique) est archivé ici.
La table de recherche du 2026-07-04 (celle des documents publiés) est dans `data_clean/`.

## 2026-08-11 (nuit) — plus un seul notebook au 00 : le rapport les absorbe

Le rapport devient LE document : **`../RAPPORT_DONNEES.md`** (ex-`RAPPORT_QUALITE.md`, renommé et
régénéré — `python -m common.quality`, step 8 du pipeline : à chaque relance, tous les chiffres
suivent la donnée ; le PDF : `python -m common.report_pdf`). Les trois notebooks d'analyse de la
racine sont convertis en sections du rapport et archivés ici :

- `Analyse_Types_Rapports_Senat.ipynb` → **§10** (les CSV mesurés sur l'eFD sont versionnés dans
  `../data/senate/`, avec leur date de mesure ; le collecteur réseau opt-in :
  `python -m senate.report_types_probe` ; la figure du deck `fig_senat_types.png` a désormais un
  producteur vivant — reproduite octet pour octet avant bascule) ;
- `Analyse_Scans_Papier_Senat.ipynb` → **§9** (100 % rejouable depuis les artefacts versionnés ;
  le « 3 985 » n'est plus un littéral, il est dérivé du corpus) ;
- `Corroboration_Externe_SSW_HSW.ipynb` → **§8** (la logique était déjà `common/crosscheck.py` —
  les outputs figés du notebook étaient d'ailleurs périmés de 12 lignes sur la table d'entrée :
  l'argument même du rapport vivant).

Le deck est renommé `SLIDES_DONNEES.*` (ex-`SLIDES_DONNEES_S1S2_V2`) ; ses figures 7a/7b portent
en dur l'entonnoir certifié du 18/07 (134 464 × 36) — la réconciliation avec la table courante
vit au §7 du rapport et dans `../NOTE_DIFF_TABLE_CLEAN.md`.
