"""senate — pipeline Sénat (digital eFD + OCR papier). N'importe le cœur QUE pour le secteur.

⚠️ ÉTAT RÉEL (cf. docs/RAPPORT_V2_ARCHI.md) : seul le secteur est mutualisé — `senate.sector_enrich`
est un **shim** qui délègue à `common.sector_enrich`. Le reste **réimplémente localement** une
logique qui DIVERGE vraiment de House : identité/clé/dédup (`senate.identity` : SCHEMA, natural_key,
make_matcher), montants (`senate.digital:amount_midpoint`), ticker (`senate.ticker`, prompt ≠
House), validation Quiver (`senate.quiver`, `reconcile` plus riche), OCR (`senate.ocr_engine`, figé
Q1 pour reproduire le golden). Une unification plus poussée a été examinée puis écartée (divergence
légitime, pas duplication accidentelle).

`senate.digital`   : scraping eFD des PTR électroniques → parsing → identité → finalize → Quiver.
`senate.ocr`       : découverte PTR papier → Vision (cache versionné, prompt FR) → normalisation.
`senate.fusion`    : fusion digital + OCR → table FINALE 27 champs (ticker dict+LLM, secteur, dates).
`senate.identity`  : référentiel + matcher bioguide + enrichissement (logique figée Q1, reproduit le golden).
`senate.quiver` : reconcile transaction-niveau (07c-f) + dédup amendements.
Données sous `data/senate/` (parité `data/house/`).
"""
