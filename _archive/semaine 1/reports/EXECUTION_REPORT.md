# Rapport d'exécution — semaine 1

Généré : 2026-06-23T21:14:28+00:00

## Ce que j'ai pu exécuter **réellement** (sources GitHub accessibles)
| Notebook | Résultat réel |
|---|---|
| 01 référentiel | **12 767** législateurs · 528 avec commission (Congrès actuel) · 197 sur commission clé |
| 05 Sénat (daily summaries) | **8 030** transactions · 1 667 sans ticker · **bioguide fourni à 100%** |
| 07 unification | 8 030 → **6 933** après dédup · **BioGuideID 100%** · 53 déclarants |
| 09 qualité | voir `data_quality.md` (achats 3539 / ventes 3312) |

## Ce que je **n'ai pas pu** exécuter dans ce sandbox
- **02-03-04 House** : `disclosures-clerk.house.gov` est bloqué ici. Le **parser (04) est validé empiriquement** sur un vrai PTR Pelosi (GOOGL en options, AAPL vente partielle, NVDA, PANW — bons types/dates/montants).
- **08 Quiver** : `api.quiverquant.com` bloqué + pas de token dans cet environnement.
- **06 provenance eFD** : nécessite des dépôts eFD que **tu** télécharges manuellement (volontaire, pas de scraping).

## À exécuter sur ta machine
1. `02 → 04` : moitié House complète (~8 000 PDF). Mesure le **vrai taux de parsing** sur le corpus.
2. `08` : validation Quiver avec ton token (`QUIVER_API_TOKEN`).
3. `theunitedstates.io` (notebook 01) fonctionne chez toi ; il n'est bloqué qu'ici (sinon miroir GitHub YAML).

## Constats data-driven (à challenger ensemble)
1. **`disclosure_date` absente** de `all_transactions.json` → **résolu** via `all_daily_summaries.json` (`date_recieved`). C'est LA date anti look-ahead.
2. **Identité** : 54% par nom seul → **100%** en utilisant le `bioguide` fourni par les daily summaries.
3. **`chamber`** : corrigé (depuis la source, plus de NaN).
4. **Fraîcheur Sénat** : le socle ouvert **s'arrête ~mars 2021** → queue 2021-2026 manquante (kadoa/eFD).
5. **~15% sans ticker** (1 073) : obligations/options/fonds → backlog/résolution.
6. **Dédup** : 8 030 → 6 933 (1 097 fusionnées). La clé naturelle n'inclut pas d'index intra-dépôt : à vérifier qu'on ne fusionne pas des trades distincts identiques le même jour.

## Points ouverts (semaine 1)
- **§105(c)** : usage commercial des déclarations (à escalader à la direction/juridique).
- Définition de **complétude** retenue (ère électronique, niveau Member, backlog documenté).
- Choix **queue récente** : kadoa vs eFD.
- Règle de **déduplication** (cf. point 6).
