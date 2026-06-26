# Refonte Sénat — architecture & validation (branche `refonte/house-core`)

*Pipeline données Congress Trading — Sénat. Même cœur partagé `congress_core` + package `senate`,
en miroir de House (`docs/REFONTE_HOUSE.md`).*

## 1. Pourquoi cette refonte

Le Sénat vivait dans `1 SENAT/toutes_annees/` (orchestrateurs) + `1 SENAT/senat_2025_test/` (pilote Q1
figé), avec dépendances par `sys.path.insert` + monkeypatch et données sous `data/`. Objectif : **même
restructuration que House** — package propre `senate/` (arbo plate) bâti sur le cœur réutilisable
`congress_core`, données autonomes sous `data/senate/`, **zéro littéral `1 SENAT` / `data_v1_senate`**
dans le code. Contrainte : **zéro changement de résultat** (les 8 841 lignes FINAL reproduites à l'identique).

## 2. Architecture

```
congress_core/          cœur partagé (commun House + Sénat)
  schema.py             + SENATE_DIGITAL_SCHEMA (23 col.) + SENATE_FINAL_SCHEMA (27 col.)
  quiver.py             reconcile (dédup amendements) — déjà présent
  identity / amounts / tickers / sector_enrich / vision_ocr / llm_resolve / reporting
senate/                 pipeline Sénat (arbo plate, miroir house/)
  digital.py            scraping eFD digital → parse_electronic → identité → finalize → Quiver
  ocr.py                PTR papier → Vision (cache versionné, prompt FR) → normalisation
  fusion.py             fusion digital + OCR → FINALE 27 champs (ticker dict+LLM, secteur, date_confidence)
  identity.py           référentiel + matcher bioguide + enrich + recover_ticker (logique figée Q1)
  quiver_audit.py       reconcile transaction-niveau (07c-f) + dédup amendements
  ocr_engine.py         moteur Vision (formulaire Sénat, prompt FR)
  sector_enrich.py      GICS → ETF SPDR (cache data/senate)
  ticker_resolve.py     résolution nom→ticker (dict + passe LLM)
  revalidate_quiver.py  re-validation Quiver offline (07c-f + dashboard)
  census_probe.py       census PTR + probe parse_electronic (diagnostic)
data/senate/            données (tables {année}/, reports/ [ignoré], ocr_cache/, reference/, caches)
```

> **Données** : `git mv "1 SENAT/toutes_annees/data" → data/senate` (renames tracés). Référentiel
> (YAML législateurs/comités) + cache Quiver copiés sous `data/senate/reference/` (autonomie, parité
> `data/house/reference/`). Caches eFD régénérables (`reports/` HTML + `.gif`) ignorés. La logique du
> pilote Q1 `senat_2025_test/` a été **absorbée en copie** dans `senate/` (c'est elle qui a produit le
> golden) ; le pilote lui-même a ensuite été **archivé** lors de la consolidation (récupérable : tag git
> `archive/pre-cleanup-2026-06-26` + tarball `Jupiter_legacy`).

## 3. Vérification « zéro changement »

Comme House, le pipeline Sénat n'est **pas re-jouable hors-ligne** (le scraping eFD exige le réseau).
La preuve passe par la **reproduction fonction-par-fonction depuis les colonnes figées**
(`tests/regression/test_senate_repro.py`), sans re-run ni appel API :

| Invariant | Preuve | Résultat |
|---|---|---|
| `natural_key_hash` | recompute via `congress_core.schema` **et** `senate.identity` | **8 841 / 8 841** ✅ |
| `recover_ticker` (asset_name) | recompute vs colonne figée | **65 / 65** ✅ |
| identité bioguide | `senate.identity` re-rattache declarant_name (noms distincts rattachés) | **67 / 67** ✅ |
| golden (sha256 des sorties) | `senate_check_golden.py` sur `data/senate` | **68 fichiers, zéro écart** ✅ |

La reproduction `natural_key_hash` **par `congress_core`** démontre concrètement que `senate/` est
**bâti sur le cœur partagé**. (Subtilité honnête : une `transaction_date` OCR illisible valait un float
NaN au hash → `'nan'`, rendue vide par le CSV ; reconstruit dans le test, vérifié exhaustivement.)

## 4. Chiffres de la donnée Sénat (golden)

- **FINAL 8 841 txns** = digital **7 161** + OCR papier **1 680** · **67 noms / 64 bioguides · identité 100 %**.
- Par an : 2020 1 961 · 2021 1 379 · 2022 1 101 · 2023 1 159 · 2024 1 030 · 2025 1 421 · 2026 790.
- Table **12/12 champs** (parité House) : `ticker` 71,4 %, secteur GICS→ETF 62,1 %, `date_confidence`.
- Validation Quiver (digital) : 98–100 %/an, 0 vrai raté ; dédup des amendements appliquée (couverture
  inchangée, surcompte de comptage retiré). OCR papier validé **hors-Quiver** (Quiver aveugle au papier).

## 5. Fait / Différé

- ✅ **Fait** : `congress_core` étendu (schemas Sénat) ; `data/senate/` (git mv + référentiel autonome) ;
  package `senate/` (11 modules, imports propres, 0 littéral `1 SENAT`) ; golden + preuve reproduction.
- ⏭ **Différé** : `senate/efd_client.py` (fusion des 3 copies de scraping). Les fonctions
  `accept_agreement` / `fetch_ptr_list` / `parse_electronic` **diffèrent réellement** entre
  digital/ocr/census (filtre électronique vs papier vs census) ; un merge fidèle exige une
  paramétrisation **non vérifiable hors-ligne** (pas d'accès eFD). Reporté pour ne pas risquer un bug de
  scraping silencieux ; le scraping inline fonctionne tel quel.
- ✅ **Secteur House 12/12** : branché (secteur 83,2 %) → les deux chambres sont à parité 12/12.
- ⏭ **Différé** (commun) : stratégie + backtest (hors périmètre données).
