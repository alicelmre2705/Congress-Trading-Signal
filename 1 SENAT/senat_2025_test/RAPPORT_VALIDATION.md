# Rapport de validation — Sénat eFD, Q1 2025

**Question** : le pipeline Sénat (37 dépôts eFD, 280 transactions électroniques) est-il fiable et
l'information extraite est-elle juste ? Critère d'arbitrage, comme pour la Chambre : **QuiverQuant**,
qui recense indépendamment ces mêmes transactions. Quiver n'entre **jamais** dans la table.

**Point de départ** : la v1 du notebook produisait 280 transactions mais **n'avait jamais été
validée** (la cellule Quiver cherchait `QUIVER_API_TOKEN`, absent → vérification sautée), avec
**27 % de lignes sans bioguide** et aucun packaging. Ce rapport documente la fiabilisation.

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
| David McCormick | 73 | 12 | +61 | nous_plus |
| Markwayne Mullin | 66 | 53 | +13 | nous_plus |
| Ashley Moody | 41 | 15 | +26 | nous_plus |
| John Boozman | 38 | 38 | 0 | concordant |
| Shelley Capito | 24 | 22 | +2 | nous_plus |
| John Fetterman | 9 | 0 | +9 | quiver_sans_donnee |
| Rick Scott | 6 | 0 | +6 | quiver_sans_donnee |
| Tuberville, Wyden, Whitehouse, McConnell, Rubio, Smith, Banks, Carper, Moran, Hagerty | 1–6 | = | **0** | **concordant** |
| **TOTAL** | **280** | **164** | **+116** | — |

**Bilan** : 11 concordants, 4 « nous ≥ Quiver », 2 sans donnée Quiver. **On ne sous-compte jamais
Quiver** (aucun delta négatif réel) — exactement le profil de la version House.

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

## 4. Limites résiduelles (assumées)

- **4 rapports papier** non traités (`backlog.csv`) : OCR à venir (pipeline réutilisable
  `0 HOUSE/house_ocr_multiyear.py`). Lacune connue de la v1, non masquée.
- **Couverture ticker 67 %** : le reste (92 lignes) = **70 bons municipaux + 18 corporate bonds +
  4 actions** sans symbole exploitable. Légitime pour le Sénat (très obligataire) ; le projet
  s'interdit d'utiliser Quiver pour combler les tickers.
- **Accès eFD fragile** (gate CSRF + Akamai, 500 possibles) : aucune évasion ; on s'appuie sur les
  37 rapports déjà cachés.
- **Surplus vs Quiver non audité ligne à ligne** au-delà du contrôle ticker : cohérent avec le
  sous-recensement obligataire de Quiver, mais non prouvé à la transaction près.

---

## 5. Fichiers

- **Script** : `senate_finalize.py` (idempotent ; seul Quiver est re-téléchargé).
- **Générés** : `tables/06_senate_2025q1_transactions.csv` (280), `tables/07_quiver_comparison.csv`,
  `tables/07b_quiver_ticker_gaps.csv`, `tables/01→05`, `tables/06c_qa_flags.csv` (vide),
  `tables/_quiver_senate_cache.csv`, `tables/senate_2025q1_FINAL.xlsx`.

**Verdict global** : le pipeline Sénat est désormais **rattaché à 100 %**, **validé** (nous ≥ Quiver
partout, 0 vraie transaction manquée), **homogène** avec la Chambre (schéma, ticker ≈ 67 %), et
**honnête** (backlog papier et limites obligataires explicités).
