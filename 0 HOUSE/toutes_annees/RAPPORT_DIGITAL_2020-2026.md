# Rapport — Pipeline House DIGITAL, années 2020→2026

> Périmètre : **PDF lisibles uniquement** (extraction texte `pdfplumber` + parser). Les PDF scannés
> sont traités à part (OCR, cf. [`BACKLOG_OCR.md`](BACKLOG_OCR.md)). Quiver = vérification externe.
> Notebook : [`notebook_digital.ipynb`](notebook_digital.ipynb) ; moteur : [`house_multiyear.py`](house_multiyear.py).
> **Dossier autonome** (PDF/index/YAML/baseline/Quiver embarqués dans `data_v1/`).

## Résultat global

**32 676 transactions digitales** extraites sur 2020→2026, rendement de parsing **99–100 %**,
**0 dérive de format** vs la baseline historique. **Concordance Quiver (niveau transaction) : 99,01 % global**,
≥ 98 % chaque année, **9 vrais-absents sur 6 ans**.

| Année | txns digitales | déclarants | ticker % | **concordance Quiver** | vrais-absents |
|---|---|---|---|---|---|
| 2020 | 6 886 | 96 | 91,0 % | **99,71 %** | 0 |
| 2021 | 5 457 | 105 | 91,1 % | **99,68 %** | 1 |
| 2022 | 3 601 | 97 | 86,8 % | **98,88 %** | 0 |
| 2023 | 4 161 | 88 | 86,9 % | **98,10 %** | 3 |
| 2024 | 2 694 | 90 | 81,8 % | **98,01 %** | 2 |
| 2025 | 7 577 | 96 | 90,5 % | **98,93 %** | 1 |
| 2026 | 2 300 | 79 | 84,0 % | **98,64 %** | 2 |
| **Total** | **32 676** | — | 88,6 % | **99,01 %** | **9** |

Concordance = `matched / (matched + only-Quiver)`, clé transaction `bioguide|ticker|date|opération`.
Reproductible dans `notebook_digital.ipynb` (et `data_v1/tables/00_quiver_q1style_status.csv`).

## Méthode de validation Quiver — honnête (standard Q1 2025)

La métrique fiable compare **digital-vs-digital** et neutralise les artefacts :
1. **Dédup des amendements Quiver** (`BioGuideID|Ticker|traded|Transaction`) dans la fenêtre année.
2. **Exclusion des déposants papier** des **deux** côtés (ils relèvent du backlog OCR, pas du digital).
3. **Cross-check `only-Quiver`** : « ticker-raté » (on a le membre+date, ticker non extrait) vs « vraiment absent ».

> ⚠️ Ne PAS utiliser l'ancien `quiver_coverage_pct` (35–74 %) : son dénominateur incluait les gros
> déposants **papier** (Khanna & co), il était mécaniquement bas et **trompeur**. La bonne métrique est
> la concordance ci-dessus.

## Les 9 vrais-absents (résiduel, tous expliqués — aucun bug d'extraction)

Malinowski (ANIK 2020), Schrader (VRNG/ELN/MSCI 2022), Calhoun (AFRM/IBM 2024), Gottheimer (IFNNY 2025),
Pelosi (INTC/UBER 2026). Causes : papier→OCR, dépôt post-snapshot, variante de date ±1 j, étiquetage Quiver.
Le reste de l'écart `only-Quiver` (≈232 sur 6 ans) = **ticker-raté** (préférentielles `DUK$A`, Trésor
`3.MONTH MATURE`, fonds), présent chez nous sans ticker boursier — cosmétique.

## Dérives de format corrigées (trouvées en validant contre Quiver)

1. **Casse** des PDF pré-2021 (`[sT]`→`[ST]`, `(aos)`→`AOS`) : `ATYPE_RE`/`TICKER_RE` tolérants à la casse → rendement 2020 **84 %→100 %**.
2. **Pollution de descriptions** (`FILING STATUS`/`SUBHOLDING OF`) ajoutées à `SKIP_RE`.
3. **MLP sans code `[XX]`** (NGL/SHLX/USAC) : un ticker en continuation suffit désormais → manques 2020 **183→15**.

Parité préservée à chaque correctif (2025 T1 = 1 105 lignes reproduites exactement).

## Déduplication (canonique, conforme `CLAUDE.md` décision 2)

Table finale **per-lot** : lots distincts identiques d'un même PTR préservés via `occurrence_index` ;
seuls les vrais doublons cross-dépôt (amendements) sont retirés (on garde la divulgation la plus récente).

## Sorties

- `data_v1/tables/{année}/06_house_{année}_transactions.csv` — table digitale par année.
- `data_v1/tables/00_quiver_q1style_status.csv` — concordance honnête (dashboard).
- `notebook_digital.ipynb` — narration + reproduction de la concordance.

## Reste à faire (cf. [`PLAN_ATTAQUE.md`](PLAN_ATTAQUE.md))

- **OCR** : passe LLM nom→ticker (Stage 3), notebook OCR (Stage 4), **run complet 2021-2025** (Stage 5).
- Lot 2 : 2016→2019 (mêmes correctifs ; formats legacy plus scannés).
