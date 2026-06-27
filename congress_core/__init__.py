"""congress_core — logique métier du pipeline Congress Trading.

ÉTAT RÉEL de la consolidation (refonte en cours — cf. docs/RAPPORT_V2_ARCHI.md) :
  • PARTAGÉ par les deux chambres : `pipeline` (orchestrateur), `enrich_tenure` (years_in_office),
    `quality` (5 contrôles) — tournent sur les FINAL House ET Sénat.
  • Utilisé PAR HOUSE (extraction/transformation) : `identity`, `schema`, `amounts`, `tickers`,
    `sector_enrich`. (`house/` garde en propre sa fusion, son OCR Vision et son `validate_quiver`.)
  • Le SÉNAT n'importe le cœur QUE pour `sector_enrich` (via un shim mince) ; le reste de sa logique
    (identité, montants, ticker, Quiver, OCR) reste réimplémenté localement dans `senate/` — par
    divergence légitime (Quiver/ticker/OCR diffèrent vraiment) ou choix figé pour le golden. Une
    unification plus poussée a été examinée puis écartée (cf. docs/RAPPORT_V2_ARCHI.md).

Modules :
    identity     ★ Doc ID → bioguide (Reference, make_matcher, enrich_identity)
    schema       SCHEMA + natural_key_hash + dédup per-lot
    tickers      normalisation / récupération ticker + asset_type
    amounts      fourchettes $, midpoint, owner, operation_type (par chambre)
    quiver       fetch + reconcile (utilisé par quality/tests ; House a son propre validate_quiver)
    crosscheck   triangulation digital (Kadoa, Stock Watcher) + statut/déposant (via quality)
    vision_ocr   rendu image + deskew + appel Vision + cache versionné (prévu : moteur OCR unique — Palier 3 ;
                 actuellement utilisé par les tests, pas encore branché en prod)
    sector_enrich GICS → ETF (importé par House ET par le shim Sénat)
"""

__version__ = "0.1.0"
