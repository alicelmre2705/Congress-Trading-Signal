# Runbook

Exécuter les notebooks dans cet ordre depuis la racine du projet.

1. `notebooks/00_setup_scope.ipynb`
2. `notebooks/01_house_index_audit.ipynb`
3. `notebooks/02_house_pdf_download_manifest.ipynb`
4. `notebooks/03_house_pdf_quality_smoke_test.ipynb`
5. `notebooks/04_quiver_access_validation_2025.ipynb`

## Contrôles attendus

- `house_ptr_index.csv` existe et contient les PTR officiels.
- `house_pdf_manifest.csv` indique les PDF attendus, obtenus, manquants et invalides.
- `house_pdf_text_quality.csv` mesure la qualité texte des PDF.
- Le rapport Quiver documente l’accès réel et les divergences sans modifier House.

## Test rapide

Dans le notebook 02, régler `MAX_FILES = 20` pour tester le téléchargement sur un petit échantillon avant le run complet. Pour le run complet, laisser `MAX_FILES = None`.
