# Congress Trading Signal — Plan d'attaque (semaine 1)
### Architecture du notebook, cellule par cellule — pour produire la table de transactions House + Sénat

**Date :** 23 juin 2026
**Base :** document d'analyse `analyse_existant_congress_trading_signal.md` (validé).
**Livrable visé :** une table transactionnelle unifiée **House + Sénat**, ère électronique, niveau Member, propre, dédupliquée, avec identité (BioGuideID) et commissions, récupérée depuis des sources **transparentes** (code dans le notebook, pas d'API boîte noire), **Quiver en vérification seulement**.

---

## Décisions retenues (les 6 questions tranchées)

1. **Ordre & Sénat** : **House d'abord**, auto-récupérée intégralement (socle canonique solide), puis **Sénat en hybride** — socle de données ouvertes transparentes (Stock Watcher + kadoa) **+** lecteur léger et poli des dépôts électroniques eFD, **sans évasion anti-bot**.
2. **§105(c)** : on avance techniquement ; le point est posé comme **checkpoint explicite** (notebook 00) à lever avec le directeur/le légal avant toute mise en production.
3. **Période** : House **2013-2026** ; Sénat **2012-2026** (ère électronique).
4. **LLM** : **fallback ciblé uniquement** (résolution de ticker en texte libre, OCR éventuel). Pas d'extraction massive.
5. **Complétude** : définition assumée = « **ère électronique, niveau Member, avec backlog scanné/papier documenté** ».
6. **Stockage** : **CSV** partout (inspectable, cohérent avec l'existant) **+ parquet** pour la table canonique finale.

---

## Principes de conception (non négociables)

- **Cellules petites, mono-tâche**, chacune précédée d'un titre Markdown. Aucune cellule « fourre-tout ».
- **Transparence = le code vit dans le notebook**, lisible et inspectable. Aucune dépendance à une API boîte noire comme source. La donnée ouverte (Stock Watcher/kadoa) compte comme transparente (JSON inspectable, parsing ouvert).
- **Cellule PROVENANCE & RÉUTILISATION en tête de chaque notebook** : sources de données et bouts de code réutilisés, avec URL et licence.
- **Reproductible & idempotent** : checkpoints, manifests, et **dédup déterministe par SHA-256 de la clé naturelle**. Deux exécutions → même résultat.
- **Aucun secret en dur** : token Quiver lu depuis l'environnement.
- **Pas d'évasion** : aucune contourne de protection anti-bot, aucun CAPTCHA, pas de proxy d'évasion. Si une source officielle bloque l'accès programmatique → repli sur la donnée ouverte.
- **Séparation stricte** : sources officielles/ouvertes = canonique ; **Quiver = vérification, jamais réinjecté** dans la table finale.
- **Honnêteté de complétude** : tout document non exploitable va dans un **backlog explicite**, jamais silencieusement ignoré.

---

## Réutilisation & attribution (transparent)

| Élément réutilisé | Source | Licence | Comment on l'utilise |
|---|---|---|---|
| Logique de parsing PDF House (regex ancrée sur marqueurs, nettoyage octets nuls, dédup SHA-256) | seralifatih/congress-trading-pipeline | MIT | **Porté de TypeScript en Python**, directement dans nos cellules (inspectable) |
| Code d'index House + client Quiver | notre projet existant (`house_index.py`, `quiver_client.py`) | interne | Repris et adapté |
| Socle Sénat (transactions ère électronique) | Senate Stock Watcher + kadoa (JSON) | open data / MIT | **Ingéré** comme données transparentes |
| Identité + commissions | unitedstates/congress-legislators | domaine public | Table de référence (clé BioGuideID) |
| Vérification externe | Quiver (compte dispo) | abonnement | **Notebook de validation uniquement** |

---

## Schéma cible de la table canonique

`source` (house/senate) · `provenance` (official/openset/efd) · `bioguide_id` · `declarant_name` · `chamber` · `party` · `state_district` · `committee_membership` · `committees_key_flag` (Finance/Defense/Intelligence) · `transaction_date` · `disclosure_date` · `ticker` · `asset_description` · `asset_type` · `operation_type` (P/S/S-partial/E) · `amount_range` · `amount_midpoint` · `owner` · `doc_id` · `source_url` · `natural_key_hash`

> **Règle de date (anti look-ahead)** : `disclosure_date` = date de dépôt public (House : `FilingDate` du XML ; Sénat : date de réception). `transaction_date` = date réelle du trade. Toute stratégie future utilisera `disclosure_date`.
> **Champs garantis sans manquant** dans la table finale : `declarant_name`, `chamber`, `party`, `committee_membership`, `transaction_date`, `disclosure_date`, `ticker`, `operation_type`, `amount_midpoint`, `asset_type`.

---

## Arborescence des données

```
data/
├── reference/        legislators.csv (identité + commissions)
├── raw/house/index/  <YEAR>FD.zip + <YEAR>FD.xml
├── raw/house/ptr_pdfs/<YEAR>/<DocID>.pdf
├── processed/house/  house_ptr_index.csv, house_transactions.csv
├── external/senate_openset/   stockwatcher + kadoa (brut, transparent)
├── external/quiver/  (vérification uniquement)
├── processed/senate/ senate_transactions.csv
├── processed/        congress_transactions.csv + .parquet  ← CANONIQUE
└── audit/            manifests, qualité, validation
reports/              rapports Markdown
```

---

## Architecture des notebooks (10 notebooks, 6 blocs)

### Bloc 0 — Fondations
**`00_setup_scope.ipynb`** — *prépare et verrouille le cadre.*
- C1 — imports + versions des libs (pandas, requests, pdfplumber/pypdf, tqdm).
- C2 — config (dataclass : `HOUSE_YEARS=2013..2026`, `SENATE_YEARS=2012..2026`, chemins, rate-limits, fenêtres de dates).
- C3 — création de l'arborescence `data/...` + `reports/`.
- C4 — **cellule PROVENANCE & RÉUTILISATION** (le tableau ci-dessus).
- C5 — **cellule CHECKPOINT LÉGAL §105(c)** : note explicite (usage commercial restreint, 2 chambres) à lever avec le directeur ; ne bloque pas la suite.
- C6 — vérif présence token Quiver (sans l'afficher).
- C7 — rappel du scope + **plafond de complétude assumé**.

### Bloc 1 — Référentiel identité & commissions (en amont)
**`01_reference_legislators.ipynb`** — *table de référence des déclarants (règle le problème des noms avant qu'il arrive).*
- C1 — download `legislators-current.json` + `legislators-historical.json`.
- C2 — parse → table (BioGuideID, nom canonique, **alias/variantes**, parti, chambre, état/district).
- C3 — download `committee-membership-current.json` → appartenance aux commissions.
- C4 — flag `committees_key_flag` (Finance / Armed Services / Intelligence).
- C5 — sauvegarde `data/reference/legislators.csv`.
- C6 — mini-rapport de couverture (nb de membres, % avec BioGuideID, % avec commission).

### Bloc 2 — House (auto-récupération canonique, déterministe)
**`02_house_index.ipynb`** — *index officiel → checklist PTR.* (Reprend `house_index.py`.)
- C1 — fonctions URL (ZIP, PDF) + download ZIP par année 2013-2026.
- C2 — extraction + parsing XML → table des filings (Member par Member).
- C3 — **contrôle FilingType** : distribution des codes + vérifier qu'aucun PTR amendé ne se cache hors `P` (échantillon).
- C4 — filtre `FilingType='P'` → checklist `DocID → URL` ; sauvegarde `house_ptr_index.csv`.
- C5 — audit : PTR/an, `DocID` manquants, doublons `year+doc_id` → `reports/house_index_audit.md`.

**`03_house_download.ipynb`** — *tous les PDF PTR, relançable.*
- C1 — charge la checklist.
- C2 — boucle de download (rate-limit ~600 ms), checkpoint (skip si déjà présent).
- C3 — manifest de complétude (attendu / obtenu / manquant / invalide).
- C4 — audit qualité texte : `ok_text` vs `no_text` → les `no_text` vont au **backlog OCR**.
- C5 — `reports/house_download_audit.md`.

**`04_house_parse.ipynb`** — *PDF → lignes de transaction (logique seralifatih portée).*
- C1 — fonction de nettoyage (suppression des octets nuls / normalisation glyphes).
- C2 — **regex ancrée sur marqueurs `(TICKER) [TYPE]`** (portée en Python, attribuée en commentaire).
- C3 — parser : pour chaque marqueur, remonter pour l'actif, descendre pour dates + fourchette ; gérer types **P / S / S(partial) / E**.
- C4 — application sur tous les PDF `ok_text` → lignes brutes House.
- C5 — lignes non-parsées → backlog ; sauvegarde `house_transactions.csv` + taux de parsing.

### Bloc 3 — Sénat (socle ouvert transparent + lecteur eFD léger, sans évasion)
**`05_senate_openset.ipynb`** — *socle historique depuis données ouvertes.*
- C1 — fetch Senate Stock Watcher (`all_transactions.json`) + slice Sénat du dataset kadoa.
- C2 — normalisation → lignes de transaction.
- C3 — flag des PTR scannés / `transactions: []` → **backlog**.
- C4 — sauvegarde `senate_transactions.csv` (socle) + couverture par an.

**`06_senate_efd_recent.ipynb`** — *queue récente / provenance, accès direct léger.*
- C1 — **note d'accès** : l'agrément eFD est accepté manuellement (humain) ; lecture à faible volume, rate-limitée ; **pas de proxy d'évasion, pas de CAPTCHA**. Si blocage → on s'arrête et on garde le socle.
- C2 — lecteur des **dépôts électroniques** récents (HTML propre) → lignes.
- C3 — recoupement avec le socle (comble la queue récente, confirme la provenance sur un échantillon).
- C4 — mise à jour `senate_transactions.csv` + note de complétude récente.

### Bloc 4 — Unification & nettoyage
**`07_unify_clean.ipynb`** — *la table canonique.*
- C1 — concat House + Sénat.
- C2 — mapping vers le **schéma cible** unifié.
- C3 — jointure `legislators.csv` sur BioGuideID + **résolution d'alias** (noms variants).
- C4 — normalisation tickers (upper, options/obligations, `--`→null) + dates ISO + `amount_midpoint`.
- C5 — **dédup déterministe** : `natural_key_hash` = SHA-256(chamber+nom+date+actif+type+montant).
- C6 — **cellule(s) de documentation** : chaque règle de nettoyage explicitée (entrée/sortie/justification).
- C7 — sauvegarde `congress_transactions.csv` **+ `.parquet`**.

### Bloc 5 — Validation & qualité
**`08_validation_quiver.ipynb`** — *Quiver = couche de vérification (jamais réinjecté).*
- C1 — pull Quiver bulk V2 (via `quiver_client.py`).
- C2 — normalisation des champs Quiver.
- C3 — triangulation par **année / déclarant / ticker** vs notre table (+ croisement kadoa).
- C4 — contrôles transaction-level ponctuels (échantillon).
- C5 — `reports/validation_report.md` (un écart Quiver ≠ une erreur de notre côté).

**`09_data_quality_report.ipynb`** — *synthèse finale.*
- C1 — couverture par chambre / an.
- C2 — **contrôle zéro-manquant** sur les champs garantis.
- C3 — frontière de complétude (électronique vs scanné) + taille du **backlog OCR**.
- C4 — distributions (montants, % achats vs ventes, transactions sans sortie déclarée).
- C5 — `reports/data_quality.md` (le document de référence pour interpréter le futur backtest).

---

## Critères de succès (fin de semaine 1)

Pouvoir affirmer, preuves à l'appui :
> « J'ai une table transactionnelle **House + Sénat**, ère électronique, niveau Member, **propre, dédupliquée et structurée**, avec identité BioGuideID et commissions, **récupérée depuis des sources transparentes dont le code vit dans le notebook**. Je connais exactement la couverture par chambre/an, les champs garantis sans manquant, le backlog scanné/papier, et l'écart avec Quiver (vérification). »

---

## Volontairement hors-scope cette semaine (pour mémoire)

- **OCR du backlog** scanné/papier (surtout Sénat < 2015) — traitement ultérieur ciblé.
- **Mapping GICS → ETF sectoriels** — semaine 2.
- **Stratégie, sélection annuelle, backtest** — semaines 3-4 (et à dimensionner en gardant en tête que l'alpha post-2012 est contesté et concentré).
