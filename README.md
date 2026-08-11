# Congress Trading Signal — pipeline de données

Extraction et validation des déclarations boursières (PTR, *STOCK Act*) des membres du Congrès américain
— **Chambre des représentants + Sénat, 2014 → 2026** — en vue d'une stratégie de copy-trading.

Sources officielles : *House Clerk* (PTR PDF) et Sénat *eFD*, **électroniques** (parsing déterministe)
**+ scannées** (OCR Claude Vision). Quiver Quantitative sert de **vérification externe uniquement**,
jamais réinjecté dans les tables.

## Les trois dossiers du dépôt

Renommés le **2026-07-31** pour dire ce qu'ils contiennent (les anciens noms disaient *quand* le travail avait
été fait). Le numéro donne l'ordre de lecture, qui est aussi l'ordre chronologique.

| dossier | ce qu'il contient | ancien nom |
|---|---|---|
| [`00_recuperation_donnees/`](00_recuperation_donnees/) | **Ce que décrit ce README** : le pipeline d'extraction des PTR (House + Sénat, digital + OCR), les données, le rapport de qualité, le filet de non-régression | `00_S1S2_donnees` |
| [`01_autres_filing_types/`](01_autres_filing_types/) | **Au-delà des PTR** : les autres types de dépôt (Schedule A/B, rapports annuels, photos d'entrée) et la reconstruction des portefeuilles House qu'ils permettent | `01_v1_house` |
| [`02_recherche_backtest/`](02_recherche_backtest/) | **La recherche stratégie et les backtests** : notebooks `05b` → `16`, les fiches qui les rendent opposables, les tables `tables/` | `00. S3S4 en cours` |

## 🧭 Comprendre tout le projet & le lancer

Nouveau ici ? Trois documents (à la racine de `00_recuperation_donnees/`) :
- **[RAPPORT_QUALITE.md](00_recuperation_donnees/RAPPORT_QUALITE.md)** — le rapport de qualité à jour
  (fenêtre **2014-2026**, couverture vs l'index officiel du Clerk, validation Quiver par ère) ;
- **[AUDIT_DONNEES_2014_2026.md](00_recuperation_donnees/AUDIT_DONNEES_2014_2026.md)** — l'audit-réparation
  du **2026-07-03** (complétude prouvée, +10 856 lignes récupérées, chaque erreur tracée → corrigée) ;
- **[RAPPORT_FINAL.pdf](00_recuperation_donnees/RAPPORT_FINAL.pdf)** — le rapport d'architecture complet
  (*voyage d'une transaction*, `common`+jumeaux, qualité, validation Quiver, nettoyage backtest) sur **2014-2026**.

**Les tables prête-recherche** vivent dans `00_recuperation_donnees/data/clean/` — **brute**
(169 000 × 41, tout le corpus avec le verdict d'entonnoir par ligne), **clean**
(`transactions_backtest_2014_2026.csv`, **134 452 × 39** — parti/commissions point-in-time,
tickers canoniques Yahoo + renommages vérifiés, flags, invariants garantis) et **gated**
(7 287 manuscrites écartées, avec motif) + la table annexe des commissions
(bioguide × Congrès, sous-commissions résolues). Produites par `common/backtest_clean.py` (step 7 du
pipeline, testé). **Les étapes du nettoyage et leur code : `00_recuperation_donnees/NETTOYAGE.md`.**

Tout le pipeline se lance par **un seul point d'entrée** :

```bash
python -m common.pipeline --years 2020-2026            # années embarquées (PDF/index déjà présents)
python -m common.pipeline --years 2014-2019 --acquire  # années anciennes : télécharge d'abord index+PDF
python -m common.pipeline --years 2024 --dry-run       # voir la séquence sans rien exécuter
```

## Structure

```
common/   contrat UNIVERSEL : reference · schema (clé, fixes read-time, canonical_ticker) · sector_enrich ·
                 vision_ocr · crosscheck · quality (rapport) · quiver_diagnosis (§6) · quiver_scopes ·
                 enrich_tenure (ancienneté) · report_pdf · pipeline (orchestrateur)
house/    pipeline Chambre  : digital · acquire (téléchargement index+PDF) · classify_scans · ocr ·
                 identity · amounts · quiver · echantillon
senate/   pipeline Sénat    : digital · ocr · ocr_engine · fusion · identity · ticker · quiver ·
                 census_probe                                ← jumeau de house/
data/            données  (house/ · senate/ · external/ · reference/ ← renommages tickers, carte
                 secteurs, snapshots commissions par Congrès · clean/ ← table canonique de recherche)
(racine)        SLIDES_DONNEES_S1S2_V2.pdf · RAPPORT_QUALITE.md · AUDIT_DONNEES_2014_2026.md ·
                 RAPPORT_FINAL.pdf · FICHE_NETTOYAGE_BACKTEST_V2.pdf · les 2 ANALYSE_*.md
png/             les images : figs_deck/ (le deck) · quality/ (le rapport) · figs_pop/ (nb 12)
                 (README de png/ = la carte qui-produit-quoi)
_archive/        code/données/docs supplantés (orphelins prouvés, conservés pour traçabilité)
tests/regression/ filet « zéro changement » : golden + preuves de reproduction (sans réseau)
pyproject.toml   installable :  pip install -e .
```

### Où vivent les figures

Règle du dépôt, posée le **2026-07-31** après avoir trouvé **17 inclusions d'images cassées** dans un dossier
d'archive — et la même faute une seconde fois dans un autre dossier. Elle tient en cinq points :

1. **Un dossier par notebook producteur**, nommé `figs_nbXX/`, contenant **exactement** ses `savefig` — rien
   d'autre. Cette égalité se teste, et c'est elle qui empêche le fourre-tout de revenir.
2. **Le dossier suit son notebook** quand celui-ci part en `_archive/` (`git mv`), jamais l'inverse.
3. Une figure lue par un document **gelé** est **copiée** à côté de lui — copiée, pas déplacée, si son
   producteur est encore vivant : un notebook actif réécrit ses figures sous le même nom, et un document figé
   ne doit pas dépendre d'un artefact qui bouge.
4. **Un chemin d'image est relatif au document, pas au terminal** : `tectonic` cherche depuis le dossier du
   `.tex`. Un document qui déménage sans ses images ne compile plus — c'est l'origine des 17 cassées.
5. **Ces dossiers restent versionnés**, contrairement à `cache/` et `build_cache/` qui sont ignorés : ceux-là se
   régénèrent, ceux-ci non. Dans un cas mesuré, **31 figures sur 32** n'étaient reproductibles par aucun code
   (extraites à la main d'un notebook qui, bien qu'actif, ne contient aucun `savefig`).

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
| **House** | **151 989** | 152 081 = 58 728 + 93 353 | 100 % (367 bioguides) | in-window : **93,5 %** des trades Quiver retrouvés — §6 |
| **Sénat** | **17 011** | 18 839 = 14 813 + 4 026 | 100 % (78 bioguides) | in-window : **92,1 %** ; 98–100 %/an |

**Périmètre d'analyse = 169 000 transactions uniques de membres élus** (House 151 989 + Sénat 17 011), après
**dédup cross-année** des re-divulgations tardives. Le pipeline produit **170 920 lignes brutes**. Une
déclaration de **collaborateur non-élu** (HASC) est exclue du périmètre membres. **100 % des 8 252 PTR
listés par l'index officiel du Clerk 2014-2026 sont traités** (parsés, OCRisés, ou gated par règle écrite).
Détail : `00_recuperation_donnees/RAPPORT_QUALITE.md` (§1 « Couverture vs l'univers officiel »).

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
./.venv/bin/python tests/regression/check_golden.py         # House  — 230 fichiers (2014-2026)
./.venv/bin/python tests/regression/senate_check_golden.py  # Sénat  — 138 fichiers (2014-2026)
# Preuves de reproduction fonction-par-fonction :
./.venv/bin/python tests/regression/test_senate_repro.py    # natural_key_hash 8 841/8 841, identité, ticker
```

Le pipeline n'est pas re-jouable hors-ligne (le scraping/téléchargement exige le réseau) ; la
correction est donc prouvée par **reproduction depuis les colonnes figées** (`tests/regression/`).

## Archive

La structure pré-consolidation (pilotes Q1, scripts d'origine, audits semaines 1-4) est archivée et
récupérable : tag git **`archive/pre-cleanup-2026-06-26`** + tarball **`~/Downloads/Jupiter_legacy_2026-06-26.tar.gz`**.
