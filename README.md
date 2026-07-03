# Congress Trading Signal — pipeline de données

Extraction et validation des déclarations boursières (PTR, *STOCK Act*) des membres du Congrès américain
— **Chambre des représentants + Sénat, 2014 → 2026** — en vue d'une stratégie de copy-trading.

Sources officielles : *House Clerk* (PTR PDF) et Sénat *eFD*, **électroniques** (parsing déterministe)
**+ scannées** (OCR Claude Vision). Quiver Quantitative sert de **vérification externe uniquement**,
jamais réinjecté dans les tables.

## 🧭 Comprendre tout le projet & le lancer

Nouveau ici ? Le rapport de qualité à jour est **[`docs/RAPPORT_QUALITE.md`](docs/RAPPORT_QUALITE.md)**
(fenêtre **2014-2026**, chiffres recalculés, validation Quiver par ère). Le rapport d'architecture
**[`docs/RAPPORT_FINAL_V2.pdf`](docs/RAPPORT_FINAL_V2.pdf)** (*voyage d'une transaction*, architecture
`common`+jumeaux, secteur GICS→ETF, annexes) décrit la construction d'origine sur **2020-2026** — la
méthode est identique, seuls les chiffres/fenêtre y sont plus anciens.

Tout le pipeline se lance par **un seul point d'entrée** :

```bash
python -m common.pipeline --years 2020-2026            # années embarquées (PDF/index déjà présents)
python -m common.pipeline --years 2014-2019 --acquire  # années anciennes : télécharge d'abord index+PDF
python -m common.pipeline --years 2024 --dry-run       # voir la séquence sans rien exécuter
```

## Structure

```
common/   contrat UNIVERSEL : reference · schema · sector_enrich · vision_ocr · crosscheck ·
                 quality (rapport) · enrich_tenure (ancienneté) · pipeline (orchestrateur) · quiver_scopes
house/    pipeline Chambre  : digital · ocr · identity · amounts · tickers · quiver · echantillon
senate/   pipeline Sénat    : digital · ocr · ocr_engine · fusion · identity · ticker · quiver ·
                 census_probe                                ← jumeau de house/
data/            données  (house/ · senate/ · external/)
docs/            RAPPORT_FINAL_V2.pdf (rapport complet) · RAPPORT_QUALITE.md · quality/ · sources/
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

| Chambre | FINAL (uniques) | brut = digital + OCR | Identité | Concordance Quiver |
|---|---|---|---|---|
| **House** | **141 161** | 141 225 = 54 170 + 87 055 | 99,97 % (358 bioguides / 382 noms) | par ère : ~87 % (2020-2026) / ~60 % (2014-2019, Quiver mince) — §6 |
| **Sénat** | **17 011** | 18 839 = 14 813 + 4 026 | 99,9 % | 99–100 %/an |

**Périmètre d'analyse = 158 172 transactions uniques de membres élus** (House 141 161 + Sénat 17 011), après
**dédup cross-année** des re-divulgations tardives (une transaction re-déposée une autre année ne compte
qu'une fois). Le pipeline produit **160 064 lignes brutes**. Une déclaration de **collaborateur non-élu**
(Natalia Henriquez, HASC) est **exclue du périmètre membres**. Détail dans `docs/RAPPORT_QUALITE.md`.

> **Fenêtre 2014-2026** (branche `feature/collecte-2014-2019`) — les scans **manuscrits** pré-2020 sont
> **écartés** (cluster `C_manuscrit`), même politique qu'en 2020-2026 (`house/classify_scans.py` +
> `_scan_census.csv`). Avant ~2017, Quiver est **mince** : nos actions « en plus » sont réelles mais peu
> corroborables (cf. §6 « honnêteté par ère »). Un backtest doit entrer sur `disclosure_date` (anti-look-ahead).

Les deux chambres ont la **table 12/12 champs** (identité, ticker, secteur GICS→ETF, date, montant…) :
House ticker **82,6 %** / secteur **80,2 %** ; Sénat ticker **79,5 %** / secteur **72,0 %** (les vides =
actifs **non cotés** — munis/obligations — sans ticker/secteur légitimes). Validation externe Quiver **par
scope** (digital/OCR/both) et **par ère** : au **Sénat**, l'OCR papier est surtout du non-coté que Quiver
ne suit pas → source **interne**.

## Installation & vérification

```bash
python3.12 -m venv .venv
./.venv/bin/pip install -e .

# Filet de non-régression (doit afficher « ZÉRO ÉCART ») :
./.venv/bin/python tests/regression/check_golden.py         # House  — 217 fichiers (2014-2026)
./.venv/bin/python tests/regression/senate_check_golden.py  # Sénat  — 137 fichiers (2014-2026)
# Preuves de reproduction fonction-par-fonction :
./.venv/bin/python tests/regression/test_senate_repro.py    # natural_key_hash 8 841/8 841, identité, ticker
```

Le pipeline n'est pas re-jouable hors-ligne (le scraping/téléchargement exige le réseau) ; la
correction est donc prouvée par **reproduction depuis les colonnes figées** (`tests/regression/`).

## Archive

La structure pré-consolidation (pilotes Q1, scripts d'origine, audits semaines 1-4) est archivée et
récupérable : tag git **`archive/pre-cleanup-2026-06-26`** + tarball **`~/Downloads/Jupiter_legacy_2026-06-26.tar.gz`**.
