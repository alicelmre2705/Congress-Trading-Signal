"""senate — pipeline Sénat (digital eFD + OCR papier) bâti sur congress_core.

`senate.digital`   : scraping eFD des PTR électroniques → parsing → identité → finalize → Quiver.
`senate.ocr`       : découverte PTR papier → Vision (cache versionné, prompt FR) → normalisation.
`senate.fusion`    : fusion digital + OCR → table FINALE 27 champs (ticker dict+LLM, secteur, dates).
`senate.identity`  : référentiel + matcher bioguide + enrichissement (logique figée Q1, reproduit le golden).
`senate.quiver_audit` : reconcile transaction-niveau (07c-f) + dédup amendements.
`senate.ocr_engine`/`senate.sector_enrich`/`senate.ticker_resolve` : moteurs réutilisés tels quels.
Toute la logique partageable vit dans `congress_core` ; ici = orchestration + spécifiques Sénat.
Données sous `data/senate/` (parité `data/house/`).
"""
