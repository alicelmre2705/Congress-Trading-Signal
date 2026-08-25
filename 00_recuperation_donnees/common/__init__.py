"""common — le contrat UNIVERSEL partagé par les deux chambres.

Ne contient QUE ce que House ET Sénat utilisent vraiment (ou le pipeline / la qualité / l'ancienneté,
qui tournent sur les deux). La logique SPÉCIFIQUE à une chambre vit dans `house/` et `senate/`, qui sont
désormais symétriques. Le matcher d'identité, les montants, le ticker, la validation Quiver et l'OCR
DIFFÈRENT par chambre → ils ne sont pas ici.

Modules :
    reference     ★ référentiel des élus partagé : nom → bioguide (Reference, load_reference,
                  add_years_in_office, enrich_identity). Le MATCHER est par chambre (house/senate.identity).
    schema        clé naturelle + natural_key_hash + dédup per-lot (contrat de table, prouvé identique aux 2)
    sector_enrich GICS → ETF SPDR (importé par house.ocr ET senate.fusion, en direct)
    enrich_tenure years_in_office, appendu aux 14 tables FINAL (House + Sénat)
    quiver_scopes validation Quiver multi-scopes (digital/ocr/both) + breakdown métriques (07c-h)
    backtest_clean step 7 : corpus → les 4 tables de recherche de data/clean/ (brute · clean ·
                  gated · commissions), 100 % offline, testé par tests/regression
    quality       step 8 : LE rapport des données (RAPPORT_DONNEES.md, §1→§10 + figures),
                  régénérable — lecture seule des FINAL + artefacts figés, aucun appel API
    quiver_diagnosis  le §6 du rapport (réconciliation Quiver stricte) + les 13 CSV de preuve
                  de data/quiver_validation/
    crosscheck    corroboration externe ligne à ligne (senate/house-stock-watcher, §8 du rapport)
                  + statuts de triangulation par déposant
    report_pdf    Markdown → PDF A4 (Chrome headless) pour le rapport et les documents .md
    vision_ocr    moteur OCR Vision de RÉFÉRENCE (deskew + cache versionné), exercé par les tests ;
                  chaque chambre a son OCR en prod (house.ocr, senate.ocr_engine)
    pipeline      orchestrateur — enchaîne house.* + senate.* + enrich_tenure + backtest_clean
                  (step 7) + quality (step 8)
    first_seen    ★ crawl d'horodatage : écrit `first_seen_at` (data/first_seen/), la date à
                  laquelle NOUS voyons un document en ligne — la seule des trois dates dont on soit
                  certain qu'elle est publique, et la seule qui NE SE RECONSTITUE PAS. N'importe
                  rien du pipeline (requests + stdlib) : ce job ne doit jamais tomber.
    live_run      run en direct : les dépôts nouveaux → lignes au format de la table de référence
                  (12 champs, p. 31 du deck) dans data/live/. Voie PARALLÈLE — n'écrit jamais dans
                  data/*/tables/, verrouillé à l'octet par le golden.
    notification_dates  récolte la 2e date du PTR House (« Date Notified of Transaction ») depuis
                  les PDF et les caches OCR déjà payés → référentiel annexe appliqué à la LECTURE
"""

__version__ = "0.1.0"
