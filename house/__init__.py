"""house — pipeline House (digital + OCR) bâti sur congress_core.

`house.digital` : index XML → manifest → parse_ptr → identité → finalize → validation Quiver.
`house.ocr`     : census A/B/C → Vision (cache versionné) → enrichissement → fusion digital+OCR.
Toute la logique partagée vit dans `congress_core` ; ici = orchestration spécifique House.
"""
