# Données de référence de la V1 House (autonomie totale)

| fichier | provenance | rôle |
|---|---|---|
| `index_instantane/{Y}FD.xml` | disclosures-clerk.house.gov, figé début juillet 2026 | la liste officielle des dépôts — IRREMPLAÇABLE : le site purge les index > ~6 ans (2014 : 2 788 → 11) |
| `legislators-{current,historical}.yaml` | projet public congress-legislators | noms, bioguide, mandats (état/district/dates) |
| `ticker_sector_map.csv` | construit sur le corpus PTR (ancien pipeline) | classe actions / ETF (les ETF sont exemptés de PTR) |

Le notebook `../V1_House.ipynb` ne lit QUE ce dossier et le web officiel.
La comparaison §12 (audit de l'ancien pipeline) lit en plus `../../00_recuperation_donnees/` —
si ce dépôt disparaît, seul §12 saute, le pipeline V1 fonctionne.
