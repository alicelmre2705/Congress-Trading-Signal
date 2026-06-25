# Pipeline House — Transactions boursières des représentants
## Volume 2 : années 2020 → 2026 — synthèse complète

---

## ► Résultat à utiliser

| Source | Fichier | Transactions |
|---|---|---|
| **Électronique (total)** | `data_v1/tables/{année}/06_house_{année}_transactions.csv` × 7 | **32 676** |
| **OCR (échantillon, A+B)** | `data_v1/tables/_ocr_echantillon_resultats.csv` | **3 876** |

L'OCR échantillon sert à **mesurer la qualité de la méthode**, pas à remplacer le digital. **Politique : livrable = clusters A+B (tapés) ; le cluster C manuscrit est conservé mais NON EXÉCUTÉ par défaut** (récupération ciblée de 3 filers, cf. §3.1). Chaque transaction porte un flag `date_confidence`.

---

## 1. Vue d'ensemble

| Indicateur | Valeur |
|---|---|
| Période couverte | 2020 → 2026 (7 années) |
| **Transactions électroniques (TOTAL)** | **32 676** |
| Concordance Quiver (élec, transaction) | 99,01 % |
| Trades vraiment absents (6 ans) | 9 |
| PDF scannés recensés | 547 (A : 74 / B : 322 / **C : 151 non exécuté**) |
| OCR — docs traités (livrable A+B) | 56 (sur 70 ; 14 C exclus) |
| OCR — transactions (A+B) | 3 876 |
| OCR — couverture ticker | 80 % |
| OCR — concordance Quiver A+B (deskew + tol. ±3 j) | **69,0 %** |

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
| A — tapé droit | 74 | 13,5 % | le plus propre ; lecture directe — **exécuté** |
| B — tapé tourné 90° | 322 | 58,9 % | le gros du corpus ; lisible une fois redressé — **exécuté** |
| C — manuscrit | 151 | 27,6 % | le point dur ; **catégorie conservée, NON EXÉCUTÉE par défaut** |

543/547 sont le même formulaire officiel House. 81 % des scans sont tournés. 6 sont illisibles.

**Politique de découpage — par QUALITÉ, pas par année.** Le cluster **C (manuscrit, 27,6 %) n'est PAS exécuté par défaut** (dates OCR manuscrites peu fiables) mais reste une **catégorie conservée** (census + cache), jamais supprimée. Un seuil chronologique serait à l'envers : une fois C retiré, 2020 saute à 0,90 (cf. §4.3) ; les pires années sont 2022/2024, pas les plus vieilles. On exécute **A+B, toutes années**.

**Cross-validation C ↔ Quiver — que perd-on si on n'exécute pas C ?** Mesuré sur les 151 docs C (bioguide résolu 149/151) : Quiver possède **~195–203 transactions distinctes** (déposants C, fenêtre de dépôt) **absentes de notre digital** — le brut 267 était gonflé ~25 % par les doublons natifs de Quiver. **~99 % de cette perte tient à 3 déposants** quasi sans aucune trace digitale : **Schrader** (~117, 0 digital), **Lamborn** (~20, 0 digital), **Harshbarger** (~61, 1 ligne digitale vs 1016 Quiver). **17/30 déposants C ont 0 trade Quiver** → perte corroborée nulle pour eux. ➡️ **Récupération ciblée** (`FILERS_C_A_RECUPERER`) : OCR'd uniquement les ~47 docs de ces 3 filers capte l'essentiel ; le reste de C reste non exécuté avec flag. *(Au niveau transaction, 1/161 seulement des trades C déjà OCR'd est confirmé par Quiver à ±3 j : ce sont les dates manuscrites qui divergent de 40–240 j, pas les trades qui manquent.)*

### 3.2 Volumétrie de l'échantillon

**56 docs A+B** (échantillon initial 70 − 14 C exclus), prompt durci + garde-fou date, **deskew par page** (cf. §3.3), cap 8 pages, cache versionné `ocr_cache_echantillon/` (clé `prompt_sha` + tag `deskew_v1`).

| Champ | Couverture |
|---|---|
| Transactions totales (A+B) | 3 876 |
| `ticker` (avec passe LLM) | 3 090 / 3 876 = **80 %** |
| — `explicit` | 174 |
| — `elec_dict` | 2 102 |
| — `llm` | 814 |
| — `none` (munis, obligations, options) | 786 |
| `date_confidence` = `plausible` | 3 647 (94 %) |
| `date_confidence` = `implausible` | 229 (6 %) |

**Flag `date_confidence`** (indépendant de Quiver, survit en table finale) : `implausible` si la transaction est *après* le dépôt ou > 75 j avant (hors fenêtre légale STOCK Act → quasi-certainement un misread d'année). Mesuré : attrape **24 %** des dates fausses (les **aberrantes**, ex. confusion d'année qui casserait un backtest) pour **1 %** de faux positifs. ⚠️ `plausible` ≠ « date juste » : il reste ~20 % de bruit jour/mois indétectable sans vérité externe.

### 3.3 Deskew — redressement des scans tournés

525/547 scans sont couchés (census : 303 `rotated90`, 137 `mixed`, 4 `rotated180`), avec `page.rotation=0` et canevas portrait → **aucun signal métadonnée**. L'ancien pipeline envoyait l'image **couchée** au modèle. On détecte désormais l'orientation par une **pré-passe Vision « montage 4-rotations »** (on montre la page aux 4 angles, le modèle choisit celle qui est droite — tâche de reconnaissance, bien plus fiable que calculer un angle), **page par page** (les `mixed` ont des pages d'orientations différentes), puis on redresse géométriquement (PIL) **avant** l'extraction. Sur l'échantillon : 170 pages tournées (270°/180°), 90 déjà droites. Le détecteur discrimine correctement les 4 orientations (contrôle : image déjà droite → 0°, +180° → 180°).

---

## 4. Validation contre QuiverQuant

### 4.1 Électronique

Voir tableau §2 : concordance ≥ 98 % sur chaque année, 99,01 % global. **0 cas** où Quiver a plus de transactions que nous.

### 4.2 OCR — diff transaction par transaction

Chaque transaction avec ticker classée (`_ocr_echantillon_diff.csv`, notebook §4b). **Deux correctifs** vs version précédente : (1) **deskew** des scans (§3.3) ; (2) **tolérance de date ±3 j** au lieu d'une égalité stricte — Quiver bruite la date de ±1-2 j (amendements, date de saisie), qu'une comparaison exacte comptait à tort comme erreurs. Une colonne `date_delta_days` (écart signé à la date Quiver la plus proche) gradue désormais l'erreur.

| Cluster | vérif. | match | date fausse | ticker absent Quiver | match % |
|---|---:|---:|---:|---:|---:|
| A — tapé droit | 1 164 | 930 | 167 | 67 | **79,9 %** |
| B — tapé tourné | 1 916 | 1 196 | 528 | 192 | **62,4 %** |
| **Total A+B (livrable)** | **3 080** | **2 126** | **695** | **259** | **69,0 %** |
| ~~C — manuscrit~~ | — | — | — | — | *exclu — non vérifiable* |

**Définition des colonnes** (une transaction n'est « vérifiable » que si elle a un ticker ET que Quiver couvre ce membre cette année-là) :
- **vérif.** = transactions comparables à Quiver (= dénominateur ; exclut les txns sans ticker et les membres non couverts).
- **match** = ticker **et** date (±3 j) corrects → transaction pleinement juste.
- **date fausse** = ticker bon (le membre a tradé cette valeur) mais date hors ±3 j → erreur de lecture **sur la date**.
- **ticker absent Quiver** = ticker que Quiver n'a jamais pour ce membre (soit nom mal lu, soit actif réel non tracé par Quiver — pas une hallucination).
- **match %** = match / vérif.

- **Livrable A+B : 69,0 %** (vs 65,4 % quand on incluait le C illisible, et 59,7 % avant deskew + tolérance). A (propre) à 80 %, B (tourné) à 62 %.
- **Le seul axe faible est la DATE** : 695 « date fausse » (le ticker, lui, passe). Le deskew améliore l'extraction et les tickers, **pas** la lecture des dates — voir §4.3 et §5.

### 4.3 Concordance (ticker, date) par cluster et par année *(A+B, deskew, tolérance ±3 j)*

Deux précisions (moyennées par document) : **préc. ticker** = a-t-on lu le **bon instrument** ? **préc. (ticker, date)** = la **ligne entière** est-elle juste ? L'écart entre les deux = le poids de l'erreur de **date**.

| Cluster | préc. ticker | préc. (ticker, date) | écart = erreur date |
|---|---:|---:|---:|
| A — tapé droit | 0,79 | 0,61 | −0,18 |
| B — tapé tourné | 0,72 | 0,54 | −0,18 |

| Année | préc. (ticker, date) |
|---|---:|
| 2020 | **0,90** |
| 2021 | 0,57 |
| 2022 | 0,35 |
| 2023 | 0,55 |
| 2024 | 0,44 |
| 2025 | 0,51 |
| **2026** | **0,79** |

- **La précision ticker reste haute** (0,72–0,79 : on n'invente pas d'instrument). **Le seul axe faible est la date** (−0,18 partout).
- **Confirme « par cluster, pas par année »** : une fois le manuscrit C retiré, **2020 saute à 0,90** (il était plombé par ses 48 docs manuscrits). Les pires années restent **2022 (0,35)** et **2024 (0,44)** — donc couper « avant 2022 » aurait gardé les pires et jeté la meilleure.
- Mode d'échec résiduel : **confusion de chiffre d'année** (date lue à plusieurs années), persistant **même après redressement** → ambiguïté OCR intrinsèque, pas la rotation. C'est exactement ce que le flag `date_confidence = implausible` attrape (§3.2).

### 4.4 Audit de la passe LLM ticker

Sur les **814 tickers LLM** (A+B), tous rapprochables d'un bioguide Quiver, concordance **≈ 83 %** (pilote 2025 : 93 %). L'écart de 10 pts = membres absents de Quiver (trusts familiaux Harshbarger) + tickers delistés (XLNX→AMD 2022, CTL→LUMN). **Aucun faux ticker LLM détecté.**

---

**À retenir.** Électronique : **0 cas** où Quiver a plus que nous ; 9 vrais-absents expliqués. OCR (livrable **A+B** ; manuscrit C conservé mais non exécuté, récupération ciblée de 3 filers) : **précision ticker fiable** (0,72–0,79) ; concordance **69,0 %** après deskew + tolérance ±3 j. La date reste le seul axe faible — **ambiguïté OCR intrinsèque**, pas la rotation ; flag `date_confidence` pour écarter les dates aberrantes.

---

## 5. Limites connues

- **Cluster C (manuscrit) — catégorie conservée, NON EXÉCUTÉE par défaut.** 27,6 % du corpus. Pas supprimé (tracé census/cache) ; juste pas extrait par défaut (dates manuscrites peu fiables). Cross-val Quiver : perte réelle mais concentrée (~195–203 trades distincts, ~99 % sur Schrader/Lamborn/Harshbarger) → **récupération ciblée** prévue (`FILERS_C_A_RECUPERER`), pas un abandon. Les 17/30 autres filers C = 0 trade Quiver.
- **OCR = échantillon, pas exhaustif.** Les A+B des 547 ne sont pas tous extraits (56 docs de mesure). Scaling complet = étape ultérieure.
- **Dates = ambiguïté OCR intrinsèque, PAS un artefact de rotation.** Le deskew a été testé : il améliore l'extraction et les tickers, mais **ne corrige pas les dates** — ~5 % de confusion d'année persistent sur images parfaitement droites. Mitigation = flag `date_confidence` (écarte les aberrations type confusion d'année ; ~20 % de bruit jour/mois résiduel restent indétectables sans vérité externe).
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
| `tables/_ocr_echantillon_resultats.csv` (3 876, A+B) | Transactions OCR échantillon (redressées, + `date_confidence`) |
| `tables/_ocr_echantillon_diff.csv` | Diff Quiver par transaction (+ `date_delta_days`, tolérance ±3 j) |
| `tables/_ocr_echantillon_quiver_doc.csv` | Concordance par doc |
| `tables/_scan_census_547.csv` | Census des 547 scannés |
| `ocr_cache/` & `ocr_cache_echantillon/` | Caches versionnés (re-run gratuit) |

---

**En une ligne.** Électronique **complet** 2020→2026 : **32 676 transactions**, **99,01 %** concordance Quiver, 9 vrais-absents. OCR (livrable **A+B** ; manuscrit C conservé mais non exécuté, sauf récupération ciblée de 3 filers ~47 docs) : **3 876 transactions**, ticker **80 %**, concordance Quiver **69,0 %** (deskew + tolérance ±3 j). Point dur résiduel : lecture des **dates** = ambiguïté OCR intrinsèque (≈5 % de confusion d'année même redressé) — mitigée par le flag `date_confidence`, pas la rotation.
