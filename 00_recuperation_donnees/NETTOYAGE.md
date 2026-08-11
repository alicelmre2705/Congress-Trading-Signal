# Le nettoyage — les étapes, et où vit leur code

**Le code du nettoyage est `common/backtest_clean.py`** — un module Python comme `house/` et
`senate/`, exécuté par le pipeline en step 7 :

```bash
python -m common.pipeline --years 2020-2026    # …le step 7 est « Nettoyage — tables de recherche »
python -m common.backtest_clean                # ou le step seul (100 % hors-ligne)
python tests/regression/test_backtest_clean.py # le contrôle : doit afficher « ZÉRO ÉCART »
```

**Entrée** : les 26 tables FINAL du pipeline (House + Sénat, 2014-2026).
**Sorties** (`data/clean/`) :

| table | lignes × colonnes | c'est quoi |
|---|---|---|
| `transactions_brut_2014_2026.csv` | 169 000 × 41 | **la donnée brute** : tout, avec pour chaque ligne écartée son étape et son motif (`exclusion_etape`, `exclusion_motif`) |
| `transactions_backtest_2014_2026.csv` | 134 452 × 39 | **la donnée clean** : celle que la recherche consomme |
| `transactions_gated_2014_2026.csv` | 7 287 × 13 | les transactions des scans manuscrits écartés par la politique OCR (`house/ocr.py`), avec leur motif |
| `commissions_membre_congres.csv` | 3 707 × 3 | annexe : le texte complet des commissions et sous-commissions par élu × Congrès (jointure `bioguide_id` × `congress`) |

## Les étapes, dans l'ordre d'exécution

**0 · Assemblage du corpus** — `common/quality.py :: load_final`
Concatène les 26 FINAL, déduplique les re-divulgations entre années (clé naturelle 7 champs,
`common/schema.py`), et applique les corrections de lecture — le figé sur disque n'est jamais
modifié : coquilles de dates (`apply_txn_date_fixes`), identités (`apply_identity_fixes`),
fourchettes tronquées (`apply_amount_range_fixes`), tickers retrouvés depuis la description
(`apply_ticker_recovery`). → **169 000 transactions uniques**.

**1 · Tickers faux-positifs** — `backtest_clean :: apply_ticker_false_positive_fixes`
Répare les tickers extraits à tort d'une parenthèse descriptive : « NetApp, Inc. stock (IRA) »
portait le ticker `IRA` ; « FACEBOOK INC CL-A » portait `A` (qui est Agilent). Règles
déclaratives dans `data/reference/ticker_false_positives.csv` (26 règles → 152 lignes :
140 corrigées vers le vrai symbole, 12 vidées car l'actif n'est pas une action ordinaire).

**2 · Montants unifiés** — `backtest_clean :: unify_amounts`
Milieu de fourchette `(lo+hi)/2` recalculé uniformément depuis `amount_range` (les sous-corpus
arrondissaient différemment) ; le palier ouvert « Over $50M » au plancher 50 M$ ; la colonne
`amount_open_bracket` marque les paliers sans borne haute.

**3 · L'entonnoir A→D** — `backtest_clean :: funnel_verdicts`
Quatre coupes, une seule cause par ligne — le verdict est **écrit dans la table brute**, rien
n'est écarté en silence :

| étape | règle | lignes écartées |
|---|---|---|
| A | dates présentes et cohérentes (divulgation ≥ transaction, année plausible) | 3 252 |
| B | actions/ETF cotés — ticker exploitable (`schema.canonical_ticker`), réellement coté, famille cotée | 29 783 (vide 27 018 · malformé 164 · option/obligation 2 601) |
| C | direction claire (achat/vente — les échanges sortent) | 826 |
| D | montant présent | 687 |

**4 · Enrichissements** — `backtest_clean :: enrich`
- **parti à la date du trade** (les switchs en cours de mandat, YAML congress-legislators) ;
- **Congrès + commissions à la date du trade** (snapshots 113-119, bascule au 3 janvier) : la
  ligne porte `congress` et `committees_key_flag` ; le texte complet, sous-commissions résolues,
  est dans l'annexe `commissions_membre_congres.csv` ;
- **ticker canonique Yahoo** (`ticker_yahoo`) + renommages/délistages
  (`data/reference/ticker_renames.csv` — 96 entrées, chacune vérifiée sur cours) ;
- **classe d'actif / secteur GICS / ETF proxy** (`data/reference/ticker_sector_map.csv`, et sa
  déclinaison datée `ticker_sector_map_datee.csv` pour les bascules d'indice 2016/2018) ;
- **flags** : dépôts tardifs (>45 j, >365 j), lots multi-comptes (`lot_size`), prudence prix
  (`flag_price_caution`), `owner_n` normalisé, `member_name_canon`, `ticker_groupe` (classes
  d'actions fusionnées GOOG/BRK-B/FOX/NWS).

**5 · Export et invariants** — `backtest_clean :: write_tables`
Les quatre tables, après six assertions bloquantes sur la clean : bioguide, ticker, montant,
direction ∈ {buy, sell}, chronologie ≥ 0, hash de clé naturelle.

## Les référentiels du nettoyage (`data/reference/`)

`ticker_false_positives.csv` (26) · `ticker_renames.csv` (96) · `ticker_sector_map.csv` (4 849)
· `ticker_sector_map_datee.csv` (47) · `committees_snapshots/113…119/` — tous versionnés,
tous déclaratifs : corriger la donnée = éditer un référentiel, jamais du code.

---
*Les documents de présentation (deck, rapport de qualité) ont été certifiés sur l'état du
2026-07-04 de la table (134 464 lignes) ; l'écart de −12 lignes vient des tickers faux-positifs
corrigés depuis. Historique détaillé : branche `presentation`.*
