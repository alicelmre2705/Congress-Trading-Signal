# Rapport de qualité des données — Congress Trading
> Livrable Ramify, Semaine 2. Généré par `python -m common.quality` (lecture seule des tables FINAL, aucun appel API).
**Périmètre :** 89 852 transactions FINAL (House 81 607 + Sénat 8 245)  années 2020–2026.

## Décomposition par sous-corpus

Les déclarations proviennent de **quatre sous-corpus** très différents (chambre × voie d'acquisition). Toute la suite distingue ces quatre familles, car leur qualité et leur composition diffèrent.

| corpus | n | part_pct |
| --- | --- | --- |
| House électronique | 32667 | 36.4 |
| House OCR | 48940 | 54.5 |
| Sénat électronique | 6566 | 7.3 |
| Sénat OCR | 1679 | 1.9 |

### Couverture des champs enrichis (taux de remplissage)

| corpus | n | ticker_% | secteur_% | etf_proxy_% | committee_% | identite_% | anciennete_% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 32667 | 88.7 | 86.6 | 86.6 | 74.7 | 100.0 | 100.0 |
| House OCR | 48940 | 83.1 | 81.0 | 81.0 | 94.5 | 100.0 | 100.0 |
| Sénat électronique | 6566 | 79.3 | 71.3 | 71.3 | 62.5 | 100.0 | 100.0 |
| Sénat OCR | 1679 | 33.2 | 19.4 | 19.4 | 96.1 | 100.0 | 100.0 |

`identite_%` = part rattachée à un `bioguide_id` ; `ticker`/`secteur`/`etf_proxy` sont vides pour les actifs non cotés (légitime, pas un défaut).

### Scorecard de qualité

| corpus | n | dates_coherentes_% | date_plausible_% | annee_implausible_n | montant_renseigne_% |
| --- | --- | --- | --- | --- | --- |
| House électronique | 32667 | 99.9 | — | 0 | 100.0 |
| House OCR | 48940 | 99.7 | 95.4 | 0 | 98.2 |
| Sénat électronique | 6566 | 100.0 | 92.5 | 0 | 100.0 |
| Sénat OCR | 1679 | 99.8 | 98.5 | 0 | 99.6 |

`date_plausible_%` (fenêtre 75 j) n'existe que pour les lignes OCR → « — » pour House électronique (pas de `date_confidence`). `amount_split_flag` est partout `False` (aucune fourchette éclatée).

### Mix par sous-corpus

**Sens des opérations :**

| corpus | n | achat_% | vente_% | echange_% | autre_% |
| --- | --- | --- | --- | --- | --- |
| House électronique | 32667 | 49.7 | 49.7 | 0.6 | 0.0 |
| House OCR | 48940 | 52.7 | 46.6 | 0.7 | 0.0 |
| Sénat électronique | 6566 | 48.6 | 50.5 | 0.9 | 0.0 |
| Sénat OCR | 1679 | 54.0 | 45.8 | 0.2 | 0.0 |

![Mix achat/vente par sous-corpus](quality/mix_operations_par_corpus.png)

**Détenteur déclaré :**

| corpus | n | perso_% | conjoint_% | joint_% | enfant_% | autre_% |
| --- | --- | --- | --- | --- | --- | --- |
| House électronique | 32667 | 51.9 | 19.7 | 26.2 | 2.2 | 0.0 |
| House OCR | 48940 | 6.7 | 51.1 | 7.0 | 35.2 | 0.0 |
| Sénat électronique | 6566 | 15.7 | 41.4 | 40.1 | 2.9 | 0.0 |
| Sénat OCR | 1679 | 26.9 | 73.0 | 0.1 | 0.1 | 0.0 |

**Familles d'actifs** (le non-coté — oblig. d'État, munis, obligations — domine l'OCR du Sénat) :

| corpus | n | action_% | option_% | oblig.Etat_% | muni_% | oblig.corp_% | fonds_% | autre_% | manquant_% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 32667 | 84.6 | 1.8 | 5.9 | 0.0 | 0.0 | 0.0 | 6.1 | 1.6 |
| House OCR | 48940 | 81.7 | 0.0 | 0.8 | 0.0 | 0.1 | 3.1 | 0.6 | 13.8 |
| Sénat électronique | 6566 | 67.2 | 9.1 | 0.0 | 10.8 | 3.0 | 0.0 | 10.0 | 0.0 |
| Sénat OCR | 1679 | 12.9 | 0.0 | 0.0 | 0.8 | 2.6 | 0.0 | 69.6 | 14.2 |

![Mix de types d'actifs par sous-corpus](quality/mix_actifs_par_corpus.png)

### Secteurs & sources de résolution

| corpus | n | secteur_renseigne_% | etf_proxy_% | top_3_secteurs |
| --- | --- | --- | --- | --- |
| House électronique | 32667 | 86.6 | 86.6 | Information Technology 20%, Financials 14%, Health Care 13% |
| House OCR | 48940 | 81.0 | 81.0 | Information Technology 20%, Financials 16%, Health Care 14% |
| Sénat électronique | 6566 | 71.3 | 71.3 | Information Technology 22%, Financials 16%, Consumer Discretionary 10% |
| Sénat OCR | 1679 | 19.4 | 19.4 | Financials 21%, Communication Services 18%, Information Technology 12% |

**Origine du ticker** (`ticker_source` ; vide pour House électronique → « — ») :

| corpus | n | elec_dict_% | llm_% | explicit_% | none_% |
| --- | --- | --- | --- | --- | --- |
| House électronique | 32667 | — | — | — | — |
| House OCR | 48940 | 45.6 | 36.2 | 1.3 | 16.9 |
| Sénat électronique | 6566 | 0.5 | 0.7 | 77.1 | 20.7 |
| Sénat OCR | 1679 | 9.5 | 8.3 | 15.4 | 66.8 |

**Origine du secteur** (`sector_source`) :

| corpus | n | yfinance_% | llm_% | manual_% | none_% |
| --- | --- | --- | --- | --- | --- |
| House électronique | 32667 | 78.7 | 7.8 | 0.2 | 13.3 |
| House OCR | 48940 | 75.4 | 5.6 | 0.1 | 18.9 |
| Sénat électronique | 6566 | 62.1 | 9.0 | 0.9 | 28.0 |
| Sénat OCR | 1679 | 12.0 | 7.4 | 1.1 | 79.5 |

![Volume par secteur GICS](quality/volume_par_secteur.png)

### Montants par sous-corpus

| corpus | n | mediane_$ | moyenne_$ | P25_$ | P75_$ | P95_$ | volume_total_M$ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 32667 | 8000 | 53307 | 8000 | 15001 | 100001 | 1741.4 |
| House OCR | 48940 | 8000 | 49627 | 8000 | 32500 | 175000 | 2386.0 |
| Sénat électronique | 6566 | 8000 | 100115 | 8000 | 32500 | 375000 | 657.4 |
| Sénat OCR | 1679 | 32500 | 171021 | 8000 | 75000 | 750000 | 285.9 |

### Concentration de l'activité

| corpus | n_deposants | HHI | Gini | top10_volume_% |
| --- | --- | --- | --- | --- |
| House électronique | 234 | 662.7 | 0.877 | 68.8 |
| House OCR | 40 | 2888.3 | 0.913 | 98.7 |
| Sénat électronique | 61 | 1269.1 | 0.835 | 84.6 |
| Sénat OCR | 5 | 6388.7 | 0.695 | 100.0 |

`HHI` ∈ [0, 10000] et `Gini` ∈ [0, 1] mesurent la concentration du volume par déposant (plus c'est haut, plus quelques déposants dominent).

![Concentration du volume (Lorenz)](quality/concentration_lorenz.png)

**Top tickers par volume estimé :**

| ticker | n_trades | volume_M$ |
| --- | --- | --- |
| MSFT | 1011 | 261.3 |
| ICE | 110 | 93.4 |
| BRP | 7 | 81.8 |
| AAPL | 739 | 80.4 |
| MET | 114 | 76.2 |
| T | 338 | 63.1 |
| NVDA | 594 | 46.1 |
| DFS | 66 | 42.9 |
| AMZN | 684 | 42.3 |
| HBI | 65 | 38.3 |
| GOOGL | 599 | 29.8 |
| ADBE | 381 | 23.2 |
| AVGO | 269 | 18.1 |
| PYPL | 355 | 17.0 |
| AESI | 5 | 15.9 |

**Volume par secteur GICS :**

| secteur | n_trades | volume_M$ |
| --- | --- | --- |
| Information Technology | 14315 | 725.9 |
| Financials | 10981 | 520.7 |
| Communication Services | 5593 | 263.1 |
| Consumer Discretionary | 8309 | 259.7 |
| Health Care | 9495 | 229.7 |
| Industrials | 8476 | 196.8 |
| Energy | 3077 | 141.5 |
| Consumer Staples | 5137 | 138.5 |
| Materials | 2898 | 61.8 |
| Real Estate | 2729 | 53.6 |
| Utilities | 1274 | 30.5 |

### Profil des clusters de scan (House OCR)

| cluster | n_lignes | n_docs | date_plausible_% | ticker_% | quiver_a_le_trade_pct |
| --- | --- | --- | --- | --- | --- |
| A_tape_droit | 5957 | 59 | 99.6 | 84.2 | 88.0 |
| B_tape_tourne | 42125 | 295 | 94.7 | 82.9 | 77.9 |
| C_manuscrit | 858 | 80 | 97.4 | 88.5 | 35.3 |

A = tapé droit, B = tapé tourné, C = manuscrit. L'appariement Quiver (`quiver_a_le_trade_pct`) **chute** sur le manuscrit (≈35 %) alors qu'il reste élevé sur le tapé (≈78–88 %) : c'est notre lecture OCR des dates manuscrites qui décroche, pas la plausibilité interne (`date_plausible_%`, fenêtre 75 j, reste haute). D'où l'exclusion par défaut du cluster C.

## (a) Cohérence des dates (`disclosure_date ≥ transaction_date`)
| chamber | n | dates_parseables_pct | coherentes_pct | incoherentes | annee_txn_implausible | date_manquante |
| --- | --- | --- | --- | --- | --- | --- |
| house | 81607 | 99.8 | 99.8 | 159 | 0 | 178 |
| senate | 8245 | 99.9 | 100.0 | 3 | 0 | 7 |

**Par sous-corpus :**

| corpus | n | dates_parseables_pct | coherentes_pct | incoherentes | annee_txn_implausible | date_manquante |
| --- | --- | --- | --- | --- | --- | --- |
| House électronique | 32667 | 100.0 | 99.9 | 18 | 0 | 0 |
| House OCR | 48940 | 99.6 | 99.7 | 141 | 0 | 178 |
| Sénat électronique | 6566 | 100.0 | 100.0 | 0 | 0 | 0 |
| Sénat OCR | 1679 | 99.6 | 99.8 | 3 | 0 | 7 |

Lecture : `dates_parseables_pct` mesure les dates exploitables (le reste = OCR papier illisible) ; `coherentes_pct` = part où la divulgation suit bien la transaction. Les `incoherentes` sont surtout des divulgations amendées/antidatées réelles ; `annee_txn_implausible` isole les rares erreurs OCR de lecture d'année (année de transaction postérieure au dépôt ou antérieure à 2012), déjà incluses dans les incohérentes. Des transactions 2013–2019 apparaissent légitimement (divulgations très tardives).

## (b) Délai légal de divulgation (STOCK Act ~45 j)
| chamber | n_dates_valides | <=45j_legal_pct | 45-75j_pct | >75j_pct | negatif_pct | delai_median_j |
| --- | --- | --- | --- | --- | --- | --- |
| house | 81429 | 87.0 | 5.2 | 7.7 | 0.2 | 28 |
| senate | 8238 | 91.0 | 2.8 | 6.2 | 0.0 | 27 |

**Par sous-corpus :**

| corpus | n_dates_valides | <=45j_legal_pct | 45-75j_pct | >75j_pct | negatif_pct | delai_median_j |
| --- | --- | --- | --- | --- | --- | --- |
| House électronique | 32667 | 81.9 | 4.9 | 13.2 | 0.1 | 28 |
| House OCR | 48762 | 90.3 | 5.4 | 4.0 | 0.3 | 28 |
| Sénat électronique | 6566 | 90.6 | 1.9 | 7.5 | 0.0 | 26 |
| Sénat OCR | 1672 | 92.4 | 6.5 | 0.9 | 0.2 | 29 |

![Délai de divulgation](quality/delai_divulgation.png)

Le pipeline tolère une fenêtre de 75 j (`date_confidence`) ; le tableau isole la part strictement dans les **45 j légaux** vs la marge 45–75 j vs les retards >75 j.

**Divulgations les plus tardives (> 365 j, suspects) :**

| declarant_name | chamber | transaction_date | disclosure_date | lag_days | ticker | operation_type |
| --- | --- | --- | --- | --- | --- | --- |
| Jefferson Shreve | house | 2015-05-08 | 2025-06-22 | 3698.0 | DHR | Purchase |
| Jefferson Shreve | house | 2015-05-08 | 2025-06-22 | 3698.0 | DAL | Purchase |
| Richard W. Allen | house | 2017-02-03 | 2023-08-10 | 2379.0 |  | Purchase |
| Richard W. Allen | house | 2017-02-13 | 2023-08-10 | 2369.0 | O | Sale |
| Richard W. Allen | house | 2017-03-23 | 2023-08-10 | 2331.0 | BBT | Sale |
| Richard W. Allen | house | 2017-03-23 | 2023-08-10 | 2331.0 | BBT | Sale (Partial) |
| Richard W. Allen | house | 2017-04-27 | 2023-08-10 | 2296.0 | XOM | Sale |
| Richard W. Allen | house | 2017-04-27 | 2023-08-10 | 2296.0 | COST | Purchase |
| Richard W. Allen | house | 2017-05-16 | 2023-08-10 | 2277.0 | GE | Sale |
| Richard W. Allen | house | 2017-05-16 | 2023-08-10 | 2277.0 | FDX | Purchase |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | PCLN | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | DFS | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | CME | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | FB | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | KMX | Sale |

## (c) Distribution des montants (`amount_midpoint`)

Stats globales (USD, midpoint des fourchettes déclarées) :

```
count       88982.0
mean        56985.0
std        595298.0
min             1.0
25%          8000.0
50%          8000.0
75%         32500.0
90%         75000.0
max      75000000.0
```

Par chambre :

```
           count      mean       std     min     25%     50%      75%         max
chamber                                                                          
house    80744.0   51116.0  569184.0     1.0  8000.0  8000.0  32500.0  75000000.0
senate    8238.0  114506.0  805522.0  8000.0  8000.0  8000.0  32500.0  50000000.0
```

Par sous-corpus :

```
                      count      mean        std     min     25%      50%      75%         max
corpus                                                                                        
House électronique  32667.0   53307.0   522013.0     1.0  8000.0   8000.0  15001.0  37500000.0
House OCR           48077.0   49628.0   599121.0  8000.0  8000.0   8000.0  32500.0  75000000.0
Sénat électronique   6566.0  100115.0   632303.0  8000.0  8000.0   8000.0  32500.0  15000000.0
Sénat OCR            1672.0  171021.0  1274262.0  8000.0  8000.0  32500.0  75000.0  50000000.0
```

![Distribution des montants](quality/distribution_montants.png)

**Top 15 déposants par volume estimé (Σ midpoint) :**

| declarant_name | chamber | n_trades | volume_estime_musd |
| --- | --- | --- | --- |
| Michael T. McCaul | house | 10738 | 974.5 |
| Rohit Khanna | house | 30516 | 667.8 |
| Diana Harshbarger | house | 3124 | 464.5 |
| Darrell E. Issa | house | 20 | 250.5 |
| RICHARD BLUMENTHAL | senate | 1226 | 221.3 |
| Josh Gottheimer | house | 2942 | 209.4 |
| Jefferson Shreve | house | 631 | 191.7 |
| Scott Franklin | house | 68 | 182.1 |
| Rick Scott | senate | 266 | 167.2 |
| Nancy Pelosi | house | 147 | 139.6 |
| Suzan K. DelBene | house | 406 | 125.9 |
| Kelly Loeffler | senate | 329 | 120.9 |
| David H McCormick | senate | 293 | 69.0 |
| Scott H. Peters | house | 334 | 64.6 |
| Kevin Hern | house | 760 | 60.1 |

## (d) Coverage par congressman

320 déposants distincts. **206** ont ≥ 10 transactions (éligibles au backtest), dont **150** actifs sur ≥ 3 années.

![Top déposants](quality/top_deposants.png)

![Transactions par an](quality/transactions_par_an.png)

**Top 20 déposants (transactions, OCR%, années actives) :**

| name | our_total | our_ocr | ocr_share_pct | n_annees | premiere_annee | derniere_annee |
| --- | --- | --- | --- | --- | --- | --- |
| Rohit Khanna | 30862 | 30862 | 100 | 8 | 2019 | 2026 |
| Michael T. McCaul | 10850 | 10850 | 100 | 7 | 2020 | 2026 |
| Diana Harshbarger | 3515 | 3514 | 100 | 4 | 2021 | 2026 |
| Josh Gottheimer | 2942 | 0 | 0 | 8 | 2019 | 2026 |
| Gilbert Cisneros | 2153 | 0 | 0 | 4 | 2019 | 2026 |
| David P. Roe | 1686 | 1686 | 100 | 1 | 2020 | 2020 |
| Lisa McClain | 1532 | 109 | 7 | 3 | 2024 | 2026 |
| Thomas H Tuberville | 1369 | 0 | 0 | 5 | 2021 | 2025 |
| Daniel Goldman | 1291 | 0 | 0 | 2 | 2023 | 2025 |
| RICHARD BLUMENTHAL | 1232 | 1232 | 100 | 8 | 2019 | 2026 |
| Thomas R Carper | 923 | 0 | 0 | 6 | 2019 | 2024 |
| Susie Lee | 857 | 0 | 0 | 8 | 2019 | 2026 |
| Donald Sternoff Beyer | 822 | 0 | 0 | 8 | 2019 | 2026 |
| Kathy Manning | 803 | 0 | 0 | 5 | 2021 | 2025 |
| JOHN BOOZMAN | 768 | 379 | 49 | 8 | 2019 | 2026 |
| Thomas Suozzi | 765 | 20 | 3 | 9 | 2017 | 2026 |
| Kevin Hern | 760 | 0 | 0 | 8 | 2019 | 2026 |
| Alan S. Lowenthal | 676 | 0 | 0 | 4 | 2019 | 2022 |
| Lois Frankel | 656 | 0 | 0 | 5 | 2019 | 2023 |
| Mark Green | 653 | 0 | 0 | 6 | 2020 | 2025 |

## (e) Taux de transactions sans sortie déclarée

Achats (avec ticker) sans vente ultérieure déclarée par le même membre sur le même ticker → positions qui seraient fermées de force à +12 mois dans la stratégie.

| chamber | n_achats_avec_ticker | avec_sortie_declaree | sans_sortie_pct |
| --- | --- | --- | --- |
| house | 34562 | 26783 | 22.5 |
| senate | 2468 | 1502 | 39.1 |

**Par sous-corpus :**

| corpus | n_achats_avec_ticker | avec_sortie_declaree | sans_sortie_pct |
| --- | --- | --- | --- |
| House électronique | 14010 | 8288 | 40.8 |
| House OCR | 20552 | 18495 | 10.0 |
| Sénat électronique | 2301 | 1373 | 40.3 |
| Sénat OCR | 167 | 129 | 22.8 |

## (f) Validation externe Quiver (vérité-terrain — actions cotées)

Quiver Quantitative (agrégateur commercial) sert de **vérité-terrain indépendante**, **jamais réinjectée**. On confronte nos transactions à Quiver au niveau transaction, par **scope** (digital / OCR / les deux) — voir `common/quiver_scopes.py` pour la définition exhaustive des métriques. Trois constats chiffrés en ressortent :

**Couverture par scope et chambre** (`couverture_pct` = part des trades Quiver qu'on retrouve ; `only_ours` = nos trades absents de Quiver ; `only_quiver` = trades Quiver qu'on n'a pas) :

| chamber | scope | matched | quiver | only_ours | only_quiver | couverture_pct |
| --- | --- | --- | --- | --- | --- | --- |
| house | both | 43279.0 | 50221.0 | 13482.0 | 6942.0 | 86.2 |
| house | digital | 25784.0 | 26252.0 | 415.0 | 468.0 | 98.2 |
| house | ocr | 17583.0 | 25743.0 | 13067.0 | 8160.0 | 68.3 |
| senate | both | 4324.0 | 4349.0 | 544.0 | 25.0 | 99.4 |
| senate | digital | 4324.0 | 4349.0 | 405.0 | 25.0 | 99.4 |
| senate | ocr | 0.0 | 15.0 | 64.0 | 15.0 | 0.0 |

**1) Quiver ne couvre que les ACTIONS.** Décomposition par type d'actif (`exact_match` = même trade, même date ; `date_mismatch` = bon trade, notre date diffère ; `no_match` = absent de Quiver ; `non_equity` = muni/obligation → **hors périmètre Quiver**, ni validable ni un défaut ; `quiver_a_le_trade_pct` = exact+date_mismatch sur les actions). — **House :**

| asset_type | exact_match | date_mismatch | no_match | non_equity | total | quiver_a_le_trade_pct |
| --- | --- | --- | --- | --- | --- | --- |
| Stock | 47475 | 9301 | 8105 | 2796 | 67677 | 87.5 |
| (inconnu) | 1704 | 211 | 1015 | 4345 | 7275 | 65.4 |
| Gov Security | 5 | 0 | 23 | 2259 | 2287 | 17.9 |
| Mutual Fund | 130 | 92 | 715 | 575 | 1512 | 23.7 |
| Other | 161 | 14 | 7 | 810 | 992 | 96.2 |
| CS | 56 | 1 | 1 | 724 | 782 | 98.3 |
| Option | 492 | 7 | 83 | 0 | 582 | 85.7 |
| HN | 5 | 0 | 0 | 134 | 139 | 100.0 |
| PS | 6 | 0 | 0 | 103 | 109 | 100.0 |
| Other Investment | 2 | 0 | 0 | 61 | 63 | 100.0 |
| CT | 5 | 0 | 0 | 52 | 57 | 100.0 |
| VA | 0 | 0 | 0 | 40 | 40 |  |
| AB | 14 | 0 | 1 | 24 | 39 | 93.3 |
| Corporate Bond | 3 | 2 | 0 | 32 | 37 | 100.0 |
| OL | 5 | 0 | 0 | 28 | 33 | 100.0 |
| ET | 16 | 0 | 0 | 0 | 16 | 100.0 |
| RS | 1 | 1 | 0 | 1 | 3 | 100.0 |
| SA | 1 | 0 | 0 | 2 | 3 | 100.0 |

— **Sénat** (l'OCR y est surtout du non-coté → `non_equity`, ce qui explique l'essentiel du « Quiver ne nous voit pas » ; les `Stock`, eux, sont très bien couverts) :

| asset_type | exact_match | date_mismatch | no_match | non_equity | total | quiver_a_le_trade_pct |
| --- | --- | --- | --- | --- | --- | --- |
| Stock | 4071 | 105 | 783 | 68 | 5027 | 84.2 |
| Other | 350 | 21 | 158 | 1283 | 1812 | 70.1 |
| Municipal Security | 0 | 4 | 7 | 755 | 766 | 36.4 |
| Option | 421 | 10 | 23 | 63 | 517 | 94.9 |
| Corporate Bond | 1 | 3 | 54 | 188 | 246 | 6.9 |
| (inconnu) | 0 | 8 | 206 | 25 | 239 | 3.7 |
| Commodities/Futures Contract | 0 | 0 | 0 | 87 | 87 |  |
| Stock Option | 75 | 0 | 2 | 3 | 80 | 97.4 |
| Non-Public Stock | 0 | 0 | 2 | 58 | 60 | 0.0 |
| Cryptocurrency | 4 | 0 | 2 | 1 | 7 | 66.7 |

**2) Quiver A le papier — notre limite est la DATE de l'OCR.** Par cluster de scan (House) : `quiver_a_le_trade_pct` reste élevé même en manuscrit (Quiver possède le trade), mais la part `exact_match` (date juste) **chute** sur le manuscrit → c'est notre lecture OCR des dates manuscrites qui est faible, **pas** une cécité de Quiver au papier :

| cluster | exact_match | date_mismatch | no_match | non_equity | total | quiver_a_le_trade_pct |
| --- | --- | --- | --- | --- | --- | --- |
| B_tape_tourne | 18558 | 8653 | 7706 | 7234 | 42151 | 77.9 |
| A_tape_droit | 3784 | 630 | 600 | 943 | 5957 | 88.0 |
| C_manuscrit | 100 | 169 | 493 | 100 | 862 | 35.3 |

### Diagnostic : qui a raison ? (nous vs Quiver)

Les tableaux ci-dessus comptent *combien* de trades Quiver on retrouve. Ce diagnostic (recalculé hors-ligne par `common/quiver_diagnosis.py`, **jamais réinjecté**) tranche **pourquoi** on diffère : chaque écart reçoit un verdict — `CONCORDANT` ; `ECART_DATE` (Quiver a le trade, notre date diffère → OCR/amendement) ; `ECART_TICKER` (notre ticker diffère/manque → **notre erreur corrigible**) ; `STRUCTUREL` (non-coté, hors périmètre Quiver) ; `ON_EST_PLUS_COMPLET` (action absente de Quiver) ; et côté Quiver `MANQUANT_PAPIER`, `NON_COTE` (CUSIP/préférentielle/fragment OCR, hors périmètre) et `NOTRE_MANQUE` (dépôt **coté** qu'on n'a pas du tout). Le corpus est **dédupliqué cross-année** avant classification (une re-divulgation tardive comptait double — Sénat 8 841 → 8 245 uniques). Ce diagnostic **raffine** les tables figées 07g/07c (qui agrègent `no_match` et ne dédupliquent pas) : mêmes ordres de grandeur côté actions, mais il sépare en plus le ticker récupérable du « vraiment plus complet », et le non-coté du vrai trou.

**Synthèse côté NOUS** (part de NOS transactions par grande catégorie ; `notre_erreur_pct` = `ECART_DATE` + `ECART_TICKER`). Attention : `ECART_TICKER` mêle du **récupérable** (action sans ticker que Quiver confirme, ou ticker lisible chez Quiver) et un **artefact de collision même-jour** (notre ticker est bon mais un autre trade du même jour collisionne la clé) ; le vrai corrigible est plus petit que ce taux — voir les annexes ligne-à-ligne :

| chamber | nos_txns | concordant_pct | notre_erreur_pct | structurel_pct | on_est_plus_complet_pct |
| --- | --- | --- | --- | --- | --- |
| house | 81607 | 61.4 | 18.6 | 12.4 | 7.6 |
| senate | 8245 | 59.7 | 2.1 | 30.0 | 8.2 |

**Verdicts nous→Quiver** (chacune de NOS transactions confrontée à Quiver) :

| côté | verdict | n | pct | a_corriger |
| --- | --- | --- | --- | --- |
| nous→Quiver (house) | CONCORDANT | 50074 | 61.4 | False |
| nous→Quiver (house) | ECART_DATE | 9629 | 11.8 | True |
| nous→Quiver (house) | ECART_TICKER | 5539 | 6.8 | True |
| nous→Quiver (house) | STRUCTUREL | 10159 | 12.4 | False |
| nous→Quiver (house) | ON_EST_PLUS_COMPLET | 6206 | 7.6 | False |
| nous→Quiver (senate) | CONCORDANT | 4922 | 59.7 | False |
| nous→Quiver (senate) | ECART_DATE | 100 | 1.2 | True |
| nous→Quiver (senate) | ECART_TICKER | 71 | 0.9 | True |
| nous→Quiver (senate) | STRUCTUREL | 2472 | 30.0 | False |
| nous→Quiver (senate) | ON_EST_PLUS_COMPLET | 680 | 8.2 | False |

**Verdicts Quiver→nous** (les trades Quiver qu'on n'a pas = `only_quiver`). `NON_COTE` = un « ticker » Quiver non appariable (CUSIP, préférentielle, fragment OCR) → hors périmètre. `NOTRE_MANQUE` = le **vrai trou** (action cotée jamais captée), résiduel après filtrage du non-coté : ~10 lignes House (Pelosi UBER/INTC, Bresnahan SPY/QQQ/IWM, James AFRM…) et 3 Sénat. Tout le reste s'explique par notre date, notre ticker, ou du papier :

| côté | verdict | n | pct | a_corriger |
| --- | --- | --- | --- | --- |
| Quiver→nous (house) | ECART_DATE | 3419 | 49.2 | True |
| Quiver→nous (house) | ECART_TICKER | 2317 | 33.4 | True |
| Quiver→nous (house) | MANQUANT_PAPIER | 1066 | 15.4 | True |
| Quiver→nous (house) | NON_COTE | 132 | 1.9 | False |
| Quiver→nous (house) | NOTRE_MANQUE | 10 | 0.1 | True |
| Quiver→nous (senate) | ECART_TICKER | 22 | 88.0 | True |
| Quiver→nous (senate) | NOTRE_MANQUE | 3 | 12.0 | True |

**Couverture (Quiver→nous) et precision (nous→Quiver) par année** (scope `both` ; comble l'axe année absent des tables figées) :

| chamber | year | matched | quiver | couverture_pct | precision_pct |
| --- | --- | --- | --- | --- | --- |
| house | 2020 | 7115 | 8359 | 85.1 | 75.0 |
| house | 2021 | 5222 | 5893 | 88.6 | 63.2 |
| house | 2022 | 6075 | 7513 | 80.9 | 60.2 |
| house | 2023 | 6128 | 7567 | 81.0 | 84.7 |
| house | 2024 | 4670 | 5442 | 85.8 | 79.7 |
| house | 2025 | 9836 | 10773 | 91.3 | 90.8 |
| house | 2026 | 4233 | 4674 | 90.6 | 84.9 |
| senate | 2020 | 1251 | 1259 | 99.4 | 93.6 |
| senate | 2021 | 398 | 406 | 98.0 | 64.1 |
| senate | 2022 | 636 | 640 | 99.4 | 96.1 |
| senate | 2023 | 682 | 684 | 99.7 | 88.2 |
| senate | 2024 | 558 | 560 | 99.6 | 97.7 |
| senate | 2025 | 520 | 521 | 99.8 | 88.0 |
| senate | 2026 | 279 | 279 | 100.0 | 89.1 |

**Accord sur les trades qu'on a TOUS LES DEUX** (cellules bio×ticker×date présentes des deux côtés) — un de nos trades « concorde » s'il existe un trade Quiver de même sens (resp. même sens+montant) dans la cellule. Mesure par **appartenance ensembliste** (robuste à la granularité des lots : l'ancien `merge` cartésien sous-estimait l'accord et gonflait `n_paires`). Un désaccord = vraie erreur d'extraction sur une donnée pourtant captée, listée et **typée** (`sens`/`montant`) dans `desaccord_champ_*.csv` :

| chamber | n_paires_appariées | accord_sens_pct | accord_montant_bas_pct |
| --- | --- | --- | --- |
| house | 52258 | 95.8 | 93.1 |
| senate | 4932 | 99.8 | 99.7 |

**Top déposants `NOTRE_MANQUE`** (dépôts Quiver qu'on n'a pas du tout — à investiguer) :

| chamber | bioguide | name | n_notre_manque |
| --- | --- | --- | --- |
| house | B001327 | Rob Bresnahan | 5 |
| house | P000197 | Nancy Pelosi | 2 |
| house | J000307 | John James | 1 |
| house | S000168 | Maria Elvira Salazar | 1 |
| house | W000797 | Debbie Wasserman Schultz | 1 |
| senate | M001198 | Roger W Marshall | 3 |

Listes actionnables complètes (cas corrigibles, ligne à ligne) → `docs/quiver_validation/` (`ecart_ticker_*.csv`, `notre_manque_*.csv`, `manquant_papier_*.csv`, `desaccord_champ_*.csv` [typé sens/montant], `on_est_plus_complet_*.csv`, `quiver_non_cote_*.csv`). Hors golden.

