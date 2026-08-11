# Référentiels transverses (House + Sénat)

Quatre référentiels + les snapshots de commissions — **tous déclaratifs** : corriger la donnée =
éditer un référentiel, jamais du code. Chacun est compté et cité au §7 du rapport.

## `ticker_renames.csv` — renommages, rachats, faillites, recyclages de symboles (96 entrées)

Créé lors de l'audit données du 2026-07-03 (finding REN-01 : 18,9 % des lignes du backtest Quiver
n'avaient aucun prix utilisable, faute de référentiel de renommages — FB/Meta, PCLN/BKNG, ATVI…).

| Colonne | Sens |
|---|---|
| `ticker_ancien` | symbole tel qu'il apparaît dans les déclarations (PTR/Quiver) |
| `ticker_nouveau` | symbole ACTUEL du même émetteur (vide si plus coté) |
| `type` | `renommage` (même société), `fusion_echange` (actionnaires payés en titres de l'absorbeur), `rachat_delisting` (sortie de cote — position à clôturer au dernier prix/à la date du deal), `faillite_delisting` (perte quasi totale — NE PAS exclure du backtest, c'est le biais de survie), `recyclage_attention` (le même symbole a désigné DEUX émetteurs différents — joindre les prix par période, jamais en aveugle) |
| `date_effet` | mois de l'événement (précision au mois, suffisant pour le join backtest) |
| `note` | contexte libre (source de la vérification, piège connu) |
| `historique_valide` | `complet` = le successeur porte tout l'historique du listing (renommage pur ou jambe survivante de la fusion — vérifié : META remonte à 2012, RTX à 1962) ; `post_fusion_seulement` = jambe ABSORBÉE (RTN, STI, MYL, LLL, DISCK) : le prix du successeur avant la fusion est celui d'une AUTRE société — ne jamais l'utiliser pré-fusion |

Usage prévu (chaîne de nettoyage canonique) : le champ `ticker` reste FIDÈLE à la déclaration ;
le champ `ticker_yahoo` (join prix) applique `renommage`/`fusion_echange` ; les `*_delisting`
alimentent `is_delisted` (traitement explicite dans le backtest au lieu d'une disparition silencieuse) ;
les `recyclage_attention` exigent un contrôle de recouvrement de dates avant tout join prix.

Sources : événements de marché publics (dates vérifiées au mois près). Toute entrée douteuse a été
OMISE plutôt que devinée — compléter au fil des besoins, jamais en aveugle.

## `ticker_sector_map.csv` — carte transverse ticker → classe d'actif / secteur GICS / ETF proxy

Dérivée du cache de résolution S3S4 (`ticker_sector.json` : yfinance factuel + repli LLM) et CORRIGÉE
des erreurs prouvées à l'audit 2026-07-03 : 97 ETF diversifiés/obligataires/commodities requalifiés
`etf_broad` (un secteur GICS n'a pas de sens pour eux — l'ancien cache leur donnait des secteurs LLM
faux : IWD→XLF, GLD→XLB…), 11 SPDR sectoriels = leur propre proxy, NP re-daté (Neenah Paper, recyclage).

| `asset_class` | Sens |
|---|---|
| `stock` | action — `sector_gics` + `etf_proxy` SPDR remplis (source yfinance/llm conservée) |
| `etf_sector` | SPDR sectoriel — proxy = lui-même |
| `etf_broad` | ETF diversifié — PAS de secteur ; à garder dans un backtest actions/ETF avec flag |
| `unknown` | non résolu (majoritairement non-coté/obligations) — à flaguer, pas à jeter en aveugle |

## `ticker_false_positives.csv` — tickers extraits à tort d'une parenthèse (26 règles)

Répare les faux-positifs d'extraction : « NetApp, Inc. stock (IRA) » portait le ticker `IRA`,
« FACEBOOK INC CL-A » portait `A` (qui est Agilent). Colonnes : `ticker_errone`,
`motif_description` (le motif à retrouver dans la description), `ticker_corrige` (vide = la
ligne sort de la clean, l'actif n'est pas une action ordinaire), `note`. Appliqué en étape 1 du
nettoyage (`common/backtest_clean.py :: apply_ticker_false_positive_fixes`).

## `ticker_sector_map_datee.csv` — bascules d'indice datées (47 règles)

« Datée » = la carte secteur→ETF **à la date du trade** : l'immobilier n'a son SPDR (XLRE) que
depuis le 16/09/2016, la communication (XLC) depuis le 21/09/2018 — avant ces dates de bascule
d'indice, les titres concernés vivaient dans XLF/XLK/XLY. 2 règles de bascule + 45 attributions
nominatives. Colonnes : `ticker`, `etf_actuel`, `etf_avant_bascule`, `date_bascule`, `regle`,
`source`.

## `committees_snapshots/{113..119}/` — commissions par Congrès (point-in-time)

Paires `committees.yaml` + `membership.yaml` (github unitedstates/congress-legislators aux tags
historiques). Source du parti et des commissions **à la date du trade** (étape 4 du nettoyage,
bascule de Congrès au 3 janvier).
