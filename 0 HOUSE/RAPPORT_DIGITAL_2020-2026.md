# Rapport — Pipeline House DIGITAL, années 2020→2026

> Périmètre : **PDF lisibles uniquement** (extraction texte `pdfplumber` + parser). Les PDF scannés
> sont différés et inventoriés dans [`BACKLOG_OCR.md`](BACKLOG_OCR.md). Quiver = vérification externe.
> Moteur : [`house_multiyear.py`](house_multiyear.py) (réutilise les PDF/index de `semaine 1/`).

## Résultat global

**32 676 transactions digitales** extraites sur 2020→2026, **rendement de parsing 99–100 %**,
**0 dérive de format** vs la baseline `semaine 1` (superset complet chaque année).

| Année | PTR | lisibles | scannés (backlog) | txns digitales | rendement | recouvr. trades Quiver* | trades vraiment manqués** |
|---|---|---|---|---|---|---|---|
| 2020 | 722 | 597 | 125 | 6 886 | 100 % | 61.9 % | 15 |
| 2021 | 674 | 565 | 109 | 5 457 | 99.6 % | 74.2 % | 26 |
| 2022 | 613 | 505 | 108 | 3 601 | 99.6 % | 35.8 % | 39 |
| 2023 | 457 | 388 | 69 | 4 161 | 99.2 % | 43.7 % | 65 |
| 2024 | 442 | 394 | 48 | 2 694 | 99.5 % | 35.4 % | 40 |
| 2025 | 510 | 449 | 61 | 7 577 | 100 % | 60.1 % | 58 |
| 2026 | 262 | 235 | 27 | 2 300 | 99.6 % | 38.6 % | 38 |

\* % des trades distincts de Quiver (clé déclarant+ticker+date+type) qu'on retrouve.
\*\* trades que Quiver a et nous pas, pour un déclarant **sans dépôt papier** (vrai candidat-manque).

## Pourquoi le « recouvrement Quiver » paraît bas (35–74 %) — c'est trompeur

Le dénominateur Quiver inclut un **énorme volume de déposants papier** qu'on ne traite pas
(digital-only) : Rohit Khanna seul fait des centaines de trades/an et **dépose en papier**. Ces
trades sont chez Quiver, pas chez nous → ils plombent mécaniquement le « recouvrement », mais c'est
le **backlog OCR assumé**, pas une erreur. Métrique honnête = les *trades vraiment manqués* (dernière
colonne) : **15–65/an**, et même ceux-ci sont en quasi-totalité des artefacts (voir plus bas).

## Validation Quiver — méthode honnête (invariante à la dédup)

- **Comparaison per-lot** : notre canonique vs Quiver **brut** (sous-comptes des deux côtés). Erreur
  initiale corrigée : on dédupliquait Quiver mais pas nous → faux « on a +263 » sur Lowenthal
  (réel : 392 vs 374 Quiver brut).
- **Recouvrement au niveau transaction** (clé `bioguide|ticker|date|type`) : indépendant de la
  philosophie de dédup ; mesure réelle des trades couverts.

## Anatomie des 281 « trades manqués » (2020→2026 cumulés)

| Catégorie | Nombre | Vrai manque ? |
|---|---|---|
| Artefacts de convention Quiver (préférentielles `DUK$A`, Trésor `3.MONTH MATURE`, fonds `GLAS FUNDS`) | 173 | **Non** — on a la transaction, Quiver invente un pseudo-ticker |
| Ticker propre mais **présent chez nous** (ticker non extrait, dans la description) | ~70 | **Non** — refinement d'extraction ticker |
| Réellement absents (digital, non trouvés) | ~quelques dizaines | Oui (résiduel marginal) |

→ Le pipeline digital est **très complet**. L'écart résiduel vs Quiver est quasi entièrement
**méthodologique** (backlog papier + conventions ticker de Quiver), pas de la perte de données.

## Dérives de format corrigées (trouvées en validant contre Quiver)

1. **Casse** des PDF pré-2021 (`[sT]`→`[ST]`, `(aos)`→`AOS`) : `ATYPE_RE`/`TICKER_RE` rendus
   tolérants à la casse. Rendement 2020 : **84 % → 100 %**.
2. **Pollution de descriptions** (lignes d'annotation `FILING STATUS` / `SUBHOLDING OF` en casse
   mixte) : ajoutées à `SKIP_RE`. Descriptions propres.
3. **MLP / « Limited Partner Interests » sans code `[XX]`** (NGL, SHLX, USAC…) : étaient comptées
   mais ticker NULL → maintenant le ticker en continuation suffit à valider. Manques 2020 : **183 → 15**.

Parité préservée à chaque correctif : **2025 T1 reproduit exactement les 1 105 lignes** de la table
existante (port fidèle).

## Déduplication (règle canonique, conforme `CLAUDE.md` décision 2)

Table finale = **per-lot** : on préserve les lots distincts identiques d'un même PTR (vrais doublons
de comptes gérés, ex. Lowenthal 73× Sunrun via ses IRA Neuberger), via `occurrence_index`. La dédup
ne retire que les vrais doublons cross-dépôt (amendements), en gardant la divulgation la plus récente.
Une vue « per-trade » (façon Quiver) peut être dérivée en aval pour le signal, sans toucher la table
canonique.

## Sorties

- `data_v1/tables/{année}/06_house_{année}_transactions.csv` — table finale digitale par année.
- `…/07_quiver_comparison.csv` (par déclarant) + `…/07b_quiver_missing_trades.csv` (trades manqués).
- `…/08_crosscheck_semaine1.csv` — vs baseline semaine 1.
- `data_v1/tables/00_year_status.csv` — tableau de bord consolidé.
- `BACKLOG_OCR.md` + `data_v1/tables/00_backlog_ocr.csv` — **547 PDF scannés** (~3 137 pages,
  ~19 $ OCR estimé), Khanna en tête (75 PDF).

## Reste à faire

- **Packaging notebook** transparent (convention projet).
- **Backlog OCR** (Khanna et al.) via la méthode PDF/Vision de `notebook_v1_house_2025q1_ocr.ipynb`.
- **Lot 2 : 2016→2019** (mêmes correctifs ; formats legacy plus scannés).
- Refinement optionnel : extraction ticker pour préférentielles/Trésor (cosmétique, sans vrai ticker).
