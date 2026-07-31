# Patchs S3/S4 à appliquer (issus de l'audit données du 2026-07-03)

> Le dossier « 02_recherche_backtest/ » était **hors périmètre** de l'audit-réparation (décision d'Alice :
> « on s'en charge après »). Les corrections ci-dessous concernent le notebook
> `02_construction_table_2014_2026.ipynb` (table Quiver) et le notebook 05 — **à appliquer lors de la
> reprise du chantier S3/S4**. Chaque point renvoie au finding de l'audit (preuves + listes de lignes
> dans les artefacts d'audit). La table primaire canonique (`data/clean/transactions_backtest_2014_2026.csv`)
> a déjà TOUTES ces corrections — la façon la plus simple d'appliquer ce document est de **basculer la
> recherche sur la table canonique** et de reléguer la table Quiver au cross-check.

## Notebook 02 — entonnoir et normalisations

1. **Étape C : ne plus jeter sur « secteur non résolu »** (SEC-01/SECT-01/QCL-01, critique). 2 774 lignes
   à ticker valide et coté sont supprimées au seul motif que `sector_gics` est vide — dont ~608 lignes
   d'ETF indiciels très liquides (SPY 105, VEA 67, QQQ 58…) dont l'absence de secteur est VOULUE par le
   notebook lui-même (MANUAL_OVERRIDES + prompt LLM). Le secteur est un enrichissement, pas un critère de
   tradabilité. → Remplacer `sector_gics.notna()` par un flag `has_sector` ; garder les ETF larges avec
   `is_broad_etf` (cf. `data/reference/ticker_sector_map.csv`).
2. **Ajouter un filtre famille d'actif** (OPT-01, majeure). Le clean Quiver garde 1 513 lignes typées
   non-« stock » dont 1 161 avérées non-actions (1 102 options — ex. 257 options MSFT dont 238 de Josh
   Gottheimer —, 55 obligations corporate, 4 Treasuries). Un backtest actions les valorise comme des
   actions. → filtrer/flaguer par `TickerType`/description.
3. **`_norm_ticker` : gérer les classes d'actions à tiret** (NORM-01/TKR-01, majeure). La regex rejette
   1 292 lignes à ticker brut non vide, dont ≥194 vraies classes cotées (BRK-A 96, LEN-B 48, RDS-A 37,
   STZ-B 10…) alors que BRK.B à point est gardé. → utiliser `common.schema.canonical_ticker` (créée à
   l'audit ; gère aussi le vrai fonds NAN vs l'artefact pandas 'nan').
4. **Montants : ne plus clipper les montants exacts < 1 001 $** (AMT-02, majeure). 440 lignes dont Quiver
   donne le montant EXACT (0,01–1 000 $) sont écrasées à 1 001 puis remontées au midpoint 8 000 $
   (inflation ×20 ; pire cas : 15 $ → 8 000 $). → garder `Trade_Size_USD` brut ; `amount_midpoint` =
   montant exact quand ce n'est pas une borne basse de bracket connue. Corriger aussi INC-01 : 12 lignes
   sans Trade_Size_USD ont size_usd=1001 (fillna) mais midpoint NaN — incohérence interne.
5. **Secteurs : remplacer la couche par `data/reference/ticker_sector_map.csv`** (SEC-ETF-01/SEC-YF-02,
   majeures). 379 lignes d'ETF diversifiés portent un secteur LLM faux (IWD→XLF, GLD→XLB, DIA→XLI…) et
   `_yf_one` résout l'occupant ACTUEL d'un ticker recyclé (NP = 149 lignes classées Financials alors que
   c'était Neenah Paper/Materials sur 2014-2020). La carte transverse corrige les deux.
6. **Symboles fantômes Quiver** (QVR-01) : VRNG (383 lignes, trades jusqu'en 2026 sous un ticker disparu
   ~2016) et consorts — croiser avec `data/reference/ticker_renames.csv` (type `recyclage_attention`)
   et vérifier le recouvrement de dates avant tout join prix.
7. **Étape A : ajouter le garde-fou « année de transaction plausible »** (GUARD-01, info) : la primaire
   exige `txn_year ∈ [2012, année de dépôt]`, le 02 non (42 lignes à lag > 5 ans passent sans contrôle).
8. **Parti point-in-time : utiliser `party_affiliations`** (PARTY-01, mineure) : `term_at` retourne le
   parti de FIN de mandat pour un switch en cours de mandat (4 lignes Amash fausses). Reprendre la
   logique `party_at` du notebook canonique (`Nettoyage_Backtest_2014_2026.ipynb`, cellule parti PIT).
9. **Commissions : angle mort du snapshot mi-Congrès** (COMM-01, mineure) : 680 lignes de membres en
   poste à la date du trade ont committee_membership=NA (partis/arrivés autour de la date du snapshot).
   + résoudre les codes de sous-commissions bruts (KEY-02 : HSAS03, SSFI02… non traduits en noms).
10. **`state_district` est une copie de `state`** (SCHEMA-01, mineure) : le district est perdu (« TN »
    vs « OH07 » côté primaire) — piège de jointure entre les deux tables.
11. **Congrès attribué par année seule** (CONG-01, info) : 146 lignes tradées les 1-2 janvier d'années
    impaires rattachées au mauvais Congrès (bascule réelle : 3 janvier). Reprendre `congress_of` du
    notebook canonique.
12. **Flag `dup_suspect`** (DUP-02, majeure) : 755 groupes de doublons exacts post-2020 (789 lignes,
    ~0,7 % de la table) n'ont qu'UNE transaction primaire correspondante = probables doubles comptages
    Quiver. Liste : artefacts d'audit `quiver_vrais_doublons_probables_post2020.csv`. À flaguer pour
    test de sensibilité (backtest avec/sans). Les ~12 % restants de « doublons » sont des lots réels
    multi-comptes (owner non publié par Quiver) — ne JAMAIS `drop_duplicates()`.

## Notebooks 03/04/05 — points d'hygiène

13. **Le 03 n'a jamais été ré-exécuté** depuis le passage à la table 100 % Quiver : ses outputs décrivent
    encore l'ancienne table hybride (« 138 345 txns, golden 90 275 / quiver 48 070 »). Re-run complet
    nécessaire avant toute présentation.
14. **03/04 lisent la table BRUTE `table_congres_2014_2026.csv`** (S3-01, mineure) qui contient 49 lignes
    traded>filed et 642 échanges — préférer la table filtrée (ou mieux : la canonique primaire).
15. **Cache prix du 05** (FAIL-01, majeure) : `failed_tickers.txt` mélange vrais délistés et échecs
    transitoires yfinance — MMC (132 lignes, cotée S&P 500), DENN, FI y sont bloqués À VIE par le
    téléchargement « resumable » (`t not in failed`). → re-tenter les 1 930 failed avec retries et
    séparer `vraiment_delistes.txt` / `echec_transitoire.txt` ; appliquer `ticker_renames.csv` AVANT le
    join prix (18,9 % des lignes du clean Quiver n'ont aujourd'hui aucun prix utilisable, et 20 lignes
    FB 2025-2026 prendraient le prix d'un AUTRE émetteur — symbole recyclé) ; garde-fou « date du trade
    ∈ [min, max] du CSV prix ».
16. **Survivorship** : la direction du biais n'est pas toujours « borne haute » — les rachats à prime
    exclus créent un biais BAISSIER ; les faillites exclues un biais haussier. Le référentiel
    `ticker_renames.csv` (types rachat/faillite) permet un traitement explicite par catégorie.

## Rappels de périmètre

- La fenêtre des deux tables est par **date de dépôt** (filed 2014-2026) : ~379-683 lignes tradées
  2012-2013 déposées en 2014+ y figurent légitimement (WIN-01).
- Lots multi-comptes : ~12,6 % de la table Quiver est en lignes identiques représentant des comptes
  Self/Spouse/Joint/Child réels (prouvé par croisement primaire : 6 715/7 845 groupes) — champ owner
  non publié par Quiver.
