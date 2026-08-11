# _archive/ — documents supplantés du dossier `01_autres_filing_types/`

Rien n'est supprimé dans ce dépôt : ce qui est remplacé est déplacé ici (`git mv`), avec son motif.
Les versions courantes vivent à la racine du dossier : **`SYNTHESE_EXTRACTION_HOUSE`** (porte
d'entrée) et **`FICHE_HOUSE`** (la fiche de référence), plus les decks de `slides/`.

**Règle des figures** (README racine du dépôt, posée le 2026-07-31) : une archive doit être
**auto-contenue** — les figures qu'un document archivé inclut sont **copiées** sous ce dossier
(`figures/`, `figs/`), jamais lues depuis l'actif. Preuve rejouable : chaque `.tex` ci-dessous
compile depuis son emplacement (`~/.local/bin/tectonic -o /tmp <fichier>.tex`), vérifié le
2026-08-11 (10/10).

⚠️ **Ne jamais dédoublonner par nom** : `figures/fig_10_recouvrement.png` (ici) ≠
`../figures_house/fig_10_recouvrement.png` (actif) — même nom, contenus différents (aussi :
`fig_10_quadrant`, `fig_10_trois_zones`, `fig_10_valeur_part`, `fig_10_nav`).

## Passe du 2026-07-21 → 26 (bascule vers le notebook unique puis FICHE_HOUSE)

| document | remplacé par | motif |
|---|---|---|
| `10_Stock_Divulgations_MathSpec_v7_20260721.ipynb` | le notebook racine homonyme | v7 archivée le 21/07 ; **le notebook racine est PLUS RÉCENT** (sections « Carte de population » + savefig ajoutées le 21/07 après la bascule). Renommé avec date le 2026-08-11 pour lever l'ambiguïté — il y avait 3 fichiers homonymes dans le dépôt (le 3ᵉ, encore plus ancien, est dans `02_recherche_backtest/_archive/`) |
| `FICHE_10_CHRONOLOGIE.pdf/.tex` (6 p., v7) | `FICHE_HOUSE` | fiche de la lignée notebook 10, close |
| `FICHE_BACKTEST_HOUSE.pdf/.tex` | `FICHE_HOUSE` | fusionnée dedans le 26/07 |
| `FICHE_DONNEES_HOUSE.pdf/.tex` | `FICHE_HOUSE` | idem ; le `.tex` avait été reconstitué à l'identique depuis le PDF (worktree perdu) |
| `FICHE_PORTEFEUILLES_HOUSE.pdf/.tex` (8 p.) | `FICHE_PORTEFEUILLES_HOUSE_V2` puis `FICHE_HOUSE` | v1 de la fiche portefeuilles |

## Passe du 2026-08-11 (rangement avant publication de la Partie 1 sur `main`)

| document | motif |
|---|---|
| `FICHE_10_CHRONOLOGIE_v5.pdf/.tex` (7 p.) | la **v5** restée à la racine alors que la v7 (ci-dessus) était déjà archivée — suffixe `_v5` pour éviter la collision de nom |
| `FICHE_PORTEFEUILLES_HOUSE_V2.pdf/.tex` (7 p.) | supplantée par `FICHE_HOUSE`. ⚠️ le PDF a été committé **5 h avant** son `.tex` (commits `f2cc6509` puis `fdafda12`) : le PDF publié ne provient pas exactement de ce `.tex` |
| `FICHE_PORTEFEUILLES_HOUSE_V2_PORTRAIT.pdf` (3 p.) | PDF orphelin — sa source `.tex` n'a jamais été committée, aucun document n'y renvoie |
| `FICHE_10_QUI_EST_QUI.pdf` (1 p.) | **pas une fiche** : une figure matplotlib exportée en PDF (doublon sémantique de `../figures/fig_10_qui_est_qui.png`), jamais eu de `.tex` |
| `livraison_backtest/` | **livraison morte** : son fichier d'entrée annoncé (`flux_backtest.csv`) n'a jamais existé, aucun notebook de `02_recherche_backtest/` ne la consomme. NB : son renvoi `../FICHE_DONNEES_HOUSE.pdf` résout désormais correctement depuis ici |
| *(racine)* `FICHE_PORTEFEUILLES_HOUSE.pdf` | **supprimé de la racine** (seule suppression) : doublon octet-à-octet (`md5 9aa93f94…`) du PDF déjà archivé ci-dessus — aucun contenu perdu |
| *(déplacé au dossier 00)* `SLIDES_DONNEES_S1S2` (81 p., 14/07) | ce deck appartient à la lignée S1/S2 du dossier `00_recuperation_donnees/` (toutes ses images y vivent) → `00_recuperation_donnees/_archive/docs/SLIDES_DONNEES_S1S2_20260714.*` |

**Réparation du même jour** : les `.tex` de ce dossier avaient **37 inclusions d'images cassées**
(documents déplacés sans leurs figures — la faute que le README racine documente). Les figures
attendues ont été **copiées** sous `_archive/figures/` depuis `../figures/` (leurs versions du
moment de la publication). Aucun `.tex` de fiche n'a été modifié.
