"""house — pipeline Chambre, modulaire et symétrique de `senate/`.

Modules (dans l'ordre du pipeline) :
    digital   index XML → manifest → parse_ptr → identité → finalize → validation Quiver
    ocr       census A/B/C → Vision (cache versionné) → enrichissement → fusion digital+OCR
    identity  matcher bioguide House (make_matcher) ; le référentiel partagé est dans congress_core.reference
    amounts   fourchettes $, midpoint, owner, operation_type (House)
    tickers   normalisation / récupération ticker + asset_type (House)
    quiver    référence de réconciliation Quiver (la validation prod « brute » 07/07b vit dans
              `digital.py:validate_quiver`)
    echantillon  ⚠️ outil hors-pipeline (pilote OCR)

House n'importe de congress_core que l'universel : `schema`, `reference`, `sector_enrich`.
"""
