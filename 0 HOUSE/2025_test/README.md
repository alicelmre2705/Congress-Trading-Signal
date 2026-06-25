# House — Transactions boursières des représentants (PTR), Q1 2025

Corpus complet et vérifié des transactions déclarées par les membres de la Chambre des
représentants américaine (Periodic Transaction Reports) sur le **1ᵉʳ trimestre 2025**, à partir des
PDF du House Clerk. Deux sources fusionnées en une seule table : **100 PDF lisibles** (parsés en
texte) + **17 PDF scannés** (OCR Claude Vision), validées contre QuiverQuant.

---

## ⭐ Le résultat à utiliser

| Fichier | Contenu |
|---|---|
| **`data_v1/tables/06_house_2025q1_transactions_FINAL.csv`** | La table **COMPLÈTE** : 2 272 transactions (1 105 électroniques + 1 167 OCR). |
| **`data_v1/tables/house_2025q1_FINAL.xlsx`** | Le même + onglets synthèse / validation / QA / index. Rendu portable. |
| **`RAPPORT_OCR_VALIDATION.md`** | Comment l'OCR a été fiabilisé et validé (à lire pour le contexte). |

### Comprendre les noms (et éviter la confusion « v1/v2 »)
Ce ne sont pas des versions concurrentes, mais des **périmètres** différents :
- `06_…transactions.csv` = transactions des PDF **électroniques seuls** (étape intermédiaire).
- `06b_…ocr_transactions.csv` = transactions des PDF **scannés seuls** (OCR).
- **`06_…transactions_FINAL.csv` = les deux réunis** ⇒ **c'est LA table de référence.**

---

## Chronologie / comment reproduire

Environnement Python : `../../semaine 1/.venv` (kernel Jupyter `jupiter-house-ocr` ; contient
`anthropic`, `pymupdf`, `pandas`, `openpyxl`). Clé `ANTHROPIC_API_KEY` + `QUIVER_API_KEY` dans
`../.env`.

1. **Étape 1 — `notebook_v1_house_2025q1.ipynb`** (électronique) : référentiel des élus, index des
   PTR, téléchargement + tri des PDF (lisibles / non-lisibles), parsing texte → `06_…transactions.csv`
   et comparaison Quiver `07_…`.
2. **Étape 2 — `notebook_v1_house_2025q1_ocr.ipynb`** (OCR) : extrait les 17 PDF scannés (Claude
   Vision, sortie structurée), enrichit ticker/asset_type, **fusionne en `…_FINAL.csv`**, valide vs
   Quiver (`06d`) et génère **`house_2025q1_FINAL.xlsx`**.

> Le cache OCR (`data_v1/ocr_cache/*.json`) est versionné : relancer l'étape 2 ne rappelle l'API que
> si un PDF n'a pas de cache valide. Sans changement de prompt, le re-run est gratuit (cache hits).

---

## Carte des fichiers (`data_v1/`)

| Fichier | Rôle | Lignes |
|---|---|---|
| **Référence** | | |
| `tables/01_ref_universe.csv` | Tous les législateurs (lookup bioguide) | 12 767 |
| `tables/02_ref_house_key.csv` | Membres des comités clés (Financial/Armed/Intelligence) | 126 |
| **Pipeline intermédiaire** | | |
| `tables/03_ptr_index.csv` | Index des 117 PTR de la fenêtre Q1 2025 | 117 |
| `tables/04_download_manifest.csv` | Statut de téléchargement + `has_text` (lisible/scanné) | 117 |
| `tables/05_parse_failures.csv` | PDF lisibles non parsés — **vide = 0 échec** | 0 |
| **Données — électronique** | | |
| `tables/06_house_2025q1_transactions.csv` | Transactions des 100 PDF lisibles | 1 105 |
| **Données — OCR** | | |
| `tables/06b_house_2025q1_ocr_transactions.csv` | Transactions des 17 PDF scannés | 1 167 |
| **★ Données — FINALES (à utiliser)** | | |
| `tables/06_house_2025q1_transactions_FINAL.csv` | **Table complète (électronique + OCR)** | 2 272 |
| `tables/house_2025q1_FINAL.xlsx` | Classeur Excel : transactions + synthèse + validation + QA | — |
| **Validation / QA** | | |
| `tables/06c_ocr_failures.csv` | Échecs de batch OCR — **vide = aucun échec** | 0 |
| `tables/06c_ocr_qa_flags.csv` | Anomalies de cohérence OCR (montant illisible…) | 1 |
| `tables/06d_ocr_quiver_comparison.csv` | Comparaison OCR ↔ Quiver par déposant (OCR ≥ Quiver) | 10 |
| `tables/07_quiver_comparison.csv` | Comparaison électronique ↔ Quiver par déposant | 56 |
| **Sources** | | |
| `pdfs/lisibles_parses/` | 100 PDF lisibles parsés | — |
| `pdfs/non_lisibles/` | 17 PDF scannés (traités par OCR) | — |
| `pdfs/lisibles_non_parses/` | PDF lisibles sans transaction — **vide = 0** | — |
| `ocr_cache/*.json` | Cache OCR versionné par doc_id (17) | — |

---

## Dictionnaire des colonnes (table FINALE)

`bioguide_id`, `declarant_name`, `chamber`, `party`, `state_district`,
`committee_membership`, `committees_key_flag` · identité du déclarant.
`transaction_date`, `disclosure_date` · dates (transaction / notification-divulgation).
`ticker`, `asset_description`, `asset_type` · actif (ticker reconstruit côté OCR — voir `ticker_source`).
`operation_type` (Purchase/Sale/Partial Sale/Exchange), `amount_range`, `amount_midpoint`,
`amount_split_flag` · nature et montant.
`owner` (SELF/Spouse/Joint Tenancy/Dependent Child), `doc_id`, `source_url`, `natural_key_hash`.
`provenance` · `house-pdf-electronic` ou `house-pdf-ocr`.
`ticker_source` · origine du ticker OCR : `explicit` (présent dans le nom) / `elec_dict`
(dictionnaire électronique) / `none` (vide pour les lignes électroniques).

---

## Validation (qualité prouvée)

- **0 échec d'extraction**, sortie OCR structurée (tool use), cache versionné/auditable.
- **Correspondance OCR ↔ QuiverQuant : ~95 % de recall** (Khanna, 89 % des données OCR : 97 %).
  Là où l'OCR dépasse Quiver, c'est Quiver qui sous-recense les dépôts papier denses (vérifié
  visuellement, PDF source vs CSV). Détail complet : **`RAPPORT_OCR_VALIDATION.md`**.
- Couverture ticker de la table finale : ~68 % (90 % côté électronique, 46 % côté OCR).

## Notes
- Les fichiers/dossiers **vides** (`05_parse_failures.csv`, `06c_ocr_failures.csv`,
  `pdfs/lisibles_non_parses/`) sont des **marqueurs « 0 échec »** — c'est le résultat attendu, pas du bruit.
- L'ancien export Excel de l'étape 1 (`house_2025q1.xlsx`) était cassé/périmé ; il est remplacé par
  **`house_2025q1_FINAL.xlsx`** produit par l'étape 2 (le seul à utiliser).
