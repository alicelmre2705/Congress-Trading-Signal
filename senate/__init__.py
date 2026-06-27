"""senate — pipeline Sénat (digital eFD + OCR papier). Actuellement AUTONOME (n'importe pas congress_core).

⚠️ ÉTAT RÉEL (cf. docs/RAPPORT_V2_ARCHI.md) : ce paquet **réimplémente localement** la logique que
`congress_core` fournit déjà à House — identité/clé/dédup (`senate.identity` : SCHEMA, natural_key,
make_matcher), montants (`senate.digital:amount_midpoint`), ticker (`senate.ticker_resolve`), secteur
(`senate.sector_enrich`), validation Quiver (`senate.quiver_audit`), OCR (`senate.ocr_engine`, figé Q1
pour reproduire le golden). Migration sur `congress_core` prévue (Palier 3) ; la logique y est quasi-identique.

`senate.digital`   : scraping eFD des PTR électroniques → parsing → identité → finalize → Quiver.
`senate.ocr`       : découverte PTR papier → Vision (cache versionné, prompt FR) → normalisation.
`senate.fusion`    : fusion digital + OCR → table FINALE 27 champs (ticker dict+LLM, secteur, dates).
`senate.identity`  : référentiel + matcher bioguide + enrichissement (logique figée Q1, reproduit le golden).
`senate.quiver_audit` : reconcile transaction-niveau (07c-f) + dédup amendements.
Données sous `data/senate/` (parité `data/house/`).
"""
