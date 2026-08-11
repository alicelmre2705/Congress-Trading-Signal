# Audit & réparation des données Congress Trading 2014-2026 — rapport final

**Date : 2026-07-03 · Branche : `2014-2026-fable` · Périmètre : couche données uniquement** (le dossier
« 02_recherche_backtest/ » n'a pas été touché — ses corrections sont consignées dans
`PATCHS_S3S4_A_APPLIQUER.md`, archivé sur la branche de travail `presentation` sous
`02_recherche_backtest/_archive/recherche_v0/`).

**Objet** : certifier que TOUTE la donnée nécessaire à la phase de recherche est récupérée, propre,
corrigée — et livrer une table de recherche canonique documentée. Règle appliquée : **chaque erreur
relevée est corrigée** ; ne restent ouvertes que les limites de fidélité-source (flaguées) ou hors de
notre contrôle (documentées avec la direction du biais).

## 1. Méthode

- **Audit interne** : 23 agents sur 10 dimensions (doublons, dates, tickers, montants, identité,
  secteurs, entonnoirs, champs, complétude vs officiel, exactitude des docs), chaque anomalie
  re-vérifiée par un agent sceptique indépendant + un juge cause-racine pour les critiques →
  **92 findings, 5 réfutés, 87 retenus** (3 critiques, 16 majeures, 35 mineures, 33 constats).
- **Cross-validation externe** (indépendante de Quiver) : dump [senate-stock-watcher](https://github.com/timothycarambat/senate-stock-watcher-data)
  (8 350 txns Sénat 2012-2020) + mirror house-stock-watcher reconstruit (23 568 txns 2012-2026,
  champs `owner`/`filing_id`) + index officiels annuels du House Clerk ({Y}FD.xml, 13 années,
  re-téléchargés). Les fichiers de réplication de Belmont et al. 2022 (JPubE) ne sont pas publics.
- **Sonde parser** : 140 documents pré-2018 re-parsés et comparés à un contrôle indépendant par
  paires de dates.
- Preuves, scripts reproductibles et listes de lignes : artefacts d'audit (scratchpad de session) ;
  chaque chiffre de ce rapport provient d'une exécution vérifiée.

## 2. Verdict global

| Avant l'audit | Après réparation |
|---|---|
| Corpus FINAL brut : 160 064 lignes (26 fichiers) | **170 920 lignes** (+10 856, zéro ligne perdue — contrôle par clé sur chaque année) |
| Uniques après dédup cross-année : 158 172 | **169 000** |
| Table backtest : 125 984 × 18 colonnes | **134 464 × 36 colonnes** (canonique, invariants vérifiés par asserts) |
| House pré-2020 (backtest, par date de transaction) : 49 957 | **56 706** (+13,5 % — la zone la plus déficitaire) |
| Ventes digitales 2014 : 555 (biais vendeur) | **1 170** (parité achats/ventes restaurée) |
| Golden : 224/137 — 1 test rouge | **Golden 230/138 — 10/10 tests verts** |

**La donnée est complète au sens fort** : 100 % des PTR listés par les index officiels du Clerk
2014-2026 sont désormais soit parsés, soit OCRisés, soit écartés par une règle écrite (manuscrits) —
plus aucun document « jamais entré dans le pipeline ».

## 3. Complétude — a-t-on tout ?

### 3.1 House vs l'univers officiel (index {Y}FD du Clerk, re-téléchargés le 2026-07-03)

- Univers officiel : **8 252 PTR** (FilingType=P, dédupliqués — zéro chevauchement de DocID entre années).
- Avant : 8 035 traités ; **217 jamais entrés** (205 listés dans {Y}FD mais déposés après le 31/12 —
  perdus par l'ancien filtre fenêtre année-civile, dont 149 déposés en janvier → biais systématique
  contre les trades de décembre — + 12 déposés après le gel de collecte 2026-06-19).
- Corrigé : `load_ptr_index` ne filtre plus par fenêtre (l'index annuel est l'autorité) ; les 217 +
  75 anciens échecs de parse + 45 filings signalés par le mirror = **293 documents acquis** (227
  téléchargés, 0 échec — y compris le 9107514 réputé 404) : 87 lisibles parsés, 136 scannés tapés
  OCRisés (551 pages, 0 échec), **70 manuscrits écartés par la politique de gating** (documentés,
  fidèles au census), 6 « nothing to report » (Harold Rogers).
- Il n'existe **plus aucun PTR House officiel non traité**. Cutoff de collecte : 2026-07-03.

### 3.2 Sénat vs census interne + source externe

- Census eFD interne : 2 153 dépôts (1 780 électroniques + 373 papier) ; 2 128 dans les FINAL ; les
  **25 sans transaction ont désormais chacun une raison écrite** (`data/senate/tables/06d_docs_sans_transaction.csv` :
  15 doublons/amendements — 169/169 txns retrouvées sous un autre uuid —, 5 scans dont l'OCR n'a lu
  que la ligne-exemple pré-imprimée, 2 « nothing to report », 3 déposés après le gel).
- **senate-stock-watcher (indépendant de Quiver)** : 6 231 transactions tickérisées 2014-2020 →
  **100,0 % retrouvées chez nous hors `Exchange`** (les 36 non-matchés = représentation : SSW éclate
  l'échange en 2 lignes, nous 1). Nous sommes un sur-ensemble strict de cette source. L'univers
  officiel Sénat n'est pas re-vérifiable sans re-scraper eFD (CSRF) — limite documentée.

### 3.3 Vs Quiver et vs le mirror House

- Mirror house-stock-watcher : 99,5 % de ses lignes 2018-2026 chez nous ; pré-2018, les manques qu'il
  révélait (1 065 lignes à ticker vide, 434 lignes absentes, 45 filings) sont **tous traités** (§4).
- Quiver reste couvert à ~88-92 % par nous (l'écart = papier/non-coté que Quiver n'a pas, et ses
  propres artefacts) ; ses « 13 715 doublons exacts » sont élucidés : **85,6 % des groupes croisables
  = lots réels multi-comptes** (owners Self/Spouse/Joint/Child différents, champ que Quiver ne publie
  pas) ; 755 groupes post-2020 (789 lignes, ~0,7 %) = probables doubles comptages côté Quiver (liste
  livrée pour flag côté S3/S4).

## 4. Erreurs trouvées → corrigées (traçabilité complète)

### Critiques

| Erreur (preuve) | Correction (commit) |
|---|---|
| **205 PTR officiels jamais entrés** : filtre fenêtre année-civile de `load_ptr_index` ; 149/205 déposés en janvier → biais anti-décembre | Cause racine corrigée (index = autorité) + 293 docs acquis et intégrés, zéro perte (`a5b2e07`, `7d0e57a`, `d362940`) |
| **7 996 fourchettes de montants tronquées à la borne basse** (le PDF imprime « $15,001 -⏎$50,000 », le parseur ne capturait que la 1re ligne) : montants sous-estimés ×2, ~331 M$ | Réparation read-time déterministe (borne basse → bracket complet, vrai milieu) : `AMOUNT_LOWER_BOUND_TO_BRACKET` dans `common/schema.py`, appliquée par `load_final` (`a5b2e07`) |
| **Aucun référentiel de renommages/délistages** : 18,9 % des lignes du backtest Quiver sans prix utilisable (FB/Meta, PCLN, ATVI…) ; risque de FAUX prix sur symboles recyclés | `data/reference/ticker_renames.csv` (84 entrées typées : renommage / fusion-échange / rachat / faillite / recyclage, + validité d'historique du successeur vérifiée contre Yahoo) (`8935805`, `afccb76`, `b76c003`) |

### Parser & pipeline House

| Erreur | Correction |
|---|---|
| **Biais vendeur systématique pré-2018** : la police rend les majuscules en petites capitales, la regex legacy exigeait `[PSE]` majuscule → ~95 % des lignes perdues étaient des VENTES | Regex insensible aux petites capitales ; recette sur 140 docs : 100,0 % du contrôle indépendant, zéro sur-extraction (`233d800`) |
| **Routage dual perdait la moitié des lignes** des docs mixtes (les 2 gabarits coexistent ; « le parser qui extrait le plus » ignorait l'autre) | Union dédupliquée en multiset — préserve les lots réels (`7d0e57a`) |
| 75 PTR lisibles à 0 ligne extraite (58 avec de vrais montants dans le texte, dont Pelosi 20008699, Boehner) | Tous ré-acquis et re-parsés/OCRisés (`7d0e57a`, `d362940`) |
| Gating des manuscrits non rejouable (33 docs C hérités 2020-2026 qu'un re-run aurait écartés) | `DOCS_C_HERITES_2020_2026` : héritage explicite, corpus reproductible (`0fc7d2f`) |
| Palier « SP/DC over $1,000,000 » : formule digitale ≠ convention canonique 1 000 001 | Cas explicite dans `amount_midpoint`, zéro ligne historique affectée (`d362940`) |
| `test_tenure` rouge à tort (assertion codée en dur : 14 fichiers de l'ère 2020-2026) | 26 fichiers 2014-2026 (`5051501`) |
| Rapport qualité non déterministe (§6.4 dépendait de PYTHONHASHSEED) | Itération triée + tri multi-clés (`a5b2e07`) |

### Identité, dates, tickers

| Erreur | Correction |
|---|---|
| **52 lignes sans bioguide** (Angie Craig 42, Van Hollen 7, Udall 3 — membres invisibles pour toute analyse par membre) + **collision d'homonymes** : le sénateur Bob Casey rattaché à C000228 (un représentant texan) | `KNOWN_IDENTITY_FIXES_BY_DOC` read-time, scopé (doc, nom) : Craig C001119, Van Hollen V000128, Udall U000039, Casey C001070 (`a5b2e07`) |
| **1 065 lignes à ticker vide** alors que la description permettait de le résoudre | Récupération par **double preuve** (notre résolution depuis la description × ticker du mirror concordants) : +403 clés → **2 540 lignes** récupérées read-time ; discordances et artefacts rejetés (`e4592c3`) |
| Parti = « dernier mandat » (24 lignes fausses : Amash, Mitchell, Manchin) ; commissions = photo 2026 appliquée à toutes les années (24,9 % de couverture en 2016) ; Congrès attribué par année seule (bascule réelle : 3 janvier) | Table canonique : **parti point-in-time** (`party_affiliations`), **commissions point-in-time** par Congrès 113-119 (99,1 % de couverture), `congress_of` au 3 janvier (`50bd685`) |
| Tickers primaires non canonisés (BRK.B/BRK-B scindés, 775 lignes non joignables Yahoo, artefacts OCR à chiffres) ; le littéral coté « NAN » (fonds Nuveen) confondu avec l'artefact pandas | `canonical_ticker()` + `ticker_yahoo`/`flag_ticker` dans la table canonique ; le champ `ticker` reste fidèle à la déclaration (`a5b2e07`, `50bd685`) |
| Dépôts tardifs invisibles (11,8 % > 45 j, 2,3 % > 365 j) | Exportés + flagués (`lag_days`, `flag_late_filing`, `flag_very_late_filing`) — jamais retirés : l'info est réelle et exploitable à sa date de publication (`50bd685`) |
| Double convention de midpoint (.0 OCR vs .5 digital/Sénat, 85 416 lignes) | Milieu exact unique recalculé depuis `amount_range` au niveau de la table canonique (`50bd685`) |
| Secteurs : ETF diversifiés avec de faux secteurs LLM (IWD→XLF, GLD→XLB…), ticker recyclé résolu à l'occupant actuel (NP=Neenah Paper classé Financials) | `data/reference/ticker_sector_map.csv` corrigée (97 ETF requalifiés `etf_broad`, NP re-daté) ; secteur actions 100 % dans la table canonique (`b76c003`, `50bd685`) |
| Lots multi-comptes exposés à un `drop_duplicates()` destructeur (info d'occurrence perdue à l'export) | `owner`, `occurrence_index`, `lot_size` exportés + avertissement en tête de notebook (`50bd685`) |
| Traçabilité Sénat : fichiers d'échecs vides, 25 docs sans-txn intraçables | `06d_docs_sans_transaction.csv` avec raison par uuid (`c33ea7d`) |
| Divers robustesse : NaN du merge manifest×index plantait le gating ; `years_in_office` perdu au re-assemblage | Garde `pd.isna` ; ré-enrichissement `common.enrich_tenure` (`d362940`) |

### Restent ouvertes — par choix documenté

- **Fidélité-source (flaguées, pas corrigées)** : coquilles de dates du déposant (le PTR imprime
  littéralement « 01/35/22 ») ; montants = fourchettes STOCK Act (précision structurelle) ;
  ~758 lignes OCR nouvelles à ticker non résolu depuis le nom (candidates à une future passe LLM).
- **Hors de notre contrôle** : prix des titres délistés (Yahoo les a purgés, Stooq verrouillé) —
  traitement PAR TYPE via le référentiel (faillite ≈ perte totale, rachat = clôture à la date du
  deal ; la direction du biais est désormais explicite, pas « borne haute » générique) ; réplication
  Belmont et al. non publique ; univers officiel Sénat non re-vérifiable sans re-scraping.

## 5. La table de recherche canonique

`data/clean/transactions_backtest_2014_2026.csv` — **134 452 lignes × 39 colonnes** (134 464 × 36
au moment de l'audit — l'écart : tickers faux-positifs corrigés depuis, cf.
`NOTE_DIFF_TABLE_CLEAN.md`), produite par
`common/backtest_clean.py` — les étapes sont recensées au **§7 de `RAPPORT_DONNEES.md`** (entonnoir A→D documenté
étape par étape, philosophie « on ne retire que l'avéré, tout le reste est flagué »,
invariants vérifiés par asserts à l'export : bioguide/ticker/montant/
direction/chronologie/hash tous garantis).

| Entonnoir | Lignes |
|---|---|
| Départ (`load_final`, corpus unique 2014-2026, réparations read-time incluses) | 169 000 |
| A — dates présentes & cohérentes | 165 748 |
| B — actions + ETF cotés (ticker-first ; ETF diversifiés GARDÉS et flagués) | 135 977 |
| C — direction achat/vente | 135 151 |
| D — montant présent | **134 464** |

La table Quiver (`transactions_backtest_quiver_2014_2026.csv`, 108 916) reste disponible en
**cross-check** ; la recherche doit basculer sur la canonique (cf. patchs S3/S4) : plus complète
(notamment pré-2020), champs owner/occurrence/doc_id, corrections intégrales, provenance tracée.

## 6. Vérification finale

- Golden re-figé **House 230 / Sénat 138 fichiers** — `check_golden` + `senate_check_golden` : zéro écart.
- **10/10 tests** de régression verts (`tests/regression/`).
- Digital 2020-2026 : append-only prouvé (zéro ligne historique modifiée, `git diff --numstat`).
- Intégration : contrôle par clé (hash, occurrence) sur chacune des 13 années — **zéro perte**.
- Notebook canonique ré-exécuté offline de bout en bout, 0 erreur, asserts passés.
