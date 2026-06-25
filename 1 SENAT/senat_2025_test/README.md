# Sénat — Transactions boursières des sénateurs (PTR), Q1 2025

Corpus vérifié des transactions déclarées par les membres du Sénat américain (Periodic Transaction
Reports) sur le **1ᵉʳ trimestre 2025**, extrait directement de l'**eFD** (efdsearch.senate.gov),
au standard de la version House Q1 (même schéma, même validation QuiverQuant, mêmes principes :
transparence, Quiver = vérification seulement, aucune évasion anti-bot).

> **Dossier 100 % autonome.** Tout est en local : référentiel des législateurs vendu dans
> `data_v1_senate/reference/`, secrets dans `.env` (gitignoré), environnement dans `.venv`
> (voir `requirements.txt`). **Aucune lecture hors de ce dossier.**

> Spécificités Sénat : rapports **HTML** derrière un **gate CSRF** (électroniques) + **formulaires
> scannés** (papier, traités par OCR) ; pas de district (l'**État** seul) ; mix d'actifs très
> **obligataire / privé** où le ticker est légitimement absent.

---

## ⭐ Le résultat à utiliser

| Fichier | Contenu |
|---|---|
| **`data_v1_senate/tables/06_senate_2025q1_FINAL.csv`** | La table **COMPLÈTE** : **375 transactions** (283 électroniques + 92 OCR papier) · **18 sénateurs** · 37 PTR. |
| **`data_v1_senate/tables/senate_2025q1_FINAL.xlsx`** | Le même + onglets synthèse / validation / QA / index. Rendu portable. |
| `data_v1_senate/tables/06_senate_2025q1_transactions.csv` | Sous-ensemble **électronique seul** (283). |
| `data_v1_senate/tables/06b_senate_2025q1_ocr_transactions.csv` | Sous-ensemble **OCR papier seul** (92). |
| **`RAPPORT_VALIDATION.md`** | Comment les données ont été validées contre Quiver. |

---

## Chronologie / comment reproduire

**Environnement local autonome** (une seule fois) :
```
cd "1 SENAT/senat_2025_test"
python3.12 -m venv .venv
.venv/bin/pip install -U pip && .venv/bin/pip install -r requirements.txt
cp .env.example .env        # puis renseigner ANTHROPIC_API_KEY (OCR) et QUIVER_API_KEY (validation)
```

1. **`notebook_v1_senate_2025q1.ipynb`** — accepte l'agrément eFD, liste les PTR de la fenêtre,
   télécharge + parse les rapports HTML électroniques (les 4 papier vont en `backlog.csv`), rattache
   l'identité (bioguide), **déduplique sans détruire** (`occurrence_index`, cf. plus bas) et écrit
   `senate_2025q1_transactions.csv` (**283** lignes électroniques).
2. **`senate_ocr.py`** — OCR des 4 PTR **papier** (tous Sénateur **Richard Blumenthal**) : récupère
   les images `.gif` du serveur public eFD, **Claude Vision** + `tool_use record_transactions`
   (cache versionné par `prompt_sha`), garde-fou sur les dates → écrit
   `tables/06b_senate_2025q1_ocr_transactions.csv` (**92** lignes, `provenance=senate-efd-ocr`).
   ```
   .venv/bin/python senate_ocr.py
   ```
3. **`senate_finalize.py`** — fiabilise l'identité, enrichit le ticker, **fusionne digital + OCR**
   (`06_..._FINAL.csv`, 375), **valide contre Quiver** (Chambre = Sénat, fenêtre de divulgation Q1),
   écrit les tables numérotées 01→07, les QA flags et l'Excel.
   ```
   .venv/bin/python senate_finalize.py
   ```

> Idempotent : ré-exécuter reproduit les mêmes sorties (seul Quiver est re-téléchargé ; l'OCR est
> servi depuis son cache). Quiver n'entre **jamais** dans la table — il sert uniquement à recouper.

---

## Carte des fichiers (`data_v1_senate/`)

| Fichier | Rôle | Lignes |
|---|---|---|
| **Autonomie** | | |
| `reference/*.yaml` | Référentiel législateurs vendu en local (offline) | 4 fichiers |
| **Référence** | | |
| `tables/01_ref_universe.csv` | Tous les législateurs (lookup bioguide) | 12 767 |
| `tables/02_ref_senate_key.csv` | Sénateurs en commissions clés (Finance/Armed/Intel/Banking) | 71 |
| **Pipeline** | | |
| `tables/03_ptr_index.csv` | Index des dépôts Q1 2025 (33 électroniques + 4 papier OCR) | 37 |
| `tables/04_report_manifest.csv` | Statut par dépôt (électronique parsé / OCR parsé) | 37 |
| `tables/05_parse_failures.csv` | Rapports électroniques non parsés — **vide = 0 échec** | 0 |
| **★ Données — à utiliser** | | |
| `tables/06_senate_2025q1_FINAL.csv` | **Table complète digital + OCR** | 375 |
| `tables/06_senate_2025q1_transactions.csv` | Électronique seul | 283 |
| `tables/06b_senate_2025q1_ocr_transactions.csv` | OCR papier seul | 92 |
| `tables/senate_2025q1_FINAL.xlsx` | Classeur Excel : transactions + synthèse + validation + QA + index | — |
| **Validation / QA** | | |
| `tables/06c_qa_flags.csv` | Anomalies (champ obligatoire manquant) — **vide = aucune** | 0 |
| `tables/06c_ocr_failures.csv` | Échecs de batch OCR — **vide = aucun** | 0 |
| `tables/07_quiver_comparison.csv` | Comparaison par sénateur (nous vs Quiver) + verdict | 19 |
| `tables/07b_quiver_ticker_gaps.csv` | Trades (ticker,date) que Quiver a et pas nous | 1 |
| `tables/_quiver_senate_cache.csv` | Cache Quiver Sénat (vérification, hors table) | 13 342 |
| **Sources / cache** | | |
| `reports/*.html` | Rapports eFD mis en cache (offline) | 37 |
| `reports/media/*.gif` | Pages scannées des PTR papier (cache offline) | 16 |
| `ocr_cache/*.json` | Extractions Vision en cache (versionnées `prompt_sha`) | 4 |
| `backlog.csv` | Papier listé par le notebook → résolu par `senate_ocr.py` | 4 |

---

## Dictionnaire des colonnes (table finale — 23 colonnes)

`bioguide_id`, `declarant_name`, `chamber`, `party`, `state_district`,
`committee_membership`, `committees_key_flag` · identité (`state_district` = **État seul**).
`transaction_date`, `disclosure_date` · dates (transaction / divulgation).
`ticker`, `asset_description`, `asset_type` · actif. **Ticker souvent absent** sur les obligations
et les **véhicules privés** (LLC/fonds familiaux Malkin de Blumenthal) — c'est normal.
`operation_type` (électronique : Purchase / Sale (Full) / Sale (Partial) ; papier : Purchase / Sale /
Exchange), `amount_range`, `amount_midpoint`, **`amount_split_flag`** (parité schéma House ; toujours
`False` côté Sénat — fourchette unique par ligne), `owner` (Self / Spouse / Joint / Child).
`doc_id`, `source_url`, `natural_key_hash`, `provenance` (`senate-efd-electronic` | `senate-efd-ocr`),
`ticker_source` (`explicit` / `asset_name` / `none`),
**`occurrence_index`** · rang d'un lot répété **dans un même rapport** (0 = première occurrence).

---

## Validation (qualité prouvée)

- **Identité : 100 %** des 375 lignes rattachées à un bioguide (0 non rattaché), **18 sénateurs**.
- **Comparaison Quiver par sénateur** (`07_quiver_comparison.csv`) : **nous = 375 ≥ Quiver = 164** —
  on ne **sous-compte jamais**. Les 92 transactions OCR de **Blumenthal** sont **100 % additives**
  (Quiver n'indexe **aucun** de ses dépôts papier → verdict `quiver_sans_donnee`).
- **Contrôle transaction-à-transaction** : **0 vraie transaction manquée** (le seul écart `07b`,
  Hagerty `AHL-C`/`AHL.C`, est la même opération à la ponctuation du ticker près).
- **OCR vérifié** : les plages de dates par rapport correspondent **exactement** aux lettres
  d'accompagnement (ex. 8e8ae815 : 26/02→04/03/2025), montants tous lus, 0 échec batch.
- **Couverture ticker** : **67 %** sur l'électronique ; **51 %** sur l'ensemble (les 92 lignes OCR
  sont des LLC/fonds privés **sans ticker** — légitime, jamais inventé).

## Déduplication non destructrice (`occurrence_index`)

L'ancienne v1 faisait `drop_duplicates(natural_key_hash)` → elle **détruisait 3 vraies transactions**
(Ashley Moody : `SYM`/`NCLH`/`SMCI CALL` vendus 2× le même jour, même fourchette = 2 lots réels).
Désormais (comme le moteur House multi-ans) : `occurrence_index` distingue les **lots répétés
intra-rapport** (préservés) et on ne fusionne que les doublons **cross-rapport** (amendement /
re-dépôt). Effet : électronique **280 → 283**.

## Notes
- Les fichiers **vides** (`05_parse_failures.csv`, `06c_*`) sont des **marqueurs « 0 échec »**.
- Le seul `quiver_seul` de `07_quiver_comparison.csv` (Eleanor Holmes Norton) est une **erreur de
  chambre côté Quiver** (déléguée DC à la Chambre, pas sénatrice) — pas un dépôt Sénat manqué.
