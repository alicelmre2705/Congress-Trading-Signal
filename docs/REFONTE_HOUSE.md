# Refonte House — architecture & validation (branche `refonte/house-core`)

*Pipeline données Congress Trading — House. Cœur partagé `congress_core` + package `house`.*

## 1. Pourquoi cette refonte

Le premier jet (12 scripts + 5 notebooks) **dupliquait massivement** la logique entre House et
Sénat, avec 3 conventions de chemins et un nommage incohérent. Objectif : un **package propre,
modulaire, présentable**, où toute la logique partagée — d'abord **Doc ID → législateur (bioguide)** —
vit dans un cœur réutilisable que le Sénat importera ensuite. Contrainte : **zéro changement de
résultat** (les chiffres validés reproduits à l'identique).

## 2. Architecture

```
congress_core/          cœur partagé (importé par House ; Sénat plus tard)
  paths.py        DataRoot, find_base_dir, load_env, get_secret
  identity.py  ★  Doc ID → bioguide : Reference + make_matcher + enrich_identity
  schema.py       natural_key_hash + add_occurrence_index + dedup_canonical + SCHEMA
  tickers.py      recover/explicit/norm_asset + infer_asset_type(., chamber)
  amounts.py      AMOUNT_MAP[chamber] + amount_midpoint + OWNER_MAP[chamber] + operation_type
  quiver.py       fetch + validate_quiver_house (clé exacte) + reconcile canonique
  crosscheck.py   triangulation digitale (Kadoa/Stock Watcher) + statut par déposant
  vision_ocr.py   VisionExtractor : rendu + deskew + cache versionné (prompt_sha)
  llm_resolve.py  VersionedLLMCache + map_batch + passe nom→ticker
  sector_enrich.py GICS → ETF SPDR (copie canonique unique)
  reporting.py    qa_flags + upsert_status + write_excel + TABLE_NUMBERING
house/                  pipeline House (orchestration spécifique)
  digital.py      index XML → manifest → parse_ptr → identité → finalize → Quiver
  ocr.py          census A/B/C → Vision (cache) → enrichissement → fusion digital+OCR
  echantillon.py  harnais de mesure (échantillon stratifié)
tests/regression/       FILET « zéro changement » (golden 93 fichiers + preuves)
pyproject.toml          package installable (pip install -e .)
```

> **Données** : sous `data/house/` (`tables/`, `pdfs/`, `index/`, `reference/`, `ocr_cache/`) —
> déplacées en Phase 7 (git mv, intégrité vérifiée : `check_golden` = zéro écart). Le code y accède
> via `house.digital.OUTDIR`. (`0 HOUSE/toutes_annees/` ne garde plus que le venv + anciens notebooks.)

## 3. Vérification « zéro changement »

Le pipeline DIGITAL n'est pas re-jouable hors-ligne (seuls les **547 PDF scannés** sont embarqués,
pas les digitaux). La preuve passe donc par la **reproduction fonction-par-fonction depuis les
colonnes figées** (`tests/regression/`), sans re-run ni appel API :

| Invariant | Preuve | Résultat |
|---|---|---|
| `natural_key_hash` | équivalence unitaire vs originaux + repro des hash figés | **161 974 / 161 974** ✅ |
| `amount_midpoint` (digital + OCR) | recompute vs colonne figée | **81 646 / 81 646** ✅ |
| `infer_asset_type` (OCR) | recompute vs colonne figée | **48 970 / 48 970** ✅ |
| `match_bioguide` (★ identité) | port == original + repro des bioguides figés | **284/284 + 3514/3514** ✅ |
| `PROMPT_SHA` (cache OCR) | formule préservée (`0d3d617274e6`) | cache valide, **0 re-OCR** ✅ |

Lancer : `"0 HOUSE/toutes_annees/.venv/bin/python" tests/regression/test_*.py` et `check_golden.py`.

## 4. Chiffres de la donnée House (golden, commit `da65aa6`)

- **FINAL 81 646 txns** = digital 32 676 + OCR 48 970 · **256 déposants · identité 99,99 %** (4 manuscrits
  non rattachés, flaggés). *(Phase 9a : +66 txns manuscrites récupérées ; puis dédup amendements NON
  destructrice −405 doublons cross-doc, parité Sénat → 81 646. Détail : `docs/RAPPORT_HOUSE.pdf`.)*
- OCR : 546/547 PDF scannés traités (clusters A+B+C). Concentration : Khanna 63 %, McCaul 22 %,
  Harshbarger 8 %.
- Validation FINAL ↔ Quiver : **aucun déposant en déficit > 30**.

## 5. Constat de validation (livrable `crosscheck`)

La triangulation externe **marche pour le DIGITAL** (Quiver + Kadoa + House Stock Watcher se
recoupent) mais est **impossible pour le PAPIER** : les trois agrégateurs **sautent tous les scans**
→ **0 ligne** pour Khanna/Harshbarger/McCaul. Notre OCR est la **source unique**.

`congress_core.crosscheck.per_filer_status(...)` matérialise ce constat — statut par déposant :

| statut | déposants | transactions |
|---|---:|---:|
| `quiver_validable` | 211 | 78 907 |
| `ocr_unique` (Quiver=Kadoa=HSW=0) | 8 | 1 926 |
| `digital` | 31 | 1 152 |

## 6. Qualité OCR — Phase 9

- ✅ **40 docs `partial_error` complétés** (Phase 9a) : re-OCR ciblée → 34 complétés (+66 txns manuscrites),
  6 vides, 0 erreur. Ajout **additif** (ces docs valaient 0 ligne), preuves cœur OK, golden re-figé.
- **Cluster C manuscrit — exclusion CONSERVÉE (décision)** : ~63+ docs C `ok` restent hors `06b`
  (dates manuscrites peu fiables = la raison même de l'exclusion). Récupérables si besoin (cache présent),
  mais qualité basse → laissés exclus.
- Dates **Harshbarger 2021** (21 % implausibles) : **ambiguïté OCR intrinsèque** (le redressement ne
  corrige pas la lecture des chiffres) → non corrigeable par re-OCR ; flaggé `date_confidence`.
