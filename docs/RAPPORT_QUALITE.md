# Rapport de qualité des données — Congress Trading
> Livrable Ramify, Semaine 2. Généré par `python -m congress_core.quality` (lecture seule des tables FINAL, aucun appel API).
**Périmètre :** 90 487 transactions FINAL (House 81 646 + Sénat 8 841)  années 2020–2026.

## (a) Cohérence des dates (`disclosure_date ≥ transaction_date`)
| chamber | n | dates_parseables_pct | coherentes_pct | incoherentes | annee_txn_implausible | date_manquante |
| --- | --- | --- | --- | --- | --- | --- |
| house | 81646 | 99.8 | 99.8 | 162 | 3 | 204 |
| senate | 8841 | 99.9 | 100.0 | 3 | 0 | 8 |

Lecture : `dates_parseables_pct` mesure les dates exploitables (le reste = OCR papier illisible) ; `coherentes_pct` = part où la divulgation suit bien la transaction. Les `incoherentes` sont surtout des divulgations amendées/antidatées réelles ; `annee_txn_implausible` isole les rares erreurs OCR de lecture d'année (année de transaction postérieure au dépôt ou antérieure à 2012), déjà incluses dans les incohérentes. Des transactions 2013–2019 apparaissent légitimement (divulgations très tardives).

## (b) Délai légal de divulgation (STOCK Act ~45 j)
| chamber | n_dates_valides | <=45j_legal_pct | 45-75j_pct | >75j_pct | negatif_pct | delai_median_j |
| --- | --- | --- | --- | --- | --- | --- |
| house | 81442 | 86.9 | 5.2 | 7.7 | 0.2 | 28 |
| senate | 8833 | 84.9 | 2.8 | 12.3 | 0.0 | 28 |

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

