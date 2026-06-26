# Congress Trading Signal — pipeline de données

Extraction et validation des déclarations boursières (PTR, *STOCK Act*) des membres du Congrès américain
— **Chambre des représentants + Sénat, 2020 → 2026** — en vue d'une stratégie de copy-trading.

Sources officielles : *House Clerk* (PTR PDF) et Sénat *eFD*, **électroniques** (parsing déterministe)
**+ scannées** (OCR Claude Vision). Quiver Quantitative sert de **vérification externe uniquement**,
jamais réinjecté dans les tables.

## Structure

```
congress_core/   cœur partagé : schema · identity · amounts · tickers · quiver · crosscheck ·
                 vision_ocr · llm_resolve · sector_enrich · reporting · paths
house/           pipeline Chambre  (digital → ocr → fusion)
senate/          pipeline Sénat    (miroir de house/)
data/            données  (house/ · senate/ · external/)
docs/            rapport superviseur (RAPPORT_HOUSE.pdf) + architecture (REFONTE_*) + synthèse Sénat
tests/regression/ filet « zéro changement » : golden + preuves de reproduction (sans réseau)
pyproject.toml   installable :  pip install -e .
```

## Chiffres clés

| Chambre | FINAL | = digital + OCR | Identité | Concordance Quiver |
|---|---|---|---|---|
| **House** | **81 646** | 32 676 + 48 970 | 99,99 % (256 déposants) | 85,9 % (txn-niveau) |
| **Sénat** | **8 841** | 7 161 + 1 680 | 100 % | 98–100 %/an |

Sénat : table 12/12 champs (ticker 71,4 %, secteur GICS→ETF 62,1 %). OCR papier validé hors-Quiver
(les agrégateurs sont aveugles au scanné → notre OCR est la source unique).

## Installation & vérification

```bash
python3.12 -m venv .venv
./.venv/bin/pip install -e .

# Filet de non-régression (doit afficher « ZÉRO ÉCART ») :
./.venv/bin/python tests/regression/check_golden.py         # House  — 108 fichiers
./.venv/bin/python tests/regression/senate_check_golden.py  # Sénat  —  68 fichiers
# Preuves de reproduction fonction-par-fonction :
./.venv/bin/python tests/regression/test_senate_repro.py    # natural_key_hash 8 841/8 841, identité, ticker
```

Le pipeline n'est pas re-jouable hors-ligne (le scraping/téléchargement exige le réseau) ; la
correction est donc prouvée par **reproduction depuis les colonnes figées** (`tests/regression/`).

## Archive

La structure pré-consolidation (pilotes Q1, scripts d'origine, audits semaines 1-4) est archivée et
récupérable : tag git **`archive/pre-cleanup-2026-06-26`** + tarball **`~/Downloads/Jupiter_legacy_2026-06-26.tar.gz`**.
