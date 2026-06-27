"""congress_core — logique métier du pipeline Congress Trading.

ÉTAT RÉEL de la consolidation (refonte en cours — cf. docs/RAPPORT_V2_ARCHI.md) :
  • PARTAGÉ par les deux chambres : `pipeline` (orchestrateur), `enrich_tenure` (years_in_office),
    `quality` (5 contrôles) — tournent sur les FINAL House ET Sénat.
  • Utilisé PAR HOUSE (extraction/transformation) : `identity`, `schema`, `amounts`, `tickers`,
    `sector_enrich`. (`house/` garde en propre sa fusion, son OCR Vision et son `validate_quiver`.)
  • Le SÉNAT n'importe PAS encore congress_core : il réimplémente cette logique localement dans
    `senate/`. La migration est prévue (Palier 3) — le cœur est conçu pour l'absorber (le paramètre
    `chamber_priority` de `make_matcher` est déjà réservé à cela).

Modules :
    identity     ★ Doc ID → bioguide (Reference, make_matcher, enrich_identity)
    schema       SCHEMA + natural_key_hash + dédup per-lot
    tickers      normalisation / récupération ticker + asset_type
    amounts      fourchettes $, midpoint, owner, operation_type (par chambre)
    quiver       fetch + reconcile (utilisé par quality/tests ; House a son propre validate_quiver)
    crosscheck   triangulation digital (Kadoa, Stock Watcher) + statut/déposant (via quality)
    vision_ocr   rendu image + deskew + appel Vision + cache versionné (prévu : moteur OCR unique — Palier 3 ;
                 actuellement utilisé par les tests, pas encore branché en prod)
    llm_resolve  cache LLM versionné générique (prévu : passe ticker House+Sénat — Palier 2 ; pas encore branché)
    sector_enrich GICS → ETF
    reporting    Excel + dashboards + nommage de tables (via quality)
"""

__version__ = "0.1.0"
