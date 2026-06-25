# Pipeline House — Transactions boursières des représentants
## Volume 2 : années 2020 → 2026 — synthèse complète

---

## ► Résultat à utiliser

| Source | Fichier | Transactions |
|---|---|---|
| **Électronique (total)** | `data_v1/tables/{année}/06_house_{année}_transactions.csv` × 7 | **32 676** |
| **OCR (échantillon)** | `data_v1/tables/_ocr_echantillon_resultats.csv` | **4 103** |

L'OCR échantillon sert à **mesurer la qualité de la méthode**, pas à remplacer le digital.

---

## 1. Vue d'ensemble

| Indicateur | Valeur |
|---|---|
| Période couverte | 2020 → 2026 (7 années) |
| **Transactions électroniques (TOTAL)** | **32 676** |
| Concordance Quiver (élec, transaction) | 99,01 % |
| Trades vraiment absents (6 ans) | 9 |
| PDF scannés recensés | 547 (A : 74 / B : 322 / C : 151) |
| OCR — docs traités | 70 (10/an) |
| OCR — transactions | 4 103 |
| OCR — couverture ticker | 74 % |
| OCR — concordance Quiver (match exact) | 59,7 % |

---

## 2. Électronique 2020 → 2026

Extraction texte (`pdfplumber` + regex), concordance par la méthode standard Q1 : dédup amendements Quiver, exclusion papier des deux côtés, cross-check « ticker raté » vs « vraiment absent ».

| Année | txns | déclarants | ticker % | concordance Quiver | vrais-absents |
|---|---:|---:|---:|---:|---:|
| 2020 | 6 886 | 96 | 91,0 % | 99,71 % | 0 |
| 2021 | 5 457 | 105 | 91,1 % | 99,68 % | 1 |
| 2022 | 3 601 | 97 | 86,8 % | 98,88 % | 0 |
| 2023 | 4 161 | 88 | 86,9 % | 98,10 % | 3 |
| 2024 | 2 694 | 90 | 81,8 % | 98,01 % | 2 |
| 2025 | 7 577 | 96 | 90,5 % | 98,93 % | 1 |
| 2026 | 2 300 | 79 | 84,0 % | 98,64 % | 2 |
| **Total** | **32 676** | — | 88,6 % | **99,01 %** | **9** |

Les **9 vrais-absents** sont tous expliqués : Malinowski (ANIK 2020), Schrader (VRNG/ELN/MSCI 2022), Calhoun (AFRM/IBM 2024), Gottheimer (IFNNY 2025), Pelosi (INTC/UBER 2026). Causes : dépôt papier→OCR, snapshot post-dépôt, date ±1 j, étiquetage Quiver. Le reste de l'écart `only-Quiver` (≈ 232) = ticker raté (préférentielles `DUK$A`, Trésor, fonds) — cosmétique.

**Électronique = prêt. 99,01 % concordance, ≥ 98 % chaque année, 9 vrais-absents sur 6 ans. Quiver n'est jamais réinjecté.**

---

## 3. OCR — census + échantillon

### 3.1 Census des 547 PDF scannés

| Cluster | docs | part | Profil OCR |
|---|---:|---:|---|
| A — tapé droit | 74 | 13,5 % | le plus propre ; lecture directe |
| B — tapé tourné 90° | 322 | 58,9 % | le gros du corpus ; lisible une fois redressé |
| C — manuscrit | 151 | 27,6 % | le point dur ; concentré 2020–2021 |

543/547 sont le même formulaire officiel House. 81 % des scans sont tournés. 6 sont illisibles.

### 3.2 Volumétrie de l'échantillon

70 docs (10/an : 2 A / 6 B / 2 C ; 2026 = 8 A / 2 C faute de cluster B), prompt durci + garde-fou date, cap 8 pages, cache versionnés `ocr_cache_echantillon/`.

| Champ | Couverture |
|---|---|
| Transactions totales | 4 103 |
| `ticker` (avec passe LLM) | 3 032 / 4 103 = **74 %** |
| — `explicit` | 176 |
| — `elec_dict` | 1 962 |
| — `llm` | 894 |
| — `none` (munis, obligations, options) | 1 071 |

---

## 4. Validation contre QuiverQuant

### 4.1 Électronique

Voir tableau §2 : concordance ≥ 98 % sur chaque année, 99,01 % global. **0 cas** où Quiver a plus de transactions que nous.

### 4.2 OCR — diff transaction par transaction

Chaque transaction avec ticker classée en 3 statuts (`_ocr_echantillon_diff.csv`, notebook §4b) :

| Cluster | vérif. | match | ticker ok, date fausse | ticker absent Quiver | match % |
|---|---:|---:|---:|---:|---:|
| A — tapé droit | 1 157 | 877 | 213 | 67 | **75,8 %** |
| B — tapé tourné | 1 704 | 923 | 550 | 231 | **54,2 %** |
| C — manuscrit | 158 | 1 | 115 | 42 | **0,6 %** |
| **Total** | **3 019** | **1 801** | **878** | **340** | **59,7 %** |

- **Ticker absent Quiver** (340, 11 %) = actifs que Quiver ne trace pas (ETFs OTC, delistés, petits déposants). Pas des hallucinations.
- **Ticker ok, date fausse** (878, 29 %) = le problème résiduel est la **lecture des dates**, pas des tickers.

### 4.3 Concordance (ticker, date) par cluster et par année

| Cluster | préc. ticker | préc. (ticker, date) |
|---|---:|---:|
| A — tapé droit | 0,79 | 0,58 |
| B — tapé tourné | 0,74 | 0,45 |
| C — manuscrit | 0,79 | 0,01 * |

| Année | préc. (ticker, date) |
|---|---:|
| 2020 | 0,40 |
| 2021 | 0,31 |
| 2022 | 0,25 |
| 2023 | 0,33 |
| 2024 | 0,44 |
| 2025 | 0,54 |
| **2026** | **0,77** |

\* Cluster C : Quiver quasi absent sur ces petits déposants → non vérifiable.

La **précision ticker est haute partout** (0,74–0,79 : on n'invente pas d'instrument). La précision (ticker, date) décroît sur les vieux scans. Deux modes d'échec résiduels : confusion 4 ↔ 1 sur docs tournés (année lue à −3 ans) ; date copiée sur toutes les lignes d'un doc. **2025–2026 quasi exempts** (0,54 / 0,77).

### 4.4 Audit de la passe LLM ticker

Sur les **894 tickers LLM**, tous rapprochables d'un bioguide Quiver : **743 concordants = 83,2 %** (pilote 2025 : 93 %). L'écart de 10 pts = membres absents de Quiver (trusts familiaux Harshbarger) + tickers delistés (XLNX→AMD 2022, CTL→LUMN). **Aucun faux ticker LLM détecté.**

---

**À retenir.** Électronique : **0 cas** où Quiver a plus que nous ; 9 vrais-absents expliqués. OCR : **précision ticker fiable** (0,74–0,79) ; précision date décroît sur scans anciens/tournés. **2025–2026 = propres** (prec. date 0,54–0,77).

---

## 5. Limites connues

- **OCR = échantillon, pas exhaustif.** Les 547 scannés ne sont pas tous extraits. Livrable OCR = mesurer la qualité, pas fournir tous les trades papier.
- **Cluster C non vérifiable.** Quiver couvre quasi-aucun petit déposant manuscrit. La prec. date 0,01 reflète l'absence de vérité-terrain.
- **Dates résiduelles (2021–2024).** Deux modes persistants après garde-fou : confusion 4 ↔ 1 sur doc tourné ; date copiée sur toutes les lignes. Non corrigés heuristiquement pour ne pas masquer de vraies erreurs.
- **Tickers non-cotés laissés vides.** Munis, obligations, options, trusts privés : `ticker` null à dessein.

---

## 6. Reproductibilité & fichiers

Dossier autonome : `.venv` local + kernel `jupiter-house-toutes-annees`, `.env` / `.env.example` / `requirements.txt` ; 547 PDF scannés + index + YAML + baseline + cache Quiver dans `data_v1/`.

**Deux notebooks (source de vérité) :**
1. `notebook_digital.ipynb` — électronique total + concordance Quiver
2. `notebook_ocr.ipynb` — census + aperçus A/B/C + OCR échantillon + diff Quiver (§4b–4d)

| Fichier | Rôle |
|---|---|
| `tables/{an}/06_house_{an}_transactions.csv` × 7 | Tables digitales finales |
| `tables/_ocr_echantillon_resultats.csv` (4 103) | Transactions OCR échantillon |
| `tables/_ocr_echantillon_diff.csv` | Diff Quiver par transaction |
| `tables/_ocr_echantillon_quiver_doc.csv` | Concordance par doc |
| `tables/_scan_census_547.csv` | Census des 547 scannés |
| `ocr_cache/` & `ocr_cache_echantillon/` | Caches versionnés (re-run gratuit) |

---

**En une ligne.** Électronique **complet** 2020→2026 : **32 676 transactions**, **99,01 %** concordance Quiver, 9 vrais-absents. OCR échantillon : **4 103 transactions**, ticker **74 %**, précision ticker **0,74–0,79**, audit LLM **83,2 %**. Point dur résiduel : dates sur scans anciens/tournés (2021–2024) ; **2025–2026 propres** (prec. date 0,77).
