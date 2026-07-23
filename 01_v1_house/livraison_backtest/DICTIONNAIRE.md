# Dictionnaire de données — livraison backtest House

> Chaque colonne de chaque fichier, avec **type · sens · clé**. Profilé sur les fichiers réels
> (dtypes, % de nuls, unicité des clés **vérifiés**, pas inventés).
> Source : notebook `../Portefeuilles_House_Complet.ipynb`. Fenêtre : transactions **2013-2026**, patrimoine **2014-2026**.

## ⚠ À lire en premier — quel fichier pour quoi

| besoin | fichier | note |
|---|---|---|
| **BACKTESTER (l'entrée)** | `flux_backtest.csv` | **129 538** transactions **dédupliquées, avec cours, 2 dates**. C'est LE fichier à trader. |
| toutes les transactions (brut) | `../cache/tables/04_transactions_v1.csv` | 166 149, **AVEC doublons** (même trade vu dans plusieurs docs) — **ne pas trader tel quel**. |
| positions déclarées (Schedule A) | `../cache/tables/11_holdings_complets.csv` | 420 916, tous types **C/H/O/A/T** (le patrimoine, pas les trades). |
| portefeuilles de départ | `portefeuilles_entree.csv` | 284 photos d'entrée retenues. |
| qui est qui | `registre_membres.csv` | 900 membres, trajectoires. |
| ce qui a un cours | `tickers_couverts.csv` | 6 552 tickers, fenêtre 2012-01-03 → 2026-07-02. |

---

## `flux_backtest.csv` — L'ENTRÉE BACKTEST · 129 538 lignes
*Flux unifié F : transactions **dédupliquées**, **valorisables** (un cours existe le jour dit), 3 sources.
Produit par la cellule `add2dates2026` du notebook (→ `flux_house_2dates.csv`, à déposer ici).*

| colonne | type | sens | clé / note |
|---|---|---|---|
| `bioguide_id` | texte | identifiant officiel du membre | → `registre_membres.bioguide` |
| `ticker` | texte | symbole boursier (Yahoo) | → `tickers_couverts.ticker` |
| `op` | texte | `buy` / `sell` | |
| `traded` | date | **date de l'opération** | l'entrée « borne haute » (idéalisée) |
| `disclosure_date` | date | **date de publication** | l'entrée « réaliste » (le public l'apprend ce jour) |
| `delai_divulgation_j` | entier | `disclosure_date − traded`, en jours | médiane **27** (ptr) / **374** (rapports) / **393** (scanné) |
| `size_usd` | réel | montant $=$ milieu de la fourchette déclarée | `8000.5` $=$ forfait du Schedule B scanné |
| `provenance` | texte | `ptr` / `oat` / `oat_ocr` | fil de l'eau / rapport électronique / Schedule B scanné |

---

## `../cache/tables/04_transactions_v1.csv` — transactions BRUTES · 166 149 lignes · **AVEC doublons**
*Toutes les transactions extraites, **tous types (P/O/A/T)**, House + Senate. **58 214 doublons** sur
la clé naturelle (même trade re-déclaré dans plusieurs documents) : dédupliquer avant tout usage — le
`flux_backtest.csv` est déjà la version propre.*

| colonne | type | sens | clé / note |
|---|---|---|---|
| `doc_id` | entier | identifiant du document source | |
| `provenance` | texte | `ptr` / `fd_T` / … | canal d'extraction |
| `filing_type` | texte | **P** (déclaration rapide) · **O** (rapport annuel) · **A** (amendement) · **T** (sortie) | |
| `annee_index` | entier | année de l'index de dépôt | 2013-2026 |
| `bioguide` | texte | membre | → registre (House) |
| `declarant_name` | texte | nom déclaré | |
| `state_district` | texte | état + district (ex. `OH07`) | |
| `transaction_date` | date | date de l'opération (normalisée) | |
| `transaction_date_brute` | texte | date telle qu'écrite sur le doc | traçabilité OCR |
| `disclosure_date` | date | date de publication | |
| `ticker` | texte | symbole (35 % nuls : pas toujours résolu) | |
| `asset_description` | texte | libellé de l'actif | |
| `asset_code` | texte | code de formulaire (GS/ST… — 75 % nuls) | pas un ticker |
| `operation_type` | texte | `Purchase` / `Sale` / … | |
| `owner` | texte | `SELF` / `SP` (conjoint) / `DC`/`JT` | propriétaire de la ligne |
| `amount_range` | texte | fourchette déclarée (ex. `$1,001 - $15,000`) | |
| `amount_lo` / `amount_hi` | réel | bornes de la fourchette | |
| `amount_mid` | réel | **milieu** (= `size_usd` du flux) | |
| `amount_mid_conventionnel` | réel | milieu avec convention sur la tranche la plus fréquente | |
| `amount_reconstruit` | booléen | montant reconstruit (fourchette illisible) | |
| `amount_exact` | booléen | montant exact connu | |
| `cle_naturelle` | texte | `bioguide\|date\|ticker\|…` | **clé de dédup** (34 955 doublons) |
| `occurrence_index` | entier | rang de l'occurrence du même trade | 0 = première |
| `n_docs_vus` | entier | nb de documents où ce trade apparaît | |
| `source` | texte | `instantane_seul` / `site` | origine de l'index |

---

## `../cache/tables/11_holdings_complets.csv` — positions Schedule A · 420 916 lignes
*Le patrimoine déclaré (ce qu'ils **possèdent**), **tous types C/H/O/A/T** — pas des transactions.
Par type : **C** 172 625 · **O** 141 311 · **A** 72 527 · **H** 21 646 · **T** 12 807.*

| colonne | type | sens | clé / note |
|---|---|---|---|
| `asset_description` | texte | libellé de la ligne (« Fidelity … ⇒ Apple Inc. ») | |
| `ticker` | texte | symbole (55 % nuls : immobilier, LLC, comptes…) | |
| `owner` | texte | `SELF` / `SP` / … | |
| `value_range` | texte | fourchette de valeur (10 tranches) | |
| `value_lo` / `value_hi` | entier/réel | bornes de la fourchette | |
| `doc_id` | entier | document source | |
| `filing_type` | texte | **C/H/O/A/T** | |
| `annee_index` | entier | année | |
| `conteneur_nu` | booléen | ligne = un conteneur (compte) sans actif | |
| `bioguide` | texte | membre (36 % nuls : candidats jamais élus) | |
| `filing_date` | date | date de dépôt du document | |
| `nom_n` | texte | libellé normalisé (minuscules) | pour rapprochement |
| `ticker_resolu` | texte | *(colonne héritée, 100 % vide — ignorer)* | |
| `classe` | texte | classe de l'actif : `fonds nommé` / `société privée / LLC` / `immobilier` / `compte bancaire/monétaire` / `retraite` / `trust` / `obligations` / `assurance-vie` / `autre` (46 % nuls = négociable) | |

---

## `portefeuilles_entree.csv` — portefeuilles de départ · 284 lignes
*La photo d'entrée retenue par membre (le point de départ de la reconstruction). Clé `bioguide` **unique**.
Le notebook étend cette base à 325 en re-sélectionnant sur les deux origines (H et C).*

| colonne | type | sens | clé / note |
|---|---|---|---|
| `bioguide` | texte | membre | **clé unique** → registre |
| `doc_id` | entier | document de la photo retenue | **unique** |
| `type_photo` | texte | `H` (entrée) ou `C` (candidature) | |
| `filing_date` | date | date de dépôt de la photo | |
| `n_tickers` | entier | nb de titres cotés dans la photo | |
| `delta_jours_mandat` | réel | jours entre l'entrée en mandat et le dépôt (89 % nuls : date de mandat inconnue) | |
| `garde_fous_ok` | booléen | contrôles de sélection passés (toujours vrai ici) | |

---

## `registre_membres.csv` — les 900 membres · 900 lignes
*Le référentiel de population. Clé `bioguide` **unique**.*

| colonne | type | sens | clé / note |
|---|---|---|---|
| `bioguide` | texte | membre | **clé unique** |
| `categorie` | texte | `reconstructible complet` / `hors d'atteinte` / … | équipement en données |
| `quadrant` | texte | `déjà-là restés` / `déjà-là partis` / `arrivés restés` / `cycle complet` | trajectoire de mandat |
| `n_photos` | entier | nb de photos de patrimoine déposées | |
| `a_flux` | booléen | a au moins une transaction exploitable | définit les **408** traders |
| `a_photo_entree` | booléen | a une photo d'entrée exploitable | |
| `dans_cohorte_Ca` / `dans_cohorte_papier` | booléen | appartenance à des cohortes de contrôle | |
| `premiere_photo` / `derniere_photo` | date | première / dernière photo (3 % nuls : aucune photo) | |

---

## `tickers_couverts.csv` — l'univers de prix · 6 552 tickers
*Quels symboles ont une série de cours dans nos caches (le tradeable). Fenêtre commune :
**2012-01-03 → 2026-07-02** (3 645 jours cotés, calendrier SPY).*

| colonne | type | sens | clé / note |
|---|---|---|---|
| `ticker` | texte | symbole (Yahoo) | **clé unique** |
| `in_prices_v2` | 0/1 | présent dans le cache principal (`prices_v2`, 3 351) | le snapshot de référence |
| `in_prices_holdings` | 0/1 | présent dans `prices_holdings_v1` (3 002) | cache des positions |
| `in_prices` | 0/1 | présent dans `prices` (2 769) | cache historique |

> Les séries elles-mêmes (fichiers `TICKER.csv`) vivent dans
> `../../00. S3S4 en cours/cache/prices_v2/` (non versionné, régénérable par le notebook).
