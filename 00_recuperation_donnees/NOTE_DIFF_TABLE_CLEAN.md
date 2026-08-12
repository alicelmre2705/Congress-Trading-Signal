# Note de version — tables de recherche du 2026-08-11 (diff contre la v1 du 2026-07-04)

**Ce qui a changé de structure.** Le nettoyage backtest est désormais **du code de pipeline** :
`common/backtest_clean.py`, step 7 de `python -m common.pipeline`, testé par
`tests/regression/test_backtest_clean.py` (« ZÉRO ÉCART »), avec le notebook
le notebook d'origine (archivé) comme trace. Avant toute correction, le module a
**reproduit octet pour octet** la table v1 (134 464 × 36) — chaque écart ci-dessous est donc
une correction voulue, pas une dérive.

**Trois tables au lieu d'une** (décision : « une table brute et une table clean ») :

| table | dimensions | contenu |
|---|---|---|
| `transactions_brut_2014_2026.csv` | 169 000 × 41 | tout le corpus assemblé ; verdict d'entonnoir par ligne (`exclusion_etape`, `exclusion_motif`) — **rien d'écarté en silence** |
| `transactions_backtest_2014_2026.csv` | **134 452 × 39** | la clean (entonnoir A→D + corrections ci-dessous) |
| `transactions_gated_2014_2026.csv` | 7 287 × 13 | les transactions des scans manuscrits gated (cluster C/B, dont 6 482 républicaines — biais du gating documenté), récupérées par une passe OCR une-fois (`data/house/ocr_gated_recovered.csv`, non régénérable) |
| `commissions_membre_congres.csv` | 3 707 × 3 | table annexe : le texte complet des commissions **et sous-commissions résolues**, par `bioguide_id × congress` (jointure) |

## Les corrections, une à une (toutes mesurées)

1. **Tickers faux-positifs — 152 lignes** (`data/reference/ticker_false_positives.csv`, 26 règles).
   Le ticker était extrait à tort d'une parenthèse descriptive : « NetApp (IRA) » portait le
   ticker `IRA`, « FACEBOOK INC CL-A » le ticker `A` (qui est… Agilent). 140 lignes corrigées
   vers le vrai symbole (NTAP ×56, FB ×18, RDS-B ×13, SHEL ×10, CMD ×8, LEN ×7, CHTR ×5, NVS ×4,
   HST ×4, CBRE ×2, STZ, LBRDA, QVCA, DATA, POAGX, CWI…) ; **12 lignes vidées** (préférentielles
   6 %/6,5 %, obligation municipale, note Nasdaq, société non cotée US) qui sortent de la clean
   — visibles dans le brut avec leur motif. D'où **134 464 → 134 452**.

2. **Renommages complétés — +12 lignes au référentiel** (`ticker_renames.csv`, 84 → 96).
   Les 10 « renommages continus » que la recherche rattrapait à la main hors pipeline
   (`cache/prices_v2_recup/`, sans producteur) sont désormais dans le référentiel, **chacun
   vérifié sur cours le 2026-08-11** : MMC→MRSH (218 lignes), FI→FISV (212), TTS→TTSH (78),
   NLOK→GEN (69), CNHI→CNH (63), DSW→DBI (40), ABB→ABBNY (39), PEAK→DOC (37), CMCSK→CMCSA (22),
   XON→PGEN (10) — soit **788 lignes re-symbolisées** ; + CMD→STE et DATA→CRM (fusions, prudence
   prix). Et la ligne **FISV inversée** : Yahoo sert la série sous FISV, pas sous FI — les
   119 lignes FISV ne sont plus redirigées vers un symbole mort. Total `ticker_yahoo` changé :
   **932 lignes**.

3. **Carte secteur réparée** (`ticker_sector_map.csv`, les deux copies 00 et 01).
   Les 8 fonds que la table contredisait (« Mutual Fund » ∧ « stock ») : EDR redevient ce qu'il
   est (un REIT — Real Estate/XLRE, pas « Communication ») ; FDN, IXP, PNQI, VOX, VNQ, IYR, SCHH
   reclassés `etf_sector` avec leur proxy ; CWI ajouté. Effet : `asset_class` change sur
   **148 lignes**, `sector_gics` sur **202** (78 ETF perdent un secteur par convention, 70 lignes
   corrigées en gagnent un, 54 sont corrigées — p.ex. les 24 « Health Care → Communication » sont
   les lignes Facebook/Charter qui portaient le secteur… d'Agilent). La carte **datée** du
   notebook 16 (bascules XLRE 16/09/2016 et XLC 21/09/2018 + 45 attributions nominatives) est
   versée au référentiel : `ticker_sector_map_datee.csv`.

4. **Sous-commissions résolues** (patch 9 de PATCHS_S3S4, le dernier résiduel).
   122 984 lignes portaient des codes bruts (`HSAG15`…) dans `committee_membership` → **0** ;
   le texte devient « House Committee on Agriculture — Conservation, Energy, and Forestry »
   (repli « parent — sous-commission NN » pour l'unique code hors référentiel). Le texte est
   **normalisé dans la table annexe** `commissions_membre_congres.csv` — l'inliner sur chaque
   ligne aurait plus que doublé le poids des tables (au-delà de la limite GitHub) ; la ligne de
   transaction garde `congress` et `committees_key_flag`. Conséquence de
   fond : **`committees_key_flag` passe de 72 793 à 86 473 lignes vraies (+13 680)** — les élus
   qui ne siégeaient qu'à une *sous-commission* d'une commission clé sont désormais comptés,
   comme le sens du flag l'exige.

5. **Le schéma passe de 36 à 39 colonnes** : +`owner_n` (owner normalisé — conjoint/élu/joint/
   enfant/autre), +`member_name_canon` (nom canonique par bioguide), +`ticker_groupe` (classes
   d'actions fusionnées GOOG/BRK-B/FOX/NWS — la table que les notebooks 11/16 déclaraient
   localement), +`amount_open_bracket` (fin de la sentinelle « 1 000 001 $ » reconnue par égalité
   flottante en aval) ; −`committee_membership` (normalisée dans la table annexe ci-dessus).

## Ce qui ne bouge PAS

- Les **FINAL gelées et les goldens** (230 + 138) : toutes les corrections sont read-time.
- **La recherche publiée** (notebooks 05b→16, FICHE_M3, PAPIER_METHODE, deck) reste adossée à la
  **v1 archivée** : `_archive/data_clean/transactions_backtest_2014_2026_v20260704.csv`. Ses
  ancres (134 464 × 36, 113 369 lignes du périmètre M3…) restent vraies **pour la v1** ; toute
  recherche future part de la table courante. La table Quiver jumelle (orpheline, producteur
  archivé) est archivée au même endroit.
- Le rapport (certifié le 18/07 sur la v1 sous le nom `RAPPORT_QUALITE.md`) a été **renommé
  `RAPPORT_DONNEES.md` et régénéré le 11/08** : il porte désormais les chiffres de la table
  courante, et se régénère à chaque run (`python -m common.quality`, step 8 du pipeline).

## 2026-08-12 — la table clean devient PROPRE au sens plein (entonnoir A→F)

Décision d'Alice : « la table propre, c'est : tu épures les tickers qui ne fonctionnent pas, et
les dates qui ne fonctionnent pas non plus. » Deux étapes rejoignent l'entonnoir du pipeline :
**E** — fenêtre 2013-2026 (35 trades exécutés en 2012, déclarés dans des dépôts ultérieurs) ;
**F** — couverture prix (16 101 trades sur 1 321 tickers sans série exploitable — référentiel
versionné `data/reference/couverture_prix_v20260812.csv`, extrait daté du cache de la recherche
par `python -m tools.couverture_prix`). **134 452 → 118 316 × 39.** Ces filtres existaient déjà —
chaque notebook de recherche les rejouait localement : les périmètres de recherche sont
INCHANGÉS (flux titre 113 645 ; famille membre 118 316/266/223 — portes vérifiées), le 𝒯^brut
(134 417, 372 membres) se lit désormais dans la table BRUTE (verdicts ∅+F). Au passage, OWNER_N
couvre « Dependent Child » et « Joint Tenancy » (fin des 26 875 « autre/inconnu »). La
corroboration externe (§8 du rapport) se mesure sur le corpus A→D (table brute) — la collecte ne
dépend pas de notre couverture prix.
