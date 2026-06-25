# Pipeline Sénat — Transactions boursières des sénateurs (PTR)
## Q1 2025 — synthèse complète des résultats

Corpus vérifié des *Periodic Transaction Reports* du Sénat américain, **1ᵉʳ trimestre 2025**, extrait
directement de l'eFD (efdsearch.senate.gov), au standard House (même schéma 23 colonnes, même
validation QuiverQuant). Quiver = **vérification externe seulement**, jamais réinjecté dans la table.

---

## ► Résultat à utiliser

| Fichier | Contenu |
|---|---|
| **`data_v1_senate/tables/06_senate_2025q1_FINAL.csv`** | Table **complète** : **375 transactions** (283 électroniques + 92 OCR papier) · 18 sénateurs · 37 PTR |
| `data_v1_senate/tables/senate_2025q1_FINAL.xlsx` | Le même + onglets synthèse / validation / QA / index (portable) |
| `data_v1_senate/tables/06_senate_2025q1_transactions.csv` | Électronique seul (283) |
| `data_v1_senate/tables/06b_senate_2025q1_ocr_transactions.csv` | OCR papier seul (92) |

---

## 1. Vue d'ensemble

| Indicateur | Valeur |
|---|---|
| Période couverte | Q1 2025 (divulgation 01/01 → 31/03) |
| PTR traités | **37** (33 électroniques + 4 papier OCR) |
| **Transactions** | **375** (283 électroniques + 92 OCR papier) |
| Sénateurs | **18** |
| Identité (bioguide rattaché) | **100 %** (0 non rattaché) |
| Couverture ticker | **50,9 %** global · 67,5 % sur l'électronique |
| Volume (midpoint) | **$41,6 M** ($23,6 M élec + $18,0 M OCR) |
| **Couverture Quiver (transaction-niveau)** | **100 %** — 0 trade manqué |
| Échecs de parsing / batch OCR / QA flags | **0 / 0 / 0** |

---

## 2. Ce qui est extrait

| Dimension | Électronique | OCR papier | **Total** |
|---|---:|---:|---:|
| Rapports | 33 | 4 | **37** |
| Transactions | 283 | 92 | **375** |
| Sénateurs | 17 | 1 (Blumenthal) | **18** |
| Volume midpoint | $23,6 M | $18,0 M | **$41,6 M** |

**`asset_type`** (100 % renseigné) :

| Stock | Option | Municipal Security | Corporate Bond | Other |
|---:|---:|---:|---:|---:|
| 166 | **28** | 70 | 18 | 93 |

> Les 28 **Option** (« AMAT PUT », « MU CALL »…) sont isolées du nom de l'actif — le formulaire eFD
> les déclare « Stock ». Les 93 « Other » = véhicules privés OCR (LLC / fonds familiaux Blumenthal).

**`ticker_source`** :

| explicit | asset_name | none |
|---:|---:|---:|
| 152 | 39 | 184 |

> `none` (184) = 88 obligations (munis 70 + corporate 18, CUSIP seulement) + 92 OCR privés + 4 cas
> nommés — **sans ticker boursier par construction**, jamais inventé. Sur les actifs *tickérisables*
> (actions / ETF / options) : **≥ 99 %**.

**Opérations** : Purchase 233 · Sale (Full) 73 · Sale (Partial) 45 · Sale 24.
**Détenteur (`owner`)** : Spouse 180 · Self 95 · Joint 91 · Child 9.
**Dates** : transaction 2024-02-18 → 2025-03-20 ; divulgation 2025-01-02 → 2025-03-29.

---

## 3. Validation contre QuiverQuant

Fenêtre comparable : Quiver filtré sur sa date de divulgation `Filed` ∈ Q1 2025 **et** sur les vrais
sénateurs de notre référentiel → **163 transactions / 15 sénateurs**.

### 3.1 Comparaison par sénateur (`07_quiver_comparison.csv`)

| Sénateur | nous | Quiver | Δ | verdict |
|---|---:|---:|---:|---|
| Richard Blumenthal (OCR papier) | 92 | 0 | +92 | quiver_sans_donnee |
| David McCormick | 73 | 12 | +61 | nous_plus |
| Markwayne Mullin | 66 | 53 | +13 | nous_plus |
| Ashley Moody | 44 | 15 | +29 | nous_plus |
| John Boozman | 38 | 38 | 0 | concordant |
| Shelley Capito | 24 | 22 | +2 | nous_plus |
| John Fetterman | 9 | 0 | +9 | quiver_sans_donnee |
| Rick Scott | 6 | 0 | +6 | quiver_sans_donnee |
| Tuberville, Wyden, Whitehouse, McConnell, Rubio, Smith, Banks, Carper, Moran, Hagerty | 1–6 | = | 0 | concordant |
| **Total** | **375** | **163** | **+212** | — |

**11 concordants · 4 nous_plus · 3 quiver_sans_donnee · 0 delta négatif.** On ne sous-compte jamais
Quiver. *(Eleanor Holmes Norton, déléguée DC à la Chambre, est exclue par le filtre chambre — colonne
`is_senator` ; ce n'était pas un dépôt Sénat manqué.)*

### 3.2 Réconciliation transaction-à-transaction (`07c` / `07f`)

Clé `bioguide × ticker × date × sens`, sénateurs communs, actifs tickérisables :

| matched | only_quiver | only_ours | **couverture** |
|---:|---:|---:|---:|
| 152 | **0** | 23 | **100,0 %** |

**0 trade Quiver manqué** (`07f_quiver_only_quiver_txn.csv` vide). Les 23 `only_ours` sont des trades
réels en plus (options Moody, occurrences Mullin) — additifs, pas du bruit.

### 3.3 Accord par champ (`07d_quiver_field_agreement.csv`)

| Champ | Accord | Note |
|---|---:|---|
| **Date** (Traded) | **100,0 %** | apparie sur `Traded` = vraie date de trade (vs `Filed` 0,7 %) |
| **Montant** (bucket) | 100 % ensemble / 95,8 % paires | Quiver `Trade_Size_USD` = borne basse exacte de la fourchette |
| **Sens** (achat/vente) | 96,9 % | résidu = artefact option-vs-action déclarées le même jour |
| **Ticker** par sénateur | Σ quiver_seul = **0** | tous les tickers de Quiver sont chez nous (`07e`) |

Écart `07b` ticker-niveau = **1** seul : Hagerty `AHL-C` (nous) vs `AHL.C` (Quiver) — même opération
du 02/01/2025, ponctuation près.

### 3.4 Catégorisation des deltas positifs (Σ = +212)

| Sénateur | Δ | Cause |
|---|---:|---|
| Blumenthal | +92 | OCR papier (Quiver n'indexe aucun de ses dépôts) |
| McCormick | +61 | 52 munis + 9 corporate bonds (Quiver ne suit pas les obligations) |
| Moody | +29 | options vendues le même jour que l'action (Quiver ne les isole pas) + ventes |
| Mullin | +13 | occurrences supplémentaires (mêmes tickers, Δ ticker = 0) |
| Fetterman | +9 | dépôt absent de Quiver |
| Rick Scott | +6 | dépôt absent de Quiver |
| Capito | +2 | obligations sans ticker |

### 3.5 Validation OCR (4 PTR papier)

Les 4 rapports papier sont tous du sénateur **Richard Blumenthal** (B001277), extraits par Claude
Vision (`tool_use`, cache versionné) → **92 transactions** (24+35+30+3), identité 100 %, **0 échec
batch**. Les plages de dates par rapport collent **exactement** aux lettres d'accompagnement
(14607985 : 08–17/01 · 4fbbf6be : 27/01–10/02 · 8e8ae815 : 26/02–04/03 · d7d35e4a : 27/12/2024),
grâce à un garde-fou millésime.

---

## 4. Limites connues (où les stats sont bonnes / pas)

- **Ticker — solide là où il existe, plafonné par construction.** 50,9 % global est un **plafond
  structurel ≈ 57 %** : 88 obligations (CUSIP seulement) + 92 OCR de véhicules privés n'ont **aucun**
  ticker boursier. Sur les actifs tickérisables : ≥ 99 %. Jamais comblé via Quiver.
- **`asset_type` / `operation_type` OCR moins précis.** Le formulaire papier n'a pas de colonne Asset
  Type (inféré du nom → « Other ») et ne distingue pas Sale (Full)/(Partial) → `Sale` simple.
- **Sens / montant à 95–97 % (et non 100 %).** Écart non dû à une erreur : artefact d'appariement
  quand un sénateur déclare une option **et** l'action sur le même titre/jour (Quiver n'en garde
  qu'une). Au niveau ensemble, montant et ticker concordent à 100 %.
- **Accès eFD fragile.** Gate CSRF + Akamai ; aucune évasion — on s'appuie sur le cache local
  (`reports/*.html` + `reports/media/*.gif`).
- **Complétude annuelle.** Q1 2025 = 37 PTR (réalité d'un trimestre). Avant une extension
  multi-années, recouper le *nombre* de PTR/an avec le dataset public `senate-stock-watcher`.

---

## 5. Reproductibilité & fichiers

**Dossier 100 % autonome** : référentiel législateurs vendu en local (`data_v1_senate/reference/`),
secrets `.env` (gitignoré), env `.venv` (`requirements.txt`). Aucune lecture hors du dossier.

```
cd "1 SENAT/senat_2025_test"
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env        # ANTHROPIC_API_KEY (OCR) + QUIVER_API_KEY (validation)
```

1. **`notebook_v1_senate_2025q1.ipynb`** — agrément eFD, liste des PTR (`report_types=[11]` = PTR),
   téléchargement + parsing HTML, identité bioguide, dédup non destructrice → 283 électroniques.
2. **`.venv/bin/python senate_ocr.py`** — OCR des 4 PTR papier (Claude Vision) → 92 transactions.
3. **`.venv/bin/python senate_finalize.py`** — fusion digital + OCR, enrichissement ticker,
   reclassement des options, **validation Quiver** (tables `07`–`07f`), Excel. *Idempotent* (seul
   Quiver est re-téléchargé ; l'OCR est servi du cache).

| Fichier (`data_v1_senate/`) | Rôle | Lignes |
|---|---|---|
| `tables/06_senate_2025q1_FINAL.csv` | **Table complète digital + OCR** | 375 |
| `tables/06_…_transactions.csv` / `06b_…_ocr_…csv` | Électronique / OCR seul | 283 / 92 |
| `tables/01_ref_universe` · `02_ref_senate_key` | Référentiel · commissions clés | 12 767 · 71 |
| `tables/03_ptr_index` · `04_report_manifest` | Index / statut des 37 PTR | 37 |
| `tables/05_parse_failures` · `06c_qa_flags` · `06c_ocr_failures` | Marqueurs « 0 échec » | 0 |
| `tables/07_quiver_comparison` | Par sénateur (+ `is_senator`, verdict) | 18 |
| `tables/07b_quiver_ticker_gaps` | Écart ticker (1 : ponctuation) | 1 |
| `tables/07c_quiver_txn_reconciliation` | Couverture txn (matched/only_*) | — |
| `tables/07d_quiver_field_agreement` | Accord sens / date / montant | — |
| `tables/07e_quiver_ticker_per_senator` · `07f_quiver_only_quiver_txn` | Ticker/sénateur · trades manqués (vide) | — / 0 |
| `tables/_quiver_senate_cache.csv` | Cache Quiver (hors table) | 13 342 |
| `reports/*.html` · `reports/media/*.gif` · `ocr_cache/*.json` | Sources / cache offline | 37 · 16 · 4 |

**Schéma (23 colonnes).** Identité : `bioguide_id, declarant_name, chamber, party, state_district`
(= État seul), `committee_membership, committees_key_flag`. Dates : `transaction_date,
disclosure_date`. Actif : `ticker, asset_description, asset_type`. Opération : `operation_type,
amount_range, amount_midpoint, amount_split_flag` (toujours False côté Sénat), `owner`. Traçabilité :
`doc_id, source_url, natural_key_hash, provenance` (`senate-efd-electronic` | `senate-efd-ocr`),
`ticker_source` (`explicit` | `asset_name` | `none`), `occurrence_index` (rang d'un lot répété
intra-rapport — dédup non destructrice).

---

**En une ligne.** Sénat Q1 2025 : **375 transactions** (283 électroniques + 92 OCR papier),
**18 sénateurs**, identité **100 %**, ticker **50,9 %** (≥ 99 % sur les tickérisables). Validation
Quiver : **couverture transaction 100 %**, **0 trade manqué**, nous ≥ Quiver partout (Σ Δ = +212),
date/montant concordants. Point dur structurel : ticker des obligations/véhicules privés, absent par
construction.
