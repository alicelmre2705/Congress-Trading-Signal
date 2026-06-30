# Rapport de qualité des données — Congress Trading
> Livrable Ramify, Semaine 2. Généré par `python -m common.quality` (lecture seule des tables FINAL, aucun appel API).
**Périmètre :** 90 487 transactions FINAL (House 81 646 + Sénat 8 841)  années 2020–2026.

## Décomposition par sous-corpus

Les déclarations proviennent de **quatre sous-corpus** très différents (chambre × voie d'acquisition). Toute la suite distingue ces quatre familles, car leur qualité et leur composition diffèrent.

| corpus | n | part_pct |
| --- | --- | --- |
| House électronique | 32676 | 36.1 |
| House OCR | 48970 | 54.1 |
| Sénat électronique | 7161 | 7.9 |
| Sénat OCR | 1680 | 1.9 |

### Couverture des champs enrichis (taux de remplissage)

| corpus | n | ticker_% | secteur_% | etf_proxy_% | committee_% | identite_% | anciennete_% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 32676 | 88.6 | 86.6 | 86.6 | 74.7 | 100.0 | 100.0 |
| House OCR | 48970 | 83.1 | 81.0 | 81.0 | 94.5 | 100.0 | 100.0 |
| Sénat électronique | 7161 | 80.3 | 72.1 | 72.1 | 58.5 | 100.0 | 100.0 |
| Sénat OCR | 1680 | 33.2 | 19.4 | 19.4 | 96.1 | 100.0 | 100.0 |

`identite_%` = part rattachée à un `bioguide_id` ; `ticker`/`secteur`/`etf_proxy` sont vides pour les actifs non cotés (légitime, pas un défaut).

### Scorecard de qualité

| corpus | n | dates_coherentes_% | date_plausible_% | annee_implausible_n | montant_renseigne_% |
| --- | --- | --- | --- | --- | --- |
| House électronique | 32676 | 99.9 | — | 3 | 100.0 |
| House OCR | 48970 | 99.7 | 95.3 | 0 | 98.2 |
| Sénat électronique | 7161 | 100.0 | 85.0 | 0 | 100.0 |
| Sénat OCR | 1680 | 99.8 | 98.5 | 0 | 99.5 |

`date_plausible_%` (fenêtre 75 j) n'existe que pour les lignes OCR → « — » pour House électronique (pas de `date_confidence`). `amount_split_flag` est partout `False` (aucune fourchette éclatée).

### Mix par sous-corpus

**Sens des opérations :**

| corpus | n | achat_% | vente_% | echange_% | autre_% |
| --- | --- | --- | --- | --- | --- |
| House électronique | 32676 | 49.7 | 49.7 | 0.6 | 0.0 |
| House OCR | 48970 | 52.7 | 46.6 | 0.7 | 0.0 |
| Sénat électronique | 7161 | 48.0 | 51.2 | 0.8 | 0.0 |
| Sénat OCR | 1680 | 54.0 | 45.8 | 0.2 | 0.0 |

![Mix achat/vente par sous-corpus](quality/mix_operations_par_corpus.png)

**Détenteur déclaré :**

| corpus | n | perso_% | conjoint_% | joint_% | enfant_% | autre_% |
| --- | --- | --- | --- | --- | --- | --- |
| House électronique | 32676 | 51.9 | 19.7 | 26.2 | 2.2 | 0.0 |
| House OCR | 48970 | 6.7 | 51.1 | 7.0 | 35.2 | 0.0 |
| Sénat électronique | 7161 | 15.0 | 41.4 | 41.0 | 2.7 | 0.0 |
| Sénat OCR | 1680 | 26.8 | 73.0 | 0.1 | 0.1 | 0.0 |

**Familles d'actifs** (le non-coté — oblig. d'État, munis, obligations — domine l'OCR du Sénat) :

| corpus | n | action_% | option_% | oblig.Etat_% | muni_% | oblig.corp_% | fonds_% | autre_% | manquant_% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 32676 | 84.6 | 1.8 | 5.9 | 0.0 | 0.0 | 0.0 | 6.1 | 1.6 |
| House OCR | 48970 | 81.7 | 0.0 | 0.8 | 0.0 | 0.1 | 3.1 | 0.6 | 13.8 |
| Sénat électronique | 7161 | 68.0 | 8.3 | 0.0 | 10.5 | 2.8 | 0.0 | 10.3 | 0.0 |
| Sénat OCR | 1680 | 12.9 | 0.0 | 0.0 | 0.8 | 2.6 | 0.0 | 69.6 | 14.2 |

![Mix de types d'actifs par sous-corpus](quality/mix_actifs_par_corpus.png)

### Secteurs & sources de résolution

| corpus | n | secteur_renseigne_% | etf_proxy_% | top_3_secteurs |
| --- | --- | --- | --- | --- |
| House électronique | 32676 | 86.6 | 86.6 | Information Technology 20%, Financials 14%, Health Care 13% |
| House OCR | 48970 | 81.0 | 81.0 | Information Technology 20%, Financials 16%, Health Care 14% |
| Sénat électronique | 7161 | 72.1 | 72.1 | Information Technology 22%, Financials 16%, Consumer Discretionary 10% |
| Sénat OCR | 1680 | 19.4 | 19.4 | Financials 21%, Communication Services 18%, Information Technology 12% |

**Origine du ticker** (`ticker_source` ; vide pour House électronique → « — ») :

| corpus | n | elec_dict_% | llm_% | explicit_% | none_% |
| --- | --- | --- | --- | --- | --- |
| House électronique | 32676 | — | — | — | — |
| House OCR | 48970 | 45.6 | 36.2 | 1.3 | 16.9 |
| Sénat électronique | 7161 | 0.5 | 0.7 | 78.2 | 19.7 |
| Sénat OCR | 1680 | 9.5 | 8.3 | 15.4 | 66.8 |

**Origine du secteur** (`sector_source`) :

| corpus | n | yfinance_% | llm_% | manual_% | none_% |
| --- | --- | --- | --- | --- | --- |
| House électronique | 32676 | 78.7 | 7.8 | 0.2 | 13.3 |
| House OCR | 48970 | 75.4 | 5.6 | 0.1 | 18.9 |
| Sénat électronique | 7161 | 62.4 | 9.5 | 0.9 | 27.2 |
| Sénat OCR | 1680 | 12.0 | 7.4 | 1.1 | 79.5 |

![Volume par secteur GICS](quality/volume_par_secteur.png)

### Montants par sous-corpus

| corpus | n | mediane_$ | moyenne_$ | P25_$ | P75_$ | P95_$ | volume_total_M$ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 32676 | 8000 | 53753 | 8000 | 15001 | 100001 | 1756.5 |
| House OCR | 48970 | 8000 | 49624 | 8000 | 32500 | 175000 | 2386.0 |
| Sénat électronique | 7161 | 8000 | 96813 | 8000 | 32500 | 375000 | 693.3 |
| Sénat OCR | 1680 | 32500 | 171021 | 8000 | 75000 | 750000 | 285.9 |

### Concentration de l'activité

| corpus | n_deposants | HHI | Gini | top10_volume_% |
| --- | --- | --- | --- | --- |
| House électronique | 234 | 670.7 | 0.878 | 69.0 |
| House OCR | 40 | 2888.3 | 0.913 | 98.7 |
| Sénat électronique | 61 | 1300.2 | 0.837 | 85.0 |
| Sénat OCR | 5 | 6388.7 | 0.695 | 100.0 |

`HHI` ∈ [0, 10000] et `Gini` ∈ [0, 1] mesurent la concentration du volume par déposant (plus c'est haut, plus quelques déposants dominent).

![Concentration du volume (Lorenz)](quality/concentration_lorenz.png)

**Top tickers par volume estimé :**

| ticker | n_trades | volume_M$ |
| --- | --- | --- |
| MSFT | 1017 | 261.5 |
| ICE | 110 | 93.4 |
| BRP | 7 | 81.8 |
| AAPL | 747 | 80.7 |
| MET | 115 | 76.2 |
| T | 348 | 63.2 |
| NVDA | 597 | 46.1 |
| DFS | 66 | 42.9 |
| AMZN | 686 | 42.5 |
| HBI | 70 | 38.5 |
| GOOGL | 600 | 29.8 |
| ADBE | 384 | 23.3 |
| AVGO | 269 | 18.1 |
| PYPL | 363 | 17.3 |
| AESI | 5 | 15.9 |

**Volume par secteur GICS :**

| secteur | n_trades | volume_M$ |
| --- | --- | --- |
| Information Technology | 14401 | 727.8 |
| Financials | 11049 | 522.1 |
| Communication Services | 5645 | 264.5 |
| Consumer Discretionary | 8350 | 261.1 |
| Health Care | 9548 | 230.7 |
| Industrials | 8520 | 197.6 |
| Energy | 3141 | 142.7 |
| Consumer Staples | 5171 | 139.2 |
| Materials | 2926 | 62.4 |
| Real Estate | 2746 | 53.9 |
| Utilities | 1278 | 30.5 |

### Profil des clusters de scan (House OCR)

| cluster | n_lignes | n_docs | date_plausible_% | ticker_% | quiver_a_le_trade_pct |
| --- | --- | --- | --- | --- | --- |
| A_tape_droit | 5957 | 59 | 99.6 | 84.2 | 88.0 |
| B_tape_tourne | 42151 | 295 | 94.7 | 82.8 | 77.9 |
| C_manuscrit | 862 | 81 | 97.4 | 88.4 | 35.3 |

A = tapé droit, B = tapé tourné, C = manuscrit. L'appariement Quiver (`quiver_a_le_trade_pct`) **chute** sur le manuscrit (≈35 %) alors qu'il reste élevé sur le tapé (≈78–88 %) : c'est notre lecture OCR des dates manuscrites qui décroche, pas la plausibilité interne (`date_plausible_%`, fenêtre 75 j, reste haute). D'où l'exclusion par défaut du cluster C.

## (a) Cohérence des dates (`disclosure_date ≥ transaction_date`)
| chamber | n | dates_parseables_pct | coherentes_pct | incoherentes | annee_txn_implausible | date_manquante |
| --- | --- | --- | --- | --- | --- | --- |
| house | 81646 | 99.8 | 99.8 | 162 | 3 | 204 |
| senate | 8841 | 99.9 | 100.0 | 3 | 0 | 8 |

**Par sous-corpus :**

| corpus | n | dates_parseables_pct | coherentes_pct | incoherentes | annee_txn_implausible | date_manquante |
| --- | --- | --- | --- | --- | --- | --- |
| House électronique | 32676 | 100.0 | 99.9 | 21 | 3 | 0 |
| House OCR | 48970 | 99.6 | 99.7 | 141 | 0 | 204 |
| Sénat électronique | 7161 | 100.0 | 100.0 | 0 | 0 | 0 |
| Sénat OCR | 1680 | 99.5 | 99.8 | 3 | 0 | 8 |

Lecture : `dates_parseables_pct` mesure les dates exploitables (le reste = OCR papier illisible) ; `coherentes_pct` = part où la divulgation suit bien la transaction. Les `incoherentes` sont surtout des divulgations amendées/antidatées réelles ; `annee_txn_implausible` isole les rares erreurs OCR de lecture d'année (année de transaction postérieure au dépôt ou antérieure à 2012), déjà incluses dans les incohérentes. Des transactions 2013–2019 apparaissent légitimement (divulgations très tardives).

## (b) Délai légal de divulgation (STOCK Act ~45 j)
| chamber | n_dates_valides | <=45j_legal_pct | 45-75j_pct | >75j_pct | negatif_pct | delai_median_j |
| --- | --- | --- | --- | --- | --- | --- |
| house | 81442 | 86.9 | 5.2 | 7.7 | 0.2 | 28 |
| senate | 8833 | 84.9 | 2.8 | 12.3 | 0.0 | 28 |

**Par sous-corpus :**

| corpus | n_dates_valides | <=45j_legal_pct | 45-75j_pct | >75j_pct | negatif_pct | delai_median_j |
| --- | --- | --- | --- | --- | --- | --- |
| House électronique | 32676 | 81.9 | 4.9 | 13.2 | 0.1 | 28 |
| House OCR | 48766 | 90.3 | 5.4 | 4.0 | 0.3 | 28 |
| Sénat électronique | 7161 | 83.1 | 1.9 | 15.0 | 0.0 | 27 |
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
| Richard W. Allen | house | 2017-03-23 | 2023-08-10 | 2331.0 | BBT | Sale (Partial) |
| Richard W. Allen | house | 2017-03-23 | 2023-08-10 | 2331.0 | BBT | Sale |
| Richard W. Allen | house | 2017-04-27 | 2023-08-10 | 2296.0 | COST | Purchase |
| Richard W. Allen | house | 2017-04-27 | 2023-08-10 | 2296.0 | XOM | Sale |
| Richard W. Allen | house | 2017-05-16 | 2023-08-10 | 2277.0 | GE | Sale |
| Richard W. Allen | house | 2017-05-16 | 2023-08-10 | 2277.0 | FDX | Purchase |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | DFS | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | BIDU | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | CERN | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | KMX | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | GOOGL | Sale |

## (c) Distribution des montants (`amount_midpoint`)

Stats globales (USD, midpoint des fourchettes déclarées) :

```
count       89590.0
mean        57168.0
std        595562.0
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
house    80757.0   51295.0  571564.0     1.0  8000.0  8000.0  32500.0  75000000.0
senate    8833.0  110860.0  779507.0  8000.0  8000.0  8000.0  32500.0  50000000.0
```

Par sous-corpus :

```
                      count      mean        std     min     25%      50%      75%         max
corpus                                                                                        
House électronique  32676.0   53754.0   528450.0     1.0  8000.0   8000.0  15001.0  37500000.0
House OCR           48081.0   49624.0   599096.0  8000.0  8000.0   8000.0  32500.0  75000000.0
Sénat électronique   7161.0   96814.0   607893.0  8000.0  8000.0   8000.0  32500.0  15000000.0
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
| Jefferson Shreve | house | 632 | 206.7 |
| Rick Scott | senate | 306 | 186.8 |
| Scott Franklin | house | 68 | 182.1 |
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
| Michael T. McCaul | 10876 | 10876 | 100 | 7 | 2020 | 2026 |
| Diana Harshbarger | 3515 | 3514 | 100 | 4 | 2021 | 2026 |
| Josh Gottheimer | 2942 | 0 | 0 | 8 | 2019 | 2026 |
| Gilbert Cisneros | 2153 | 0 | 0 | 4 | 2019 | 2026 |
| David P. Roe | 1686 | 1686 | 100 | 1 | 2020 | 2020 |
| Lisa McClain | 1532 | 109 | 7 | 3 | 2024 | 2026 |
| Thomas H Tuberville | 1369 | 0 | 0 | 5 | 2021 | 2025 |
| Daniel Goldman | 1291 | 0 | 0 | 2 | 2023 | 2025 |
| RICHARD BLUMENTHAL | 1233 | 1233 | 100 | 8 | 2019 | 2026 |
| Thomas R Carper | 1113 | 0 | 0 | 6 | 2019 | 2024 |
| Susie Lee | 857 | 0 | 0 | 8 | 2019 | 2026 |
| Donald Sternoff Beyer | 822 | 0 | 0 | 8 | 2019 | 2026 |
| Kathy Manning | 803 | 0 | 0 | 5 | 2021 | 2025 |
| JOHN BOOZMAN | 775 | 379 | 49 | 8 | 2019 | 2026 |
| Thomas Suozzi | 766 | 20 | 3 | 9 | 2017 | 2026 |
| Kevin Hern | 760 | 0 | 0 | 8 | 2019 | 2026 |
| David A Perdue , Jr | 711 | 0 | 0 | 2 | 2019 | 2020 |
| Alan S. Lowenthal | 676 | 0 | 0 | 4 | 2019 | 2022 |
| Lois Frankel | 656 | 0 | 0 | 5 | 2019 | 2023 |

## (e) Taux de transactions sans sortie déclarée

Achats (avec ticker) sans vente ultérieure déclarée par le même membre sur le même ticker → positions qui seraient fermées de force à +12 mois dans la stratégie.

| chamber | n_achats_avec_ticker | avec_sortie_declaree | sans_sortie_pct |
| --- | --- | --- | --- |
| house | 34565 | 26783 | 22.5 |
| senate | 2689 | 1625 | 39.6 |

**Par sous-corpus :**

| corpus | n_achats_avec_ticker | avec_sortie_declaree | sans_sortie_pct |
| --- | --- | --- | --- |
| House électronique | 14013 | 8288 | 40.9 |
| House OCR | 20552 | 18495 | 10.0 |
| Sénat électronique | 2522 | 1496 | 40.7 |
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

Les tableaux ci-dessus comptent *combien* de trades Quiver on retrouve. Ce diagnostic (recalculé hors-ligne par `common/quiver_diagnosis.py`, **jamais réinjecté**) tranche **pourquoi** on diffère : chaque écart reçoit un verdict — `CONCORDANT` ; `ECART_DATE` (Quiver a le trade, notre date diffère → OCR/amendement) ; `ECART_TICKER` (notre ticker diffère/manque → **notre erreur corrigible**) ; `STRUCTUREL` (non-coté, hors périmètre Quiver) ; `ON_EST_PLUS_COMPLET` (action absente de Quiver) ; et côté Quiver `MANQUANT_PAPIER` / `NOTRE_MANQUE` (dépôt qu'on n'a pas du tout). Les sommes reproduisent **exactement** les tables figées (07g pour le côté nous, 07c pour `only_quiver`).

**Synthèse côté NOUS** (part de NOS transactions par grande catégorie ; `notre_erreur_pct` = date OCR + ticker, corrigible) :

| chamber | nos_txns | concordant_pct | notre_erreur_pct | structurel_pct | on_est_plus_complet_pct |
| --- | --- | --- | --- | --- | --- |
| house | 81646 | 61.3 | 16.4 | 14.7 | 7.6 |
| senate | 8841 | 55.7 | 2.4 | 28.6 | 13.3 |

**Verdicts nous→Quiver** (chacune de NOS transactions confrontée à Quiver) :

| côté | verdict | n | pct | a_corriger |
| --- | --- | --- | --- | --- |
| nous→Quiver (house) | CONCORDANT | 50081 | 61.3 | False |
| nous→Quiver (house) | ECART_DATE | 9629 | 11.8 | True |
| nous→Quiver (house) | ECART_TICKER | 3741 | 4.6 | True |
| nous→Quiver (house) | STRUCTUREL | 11986 | 14.7 | False |
| nous→Quiver (house) | ON_EST_PLUS_COMPLET | 6209 | 7.6 | False |
| nous→Quiver (senate) | CONCORDANT | 4922 | 55.7 | False |
| nous→Quiver (senate) | ECART_DATE | 151 | 1.7 | True |
| nous→Quiver (senate) | ECART_TICKER | 63 | 0.7 | True |
| nous→Quiver (senate) | STRUCTUREL | 2531 | 28.6 | False |
| nous→Quiver (senate) | ON_EST_PLUS_COMPLET | 1174 | 13.3 | False |

**Verdicts Quiver→nous** (les trades Quiver qu'on n'a pas = `only_quiver` = ce que Quiver a et nous non). `NOTRE_MANQUE` = le seul **vrai trou** (dépôt jamais capté) ; tout le reste s'explique par notre date, notre ticker, ou du papier :

| côté | verdict | n | pct | a_corriger |
| --- | --- | --- | --- | --- |
| Quiver→nous (house) | ECART_DATE | 3418 | 49.2 | True |
| Quiver→nous (house) | ECART_TICKER | 2316 | 33.4 | True |
| Quiver→nous (house) | MANQUANT_PAPIER | 1092 | 15.7 | True |
| Quiver→nous (house) | NOTRE_MANQUE | 116 | 1.7 | True |
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

**Accord sur les trades qu'on a TOUS LES DEUX** (paires appariées bio×ticker×date) — un désaccord ici = notre erreur d'extraction sur une donnée pourtant captée :

| chamber | n_paires_appariées | accord_sens_pct | accord_montant_bas_pct |
| --- | --- | --- | --- |
| house | 72907 | 91.9 | 88.8 |
| senate | 7172 | 93.3 | 87.7 |

`accord_montant_bas_pct` est **sous-estimé** par un artefact connu : quand un membre trade le même ticker le même jour à deux montants, le merge bio×ticker×date produit un appariement croisé (cf. `note` du `07d` Sénat). Le sens, lui, est robuste.

**Top déposants `NOTRE_MANQUE`** (dépôts Quiver qu'on n'a pas du tout — à investiguer) :

| chamber | bioguide | name | n_notre_manque |
| --- | --- | --- | --- |
| house | A000372 | Richard W. Allen | 33 |
| house | Y000067 | Rudy Yakym | 28 |
| house | F000450 | Virginia Foxx | 18 |
| house | B001327 | Rob Bresnahan | 5 |
| house | G000591 | Michael Patrick Guest | 4 |
| house | B000740 | Stephanie Bice | 3 |
| house | B001325 | Sheri Biggs | 3 |
| house | C001068 | Steve Cohen | 2 |
| senate | M001198 | Roger W Marshall | 3 |

Listes actionnables complètes (cas corrigibles, ligne à ligne) → `docs/quiver_validation/` (`ecart_ticker_*.csv`, `notre_manque_*.csv`, `manquant_papier_*.csv`, `desaccord_champ_*.csv`, `on_est_plus_complet_*.csv`). Hors golden.

