# Congress Trading Signal — pipeline de données

Extraction et validation des déclarations boursières (PTR, *STOCK Act*) des membres du Congrès américain
— **Chambre des représentants + Sénat, 2020 → 2026** — en vue d'une stratégie de copy-trading.

Sources officielles : *House Clerk* (PTR PDF) et Sénat *eFD*, **électroniques** (parsing déterministe)
**+ scannées** (OCR Claude Vision). Quiver Quantitative sert de **vérification externe uniquement**,
jamais réinjecté dans les tables.

## 🧭 Comprendre tout le projet & le lancer

Nouveau ici ? Lis **[`docs/ARCHITECTURE.pdf`](docs/ARCHITECTURE.pdf)** — le guide visuel complet
(les 3 couches de code, chaque module/fonction et **ce qu'elle renvoie**, le *voyage d'une transaction*,
la couche données, et l'enchaînement de bout en bout). Dérivé du **code source réel**.

Tout le pipeline se lance par **un seul point d'entrée** :

```bash
python -m common.pipeline --years 2020-2026   # 7 étapes : House/Sénat digital→OCR→fusion→enrichissement
python -m common.pipeline --years 2024 --dry-run   # voir la séquence sans rien exécuter
```

## Structure

```
common/   contrat UNIVERSEL : reference · schema · sector_enrich · vision_ocr · crosscheck ·
                 quality (rapport) · enrich_tenure (ancienneté) · pipeline (orchestrateur)
house/    pipeline Chambre  : digital · ocr · identity · amounts · tickers · quiver · echantillon
senate/   pipeline Sénat    : digital · ocr · ocr_engine · fusion · identity · ticker · quiver ·
                 census_probe                                ← jumeau de house/
data/            données  (house/ · senate/ · external/)
docs/            ARCHITECTURE.pdf (guide structure) · RAPPORT_COMPLET.pdf · RAPPORT_QUALITE.md
_archive/        code/données/docs supplantés (orphelins prouvés, conservés pour traçabilité)
tests/regression/ filet « zéro changement » : golden + preuves de reproduction (sans réseau)
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

| Chambre | FINAL | = digital + OCR | Identité | Concordance Quiver |
|---|---|---|---|---|
| **House** | **81 646** | 32 676 + 48 970 | 99,99 % (256 bioguides / 275 noms) | 85,9 % (txn-niveau) |
| **Sénat** | **8 841** | 7 161 + 1 680 | 100 % | 98–100 %/an |

Les deux chambres ont la **table 12/12 champs** (identité, ticker, secteur GICS→ETF, date, montant…) :
House ticker **85,3 %** / secteur **83,2 %** ; Sénat ticker **71,4 %** / secteur **62,1 %**. OCR papier
validé hors-Quiver (les agrégateurs sont aveugles au scanné → notre OCR est la source unique).

## Installation & vérification

```bash
python3.12 -m venv .venv
./.venv/bin/pip install -e .

# Filet de non-régression (doit afficher « ZÉRO ÉCART ») :
./.venv/bin/python tests/regression/check_golden.py         # House  — 111 fichiers
./.venv/bin/python tests/regression/senate_check_golden.py  # Sénat  —  69 fichiers
# Preuves de reproduction fonction-par-fonction :
./.venv/bin/python tests/regression/test_senate_repro.py    # natural_key_hash 8 841/8 841, identité, ticker
```

Le pipeline n'est pas re-jouable hors-ligne (le scraping/téléchargement exige le réseau) ; la
correction est donc prouvée par **reproduction depuis les colonnes figées** (`tests/regression/`).

## Archive

La structure pré-consolidation (pilotes Q1, scripts d'origine, audits semaines 1-4) est archivée et
récupérable : tag git **`archive/pre-cleanup-2026-06-26`** + tarball **`~/Downloads/Jupiter_legacy_2026-06-26.tar.gz`**.
