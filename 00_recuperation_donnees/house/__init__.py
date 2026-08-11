"""house — pipeline Chambre, modulaire et symétrique de `senate/`.

Modules (dans l'ordre du pipeline) :
    acquire   étape 0, à la demande : télécharge index {Y}FD.xml + PDF du Clerk (idempotent —
              la source primaire 2014-2026 est déjà embarquée dans data/house/)
    digital   index XML → manifest → parse_ptr → identité → finalize → validation Quiver
    classify_scans  classement des scans par cluster A/B/C (census)
    ocr       census A/B/C → Vision (cache versionné) → enrichissement → fusion digital+OCR
    identity  matcher bioguide House (make_matcher) ; le référentiel partagé est dans common.reference
    amounts   fourchettes $, midpoint, owner, operation_type (House)
    tickers   normalisation / récupération ticker + asset_type (House)
    quiver    référence de réconciliation Quiver (la validation prod « brute » 07/07b vit dans
              `digital.py:validate_quiver`)
    echantillon  ⚠️ outil hors-pipeline (pilote OCR)

House n'importe de common que l'universel : `schema`, `reference`, `sector_enrich`.
"""
