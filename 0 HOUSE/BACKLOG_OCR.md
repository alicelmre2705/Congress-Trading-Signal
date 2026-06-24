# Backlog OCR — PTR House scannés (non lisibles)

> **Statut : NON TRAITÉ (différé).** Ces PDF n'ont pas de couche texte (scans/dépôts papier, DocID commençant par `8`/`9`). Le pipeline digital `house_multiyear.py` les **inventorie mais ne les extrait pas**.

> **Méthode prévue (ultérieure) :** OCR PDF/Vision de Claude (`claude-sonnet-4-6`, tool_use `record_transactions`), cf. `notebook_v1_house_2025q1_ocr.ipynb` qui le fait déjà pour 2025 T1.


**Total inventorié : 564 PDF / 52 déclarants distincts.**


## Volume par année

| Année | PDF non lisibles | Déclarants | Pages (≈ coût OCR) |
|---|---|---|---|
| 2020 | 125 | 24 | 646 |
| 2021 | 109 | 20 | 425 |
| 2022 | 108 | 21 | 594 |
| 2023 | 69 | 16 | 388 |
| 2024 | 48 | 9 | 399 |
| 2025 | 61 | 14 | 421 |
| 2025q1 | 17 | 11 | 90 |
| 2026 | 27 | 6 | 264 |
| **Total** | **564** | — | **3227** |

_Estimation coût OCR Claude Vision ≈ 3227 pages × ~0,006 $ ≈ **19 $**._


## Top déposants papier (priorité OCR)

| Déclarant | PDF scannés | Pages |
|---|---|---|
| Rohit Khanna | 75 | 1543 |
| Harold Dallas Rogers | 75 | 86 |
| Michael T. McCaul | 72 | 460 |
| Kurt Schrader | 36 | 101 |
| Charles J. "Chuck" Fleischmann | 35 | 92 |
| Doug Lamborn | 30 | 55 |
| Diana Harshbarger | 25 | 247 |
| Trey Hollingsworth | 23 | 42 |
| Ann Wagner | 21 | 40 |
| Mike Kelly | 20 | 21 |
| Fred Upton | 16 | 29 |
| David Kustoff | 13 | 18 |
| Francis Rooney | 12 | 23 |
| Tony Wied | 12 | 20 |
| David P. Roe | 11 | 249 |
| Nicole Malliotakis | 7 | 7 |
| Brad Sherman | 6 | 10 |
| Scott Franklin | 6 | 15 |
| Vicente Gonzalez | 6 | 6 |
| Tom Cole | 5 | 6 |

## Détail complet

Voir `data_v1/tables/00_backlog_ocr.csv` (year, doc_id, declarant_name, state_district, disclosure_date, n_pages).
