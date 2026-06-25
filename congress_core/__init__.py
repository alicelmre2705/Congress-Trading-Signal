"""congress_core — cœur partagé du pipeline Congress Trading (House + Sénat).

Logique métier commune extraite des moteurs par chambre, pour que House et Sénat l'importent
sans copier-coller. Construit d'abord pour House ; le Sénat le consommera après sa finalisation.

Modules (remplis au fil des phases de la refonte) :
    paths        bootstrap chemins/env (DataRoot)
    identity     ★ Doc ID → bioguide (Reference, make_matcher, enrich_identity)
    schema       SCHEMA + natural_key_hash + dédup per-lot
    tickers      normalisation / récupération ticker + asset_type
    amounts      fourchettes $, midpoint, owner, operation_type (par chambre)
    quiver       fetch + reconcile (vérification externe)
    crosscheck   triangulation digital (Kadoa, Stock Watcher) + statut/déposant
    vision_ocr   rendu image + deskew + appel Vision + cache versionné
    llm_resolve  cache LLM versionné générique (ticker, secteur)
    sector_enrich GICS → ETF
    reporting    Excel + dashboards + nommage de tables
"""

__version__ = "0.1.0"
