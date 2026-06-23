# Deliverables

Livrables créés pour la phase House J1–J4 + validation Quiver.

## Notebooks

1. `notebooks/00_setup_scope.ipynb` — setup, scope, dossiers, token check sans affichage.
2. `notebooks/01_house_index_audit.ipynb` — download/parsing XML House 2013–2026, filtre `FilingType = P`, index PTR.
3. `notebooks/02_house_pdf_download_manifest.ipynb` — téléchargement PDF PTR, manifest de complétude, checkpoint.
4. `notebooks/03_house_pdf_quality_smoke_test.ipynb` — audit qualité PDF/texte, smoke test regex sur échantillon.
5. `notebooks/04_quiver_access_validation_2024.ipynb` — diagnostic Quiver, normalisation, comparaison House/Quiver 2024.

## Code réutilisable

- `src/house_index.py`
- `src/house_download.py`
- `src/pdf_quality.py`
- `src/quiver_client.py`
- `src/utils.py`

## Documentation

- `README.md` — installation, ordre d’exécution, règles critiques.
- `docs/00_scope.md` — scope et hors-scope.
- `docs/01_runbook.md` — ordre d’exécution.
- `docs/02_quiver_security.md` — sécurité du token Quiver.

## Configuration

- `.env.example`
- `.gitignore`
- `requirements.txt`

## Remarque sécurité

Aucun token Quiver réel n’est présent dans le repo. Le code lit uniquement `QUIVER_API_TOKEN` depuis l’environnement.
