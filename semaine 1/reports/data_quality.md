# Rapport de qualité — congress_transactions

Généré : 2026-06-23T21:14:28+00:00

> ⚠️ Périmètre de CE run : **Sénat uniquement** (socle ouvert). La moitié House se génère sur ta machine (notebooks 02→04, sites .gov non accessibles depuis le sandbox).

- Transactions : 6933
- Déclarants uniques : 53
- Achats / Ventes : 3539 / 3312

## Couverture (source x an)
```
source           senate
disclosure_date        
2014                594
2015                896
2016                806
2017               1137
2018               1021
2019                972
2020               1435
2021                 72
```

## Champs garantis — valeurs manquantes
```
{
  "declarant_name": 0,
  "chamber": 0,
  "transaction_date": 0,
  "disclosure_date": 0,
  "ticker": 1073,
  "operation_type": 0,
  "amount_midpoint": 0
}
```

## Frontière de complétude
- Sénat : socle ouvert (Senate Stock Watcher, daily summaries), **s'arrête ~mars 2021**.
- Queue 2021→aujourd'hui : à compléter (kadoa / eFD).
- Sans ticker : 1073 lignes (obligations/options/fonds) → backlog/résolution.
- Commissions : Congrès actuel uniquement.
