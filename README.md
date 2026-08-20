# Congress Trading Signal — pipeline de données

Extraction et validation des déclarations boursières (PTR, *STOCK Act*) des membres du Congrès américain
— **Chambre des représentants + Sénat, 2014 → 2026** — en vue d'une stratégie de copy-trading.

Sources officielles : *House Clerk* (PTR PDF) et Sénat *eFD*, **électroniques** (parsing déterministe)
**+ scannées** (OCR Claude Vision). Quiver Quantitative sert de **vérification externe uniquement**,
jamais réinjecté dans les tables.

> **Publication par parties** — un commit par partie, dans l'ordre du projet :
> **Partie 0 — récupération & nettoyage des données** (`00_recuperation_donnees/`) ·
> **Partie 1 — au-delà des PTR** (`01_autres_filing_types/` : Schedule A/B, rapports annuels,
> photos d'entrée, portefeuilles House reconstruits) ·
> **Partie 2 — la recherche stratégie & les backtests** (`02_recherche_backtest/`).
> Cette branche ne garde que **ce qui se montre** : les supports de présentation, les documents de
> référence et la donnée certifiée. Le brief de mission, les documents de travail (audit-réparation,
> rapport d'architecture, analyses intermédiaires), les archives et tout l'historique vivent sur la
> branche `presentation`.

## 🧭 Par où commencer — Partie 2 (la stratégie)

0. **[le README de la partie](02_recherche_backtest/README.md)** — le résultat et le chemin en
   trois dossiers ; et **[PISTES_TESTEES.md](02_recherche_backtest/PISTES_TESTEES.md)** —
   l'inventaire complet des **~90 pistes testées**, chacune avec son résultat chiffré et
   l'endroit où c'est prouvé, pour ne jamais ré-explorer une piste morte ;
1. **[FICHE_M3.pdf](02_recherche_backtest/3_livrable_M3/FICHE_M3.pdf)** — **LE livrable** : la stratégie M3
   (pondérer au dollar *et* au nombre d'élus, +3,40 %/an d'excès côté démocrate sur 2014-2026),
   sa version ETF, et le portefeuille final à **deux poches** (SPY + signal sectoriel, dose pilotée
   par le budget de risque). Adossée au notebook `M3_preuve_complete.ipynb` — tout ce que la fiche
   affirme y est établi ;
2. **[PAPIER_METHODE.pdf](02_recherche_backtest/2_noter_les_titres/PAPIER_METHODE.pdf)** — les quatre méthodes M1→M4
   côte à côte (établies dans `noter_les_titres.ipynb`) ;
3. **[FICHE_NOTER_LES_TITRES.pdf](02_recherche_backtest/2_noter_les_titres/FICHE_NOTER_LES_TITRES.pdf)** — la
   spécification de la ligne « par titre » et ses six tests ;
4. **[AUDIT_FONDS_NANC_GOP.pdf](02_recherche_backtest/2_noter_les_titres/AUDIT_FONDS_NANC_GOP.pdf)** — ce que les
   documents officiels des ETF NANC/GOP disent (17 pièces citées, passages surlignés ;
   version auto-portante : `AUDIT_FONDS_NANC_GOP_COMPLET.pdf`, 798 p.) ;
5. **[ETAT_DE_L_ART_STRATEGIES.md](02_recherche_backtest/2_noter_les_titres/ETAT_DE_L_ART_STRATEGIES.md)** — 69
   fiches de littérature vérifiées en source primaire.

Le chemin de la recherche, dans l'ordre des trois dossiers : `copier_les_membres` (**pas
d'alpha** ; + `etudes/` — la population, les portraits) →
`noter_les_titres` (noter les **titres** plutôt que copier les élus : méthodes M1-M4, répliques
NANC/GOP et Quiver) → **`M3_preuve_complete`** (M3 complet + version ETF + le livrable deux
poches) et `M3_table_pipeline` (la même lignée rejouée sur la table courante du pipeline —
aucune conclusion ne change). Le socle des deux derniers est le paquet
**[`tools/`](02_recherche_backtest/tools/README.md)** — les moteurs extraits et prouvés
(`python -m tools.test_ancres` rejoue M3 et retrouve les ancres gelées ;
`python -m tools.membre.test_ancres_membre` fait de même pour la famille membre, dont
`copier_les_membres` et `tables_membres_tickers` sont aussi en génération 2 sur la table
courante du pipeline).

## 🧭 Par où commencer — Partie 1 (au-delà des PTR)

1. **[SYNTHESE_EXTRACTION_HOUSE.pdf](01_autres_filing_types/SYNTHESE_EXTRACTION_HOUSE.pdf)** —
   le document maître de la partie : ce qui a été extrait, vérifié, et avec quelles garanties ;
2. **[FICHE_HOUSE.pdf](01_autres_filing_types/FICHE_HOUSE.pdf)** — la fiche de référence
   (synthèse graphique données + backtest) ;
3. les deux decks : **[SLIDES_DONNEE_HOUSE_court.pdf](01_autres_filing_types/slides/SLIDES_DONNEE_HOUSE_court.pdf)**
   (39 p.) et **[SLIDES_AUTRES_DEPOTS.pdf](01_autres_filing_types/slides/SLIDES_AUTRES_DEPOTS.pdf)** (35 p.).

La chaîne de production : `V1_House.ipynb` (l'usine — index du Clerk → **20 tables gelées** dans
`cache/tables/` + `MANIFEST.json` sha256) → `Portefeuilles_House_Complet.ipynb` (**le notebook de
livraison**, P0→P7, chaque partie avec son bloc de validation) + `10_Stock_Divulgations_MathSpec.ipynb`
(la stratégie « partir du portefeuille d'entrée ») + `Recuperation_photos_entree.ipynb`.
`reference/` embarque des entrées **irremplaçables** (les 13 index XML instantanés du Clerk — le
site purge les années anciennes — et les caches OCR payés).

## 🧭 Par où commencer — Partie 0 (les données)

0. **[le README de la partie](00_recuperation_donnees/README.md)** — la carte du dossier :
   structure, commandes, les 4 tables livrées ;
1. **[SLIDES_DONNEES.pdf](00_recuperation_donnees/SLIDES_DONNEES.pdf)** — le
   deck de présentation de la partie (certifié conforme à sa source `.tex`) ;
2. **[RAPPORT_DONNEES.md](00_recuperation_donnees/RAPPORT_DONNEES.md)** — **LE rapport,
   régénérable** (`python -m common.quality`, dernier step du pipeline — relancer = tous les
   chiffres recalculés depuis la donnée) : couverture vs l'index officiel du Clerk, validation
   Quiver par ère, nettoyage (§7), corroboration externe (§8), papier Sénat (§9), types de
   dépôts Sénat (§10) — les preuves derrière chaque nombre.

**Les tables prête-recherche** vivent dans `00_recuperation_donnees/data/clean/` — **brute**
(169 000 × 41, tout le corpus avec le verdict d'entonnoir par ligne), **clean**
(`transactions_backtest_2014_2026.csv`, **118 316 × 39** — PROPRE au sens plein depuis le
2026-08-12 : fenêtre 2013-2026 et couverture prix dans l'entonnoir A→F du pipeline ;
parti/commissions point-in-time, tickers canoniques Yahoo, flags, invariants garantis) et **gated**
(7 287 manuscrites écartées, avec motif) + la table annexe des commissions
(bioguide × Congrès, sous-commissions résolues). Produites par `common/backtest_clean.py` (step 7 du
pipeline, testé par le filet de non-régression). **Les étapes du nettoyage et leur code :
le §7 du rapport.**

Tout le pipeline se lance par **un seul point d'entrée** :

```bash
python -m common.pipeline --years 2014-2026            # tout est embarqué : la source primaire des DEUX chambres
python -m common.pipeline --years 2026 --acquire       # --acquire : compléter une année nouvelle (idempotent)
python -m common.pipeline --years 2024 --dry-run       # voir la séquence sans rien exécuter
```

## Structure

```
00_recuperation_donnees/
  common/   contrat UNIVERSEL : reference · schema (clé, fixes read-time, canonical_ticker) ·
                   sector_enrich · vision_ocr · crosscheck · backtest_clean (step 7 : brute→clean) ·
                   quality (step 8 : LE rapport, régénérable) · quiver_diagnosis (§6) ·
                   quiver_scopes · enrich_tenure (ancienneté) · report_pdf · pipeline (orchestrateur)
  house/    pipeline Chambre  : digital · acquire (téléchargement index+PDF) · classify_scans ·
                   ocr · identity · amounts · tickers · quiver · echantillon
  senate/   pipeline Sénat    : digital · ocr · ocr_engine · fusion · identity · ticker · quiver ·
                   census_probe · report_types_probe (collecteurs eFD opt-in) ← jumeau de house/
  data/            données  (house/ · senate/ · external/ · reference/ ← renommages tickers, carte
                   secteurs, snapshots commissions par Congrès · clean/ ← table canonique)
  (racine)         README.md (la carte du dossier) · SLIDES_DONNEES (le deck, .tex + .pdf) ·
                   RAPPORT_DONNEES (.md + .pdf — régénérable)
  png/             les images : figs_deck/ (le deck) · quality/ (le rapport) · figs_pop/
                   (etude_portraits du 02) — le README de png/ dit qui produit quoi
  tests/regression/ filet « zéro changement » : golden + preuves de reproduction (sans réseau)
01_autres_filing_types/
  V1_House.ipynb · Portefeuilles_House_Complet.ipynb · 10_Stock_Divulgations_MathSpec.ipynb ·
  Recuperation_photos_entree.ipynb          la chaîne décrite ci-dessus
  FICHE_HOUSE.* · SYNTHESE_EXTRACTION_HOUSE.*   les deux documents de référence
  slides/          SLIDES_DONNEE_HOUSE_court · SLIDES_AUTRES_DEPOTS (+ leurs figures)
  cache/           le contrat gelé : 20 tables CSV + MANIFEST.json (sha256)
  reference/       entrées irremplaçables : index XML instantanés du Clerk, caches OCR, YAML élus
  figures/ figures_house/   figures des fiches et decks
02_recherche_backtest/
  README.md        le résultat et le chemin en trois dossiers
  PISTES_TESTEES.md  l'inventaire : ~90 pistes testées, résultats chiffrés, pièges,
                   et la correspondance noms historiques ↔ fichiers renommés
  tools/           les moteurs des DEUX familles (titre · membre/), extraits et prouvés sur
                   leurs chiffres témoins
  tables_membres_tickers.ipynb + tables/   le socle : les 4 tables propres et leur producteur
  1_copier_les_membres/   copier_les_membres (la strate) + etudes/ (population · portraits)
  2_noter_les_titres/     noter_les_titres (socle, tests, méthodes) · replique_NANC_GOP ·
                          repliques_quiver · PAPIER_METHODE · FICHE_NOTER_LES_TITRES ·
                          AUDIT_FONDS_NANC_GOP(_COMPLET) · ETAT_DE_L_ART · figs/ ·
                          docs_nanc_gop/ · docs_nanc_gop_surlignes/ (les 18 pièces)
  3_livrable_M3/          M3_preuve_complete (sur tools, gen 2) · M3_table_pipeline (la table
                          courante) · FICHE_M3 · figs/ · ancres_table_courante.json
pyproject.toml   installable :  pip install -e .
```

**Asymétries House/Sénat assumées** (le reste des modules est symétrique) :
- `senate/fusion.py` (House fusionne *inline* dans `ocr.py`) — **volume** : le Sénat enrichit sur tout le
  corpus en une passe (mutualise le dico de tickers), House fusionne année par année.
- `senate/ocr_engine.py` (House garde son OCR *inline*) — **forme OCR divergente** (House : scans PDF,
  cases A–K ; Sénat : `.gif`, fourchettes \$ explicites) + moteur figé pour le golden.
- montants : `house/amounts.py` (midpoints `.0`) vs map Sénat (`.5`) dans `senate/ocr_engine.py` —
  divergence **voulue** ; la formule `amount_midpoint` (6 l.) reste propre à chaque chambre (découplage).

## Chiffres clés

| Chambre | FINAL (uniques) | brut = digital + OCR | Identité | Concordance Quiver |
|---|---|---|---|---|
| **House** | **151 989** | 152 081 = 58 756 + 93 325 | 100 % (367 bioguides) | in-window : **93,5 %** des trades Quiver retrouvés — §6 |
| **Sénat** | **17 011** | 18 839 = 14 813 + 4 026 | 100 % (78 bioguides) | in-window : **92,1 %** ; 98–100 %/an |

**Périmètre d'analyse = 169 000 transactions uniques de membres élus** (House 151 989 + Sénat 17 011), après
**dédup cross-année** des re-divulgations tardives. Le pipeline produit **170 920 lignes brutes**. Une
déclaration de **collaborateur non-élu** (HASC) est exclue du périmètre membres. **100 % des 8 252 PTR
listés par l'index officiel du Clerk 2014-2026 sont traités** (parsés, OCRisés, ou gated par règle écrite).
Détail : `00_recuperation_donnees/RAPPORT_DONNEES.md` (§1 « Couverture vs l'univers officiel »).

> **Fenêtre 2014-2026** — les scans **manuscrits** sont **écartés** par une politique uniforme et
> **rejouable** (cluster `C_manuscrit`, 582 docs gated ; exceptions explicites dans `house/ocr.py`).
> Avant ~2017, Quiver est **mince** : nos actions « en plus » sont réelles mais peu corroborables (§6
> « honnêteté par ère ») — senate-stock-watcher les confirme côté Sénat (100 % hors échanges). Un
> backtest doit entrer sur `disclosure_date` (anti-look-ahead).

Les deux chambres ont la **table 12/12 champs** (identité, ticker, secteur GICS→ETF, date, montant…) :
House ticker **84,1 %** / secteur **79,8 %** ; Sénat ticker **77,9 %** / secteur **70,4 %** (les vides =
actifs **non cotés** — munis/obligations — sans ticker/secteur légitimes ; taux sur le corpus unique,
récupérations read-time incluses). Validation externe Quiver **par scope** (digital/OCR/both) et **par
ère** ; au **Sénat**, l'OCR papier est surtout du non-coté que Quiver ne suit pas → source **interne**.

## Installation & vérification

```bash
python3.12 -m venv .venv
./.venv/bin/pip install -e .

# Filet de non-régression (doit afficher « ZÉRO ÉCART ») :
./.venv/bin/python 00_recuperation_donnees/tests/regression/check_golden.py         # House — 230 fichiers
./.venv/bin/python 00_recuperation_donnees/tests/regression/senate_check_golden.py  # Sénat — 138 fichiers
./.venv/bin/python 00_recuperation_donnees/tests/regression/test_backtest_clean.py  # les 4 tables clean
# Preuve de reproduction fonction-par-fonction (Sénat entier) :
./.venv/bin/python 00_recuperation_donnees/tests/regression/test_senate_repro.py    # natural_key_hash 18 839/18 839 (2014-2026)
```

Seuls les dépôts nouveaux et la validation Quiver exigent le réseau ; la correction est prouvée
par **reproduction depuis les colonnes figées** (`tests/regression/`), et le nettoyage + le
rapport (steps 7-8) se rejouent **100 % hors-ligne** depuis un clone.

**Note data** : la **source primaire des deux chambres est embarquée en entier**. House : les 13
index `{Y}FD.xml` et **tous les PDF bruts des PTR 2014-2026** (`data/house/pdfs/`, un dossier
par année — 8 252 documents, un par dépôt officiel de l'index). Sénat : **toutes les pages eFD
brutes** (`data/senate/reports/` — un HTML par dépôt des tables FINAL, 2 128 / 2 128, plus les
scans `.gif` du papier). Chaque ligne des tables est re-vérifiable contre son document source,
sans rien télécharger ; le filet golden ne lit que `data/*/tables/`. Compter **~1 Go** au clone —
c'est le prix de l'autonomie.
Re-exécuter certains notebooks des Parties 1 et 2 exige en plus des caches de prix locaux non
versionnés (ils se reconstruisent via yfinance) ; les tables gelées (`cache/tables/` du 01,
`tables/` du 02) et les quelques caches non re-téléchargeables (N-PORT, OCR récupéré, prix de
tickers disparus) sont, eux, embarqués. Les sorties des notebooks restent lisibles dans les
`.ipynb` sans rien exécuter.

## Avertissement

Les données proviennent de documents **publics officiels** (STOCK Act — déclarations obligatoires
des élus) ; elles restent **nominatives** et sont fournies telles que déclarées, avec leurs limites
documentées. Ce dépôt est un **travail de recherche** : rien ici ne constitue un conseil en
investissement.
