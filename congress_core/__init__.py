"""congress_core — le contrat UNIVERSEL partagé par les deux chambres.

Ne contient QUE ce que House ET Sénat utilisent vraiment (ou le pipeline / la qualité / l'ancienneté,
qui tournent sur les deux). La logique SPÉCIFIQUE à une chambre vit dans `house/` et `senate/`, qui sont
désormais symétriques. Le matcher d'identité, les montants, le ticker, la validation Quiver et l'OCR
DIFFÈRENT par chambre → ils ne sont pas ici.

Modules :
    reference     ★ référentiel des élus partagé : nom → bioguide (Reference, load_reference,
                  add_years_in_office, enrich_identity). Le MATCHER est par chambre (house/senate.identity).
    schema        clé naturelle + natural_key_hash + dédup per-lot (contrat de table, prouvé identique aux 2)
    sector_enrich GICS → ETF SPDR (importé par House ET par le shim Sénat)
    enrich_tenure years_in_office, appendu aux 14 tables FINAL (House + Sénat)
    quality       5 contrôles qualité (lecture seule des FINAL des deux chambres)
    crosscheck    triangulation Quiver / Kadoa / Stock Watcher + statut par déposant (via quality)
    vision_ocr    moteur OCR Vision de RÉFÉRENCE (deskew + cache versionné), exercé par les tests ;
                  chaque chambre a son OCR en prod (house.ocr, senate.ocr_engine)
    pipeline      orchestrateur (enchaîne house.* + senate.* + enrich_tenure)
"""

__version__ = "0.1.0"
