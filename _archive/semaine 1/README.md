# Congress Trading Signal — pipeline données (semaine 1)

Pipeline transparent et relançable pour constituer une table **propre et structurée** des transactions boursières déclarées par les membres du Congrès US (House + Sénat), prête pour un futur backtest.

**Principe :** tout le code de transformation vit **dans les notebooks** (inspectable) ; aucune dépendance à une API boîte noire comme source. Quiver sert **uniquement** de vérification externe.

## Structure
```
notebooks/   00→09, exécutés dans l'ordre (cellules courtes, chacune précédée d'un guide)
docs/        analyse de l'existant + plan d'attaque
data/        reference/ (référentiel) · processed/ (sorties) · raw/ external/ audit/ (à remplir)
reports/     EXECUTION_REPORT.md (à lire en premier) · data_quality.md
```

## Installation
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Exécution (dans l'ordre)
| # | Notebook | Sortie | Réseau requis |
|---|---|---|---|
| 00 | setup_scope | config, checkpoint §105(c) | — |
| 01 | reference_legislators | `data/reference/legislators.csv` | theunitedstates.io |
| 02 | house_index | index PTR House | disclosures-clerk.house.gov |
| 03 | house_download | PDF + audit qualité | disclosures-clerk.house.gov |
| 04 | house_parse | `house_transactions.csv` | — |
| 05 | senate_openset | `senate_transactions.csv` | github.com |
| 06 | senate_efd_provenance | vérif. provenance (échantillons manuels) | — |
| 07 | unify_clean | **`congress_transactions.csv` (+ parquet)** | — |
| 08 | validation_quiver | `reports/validation_report.md` | api.quiverquant.com (+ token) |
| 09 | data_quality_report | `reports/data_quality.md` | — |

## État des données livrées
Les CSV dans `data/` sont issus d'un **run réel partiel** (Sénat + référentiel + unification + qualité).
La moitié **House** et la **validation Quiver** sont à générer sur ta machine. Détails et constats : **`reports/EXECUTION_REPORT.md`**.

## Schéma de la table canonique
source · provenance · bioguide_id · declarant_name · chamber · party · state_district ·
committee_membership · committees_key_flag · transaction_date · **disclosure_date** ·
ticker · asset_description · asset_type · operation_type · amount_range · amount_midpoint ·
owner · doc_id · source_url · natural_key_hash
