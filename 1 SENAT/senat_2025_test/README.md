# Sénat — Transactions boursières des sénateurs (PTR), Q1 2025

Corpus vérifié des transactions déclarées par les membres du Sénat américain (Periodic Transaction
Reports) sur le **1ᵉʳ trimestre 2025**, extrait directement de l'**eFD** (efdsearch.senate.gov). C'est
l'**équivalent Sénat** de la version figée `0 HOUSE/Q1_2025/` — même schéma, même validation
QuiverQuant, mêmes principes (transparence, Quiver = vérification seulement, aucune évasion anti-bot).

> Le Sénat n'est **pas** présenté comme la Chambre : pas de PDF/XML en masse mais des **rapports HTML**
> derrière un **gate CSRF** ; pas de district (l'État seul) ; et un mix d'actifs **beaucoup plus
> obligataire** (bons municipaux, corporate bonds) où le ticker est légitimement absent.

---

## ⭐ Le résultat à utiliser

| Fichier | Contenu |
|---|---|
| **`data_v1_senate/tables/06_senate_2025q1_transactions.csv`** | La table **COMPLÈTE** : 280 transactions électroniques · 17 sénateurs · 33 PTR. |
| **`data_v1_senate/tables/senate_2025q1_FINAL.xlsx`** | Le même + onglets synthèse / validation / QA / index. Rendu portable. |
| **`RAPPORT_VALIDATION.md`** | Comment les données ont été validées contre Quiver (à lire pour le contexte). |

---

## Chronologie / comment reproduire

Environnement Python : `../../semaine 1/.venv` (pandas, requests, pyyaml, openpyxl). Clé
`QUIVER_API_KEY` dans `../../.env` (racine du dépôt).

1. **`notebook_v1_senate_2025q1.ipynb`** — accepte l'agrément eFD, liste les PTR de la fenêtre,
   télécharge + parse les rapports HTML électroniques (les 4 papier vont en `backlog.csv`), rattache
   l'identité (bioguide) et écrit `senate_2025q1_transactions.csv`.
2. **`senate_finalize.py`** — reprend cette sortie et l'amène au standard House Q1 :
   - **fiabilise l'identité** (les 4 sénateurs récents : McCormick `M001243`, McConnell `M000355`,
     Banks `B001299`, Hagerty `H000601`) → **100 % rattachées** ;
   - **enrichit le ticker** depuis l'Asset Name quand la colonne Ticker eFD est vide (`--`) → 54 % → **67 %** ;
   - **valide contre Quiver** (1 appel, Chambre = Sénat, fenêtre de divulgation Q1) ;
   - écrit les **tables numérotées 01→07**, les **QA flags** et l'**Excel** final.

```
cd "1 SENAT/senat_2025_test" && ../../"semaine 1"/.venv/bin/python senate_finalize.py
```

> Idempotent : ré-exécuter `senate_finalize.py` reproduit exactement les mêmes sorties (seul Quiver
> est re-téléchargé). Quiver n'entre **jamais** dans la table — il sert uniquement à recouper.

---

## Carte des fichiers (`data_v1_senate/`)

| Fichier | Rôle | Lignes |
|---|---|---|
| **Référence** | | |
| `tables/01_ref_universe.csv` | Tous les législateurs (lookup bioguide) | 12 767 |
| `tables/02_ref_senate_key.csv` | Sénateurs en commissions clés (Finance/Armed/Intel/Banking) | 71 |
| **Pipeline** | | |
| `tables/03_ptr_index.csv` | Index des dépôts Q1 2025 (33 électroniques + 4 papier) | 37 |
| `tables/04_report_manifest.csv` | Statut par dépôt (électronique parsé / backlog OCR) | 37 |
| `tables/05_parse_failures.csv` | Rapports électroniques non parsés — **vide = 0 échec** | 0 |
| **★ Données — à utiliser** | | |
| `tables/06_senate_2025q1_transactions.csv` | **Table complète (électronique)** | 280 |
| `tables/senate_2025q1_FINAL.xlsx` | Classeur Excel : transactions + synthèse + validation + QA + index | — |
| **Validation / QA** | | |
| `tables/06c_qa_flags.csv` | Anomalies (champ obligatoire manquant) — **vide = aucune** | 0 |
| `tables/07_quiver_comparison.csv` | Comparaison par sénateur (nous vs Quiver) + verdict | 18 |
| `tables/07b_quiver_ticker_gaps.csv` | Trades (ticker,date) que Quiver a et pas nous | 1 |
| `tables/_quiver_senate_cache.csv` | Cache Quiver Sénat (vérification, hors table) | 13 342 |
| **Backlog** | | |
| `backlog.csv` | 4 rapports **papier** (OCR requis) — lacune connue v1 | 4 |
| `reports/*.html` | Rapports eFD mis en cache (offline) | 37 |

---

## Dictionnaire des colonnes (table finale)

`bioguide_id`, `declarant_name`, `chamber`, `party`, `state_district`,
`committee_membership`, `committees_key_flag` · identité du sénateur (`state_district` = **État seul**,
le Sénat n'a pas de district).
`transaction_date`, `disclosure_date` · dates (transaction / divulgation).
`ticker`, `asset_description`, `asset_type` · actif. **Ticker souvent absent sur les obligations**
(bons municipaux, corporate bonds) — c'est normal, pas une faille.
`operation_type` (Purchase / Sale (Full) / Sale (Partial)), `amount_range`, `amount_midpoint`,
`owner`, `doc_id`, `source_url`, `natural_key_hash`.
`provenance` · `senate-efd-electronic`.
`ticker_source` · `explicit` (colonne Ticker eFD) / `asset_name` (récupéré du nom de l'actif) / `none`.

---

## Validation (qualité prouvée)

- **Identité : 100 %** des 280 lignes rattachées à un bioguide (0 non rattaché).
- **Comparaison Quiver par sénateur** (`07_quiver_comparison.csv`) : sur 17 sénateurs,
  **11 concordants** (delta = 0), **4 « nous ≥ Quiver »**, **2 sans données Quiver**. Total
  **nous = 280 ≥ Quiver = 164** : on ne **sous-compte jamais** Quiver.
- **Contrôle transaction-à-transaction** : **0 vraie transaction manquée** (le seul écart `07b`,
  Hagerty `AHL-C`/`AHL.C`, est la même opération à la ponctuation du ticker près).
- **Couverture ticker 67 %** (≈ House 68 %) ; le reste = obligations sans ticker.
- Détail complet : **`RAPPORT_VALIDATION.md`**.

## Notes
- Les fichiers **vides** (`05_parse_failures.csv`, `06c_qa_flags.csv`) sont des **marqueurs « 0 échec »**.
- **Backlog v1** : 4 rapports papier non traités (OCR à venir, réutilisable via `0 HOUSE/house_ocr_multiyear.py`).
- Le seul `quiver_seul` de `07_quiver_comparison.csv` (Eleanor Holmes Norton) est une **erreur de
  chambre côté Quiver** (déléguée DC à la Chambre, pas sénatrice) — pas un dépôt Sénat manqué.
