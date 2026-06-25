# Prompt — Générer la synthèse LaTeX unique de `0 HOUSE/2025_test`

> **But** : produire un **unique** document LaTeX (`SYNTHESE_PRESENTATION.tex`), compilable avec
> `tectonic`, qui consolide l'ancien README + RAPPORT + SYNTHESE en **un seul livrable complet,
> détaillé, exact et structuré**. Ce prompt est auto-suffisant : tous les chiffres ci-dessous ont
> été **recalculés depuis les données réelles** (`data_v1/`), pas depuis la prose. Ne réintroduis
> aucune valeur extérieure.

## Rôle & règles de rédaction (impératives)

- Tu écris en **français**, registre technique sobre. **Zéro blabla** : aucune phrase de remplissage,
  aucune redite, aucun superlatif gratuit.
- **Chaque affirmation chiffrée est adossée à un nombre exact** issu de la section « Faits ».
- **Privilégie les tableaux** (`booktabs`) aux paragraphes dès qu'il y a ≥ 3 valeurs.
- **Honnêteté** : la section Limites doit être précise et non minimisée.
- Sortie = **un seul fichier `.tex` compilable tel quel** avec `tectonic` (aucune dépendance externe,
  aucune image ; le seul schéma est en TikZ).

## Contraintes LaTeX (réutiliser à l'identique)

Réutilise **ce préambule exact** (portable pdflatex/xelatex/tectonic) et ces macros :

```latex
\documentclass[11pt,a4paper]{article}
\usepackage{iftex}
\ifPDFTeX \usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}\else\usepackage{fontspec}\fi
\usepackage[french]{babel}
\usepackage[margin=2cm]{geometry}
\usepackage{booktabs}\usepackage{array}\usepackage{longtable}\usepackage{xcolor}
\usepackage{tikz}\usetikzlibrary{positioning,calc,arrows.meta}\usepackage{hyperref}
\definecolor{accent}{HTML}{1F4E79}\definecolor{accentlight}{HTML}{EAF1F8}
\definecolor{okgreen}{HTML}{2E7D32}\definecolor{warn}{HTML}{B25E00}
\hypersetup{colorlinks=true, linkcolor=accent, urlcolor=accent}
\newcommand{\file}[1]{\texttt{\small #1}}
\newcommand{\nb}[1]{\textbf{#1}}
\newcommand{\boite}[1]{\begin{center}\fcolorbox{accent}{accentlight}{%
  \parbox{0.94\textwidth}{\vspace{2pt}#1\vspace{2pt}}}\end{center}}
```

- Après `\begin{document}`, garder la tolérance d'espacement (noms de fichiers longs) :
  `\tolerance=4000 \hbadness=4000 \setlength{\emergencystretch}{6em}`.
- Titre : « Pipeline House — Transactions boursières des représentants / Pilote « Test » T1 2025 ».
- Inclure `\tableofcontents`.
- Échapper `_`, `&`, `%`, `$` dans le texte ; `\texttt{}` pour les noms de fichiers/colonnes.
- Conserver le **schéma TikZ du flux** (source ZIP+117 PDF → 100 lisibles/17 scannés → parsing/OCR →
  1 105 / 1 167 → FUSION 2 272 → validation Quiver ; enrichissement par le référentiel élus en pointillé).

## Faits — VÉRITÉ TERRAIN (exacts, à utiliser tels quels)

**Volumétrie.** 117 PTR (T1 2025) ; **100 lisibles / 17 scannés** ; **66** élus uniques.
Table FINALE = **2 272** transactions = **1 105** électroniques + **1 167** OCR.
Période (date de transaction) : **25/11/2024 → 25/03/2025**. **0** échec parsing, **0** échec OCR.

**Complétude.**
- ticker **90,4 %** (2 053/2 272) — électronique 90,3 % (998/1 105), OCR 90,4 % (1 055/1 167).
- `ticker_source` (OCR 1 167) : `explicit` 23 · `elec_dict` 517 · `llm` **515** · `none` 112.
- asset_type **97,2 %** (2 208/2 272) — **hétérogène** (voir Limites).
- montant : **99,96 %** (1 seule ligne manquante) ; **volume total ≈ 107 016 376 $** (Σ mi-fourchette).

**operation_type (FINALE).** Purchase 1 206 (53,1 %) · Sale 791 (34,8 %) · Sale (Partial) 209 (9,2 %) ·
Partial Sale 61 (2,7 %) · Exchange 5 (0,2 %) · Total 2 272.

**Top 10 déposants (par nb de transactions).** Rohit Khanna 1 036 · Rob Bresnahan 235 ·
Josh Gottheimer 186 · Julie Johnson 99 · Gilbert Cisneros 82 · Michael T. McCaul 82 ·
Jefferson Shreve 67 · Marjorie Taylor Greene 65 · Tim Moore 46 · April McClain Delaney 37.
*Khanna ≈ 45,6 % du total (1 036/2 272), entièrement via OCR — cas réel (confirmé Quiver + visuel), pas une anomalie.*

**Validation QuiverQuant (arbitre indépendant ; jamais utilisé pour extraire).**
- Côté électronique (56 déposants comparés) : nous **1 105** vs Quiver **980** ; **26** match exact,
  **30** nous > Quiver, **0** Quiver > nous. Exemples : Bresnahan 235/234, Gottheimer 186/182,
  MTG 65/59, Tim Moore 46/31, Julie Johnson 99/99.
- Côté OCR (10 déposants) : **OCR ≥ Quiver partout** — 4 « OCR ≥ Quiver » (Khanna 1 036/756,
  McCaul 82/56, Fleischmann 21/13, Wied 11/4) + 6 « Quiver sans donnée » (Self, Gonzalez, Sherman,
  Bilirakis, A. Smith, Wagner). **Aucun cas où Quiver a plus que nous.**
- Audit ticker LLM (`06e_ticker_llm_audit.csv`) : **466/500 = 93 %** de concordance ; les 34 écarts
  sont en majorité des **artefacts Quiver** (parts préférentielles `-PA/-PG`, société voisine :
  AIG/AFG, VRTX/VERX) où notre ticker d'action ordinaire est le bon.

**Pipeline.**
- *Amont* : référentiel élus `01_ref_universe.csv` (12 767) + `02_ref_house_key.csv` (126 ; comités
  Financial/Armed/Intelligence) ; index PTR `03_ptr_index.csv` (117) ; téléchargement + test `has_text`
  `04_download_manifest.csv` (117 → 100 lisibles / 17 scannés).
- *Étape 1 — électronique* (`notebook_v1_house_2025q1.ipynb`) : `pdfplumber` + regex (type, dates,
  ticker, montant, propriétaire), gestion des lignes de continuation, jointure identité (bioguide) →
  `06_house_2025q1_transactions.csv` (**1 105**), `05_parse_failures.csv` vide.
- *Étape 2 — OCR* (`notebook_v1_house_2025q1_ocr.ipynb`) : 17 PDF scannés → images (DPI 200) →
  **Claude Vision `claude-sonnet-4-6`**, **sortie structurée forcée** (`tool_use record_transactions`),
  **cache versionné** par `doc_id` + `prompt_sha` (re-run sans changement = 0 appel API),
  **filtre déterministe** de la ligne-exemple « Example Mega Corp », **enrichissement ticker en 3
  passes tracées** (`explicit` → `elec_dict` [dico bâti sur l'électronique] → **`llm`** [Claude
  nom→ticker, cache `ticker_llm_cache.json`, prompt_sha 8915bf5559f7bc38 ; 228/310 noms résolus]),
  `asset_type` par règles, **déduplication inter-source uniquement** → `06b_…ocr_transactions.csv`
  (**1 167**), `06c_ocr_failures.csv` vide.
- *Fusion* → `06_house_2025q1_transactions_FINAL.csv` (**2 272**) ; packaging `house_2025q1_FINAL.xlsx`.

**Schéma (22 colonnes).** Identité (7) : `bioguide_id, declarant_name, chamber, party, state_district,
committee_membership, committees_key_flag`. Dates (2) : `transaction_date, disclosure_date`.
Actif (3) : `ticker, asset_description, asset_type`. Opération & montant (4) : `operation_type,
amount_range, amount_midpoint, amount_split_flag`. Traçabilité (6) : `owner, doc_id, source_url,
natural_key_hash, provenance` (`house-pdf-electronic`|`house-pdf-ocr`), `ticker_source`
(`explicit`|`elec_dict`|`llm`|`none` ; vide pour l'électronique).

**Reproductibilité (dossier autonome).** `.venv` local + kernel **`jupiter-house-2025test`** +
`requirements.txt` (pins : anthropic 0.112.0, pandas 3.0.3, pdfplumber 0.11.10, pymupdf 1.27.2.3,
python-dotenv 1.2.2, openpyxl 3.1.5, requests 2.34.2, + ipykernel/nbconvert) ; clés dans `.env` local
(`ANTHROPIC_API_KEY` + `QUIVER_API_KEY` ; gabarit `.env.example`) ; Quiver embarqué
`data_v1/external/quiver_congress_trading_2025.csv` ; chemins ancrés par `BASE_DIR` (indépendant du
répertoire de lancement). Lancer Étape 1 puis Étape 2.

## Corrections d'exactitude (impératif — remplacent toute version antérieure)

1. **Gonzalez** : il a déposé **2 PTR scannés**. Doc `8220796` → **3 transactions captées** (HSBC ;
   TESLA achat 01/03 ; TESLA achat 12/03). Doc `8220809` → **formulaire pâle** : le modèle n'a lu que
   la **ligne-exemple** (filtrée) → **0 ligne** extraite ; sa transaction réelle (vente TESLA ~17/03)
   est **manquée**. Quiver = 0 sur Gonzalez → pas de référence externe. Énoncer ainsi, sans
   généraliser « tout Gonzalez manqué ».
2. **asset_type** : 97,2 % rempli **mais non harmonisé**. Côté électronique, ~**39 lignes** portent les
   **codes bruts du formulaire** : `CT` = crypto (Ethereum, mèmecoins), `CS` = notes corporate / MBS
   (MTN, agency pools), `HN`/`PS`/`OL`. À présenter comme limite « champ non normalisé entre sources »,
   pas comme 97 % homogènes.
3. **47 doublons exacts Khanna** : **conservés** (pas de déduplication sur le hash). Ses déclarations
   couvrent plusieurs **trusts familiaux** (Ahuja/Khanna) passant le même ordre le même jour, tous codés
   sous le même `owner` → même `natural_key_hash` apparaissant N fois (réel, confirmé page à page :
   SALESFORCE 27/02 DC ×4). Une minorité d'artefacts OCR subsistent, non séparables auto (≈ 0,1–0,5 %,
   confinés à Khanna). Dédupliquer serait destructeur.
4. **Bilirakis** : **seul** flag QA (doc 8220747, « GE Vernova », montant + date illisibles).

## Structure imposée (9 sections, dans cet ordre)

1. **Objectif & résultat à utiliser** — 2-3 phrases d'objectif + `\boite` pointant `06_…_FINAL.csv`
   (2 272 = 1 105 élec + 1 167 OCR) et `house_2025q1_FINAL.xlsx`.
2. **Vue d'ensemble** — schéma TikZ du flux + tableau « chiffres clés » + encadré vocabulaire
   (PTR = Periodic Transaction Report ; T1 2025 = divulgué au 1ᵉʳ trimestre ; OCR = lecture vision).
3. **Sources** — tableau 4 lignes (House Clerk ZIP, House Clerk PDF, unitedstates.github.io, Quiver =
   validation seule), avec rôle et accès.
4. **Pipeline détaillé** — amont + Étape 1 + Étape 2 (insister sortie structurée / cache / filtre
   ligne-exemple / 3 passes ticker dont LLM / dédup inter-source) + fusion.
5. **Statistiques de sortie** — complétude (ticker/asset_type/montant/volume) + operation_type + top 10.
6. **Validation contre QuiverQuant** — élec (56) + OCR (10) + encadré « nous ≥ Quiver partout » +
   audit ticker LLM 93 %.
7. **Limites connues (honnêteté)** — Gonzalez (corrigé) · Bilirakis · asset_type non harmonisé ·
   ticker résiduel ~10 % (actifs non cotés : structurés, perpétuelles, options) · 47 doublons Khanna.
8. **Schéma des colonnes** — 22 colonnes groupées + dictionnaire `provenance` / `ticker_source`.
9. **Reproductibilité & fichiers** — env autonome + ordre des 2 notebooks + carte `data_v1/`
   (tables 01→07, FINAL, 06b/c/d/e, xlsx ; `pdfs/` ; `ocr_cache/` ; `external/` ;
   `ticker_llm_cache.json`) + marqueurs « 0 échec » (fichiers vides = succès attendu).

Terminer par un `\boite` « message en une ligne » : pipeline complet T1 2025 (117 PTR → 2 272
transactions), double extraction (texte + OCR vision) + passe LLM ticker (→ 90 %), **0 échec**,
validé contre une source indépendante (nous ≥ Quiver partout).
