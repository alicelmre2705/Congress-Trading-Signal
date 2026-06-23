# Congress Trading Signal — House J1-J4 foundation

## Projet

Ce dépôt construit la fondation data officielle **House** pour le projet Ramify/QIS “Congress Trading Signal”. Le livrable couvre uniquement les jours 1 à 4 : index House, PDF PTR, manifest de complétude, audit de qualité PDF, et validation externe Quiver.

## Scope actuel

- Source officielle : House XML + PDF.
- Période : 2013–2026.
- Dépôts retenus : PTR uniquement, `FilingType = P`.
- Validation externe : Quiver 2025 uniquement.
- Livrables principaux : notebooks Jupyter courts et auditables.

## Hors scope volontaire

- Pas de Senate.
- Pas d’OCR.
- Pas d’extraction LLM massive.
- Pas de backtest.
- Pas de commissions.
- Pas de mapping GICS / ETF.
- Pas de table finale transaction par transaction.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration Quiver

Créer un fichier `.env` local non versionné :

```bash
cp .env.example .env
```

Puis renseigner :

```bash
QUIVER_API_TOKEN=...
```

Ne jamais mettre le token en dur dans un notebook ou dans `src/`.

## Ordre d’exécution des notebooks

1. `notebooks/00_setup_scope.ipynb`
2. `notebooks/01_house_index_audit.ipynb`
3. `notebooks/02_house_pdf_download_manifest.ipynb`
4. `notebooks/03_house_pdf_quality_smoke_test.ipynb`
5. `notebooks/04_quiver_access_validation_2025.ipynb`

## Fichiers produits

### Notebook 01

- `data/processed/house/house_filings_index.csv`
- `data/processed/house/house_ptr_index.csv`
- `data/processed/house/ptr_index_YYYY.csv`
- `reports/house_index_audit.md`

### Notebook 02

- `data/raw/house/ptr_pdfs/YYYY/DOCID.pdf`
- `data/audit/house_pdf_manifest.csv`
- `reports/house_download_audit.md`

### Notebook 03

- `data/audit/house_pdf_text_quality.csv`
- `data/audit/house_sample_extraction_smoke_test.csv`

### Notebook 04

- `data/audit/quiver_api_access_diagnostic.json`
- `data/external/quiver/quiver_congress_trading_2025.csv` si accès disponible
- `data/audit/quiver_house_validation_2025.csv` si accès disponible
- `reports/house_quiver_validation_report.md`

## Règles critiques

- House XML + PDF = source officielle.
- Quiver = validation externe, pas source canonique.
- `disclosure_date` = `FilingDate` XML House.
- `Notification Date` du PDF ≠ `disclosure_date` stratégique.
- Ne pas faire de backtest avant la data quality.
- Ne pas utiliser Senate dans cette phase.
- Ne jamais hardcoder de token.

## Définition du succès J+4

À J+4, on veut pouvoir dire :

> J’ai reconstruit une base House officielle, documentée et relançable. Je connais le nombre de PTR attendus, les PDF obtenus, les échecs éventuels, la qualité texte des PDF, et ce que Quiver permet réellement de vérifier avec le compte disponible.

## Prochaines étapes

Après validation House J1-J4 : extraction transactionnelle, nettoyage tickers/noms, Senate isolé, puis stratégie et backtest.
