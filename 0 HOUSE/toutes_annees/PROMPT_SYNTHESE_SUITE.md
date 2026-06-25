# Prompt — Générer la synthèse LaTeX de `toutes_annees` (VOLUME 2 — suite du pilote 2025)

> **But** : produire UN fichier LaTeX `toutes_annees/SYNTHESE_PRESENTATION.tex`, compilable `tectonic`,
> qui est la **suite directe** du pilote 2025 (`../2025_test/SYNTHESE_PRESENTATION.pdf`). Le pilote a DÉJÀ
> expliqué toute la méthodologie ; ce document **ne la répète pas** — il couvre le NOUVEAU : le passage à
> l'échelle **électronique 2020→2026 (TOTAL)** et l'**OCR repensé** (census des 547 scannés + **échantillon
> représentatif par année**, et NON l'OCR complet). Tous les chiffres sont recalculés depuis `data_v1/` ;
> ne réintroduis aucune valeur extérieure.

## Continuité avec le 2025 (impératif)
- Réutilise **le préambule + les macros EXACTS** de `../2025_test/SYNTHESE_PRESENTATION.tex` (mêmes packages,
  couleurs `accent/accentlight/okgreen/warn`, `\file`, `\nb`, `\boite`, `\tolerance=4000…`, hyperref, babel français).
- Titre : « \textbf{Pipeline House — Transactions boursières des représentants}\\ Volume 2 : années
  2020→2026 (électronique) + OCR par échantillon ». Sous-titre : « suite du pilote « Test » T1 2025 ».
- `\tableofcontents`. Français, registre technique sobre, zéro blabla, tableaux `booktabs` dès ≥3 valeurs.

## NE PAS répéter (déjà dans la synthèse 2025 — y RENVOYER, ne pas redévelopper)
- Vocabulaire PTR / OCR / Quiver ; la mécanique du pipeline (pdfplumber+regex ; OCR Claude Vision `tool_use`
  `record_transactions` ; cache versionné `prompt_sha`) ; le **mécanisme** des 3 passes ticker
  (`explicit/elec_dict/llm`) — n'en citer que le **résultat** ; le schéma des 22 colonnes ; le dictionnaire
  `provenance/ticker_source` ; le boilerplate de reproductibilité générique.
- Pour tout cela : écrire « cf. synthèse du pilote 2025 (`../2025_test/`) » plutôt que de réexpliquer.

## Faits — VÉRITÉ TERRAIN (exacts, recalculés depuis `data_v1/`)

**A. Électronique TOTAL 2020→2026** (table figée `06_house_{année}_transactions.csv` ; concordance honnête
« standard Q1 », reproduite par `notebook_digital.ipynb` / `data_v1/tables/00_quiver_q1style_status.csv`) :

| Année | txns | déclarants | ticker % | concordance Quiver | vrais-absents |
|---|---|---|---|---|---|
| 2020 | 6 886 | 96 | 91,0 | 99,71 % | 0 |
| 2021 | 5 457 | 105 | 91,1 | 99,68 % | 1 |
| 2022 | 3 601 | 97 | 86,8 | 98,88 % | 0 |
| 2023 | 4 161 | 88 | 86,9 | 98,10 % | 3 |
| 2024 | 2 694 | 90 | 81,8 | 98,01 % | 2 |
| 2025 | 7 577 | 96 | 90,5 | 98,93 % | 1 |
| 2026 | 2 300 | 79 | 84,0 | 98,64 % | 2 |
| **Total** | **32 676** | — | **88,6** | **99,01 %** | **9** |

- Concordance globale niveau transaction **99,01 %** (matched 24 212 / only-Quiver 241). only-Quiver = **232
  ticker-raté** (présents chez nous, ticker non extrait : préférentielles, Trésor, fonds) + **9 vrais-absents**.
- Les 9 vrais-absents (tous expliqués, aucun bug) : Malinowski ANIK 2020 ; Schrader VRNG/ELN/MSCI 2022 ;
  Calhoun AFRM/IBM 2024 ; Gottheimer IFNNY 2025 ; Pelosi INTC/UBER 2026.
- 3 dérives de format corrigées en validant vs Quiver : casse pré-2021 (rendement 2020 84 %→100 %) ;
  pollution de descriptions ; MLP sans code `[XX]` (manques 2020 183→15).

**B. Census OCR — les 547 PDF scannés** (`_scan_census_547.csv`, recensement visuel complet 547/547) :

| Cluster | docs | part |
|---|---|---|
| A — tapé droit | 74 | 13,5 % |
| B — tapé tourné 90° | 322 | 58,9 % |
| C — manuscrit | 151 | 27,6 % |

- **543/547 = le même formulaire officiel House** ; **2 seuls vrais relevés externes** (Ted Yoho 2020,
  Morgan Stanley) ; 81 % des scans sont **tournés** ; **6 docs réellement illisibles** ; le **manuscrit est
  concentré en 2020-2021** (78/151) et quasi nul en 2026.

**C. OCR par ÉCHANTILLON (le livrable OCR — PAS les 547)** (`echantillon_ocr.py`, prompt durci + cap 8 pages
+ cache `ocr_cache_echantillon/` ; sélection `_ocr_echantillon.csv` ; restitué par `notebook_ocr.ipynb`) :
- **70 docs (10/an : 2 A / 6 B / 2 C ; 2026 = 8 A / 2 C)**, stratifiés, déposants couverts par Quiver priorisés.
- **4 596 transactions** ; ticker **78 %** (3 565/4 596) — sources : explicit 170 · elec\_dict 2 399 · **llm 996**
  · none 1 031 (= vrais non-cotés : munis/obligations/options, ticker null à juste titre).
- Concordance Quiver fenêtrée — **par cluster** (prec\_ticker / prec\_(ticker,date)) :
  A 0,78 / 0,58 · B 0,74 / 0,45 · C 0,76 / 0,02 (C : Quiver quasi absent → non vérifiable).
- **Par année** (prec\_(ticker,date)) : 2020 0,38 · 2021 0,33 · 2022 0,25 · 2023 0,39 · 2024 0,44 · 2025 0,54
  · **2026 0,77** (scans récents propres). prec\_ticker par année : 0,57–0,94.
- 2020 et 2026 sont par ailleurs OCR **à 100 %** hors échantillon (7 764 / 3 850 txns) — bonus déjà sur disque.

**D. Autonomie du dossier** : `toutes_annees/` autonome (modèle 2025) — `.venv` local + kernel
`jupiter-house-toutes-annees`, `.env`/`.env.example`/`.gitignore`/`requirements.txt`, **547 PDF + index +
YAML + baseline + cache Quiver embarqués** dans `data_v1/`, moteurs (`house_multiyear.py`,
`house_ocr_multiyear.py`) à la racine ancrés `BASE_DIR`, `grep "semaine 1"` = 0, l'écarté dans `_archive/`.

## Structure imposée (sections — focalisées sur le NOUVEAU)
1. **Ce document est la suite du pilote 2025** — `\boite` qui renvoie au 2025 pour la méthodo et liste ce
   qu'on ne réexplique pas ici (vocabulaire, mécanique pipeline, passe LLM, schéma colonnes).
2. **Vue d'ensemble (Volume 2)** — NOUVEAU schéma TikZ : `électronique 2020→2026 (TOTAL)` ‖ `547 scannés →
   census 3 clusters → échantillon 10/an → OCR` → `validation Quiver` ; + tableau « chiffres clés Volume 2 ».
3. **Électronique 2020→2026** — table par année (Faits A) ; méthode de concordance honnête (citée, pas
   redéveloppée) ; les 9 vrais-absents ; les 3 dérives de format corrigées.
4. **L'OCR repensé** — (a) **census 547** = typologie 3 clusters (tableau + 1 phrase/cluster) ; (b) la
   **décision** « échantillon représentatif par année, pas l'OCR des 547 » et son pourquoi (coût ; manuscrit
   inhérentement dur et peu vérifiable Quiver) ; (c) **résultats de l'échantillon** (Faits C) : tickers (dont
   passe LLM, résultat seul) + concordance Quiver par cluster ET par année.
5. **Limites (honnêteté)** — OCR = échantillon, **PAS exhaustif** (547 non OCR au trade-level) ; manuscrit
   ancien dur + Quiver mince ; la concordance (ticker,date) est gatée par la **lecture des dates** sur scans
   dégradés (prec\_ticker élevé mais prec\_(ticker,date) plus bas sur vieux/manuscrit) ; tickers non-cotés
   laissés vides à dessein.
6. **Reproductibilité (court, spécifique)** — dossier autonome (Faits D) + les 2 notebooks (`notebook_digital`,
   `notebook_ocr`) ; renvoyer au 2025 pour le reste.

Terminer par un `\boite` « message en une ligne » : **électronique TOTAL 2020→2026 (32 676 txns, 99 % Quiver)
+ OCR validé par échantillon représentatif par année (census 547 → 3 clusters → 10 docs/an)** ; suite directe
du pilote 2025, dossier autonome.

## Règles de rédaction (identiques au 2025)
Français sobre ; chaque chiffre adossé aux Faits ; tableaux `booktabs` ; section Limites précise et non
minimisée ; sortie = **un seul `.tex` compilable `tectonic`**, aucun asset externe (seul schéma = TikZ) ;
échapper `_ & % $` dans le texte, `\texttt{}` pour fichiers/colonnes.
