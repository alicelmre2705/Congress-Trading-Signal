# PROMPT — Rapport complet du projet « Congress Trading Signal » (dossier Jupiter)

## Rôle
Tu es rédacteur technique. Tu produis **un rapport LaTeX → PDF** complet, clair et **pédagogique** du
projet *Congress Trading Signal* (dossier `Jupiter`), couvrant **la Chambre (House) ET le Sénat**.
Le rapport doit pouvoir être lu par quelqu'un qui connaît le projet de loin et veut **tout comprendre
dans l'ordre**, puis le **présenter**. Pas d'expert OCR ni finance présumé.

## Objectif et double usage
Le projet extrait et valide les déclarations boursières (PTR, *STOCK Act*) des membres du Congrès US,
2020–2026, pour une stratégie de copy-trading. Le rapport existant `docs/RAPPORT_HOUSE.tex` est mal
organisé, ne couvre que le House, et liste des métriques sans les définir. Ton rapport doit : **(1)**
faire comprendre l'intégralité du projet (le « comment » et le « pourquoi », pas seulement les
chiffres), **(2)** être présentable.

## Contraintes de rédaction — IMPÉRATIVES
- **Français. Phrases courtes et claires. Zéro blabla, zéro remplissage.**
- **Chronologique** : on suit le déroulé réel du pipeline, étape après étape, de l'acquisition jusqu'aux
  métriques finales. Pas de saut.
- Pour **chaque étape** : (a) à quoi elle sert, (b) comment elle marche concrètement, (c) le choix fait
  et **pourquoi**, (d) si pertinent l'**avant/après chiffré** (ex. ticker 46 % → 90 %), (e) le résultat.
- **Chaque métrique est définie en langage simple AVANT de donner sa valeur** (le sens + le calcul).
  Ne jamais citer une métrique sans l'avoir définie.
- **Couvre House ET Sénat.** À chaque étape : d'abord le **mécanisme partagé** (`congress_core`), puis
  les spécificités **House**, puis **Sénat** (avec leurs différences). C'est ce va-et-vient
  partagé ↔ spécifique qui doit être lisible.
- **Justifie les choix par les échecs qui les ont motivés** : un premier essai donne un résultat
  insuffisant → on ajoute une règle. (Ex. : le dictionnaire ticker plafonne → on ajoute le LLM ; les
  scans sont couchés → on ajoute le deskew ; dédup naïve détruirait les lots multi-trust → clé naturelle
  + `occurrence_index`.)
- **Honnêteté** : une section dédiée à ce qui reste **imparfait / non résolu / « pas tout à fait vrai »**.
- **Quiver n'est jamais une source** : c'est une vérification externe, jamais réinjectée dans les tables.
  Dis-le explicitement.
- **Chiffres exacts** : utilise l'annexe « Valeurs vérifiées » ci-dessous telle quelle. En cas de doute,
  recompute via `tests/regression/audit_metrics.py`. Si une lecture du code contredit l'annexe, signale-le
  plutôt que d'inventer.

## Avant d'écrire — lis ces fichiers pour t'ancrer
- `README.md` (vue d'ensemble, chiffres clés)
- `docs/RAPPORT_HOUSE.tex` (rapport actuel — reprends son préambule LaTeX et ses bons passages, corrige
  l'organisation)
- `tests/regression/audit_metrics.py` (**source de vérité chiffrée** — toutes les métriques s'y recalculent)
- `congress_core/` : `schema.py`, `identity.py`, `tickers.py`, `vision_ocr.py`, `llm_resolve.py`,
  `quiver.py`, `crosscheck.py`, `sector_enrich.py`, `amounts.py`, `paths.py`
- `house/digital.py`, `house/ocr.py`, `house/echantillon.py`
- `senate/digital.py`, `senate/ocr.py`, `senate/ocr_engine.py`, `senate/identity.py`,
  `senate/ticker_resolve.py`, `senate/quiver_audit.py`, `senate/fusion.py`
- `docs/REFONTE_HOUSE.md`, `docs/REFONTE_SENATE.md`, `docs/SYNTHESE_senate.md`
- Survole `data/house/tables/2022/` et `data/senate/2022/` pour voir les tables réelles (06, 06b,
  06_FINAL, 07x).

## Questions auxquelles le rapport DOIT répondre explicitement
(Ce sont les points actuellement mal expliqués. Chacun doit avoir sa réponse claire dans le texte.)
1. **Comment récupère-t-on les données ?** House Clerk (index XML + PDF) côté House ; eFD côté Sénat,
   avec le « piège CSRF ». Explique le mécanisme concret, pas juste « on télécharge ».
2. **Que fait l'identité (`identity.py`) ?** Comment on associe à chaque membre son bioguide, nom,
   surnom, parti, état, commissions. Comment on désambiguïse et on **évite les doublons de personnes**.
3. **Que fait `schema.py` / la clé naturelle ?** Pourquoi une clé à 7 champs **sans ticker**, et à quoi
   sert `occurrence_index`. Donne le schéma de la table FINALE.
4. **Comment distingue-t-on lisible vs non lisible ?** Le **critère exact** (couche texte du PDF via
   `pdfplumber` : `bool(text.strip())`), et les trois cas lisible / non_lisible / absent.
5. **Comment parse-t-on le digital ?** Les marqueurs regex, le rendement, les échecs.
6. **Les 3 clusters OCR (A/B/C) :** comment ils sont définis, **pourquoi un pilote sur un échantillon
   stratifié des trois** d'abord (pour comprendre et adapter), pourquoi **C (manuscrit) est exclu par
   défaut** (dates peu fiables) avec récupération ciblée de 3 déposants.
7. **L'OCR :** deskew (montage 4-rotations — pourquoi ça plutôt que « de combien tourner ? »), Vision
   (Claude Sonnet, `tool_use` forcé, cache versionné, reprise au batch, filtre ligne-exemple), puis
   « normalize » (montants A–K → fourchette/milieu, owner, `date_confidence`). Dis ce qu'est « normalize ».
8. **Les tickers :** les 3 voies (explicite → dictionnaire électronique → passe LLM), **avant/après**
   (dict ~46 % → +LLM ~90 %), pourquoi le LLM a été ajouté, et ce qui reste `none` **à dessein** (non cotés).
9. **L'identité — résultats :** taux dans Bioguide (99,99 % House / 100 % Sénat), qui sont les manquants.
10. **Fusion digital + OCR :** comment, et **pourquoi il y a plus d'OCR que de digital côté House**
    (c'est normal : gros déposants-papier) — et pourquoi c'est l'inverse au Sénat.
11. **Validation Quiver :** la méthode honnête (2 axes), ce que veut dire chaque résultat.
12. **Toutes les métriques finales, définies :** couverture, accord de sens, accord de montant,
    `only_ours`/`only_quiver`, **vrais-absents** (248 brut → 9 réels, avec la décomposition des artefacts),
    couverture identité/ticker/date, **`date_confidence`** (plausible/implausible, fenêtre 75 j, le pic
    2021 Harshbarger localisé), concentration par cluster/déposant.
13. **Le « verdict 35–74 % » :** explique clairement que c'est la couverture Quiver du **numérique seul**,
    par an, et **pourquoi la fenêtre est si large** (variance annuelle de la part des déposants-papier) —
    **pas** un verdict de qualité sur le FINAL, que l'OCR porte à 85,9 %.
14. **Ce qui reste imparfait / non résolu / pas tout à fait vrai.**

## Plan imposé du rapport
> Chaque section suit la trame : *mécanisme partagé → House → Sénat → résultats → choix & justification*.

0. **Vue d'ensemble & structure visuelle**
   - Mission (copy-trading, PTR/STOCK Act, House + Sénat 2020–2026).
   - **Schéma TikZ du pipeline** : la colonne vertébrale chronologique (acquisition → identité → manifeste
     → digital → OCR → tickers → secteur → fusion → Quiver → métriques), avec les branches House / Sénat.
   - **Carte des dossiers** : `congress_core/` (cœur partagé, 11 modules), `house/`, `senate/`, `data/`,
     `tests/regression/` — et le principe « cœur partagé, chambres = orchestration ».
   - **Tableau des chiffres clés** des deux chambres (résumé exécutif).
   - **Numérotation des tables** (03 index, 04 manifeste, 05 échecs, 06 digital, 06b OCR, 06_FINAL,
     06c/06d, 07/07b…07f, 08, 00 dashboards).
   - Principe transversal : **Quiver = vérification externe, jamais réinjecté**.
1. **Acquisition** — House Clerk (XML `{an}FD.xml`, `FilingType=P`, PDF) ; Sénat eFD (CSRF
   `accept_agreement`, `report_types=[11]`, HTML électronique + `.gif` papier). `disclosure_date =
   FilingDate` (anti look-ahead). Différence des sources.
2. **Identité (bioguide)** — référentiel `congress-legislators` (12 767), `make_matcher` (normalisation,
   suffixes, 36 surnoms, middle, overrides Van Taylor / JD Vance), dédup personnes. Résultats : House
   99,99 %, Sénat 100 % ; délégués exclus côté Sénat.
3. **Schéma & clé naturelle** — `natural_key_hash` (7 champs, sans ticker), `occurrence_index`, dédup
   non destructrice (le piège évité : 2 425 lignes Khanna). Schéma FINAL **27 colonnes** pour les DEUX
   chambres (ordre des colonnes légèrement différent entre House et Sénat — même contenu 12/12).
4. **Manifeste : lisible / non lisible / absent** — critère `pdfplumber` exact ; chiffres par année.
5. **Piste électronique (digital)** — `parse_ptr` (regex P/S/E, dates, montants), rendement 99–100 %,
   échecs `05`. Volumes (House 32 676 ; Sénat 7 161).
6. **Clusters OCR A/B/C & pilote** — census 547 (A 74 / B 322 / C 151), l'échantillon stratifié
   (`echantillon.py`, prompt durci, tolérance ±3 j) pour comprendre avant le run complet ; décision
   C exclu + récupération ciblée. (Sénat : pas de clusters — 5 sénateurs papier.)
7. **Pipeline OCR** — deskew (montage 4-rotations, 59,7 % → 69,0 %), Vision (Sonnet 4.6, `tool_use`
   forcé, `PROMPT_SHA`, reprise au batch, garde-fou année, filtre ligne-exemple), normalize (A–K,
   owner, `date_confidence` fenêtre 75 j). Volumes (House 48 970 ; Sénat 1 680).
8. **Résolution des tickers** — explicit → elec_dict → LLM (Sonnet, filtre `is_equity`, cache versionné).
   Avant/après dict ~46 % → +LLM ~90 %. House 85,3 % ; Sénat 71,4 % (Blumenthal munis → `none` à dessein).
9. **Enrichissement secteur GICS → ETF** — yfinance + repli LLM, 11 secteurs → ETF SPDR. **House 83,2 %
   et Sénat 62,1 %** → les DEUX chambres à **12/12 champs** (le FINAL House passe de 24 à 27 colonnes :
   ajout `sector_gics`/`etf_proxy`/`sector_source`, parité Sénat).
10. **Fusion digital + OCR → FINAL** — dédup `(nk, occ)`, 405 doublons cross-doc retirés (House) / 0
    (Sénat). **House FINAL 81 646 ; Sénat 8 841.** Explique OCR > digital (House) vs inverse (Sénat).
11. **Validation Quiver** — 2 axes (comptes per-lot ; recouvrement transaction-niveau, clé
    `bioguide|ticker|date|type`). Sénat : audit 7 aspects (dédup amendements 554, couverture 98–100 %,
    accords sens/date/montant, deltas). OCR papier validé **hors Quiver** (agrégateurs aveugles au scanné).
12. **Métriques finales — chacune définie** — couverture, accord sens, accord montant, only_ours/only_quiver,
    vrais-absents (248 → 9, décomposition), identité/ticker/date, `date_confidence`, concentration. **Et le
    verdict 35–74 % expliqué.**
13. **Reproductibilité / zéro changement** — golden (House 108 / Sénat 68 fichiers), `check_golden`,
    `test_*_repro` (8 841/8 841, 67/67, 65/65), invariants. Pipeline non re-jouable hors-ligne → preuve
    par reproduction depuis colonnes figées.
14. **Limites & imperfections** — validation papier externe impossible ; comités non point-in-time ; pas
    de tolérance date House (85,9 % = plancher) ; only_quiver non décomposé auto ; asset_type 91,1 % ;
    `date_confidence` heuristique binaire ; cluster C ; Harshbarger 2021 ambiguïté intrinsèque.
15. **Synthèse / verdict** — la donnée concorde bien ; ce qui est fait / différé / non fait.

## Annexe — VALEURS VÉRIFIÉES (à utiliser telles quelles)

**Provenances** : House `house-pdf-electronic` / `house-pdf-ocr` ; Sénat `senate-efd-electronic` /
`senate-efd-ocr`.

**Chiffres clés**
- **House FINAL 81 646** = 32 676 électronique + 48 970 OCR. 256 bioguides / 275 noms, identité **99,99 %**
  (4 sans bioguide = Ada Norah Henriquez, manuscrit, 2023, doc 8219483). Quiver FINAL **85,9 %** (81–91 %/an).
  Accord sens ~93 %, montant ~93 %. **Vrais-absents 9 / 81 646.** Ticker 85,3 %. asset_type 91,1 %.
  **Secteur GICS→ETF 83,2 %** (67 932/81 646) → **table 12/12** (FINAL House = **27 colonnes**).
- **Sénat FINAL 8 841** = 7 161 électronique + 1 680 OCR papier. 64 bioguides / 67 noms, identité **100 %**
  (0 sans bioguide). Quiver digital **98–100 %/an**, **0 vrai raté**, 554 amendements dédupliqués.
  Ticker **71,4 %**, secteur GICS→ETF **62,1 %** (12/12 champs).

**Volumes House / an** (Digital · OCR · FINAL · déposants · sans bio) — *autoritatif (RAPPORT_HOUSE.tex)* :
2020 6 886·8 791·15 677·109·0 | 2021 5 457·6 816·12 273·120·0 | 2022 3 601·10 900·14 501·110·0 |
2023 4 161·6 329·10 490·100·4 | 2024 2 694·6 277·8 971·97·0 | 2025 7 577·6 067·13 644·107·0 |
2026 2 300·3 790·6 090·84·0 | **Total 32 676·48 970·81 646·256·4**.

**Concordance Quiver House / an** (cov % · sens % · montant % · nous≥Q / nous<Q · déficits>30) :
2020 85,0·94,6·89,0·103/6·0 | 2021 88,6·94,4·90,1·115/5·1 | 2022 80,7·88,8·89,1·108/2·0 |
2023 81,0·94,1·93,8·98/3·0 | 2024 85,8·92,2·94,0·96/1·0 | 2025 91,3·93,8·98,6·104/3·0 |
2026 88,0·95,8·98,4·81/3·0 | **Global 85,9·~93·~93·—·2**.
Clé House `bioguide|ticker|date|type[:4]` (date brute). `only_ours` global 16 166 (= papier que Quiver
ne voit pas). Date appariée = **Traded** de Quiver (Filed ≈ 1 %). **Numérique seul = 35–74 %/an** ;
l'OCR fait monter à 81–91 %.

**Vrais-absents House** : 248 brut → **9 réels** — 2021 Malinowski ×1 (date ±1 j) ; 2023 Schrader ×3
(papier, cluster C) ; 2024 « Calhoun » ×2 (étiquetage Quiver J. James) ; 2025 Gottheimer ×1
(post-snapshot) ; 2026 Pelosi ×2 (dépôt post-snapshot). Aucun bug d'extraction. Le reste des 248 =
artefacts ticker Quiver, amendements, dates ±1 j, obligations/options.

**`date_confidence` House (OCR) / an** (n OCR · plausible % · implausible) :
2020 8 791·98,6·120 | 2021 6 816·**79,6·1 389** | 2022 10 900·96,4·394 | 2023 6 329·99,2·50 |
2024 6 277·96,5·220 | 2025 6 067·98,1·118 | 2026 3 790·100,0·0 | **Total 48 970·95,3·2 291**.
Pic 2021 = Diana Harshbarger (1 389 sur 2 documents) — manuscrit dense, localisé, non systémique.

**Clusters OCR House** (docs census · docs avec txns · txns · ticker % · plausible %) :
A tapé droit 74·59·5 957·84,2·99,6 | B tapé tourné 322·295·**42 151**·82,8·94,7 | C manuscrit 151·81·862·88,4·97,4.
B = 86 % du volume OCR. **Concentration** : Khanna **63,0 %**, McCaul 22,2 %, Harshbarger 7,2 %
(top 3 = 92,4 % ; top 10 = 99,0 %).

**Crosscheck House** (statut · déposants · txns · dont OCR) :
`quiver_validable` 212·78 530·47 004 | `ocr_unique` 13·1 957·1 949 | `digital` 31·1 155·13.
`ocr_unique` (Quiver = 0, notre OCR seule source) : ex. David P. Roe 1 686, Francis Rooney 189.

**Sénat — fusion / an** (Digital · OCR · FINAL · sénateurs) — *vérifié sur les tables
`data/senate/{an}/06_senate_{an}_FINAL.csv`* : 2020 1 706·255·1 961·33 | 2021 1 098·281·1 379·35 |
2022 919·182·1 101·27 | 2023 1 062·97·1 159·30 | 2024 946·84·1 030·24 | 2025 943·478·1 421·31 |
2026 487·303·790·22 | **Total 7 161·1 680·8 841·64**.
OCR papier : Blumenthal ~1 233 (≈73 %), Boozman ~379, Burr ~52, Feinstein ~47, Fetterman ~2.
Blumenthal = munis/Treasuries (ticker bas) **et 0 ligne Quiver** → papier validé hors Quiver.

**Sénat — Quiver** : dédup amendements 554 ; couverture 98–100 %/an ; `only_quiver` 25
(tickers composites / transitions de chambre) ; accord sens ~95,7 %, date Traded ~99,4 %, montant ~93,2 % ;
**0 vrai raté**. **Tickers Sénat** : digital 79,1 % → FINAL 71,4 % (dict +197, LLM +190, asset_name 65,
none 2 531 ≈ non cotés). `date_confidence` OCR : plausible 1 654 (98,5 %), implausible 18 (lot Perdue
2021 = divulgations tardives **réelles**).

**Mécanismes (rappels factuels)**
- **Manifeste** : `pdfplumber.extract_text()` → `bool(text.strip())` ; buckets lisible / non_lisible / absent.
- **Clé naturelle** : SHA-256 de `chambre|declarant_name|transaction_date|asset_description|operation_type|
  amount_range|owner` (7 champs, **sans ticker**). `occurrence_index = cumcount(doc_id, nk)` ; dédup `(nk, occ)`.
- **Deskew** : `ROT_CANDIDATES = [0, 90, 180, 270]`, pré-passe Vision basse résolution qui **reconnaît**
  la page droite (plus robuste que demander l'angle), redressement PIL. 59,7 % → 69,0 %.
- **Vision** : `claude-sonnet-4-6`, `tool_choice` forcé `record_transactions`, `max_tokens` 16 000,
  7 retries, cache `PROMPT_SHA`, reprise au batch. Prompt : ignorer la ligne-exemple « Mega Corp »,
  garde-fou année = `filing_year` ou `prev_year`.
- **Montants** : `HOUSE_OCR_AMOUNT_MAP` A–K (ex. B → « $15,001 – $50,000 », milieu 32 500). Milieux
  House `.0`, Sénat `.5` (copies exactes différentes, voulu).
- **CSRF Sénat** : `accept_agreement` (GET → `csrftoken`, POST `prohibition_agreement` +
  `csrfmiddlewaretoken` + en-tête `X-CSRFToken`). Images papier `.gif` via `efd-media-public.senate.gov`.
  Correctif cache : nom = `sha1(url)[:16]` (évite les collisions de basename `.gif`).
- **GICS → ETF SPDR** : Energy XLE · Materials XLB · Industrials XLI · Cons. Disc. XLY · Cons. Staples XLP ·
  Health Care XLV · Financials XLF · IT XLK · Comm. Services XLC · Utilities XLU · Real Estate XLRE.
- **Golden / repro** : House 108 fichiers, Sénat 68 ; `check_golden` (0 écart), `test_senate_repro`
  (8 841/8 841 nkh, 67/67 identité, 65/65 ticker). Pipeline non re-jouable hors-ligne → preuve par
  reproduction depuis colonnes figées.

## Format de sortie
- **Un fichier `docs/RAPPORT_COMPLET.tex`**, compilable, **français** (`babel french`), réutilisant le
  préambule de `docs/RAPPORT_HOUSE.tex` (`booktabs`, `longtable`, `array`, `enumitem`, `xcolor`,
  `tcolorbox`, `hyperref`, `titlesec`) **+ `tikz`** pour les schémas.
- **Schémas en TikZ** : au minimum le flux du pipeline (section 0) ; idéalement aussi un schéma
  partagé ↔ House/Sénat.
- `\tableofcontents`, encadré `tcolorbox` « Chiffres clés » en tête, tableaux `booktabs`.
- À la fin, **compile** : `latexmk -pdf docs/RAPPORT_COMPLET.tex` (ou `pdflatex` ×2). Corrige les erreurs
  jusqu'à obtenir `docs/RAPPORT_COMPLET.pdf`.
- Longueur attendue : **exhaustif** (toutes les étapes, tous les chiffres, toutes les justifications) —
  la clarté prime, mais on ne sacrifie aucun contenu demandé.
