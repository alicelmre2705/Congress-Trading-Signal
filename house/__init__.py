"""house — pipeline House (digital + OCR), bâti sur congress_core.

`house.digital` : index XML → manifest → parse_ptr → identité → finalize → validation Quiver.
`house.ocr`     : census A/B/C → Vision (cache versionné) → enrichissement → fusion digital+OCR.

House importe `congress_core` pour identity, schema, amounts, tickers, sector_enrich. Restent LOCAUX à
`house/` : la fusion digital+OCR, le moteur OCR Vision (`house.ocr`) et `house.digital:validate_quiver`
(cf. docs/RAPPORT_V2_ARCHI.md).
"""
