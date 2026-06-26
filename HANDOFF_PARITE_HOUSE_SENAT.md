# Handoff — Parité House ↔ Sénat (session 2026-06-26)

> **But de ce fichier.** Passerelle entre cette session (parité Sénat + A2-House) et la conversation
> parallèle sur la **restructuration House**. À lire dans l'autre chat (`« lis HANDOFF_PARITE_HOUSE_SENAT.md »`)
> pour coordonner : appliquer au **Sénat** la même restructuration que House, et figer ce qui reste côté House.
> Même projet `Jupiter` → la mémoire (`MEMORY.md`) et les synthèses MD sont déjà partagées entre les deux chats.

---

## 1. TL;DR — ce que cette session a abouti

Point de départ : audit comparatif **« quels raffinements House n'ont PAS été portés au Sénat ? »**. 7 écarts
trouvés (vérifiés dans le code). **Phase A (Sénat) faite et vérifiée** ; **A2-House préparé et gelé**.

| Axe | Avant | Après | Où |
|---|---|---|---|
| Ticker Sénat (dict + LLM `is_equity`) | 67,0 % | **71,4 %** | `1 SENAT/toutes_annees/ticker_resolve.py` + `merge_ocr.py` |
| Secteur Sénat (`sector_gics`/`etf_proxy`) | absent | **62,1 %** → table **12/12 champs** | `merge_ocr.py` appelle `sector_enrich` |
| `date_confidence` Sénat | absent | **ajouté** (fenêtre 75 j) | `merge_ocr.py` |
| Dédup amendements Quiver Sénat | absente | **554 retirés**, couverture inchangée 98-100 % | `validate_quiver_sample.py` + `revalidate_quiver.py` |
| A2-House (secteur + dédup) | — | **script écrit + validé, run complet GELÉ** | `0 HOUSE/toutes_annees/finalize_house_sector.py` |

**8 841 lignes Sénat préservées, identité 100 %.** Aucun commit (en attente du feu vert utilisateur).

---

## 2. Découvertes importantes (à connaître pour la restructuration House)

1. **L'OCR House EST scalé** (commit `da65aa6`, run complet **49 309 txns**, 443 docs) — PAS un échantillon.
   Les `0 HOUSE/toutes_annees/data_v1/tables/{an}/06_house_{an}_FINAL.csv` (**81 985 lignes**) ont déjà
   `date_confidence` + `ticker_source`. ⚠️ **Les docs House (`SYNTHESE_PRESENTATION.md`) disent encore
   « OCR échantillon 3 876 » → PÉRIMÉES, à réconcilier** (probablement dans le chat restructuration House).
2. **Bug de dédup House** : ~**2 855 lignes OCR exactement dupliquées** dans les FINAL — la fusion House
   (`house_ocr_multiyear.py` ~ligne 534) ne déduplique que OCR-vs-digital sur `natural_key_hash`, **pas**
   sur `(natural_key_hash, occurrence_index)`. Le Sénat (`merge_ocr.py`) le fait. **Fix racine = 1 ligne**
   à ajouter dans la fusion FINAL House.
3. **Khanna = légitime** : 30 866 txns OCR sur 73 PTR réels (1 046 tickers, 1 441 dates distinctes) — gros
   trust actif, pas une sur-extraction.
4. **Plafond ticker structurel** : le « 90 % House » N'EST PAS atteignable au Sénat (≈60 % du sans-ticker =
   munis/Treasuries/LLC privées ; Blumenthal = 1 233 lignes OCR de munis). 71,4 % est un bon résultat, pas
   un défaut. Le filtre `is_equity` refuse (à juste titre) de tickeriser un bond.
5. **`date_confidence=implausible`** ≠ erreur OCR : surtout des **divulgations tardives/amendées réelles**
   (lot Perdue 2021, délai médian 382 j). Utile au backtest (signal connu trop tard).

---

## 3. Code & patterns réutilisables (cross-chambre)

Le pipeline Sénat toutes_annees a été aligné sur House au **stade FINAL** (post-traitement additif, sans
ré-extraction). Patterns directement transposables d'une chambre à l'autre :

| Pattern | Fichier Sénat (réf) | Équivalent / statut House |
|---|---|---|
| Résolution ticker dict + LLM `is_equity` | `1 SENAT/toutes_annees/ticker_resolve.py` | porté de `0 HOUSE/toutes_annees/house_ocr_multiyear.py:149-193` |
| Secteur GICS→ETF (yfinance + repli LLM, cache) | `0 HOUSE/2025_test/sector_enrich.py` (`enrich_sectors`) | **partagé** (même module, importé des deux côtés) |
| Enrichissement au stade FINAL en une passe | `1 SENAT/toutes_annees/merge_ocr.py` | `0 HOUSE/toutes_annees/finalize_house_sector.py` (calque) |
| Dédup `(nk, occ)` non destructrice | `merge_ocr.py` / `senate_finalize.py:195` | **à brancher** dans la fusion FINAL House |
| Re-validation Quiver offline (dédup amendements) | `1 SENAT/toutes_annees/revalidate_quiver.py` | — |
| Flag `date_confidence` (fenêtre 75 j) | `merge_ocr.py` | déjà présent House (`house_ocr_multiyear.py:360`) |

**Schéma FINAL cible (12 champs garantis), ordre commun** : `…, asset_type, sector_gics, etf_proxy,
operation_type, …, ticker_source, sector_source, occurrence_index`. Le Sénat l'expose déjà ; House l'aura
après le run A2 gelé.

---

## 4. En attente / GELÉ (ne pas relancer sans coordination)

- **A2-House run complet** (`finalize_house_sector.py --years 2020,…,2026`, sans `--no-llm`) : ~50 min,
  2 468 tickers. **GELÉ** jusqu'à « House figé » (l'utilisateur édite House en parallèle ; relancer
  `house_ocr_multiyear` régénère les FINAL et écraserait l'enrichissement → il doit être le **dernier**
  passage). Validé sur 2024 : dédup −312, secteur 78 % (yfinance seul, plancher), non-régression OK.
- **Fix racine dédup House** : `drop_duplicates(["natural_key_hash","occurrence_index"])` dans la fusion
  FINAL de `house_ocr_multiyear.py` (~l.534) — à intégrer côté restructuration House pour rendre la dédup
  permanente.
- **Réconcilier docs House** (`SYNTHESE_PRESENTATION.md` : 3 876 → 49 309) — après le run final.

---

## 5. Comment coordonner les deux conversations

1. **Mémoire & MD déjà partagés** (même projet) : `MEMORY.md` (index), `ETAT_AVANCEMENT_PROJET.md` (statut
   maître, à jour), `1 SENAT/toutes_annees/SYNTHESE_RESULTATS.md` (Sénat à jour). Mémoire pertinente :
   `project_senate_multiyear_phase0` (mise à jour avec la parité).
2. **Dans le chat restructuration House**, dire : *« lis `HANDOFF_PARITE_HOUSE_SENAT.md` + `ETAT_AVANCEMENT_PROJET.md` »*.
3. **Pour adapter la restructuration House au Sénat** : la structure Sénat vit dans `1 SENAT/toutes_annees/`
   (`senat_multiyear.py` digital, `senat_ocr_multiyear.py` OCR, `merge_ocr.py` fusion+enrichissement,
   `ticker_resolve.py`, `revalidate_quiver.py`, `SYNTHESE_RESULTATS.md`) + le code figé Q1 réutilisé dans
   `1 SENAT/senat_2025_test/` (`senate_finalize.py`, `validate_quiver_sample.py`, `sector_enrich.py`).
   Appliquer la même convention de dossiers/nommage que celle décidée pour House.
4. **Garde-fou git** : ne pas faire `git checkout`/branch pendant que l'autre chat édite — ça déplace le
   HEAD du dépôt entier. Préférer un **worktree** isolé si une branche est nécessaire.

---

*Rédigé en fin de session parité Sénat. Fichiers créés cette session : `ticker_resolve.py`,
`revalidate_quiver.py`, `finalize_house_sector.py` (+ ce handoff). Modifiés : `merge_ocr.py`,
`validate_quiver_sample.py`, `SYNTHESE_RESULTATS.md`, `ETAT_AVANCEMENT_PROJET.md`. Rien n'est commité.*
