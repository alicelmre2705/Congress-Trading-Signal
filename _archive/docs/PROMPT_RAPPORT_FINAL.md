# PROMPT — Document de recherche final « Congress Trading Signal · Couche données » (LaTeX → PDF)

> **Livrable de cette exécution** = UN document **LaTeX → PDF de niveau publication de recherche**,
> qui présente à **Ramify** l'intégralité du travail de la **couche données (Semaines 1-2)**, et qui se
> lit **main dans la main avec le dépôt GitHub** : architecture, **chaque fonction Python**, métriques,
> choix méthodologiques, et **hypothèses explorées puis révisées**.
> **Auto-suffisant** : un exécutant sans mémoire de la conversation doit pouvoir le réaliser depuis
> `/Users/lemairealice/Downloads/Jupiter`. À lancer dans une **session fraîche**.

---

## 0. Règles d'or (NON négociables)
1. **Sortie unique** : `docs/RAPPORT_FINAL.tex` (+ `docs/RAPPORT_FINAL.pdf` compilé avec **tectonic**).
   N'écris **rien d'autre** ; ne **modifie/supprime AUCUN** fichier existant (données, code, tests,
   autres docs, golden). Lecture seule partout ailleurs.
2. **Le CODE et les DONNÉES font autorité** — pas les docs (qui ont déjà été incohérentes). Avant
   d'écrire un chiffre, **recalcule-le depuis les tables FINAL** (`data/house/tables/{an}/06_house_{an}_FINAL.csv`,
   `data/senate/{an}/06_senate_{an}_FINAL.csv`). L'annexe « Valeurs vérifiées » (§6) est déjà recalculée :
   utilise-la, et re-vérifie au moindre doute.
3. **Périmètre = Semaines 1-2 (DONNÉES) UNIQUEMENT.** La **stratégie/backtest (Semaines 3-4)** est
   **HORS-PÉRIMÈTRE** : la mentionner en une phrase (« travaux de recherche séparés, en cours »), sans
   la détailler. (Elle vit isolée dans `00. S3S4 en cours/` ; ne pas y toucher, ne pas la décrire.)
4. **Langue = français.** Style **publication de recherche** : rigoureux, sobre, **honnête** (rapporter
   les limites et les nuances). **Aucune sur-vente** : ce n'est pas un pitch, c'est un rapport technique.
5. **Main dans la main avec le GitHub** : chaque mécanisme **cite le `fichier:fonction` réel**
   (ex. `congress_core/identity.py:make_matcher`). Objectif : doc + repo ⇒ on comprend **tout**.
6. **LaTeX reproductible** : réutilise le préambule de `docs/ARCHITECTURE.tex` (tectonic-compatible :
   `babel french`, `geometry`, `booktabs`, `longtable`, `tabularx`→ **attention** préférer `tabular`/`longtable`
   à largeurs fixes, `xcolor`, `tcolorbox`, `hyperref`, `tikz`, `newunicodechar` pour `→ — − · …`).
   **Inclure les 4 figures réelles** de `docs/quality/*.png`. Compile **sans erreur**.

---

## 1. Avant d'écrire — lis ces sources (dans cet ordre)
- `docs/ARCHITECTURE.tex` — structure dérivée du **code réel** (diagrammes TikZ, 3 couches, schéma FINAL
  28 colonnes, « voyage d'une transaction », annexe des 44 `.py`). **Base de la partie architecture.**
- `docs/RAPPORT_COMPLET.tex` — déroulé réel du pipeline, étape par étape (le cœur narratif à consolider).
- `docs/RAPPORT_QUALITE.md` + `docs/quality/*.png` — les **5 contrôles qualité** + les figures.
- `README.md`, `tests/regression/README.md`, `data/external/README.md`.
- `0.Notion_Ramify.pdf` — **ce que Ramify attend** (pour mapper le document à leurs livrables).
- **Le CODE** : `congress_core/*.py`, `house/*.py`, `senate/*.py` (lis les **corps** des fonctions).
- **Recalcule** les métriques depuis les FINAL (cf. §6).

---

## 2. Structure imposée du document (≈ 20-30 pages)
0. **Page de titre** + **Résumé (abstract)** : 8-12 lignes — problème, ce qui est construit, chiffres clés
   (90 487 transactions, 2 chambres, 2020-2026, table 12/12, validé Quiver, reproductible).
1. **Introduction & contexte** : le *copy-trading* du Congrès, le **STOCK Act**, ce que Ramify a
   commandé (Semaines 1-2 = couche données), périmètre et limites de l'étude.
2. **Sources & acquisition** : House Clerk (index XML + PDF), Sénat eFD (HTML + scans `.gif`) ; piste
   **électronique (parsing déterministe)** vs **scannée (OCR Claude Vision)** ; **Quiver = vérification
   externe uniquement** (jamais réinjecté).
3. **Architecture & méthodologie** (s'appuyer sur `ARCHITECTURE.tex`) : les **3 couches**
   (`congress_core` partagé · `house`/`senate` orchestrateurs · `data`/`tests`), le **pipeline en 7
   étapes** (`congress_core/pipeline.py`), la **convention de numérotation des fichiers** (03/04/05/06/06b/
   06_FINAL/07/00). Inclure le diagramme de flux.
4. **Le pipeline pas à pas + CHAQUE fonction Python** (voir §3 ci-dessous) : pour chaque module, un
   tableau `fonction → ce qu'elle fait → ce qu'elle renvoie`, + l'étape du flux.
5. **Résolution d'identité** (priorité #1) : nom → `bioguide_id`, la cascade `make_matcher`
   (exact → surnom → override), **99,99 % House / 100 % Sénat**, les 4 cas non rattachés (manuscrit).
6. **OCR (Claude Vision)** : scans, **deskew** (montage 4-rotations), **cache versionné** (`prompt_sha`),
   clusters A/B/C, **exclusion du cluster C manuscrit** (dates peu fiables) ; volumes OCR (House 48 970,
   Sénat 1 680).
7. **Enrichissement** : tickers (3 voies : explicite → dictionnaire → LLM), **secteur GICS → ETF SPDR**
   (yfinance + repli LLM), montants → **midpoint**, **`years_in_office`**.
8. **La table finale** : **schéma 12/12 champs** (les nommer) sur 27-28 colonnes ; expliquer chaque
   colonne et son origine (cf. tableau dans `ARCHITECTURE.tex`). **Nuance d'honnêteté** : « 12 champs
   *présents* » ≠ « 12 champs *sans manquants* » (ticker/secteur non cotés par nature ; commissions =
   snapshot courant).
9. **Rapport de qualité & métriques** : les **5 contrôles** ((a) cohérence dates, (b) délai légal 45 j,
   (c) distribution des montants, (d) coverage par congressman, (e) achats sans sortie) **avec les 4
   figures** (cf. §4). **Présenter la couverture PAR ANNÉE** (pas seulement le global) et **expliquer la
   baisse Sénat 2025-26** (plus de munis/Treasuries non cotés, papier).
10. **Validation externe (Quiver)** : méthode **2 axes** (comptes par déposant + recouvrement
    transaction-niveau, clé `bioguide|ticker|date|type`), concordance (House ~85,9 %/an, Sénat 98-100 %/an),
    et le constat **« OCR = source unique »** (les agrégateurs sont aveugles au papier). Recalcule depuis
    `07_quiver_*` si possible.
11. **Assurance qualité & reproductibilité** : le filet `tests/regression/` — **golden** (photo octet-à-octet,
    House 108 / Sénat 69 fichiers) **+ reproduction** (recompute des colonnes clés) ; pourquoi « non
    rejouable hors-ligne ⇒ preuve par reproduction ». (cf. `tests/regression/README.md`.)
12. **Hypothèses explorées puis révisées** (le récit « recherche » — voir §5) : les choix méthodologiques
    qui ont évolué, et **pourquoi**.
13. **Limites (honnêteté)** : cluster C manuscrit exclu ; commissions non *point-in-time* ; pas de
    tolérance de date dans l'appariement Quiver House (couverture = plancher) ; ticker/secteur
    structurellement absents pour munis/obligations ; `date_confidence` heuristique (et **colonne OCR
    seulement**).
14. **Périmètre & suite** : couche données (S1-2) **livrée** ; la **stratégie/backtest (S3-4)** = travaux
    séparés en cours (une phrase, sans détail).
15. **Conclusion**.
16. **Annexes** : (A) **tableau de référence des 44 `.py`** (1 ligne chacun) ; (B) **arbre `data/`
    annoté** ; (C) **valeurs vérifiées** (§6) ; (D) **comment lancer/reproduire** (`pip install -e .`,
    `python -m congress_core.pipeline`, `tests/regression/check_golden.py`).

---

## 3. Exigence spéciale — « expliquer TOUTES les fonctions Python »
Pour **chaque** module de `congress_core/` (15), `house/` (4), `senate/` (11), produire un **tableau**
`Fonction | Ce qu'elle fait (corps réel) | Ce qu'elle renvoie`, + l'étape du pipeline où elle intervient.
Base de départ : l'annexe de `docs/ARCHITECTURE.tex` (déjà dérivée du code) ; **re-vérifie chaque entrée
contre le code**. Ne liste que des fonctions **réelles**. Couvre au minimum les modules cœur :
`schema` (natural_key_hash, dedup), `identity★` (make_matcher, enrich_identity, add_years_in_office),
`amounts`, `tickers`, `vision_ocr` (extract_cached, prompt_sha, detect_rotation), `llm_resolve`, `quiver`
(validate_quiver_house, reconcile), `crosscheck`, `sector_enrich` (enrich_sectors), `reporting`, `paths`,
`pipeline` (build_steps), `quality` (les 5 contrôles), `enrich_tenure` ; et les orchestrateurs
`house/digital.py:run_year`, `house/ocr.py:run_ocr_year`, `senate/digital.py:run_year`, `senate/fusion.py:main`.

---

## 4. Les figures (provenance — À EXPLIQUER dans le doc, fini le « d'où viennent ces images »)
Les 4 figures de `docs/quality/` sont **générées automatiquement** par
`python -m congress_core.quality` (fonction `build_report` → `_figures`, matplotlib, **lecture seule des
FINAL, aucun appel API**). Les inclure avec des légendes qui le disent :
- `delai_divulgation.png` — histogramme du délai `disclosure − transaction` (lignes 45 j / 75 j) ←
  `quality.delay_buckets`.
- `distribution_montants.png` — distribution de `amount_midpoint` (échelle log) ← `quality.amount_distribution`.
- `top_deposants.png` — top déposants par volume estimé (Σ midpoint) ← `quality.amount_distribution`.
- `transactions_par_an.png` — transactions par an et par chambre ← `quality.coverage_per_member`/`_figures`.

---

## 5. Hypothèses explorées puis révisées (à NARRER honnêtement — la valeur « recherche »)
Raconter, pour chaque point, **l'hypothèse de départ → le problème constaté → la décision finale** :
- **Deskew OCR** : demander au modèle « de combien tourner ? » (échec : répondait toujours « 90 ») →
  **montage 4-rotations**, le modèle *reconnaît* la page droite (concordance 59,7 % → ~69 %).
- **Déduplication** : dédup naïve sur la clé seule (écrasait des lots multi-comptes réels, ex. Khanna) →
  **`occurrence_index`** (dédup non destructrice).
- **OCR par échantillon d'abord** (`house/echantillon.py`) : pilote stratifié pour mesurer la qualité
  *avant* le run complet des 547 PDF.
- **Cluster C manuscrit** : tenté, puis **exclu** (dates manuscrites trop incertaines pour une stratégie
  datée) ; sonde **Opus vs Sonnet** sur le cluster C → Opus ne corrige pas le goulot (les dates), coût ×3
  → on garde Sonnet, C reste exclu.
- **Fenêtre de plausibilité de date** : STOCK Act ~45 j, mais on tolère **75 j** (`date_confidence`) pour
  le bruit OCR — à expliquer (et noter que la colonne n'est calculée que pour l'OCR).
- **Ticker en 3 voies** (explicite → dictionnaire électronique → LLM) : ajoutées par échecs successifs ;
  passe LLM filtrée `is_equity` (ne tickerise jamais une obligation/muni).
- **Quiver** : validation **per-lot** vs **transaction-niveau** ; clé House « brute » (sans tolérance de
  date) vs Sénat « normalisée » ; dédup des amendements.
(Compléter en lisant `docs/_archive/REFONTE_*.md`, `docs/_archive/SYNTHESE_senate.md` et les docstrings.)

---

## 6. Annexe — VALEURS VÉRIFIÉES (recalculées depuis les FINAL — utiliser telles quelles)
**Volumes** : House **81 646** (digital **32 676** + OCR **48 970**) ; Sénat **8 841** (digital **7 161**
+ OCR **1 680**) ; **total 90 487** ; 7 ans (2020-2026).
**Identité** : House **99,99 %** (256 bioguides / 275 noms ; **4 lignes sans bioguide** = un cas manuscrit
2023) ; Sénat **100 %** (64 bioguides / 67 noms).
**Couverture (taux de remplissage GLOBAL, rows-based — chiffre canonique)** :
- `ticker` : House **85,3 %** · Sénat **71,4 %**
- `sector_gics`/`etf_proxy` : House **83,2 %** · Sénat **62,1 %**
- `asset_type` : House **91,1 %** · Sénat **97,6 %**
- `committee_membership` : House **88,6 %** · Sénat **69,6 %**
**Validation Quiver** : House **~85,9 %/an** (transaction-niveau) ; Sénat **98-100 %/an** (recalcule via
`07_quiver_*` ; 0 vrai raté Sénat, 9 vrais-absents House après explication des 248 bruts).
**Golden (zéro écart)** : House **108** fichiers · Sénat **69** fichiers.
**Qualité (5 contrôles, depuis `RAPPORT_QUALITE.md`)** : (a) cohérence dates House **99,8 %** / Sénat
**100 %** ; (b) **~87 %** des dépôts House ≤ **45 j** ; (c) montants médiane **8 000 $**, p75 **32 500 $** ;
(d) **320** déposants, **206** avec ≥ 10 trades, **150** actifs ≥ 3 ans ; (e) achats sans sortie **22,5 %**
House / **39,6 %** Sénat.
**Concentration** : Rohit Khanna ≈ **30 516** transactions (gros déposant OCR ; top 3 House = ~92 % de l'OCR).

**Nuances HONNÊTES à intégrer (ne pas masquer)** :
- **Couverture Sénat en baisse 2025-26** (ticker ≈ 45 %, secteur ≈ 37 % ces années vs 80 %/70 % avant) :
  présenter la couverture **par an** et l'expliquer (papier OCR + obligations municipales non cotées,
  ex. Blumenthal). Le global (71,4 % / 62,1 %) est tiré vers le haut par les années antérieures.
- **« 12 champs présents » ≠ « sans valeurs manquantes »** : `ticker`/`sector`/`committee` ont des trous
  **légitimes** (actifs non cotés ; commissions = snapshot courant). À assumer explicitement.
- **`date_confidence`** = heuristique (fenêtre 75 j), **colonne renseignée pour l'OCR seulement** (NaN sur
  le digital) ; les contrôles (a)/(b) sont calculés **directement sur les dates** dans `quality.py`.
- **256 bioguides vs 275 noms** (House) : variantes orthographiques d'un même élu — expliquer.

---

## 7. Vérification (avant de rendre)
- `tectonic docs/RAPPORT_FINAL.tex` **compile sans erreur** → PDF multi-pages.
- **Chaque chiffre** du document est cohérent avec §6 / recalculable depuis les FINAL ; **chaque
  `fichier:fonction`** cité existe (grep de contrôle).
- Les **4 figures** apparaissent avec une légende mentionnant leur génération par `congress_core/quality.py`.
- La section « Hypothèses révisées » est présente et honnête ; les **limites** sont explicites.
- **Aucun fichier existant modifié** (`git status` ne montre que `docs/RAPPORT_FINAL.tex/.pdf` en nouveaux).
- La partie **Stratégie/Backtest (S3-4) n'est PAS développée** (une phrase max).
