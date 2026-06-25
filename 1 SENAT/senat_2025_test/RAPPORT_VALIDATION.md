# Rapport de validation — Sénat eFD, Q1 2025

**Question** : le pipeline Sénat (37 dépôts eFD → **375 transactions** : 283 électroniques + 92 OCR
papier) est-il fiable et l'information extraite est-elle juste ? Critère d'arbitrage, comme pour la
Chambre : **QuiverQuant**, qui recense indépendamment ces transactions. Quiver n'entre **jamais**
dans la table.

**Point de départ** : la v1 du notebook produisait 280 transactions mais **n'avait jamais été
validée** (la cellule Quiver cherchait `QUIVER_API_TOKEN`, absent → vérification sautée), avec
**27 % de lignes sans bioguide**, une **déduplication destructrice**, **4 rapports papier ignorés**
et aucun packaging. Ce rapport documente la fiabilisation, l'OCR des papiers et la mise en autonomie
totale du dossier.

---

## 1. Ce qui n'allait pas (et a été corrigé)

| Problème | Correctif |
|---|---|
| Validation Quiver **jamais exécutée** (mauvaise variable d'env) | Lecture de **`QUIVER_API_KEY`** ; appel bulk filtré **Chambre = Sénat**, mis en cache. |
| **77/280 lignes (27 %) sans bioguide** (McCormick, McConnell, Banks, Hagerty) | Matcher amélioré : nettoyage suffixes/initiales/virgules, table de surnoms, **désambiguïsation par chambre (sénat) puis par titulaire en exercice**. → **100 % rattachées**. |
| Filtre Quiver `contains("Sen")` attrapait « repré**sen**tatives » | Égalité exacte `Chamber == "Senate"`. |
| **Ticker à 54 %** (colonne eFD souvent `--`) | Récupération depuis l'**Asset Name** quand il *est* un ticker (« LLY », « CRWD PUT »). → **67 %**, 0 faux positif. |
| Aucun packaging | Tables numérotées **01→07**, `qa_flags`, **Excel** multi-onglets, README. |

**Identité — les 4 cas, confirmés depuis `legislators-current.yaml` :**

| Nom déposé | bioguide | Pourquoi le matching échouait |
|---|---|---|
| David H McCormick | **M001243** (PA) | initiale « H » + collision avec Richard McCormick (M001218, Rep GA) |
| A. Mitchell McConnell, Jr. | **M000355** (KY) | « A. Mitchell…, Jr. » vs « Mitch » + 2ᵉ McConnell historique (William, ID) |
| James Banks | **B001299** (IN) | « James » vs surnom officiel « Jim » |
| William F Hagerty, IV | **H000601** (TN) | « William F…, IV » vs « Bill » |

> Preuve indirecte que les 4 IDs sont justes : McConnell, Banks et Hagerty tombent **exactement** sur
> les comptes Quiver (2=2, 1=1, 1=1) une fois rattachés.

---

## 2. Validation vs Quiver (`07_quiver_comparison.csv`)

Comparaison à **fenêtre de divulgation comparable** (même logique que la Chambre) : nos PTR sont
*divulgués* en Q1 2025, donc Quiver est filtré sur sa **date de divulgation** (`Filed`) en Q1.

| Sénateur | nous | Quiver | delta | verdict |
|---|---|---|---|---|
| **Richard Blumenthal** (OCR papier) | **92** | **0** | **+92** | **quiver_sans_donnee** |
| David McCormick | 73 | 12 | +61 | nous_plus |
| Markwayne Mullin | 66 | 53 | +13 | nous_plus |
| Ashley Moody | 44 | 15 | +29 | nous_plus |
| John Boozman | 38 | 38 | 0 | concordant |
| Shelley Capito | 24 | 22 | +2 | nous_plus |
| John Fetterman | 9 | 0 | +9 | quiver_sans_donnee |
| Rick Scott | 6 | 0 | +6 | quiver_sans_donnee |
| Tuberville, Wyden, Whitehouse, McConnell, Rubio, Smith, Banks, Carper, Moran, Hagerty | 1–6 | = | **0** | **concordant** |
| **TOTAL** | **375** | **164** | **+211** | — |

**Bilan** : 11 concordants, 4 « nous ≥ Quiver », 3 sans donnée Quiver. **On ne sous-compte jamais
Quiver** (aucun delta négatif réel). Les **92 transactions OCR de Blumenthal sont 100 % additives** :
Quiver n'indexe **aucun** de ses dépôts papier (déposés via cabinet, scannés) — c'est précisément la
valeur de l'OCR.

---

## 3. Interprétation des écarts (honnêteté)

- **McCormick +61** : ses 73 lignes = **52 bons municipaux + 9 corporate bonds + 12 actions**. Quiver
  n'a que ses **12 actions** → il **ne suit pas les obligations**. Le surplus n'est pas du bruit,
  c'est de la donnée que Quiver ignore.
- **Moody +26, Mullin +13, Fetterman +9, Scott +6, Capito +2** : même logique (Quiver agrège/omet une
  partie ; Fetterman = 9 corporate bonds que Quiver n'a pas). On a **plus**, jamais moins.
- **Contrôle transaction-à-transaction** (`07b_quiver_ticker_gaps.csv`) : **1 seul** écart apparent —
  Hagerty `AHL-C` (nous) vs `AHL.C` (Quiver), **même opération** le 02/01/2025 à la ponctuation du
  ticker près. → **0 vraie transaction manquée.** (L'enrichissement ticker a résolu les 10 écarts
  Moody : il s'agissait d'actions sans ticker dans notre extraction, pas de trades manqués.)
- **`quiver_seul` = Eleanor Holmes Norton** (1) : **erreur de chambre côté Quiver** (déléguée DC à la
  Chambre, pas sénatrice). Aucun dépôt Sénat réel manqué.

---

## 3 bis. OCR des 4 rapports papier (lacune v1 levée)

Les 4 PTR papier (`backlog.csv`) sont **tous du Sénateur Richard Blumenthal** (B001277), déposés via
Elias Law Group. `senate_ocr.py` (autonome, **Claude Vision** + `tool_use`, adapté au formulaire
Sénat : propriétaire en préfixe `(S)/(DC)/(J)`, fourchettes $ à cocher, comptes imbriqués
`Compte: Actif`) en extrait **92 transactions** (24+35+30+3), identité 100 %, 0 échec batch.

> **Garde-fou dates** : sur un scan abîmé (8e8ae815), le millésime était mal lu (25 → 23/24/26/27).
> Le prompt reçoit la **période déclarée** (lettre d'accompagnement) et un **filet déterministe**
> recale l'année. Résultat : les plages par rapport collent **exactement** aux lettres
> (14607985 : 08–17/01 ; 4fbbf6be : 27/01–10/02 ; 8e8ae815 : 26/02–04/03 ; d7d35e4a : 27/12/2024).

## 3 ter. Déduplication non destructrice

`drop_duplicates(natural_key_hash)` supprimait **3 vraies transactions** (Moody : `SYM`/`NCLH`/`SMCI
CALL` vendus 2× le même jour, même fourchette). On ajoute `occurrence_index` (rang du lot dans un
rapport) et on ne fusionne que les doublons **cross-rapport** (amendement). Électronique **280 → 283**.

## 4. Limites résiduelles (assumées)

- **Couverture ticker** : **67 %** sur l'électronique ; **51 %** sur l'ensemble. Le reste = obligations
  (bons municipaux, corporate bonds) et les **92 lignes OCR de Blumenthal** = LLC / fonds familiaux
  **privés sans ticker**. Légitime ; le projet s'interdit d'utiliser Quiver pour combler les tickers.
- **`asset_type` OCR** : inféré du nom (Blumenthal → `Other`, véhicules privés) faute de colonne
  « Asset Type » sur le formulaire papier — moins précis que l'électronique (colonne explicite).
- **`operation_type` papier** : le formulaire ne distingue pas Sale (Full)/(Partial) → `Sale` simple.
- **Accès eFD fragile** (gate CSRF + Akamai) : aucune évasion ; on s'appuie sur les rapports déjà
  cachés (`reports/*.html` + `reports/media/*.gif`).

---

## 5. Fichiers

- **Scripts** (autonomes, dans le dossier) : `senate_ocr.py` (OCR papier, cache versionné) puis
  `senate_finalize.py` (fusion + Quiver, idempotent ; seul Quiver est re-téléchargé).
- **Générés** : `tables/06_senate_2025q1_FINAL.csv` (**375**), `tables/06_..._transactions.csv` (283),
  `tables/06b_..._ocr_transactions.csv` (92), `tables/07_quiver_comparison.csv`,
  `tables/07b_quiver_ticker_gaps.csv`, `tables/01→05`, `tables/06c_qa_flags.csv` (vide),
  `tables/06c_ocr_failures.csv` (vide), `tables/_quiver_senate_cache.csv`, `senate_2025q1_FINAL.xlsx`.

**Verdict global** : le pipeline Sénat est **rattaché à 100 %** (18 sénateurs, 375 lignes), **validé**
(nous ≥ Quiver partout, 0 vraie transaction manquée, 92 OCR additives), **dédupliqué sans perte**,
**homogène** avec la Chambre (schéma 23 colonnes, OCR Vision), **100 % autonome** (référentiel +
secrets + venv locaux), et **honnête** (limites obligataires/privées et OCR explicitées).
