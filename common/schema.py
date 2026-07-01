"""Schéma canonique + clé naturelle + dédup per-lot — source unique pour House et Sénat.

Remplace les 4-5 copies de `natural_key_hash` / `_legacy_key` / `natural_key` éparpillées dans les
moteurs, qui n'étaient PAS byte-identiques (House OCR codait 'house' en dur + `row.get(k,'')`, les
autres `str(r[c])`). Politique de valeur-manquante UNIQUE et figée ici (`_cell`), `chamber` toujours
explicite. Le test `tests/regression/test_schema.py` PROUVE que cette fonction reproduit tous les
hash figés des tables actuelles (House digital, OCR, FINAL).
"""
import hashlib
import math

# Les 7 champs de la clé naturelle (n'inclut PAS le ticker → robuste à l'enrichissement).
NATURAL_KEY_FIELDS = ["chamber", "declarant_name", "transaction_date",
                      "asset_description", "operation_type", "amount_range", "owner"]

# 12 champs obligatoires de la table finale (le contrat « table finale »).
CORE_FIELDS = ["declarant_name", "chamber", "party", "committee_membership",
               "transaction_date", "disclosure_date", "ticker", "sector_gics", "etf_proxy",
               "operation_type", "amount_midpoint", "asset_type"]

# Ordres de colonnes EXACTS par pipeline (préservés tels quels pour la garantie zéro-changement).
HOUSE_DIGITAL_SCHEMA = [
    "bioguide_id", "declarant_name", "chamber", "party", "state_district",
    "committee_membership", "committees_key_flag", "transaction_date", "disclosure_date",
    "ticker", "asset_description", "asset_type", "operation_type", "amount_range",
    "amount_midpoint", "amount_split_flag", "owner", "doc_id", "source_url",
    "natural_key_hash", "occurrence_index"]

HOUSE_OCR_SCHEMA = [
    "bioguide_id", "declarant_name", "chamber", "party", "state_district",
    "committee_membership", "committees_key_flag", "transaction_date", "disclosure_date",
    "date_confidence", "ticker", "asset_description", "asset_type", "operation_type", "amount_range",
    "amount_midpoint", "amount_split_flag", "owner", "doc_id", "source_url", "natural_key_hash"]

# House — table FINALE (digital + OCR, enrichie secteur), 27 colonnes = ordre House actuel +
# sector_gics/etf_proxy (après asset_type) + sector_source (en fin) → parité 12/12 avec le Sénat.
HOUSE_FINAL_SCHEMA = [
    "bioguide_id", "declarant_name", "chamber", "party", "state_district",
    "committee_membership", "committees_key_flag", "transaction_date", "disclosure_date",
    "ticker", "asset_description", "asset_type", "sector_gics", "etf_proxy",
    "operation_type", "amount_range", "amount_midpoint", "amount_split_flag", "owner",
    "doc_id", "source_url", "natural_key_hash", "occurrence_index", "provenance",
    "date_confidence", "ticker_source", "sector_source"]

# Sénat — table électronique (eFD), 23 colonnes (== senate_finalize.SCHEMA, reproduit 06_senate_*).
SENATE_DIGITAL_SCHEMA = [
    "bioguide_id", "declarant_name", "chamber", "party", "state_district",
    "committee_membership", "committees_key_flag", "transaction_date", "disclosure_date",
    "ticker", "asset_description", "asset_type", "operation_type", "amount_range",
    "amount_midpoint", "amount_split_flag", "owner", "doc_id", "source_url",
    "natural_key_hash", "provenance", "ticker_source", "occurrence_index"]

# Sénat — table FINALE (digital + OCR, enrichie), 27 colonnes (== merge_ocr.FINAL_COLS, reproduit
# 06_senate_*_FINAL). Ajoute date_confidence + sector_gics/etf_proxy/sector_source à la digitale.
SENATE_FINAL_SCHEMA = [
    "bioguide_id", "declarant_name", "chamber", "party", "state_district",
    "committee_membership", "committees_key_flag", "transaction_date", "disclosure_date",
    "date_confidence", "ticker", "asset_description", "asset_type", "sector_gics", "etf_proxy",
    "operation_type", "amount_range", "amount_midpoint", "amount_split_flag",
    "owner", "doc_id", "source_url", "natural_key_hash",
    "provenance", "ticker_source", "sector_source", "occurrence_index"]

# Colonnes AJOUTÉES après l'assemblage (post-FINAL), hors *_FINAL_SCHEMA ci-dessus : `years_in_office`
# (ancienneté du déposant, métadonnée Ramify) est appendue par `common.enrich_tenure`. Gardée
# HORS des schémas d'assemblage pour ne pas créer une colonne vide quand `house.ocr`/`senate.fusion`
# réindexent sur ces schémas ; le pipeline unifié exécute l'enrichissement en dernière étape.
FINAL_POST_ENRICH = ["years_in_office"]


def natural_key(row, chamber="house"):
    """Représentation textuelle stable de la clé naturelle, FIDÈLE aux deux moteurs originaux :
    `str(row.get(c, ''))` champ par champ (clé absente → '' ; valeur None → 'None' ; NaN → 'nan' ;
    '' → ''). C'est exactement `_legacy_key` (digital, `str(r[c])`, clés toujours présentes) ET
    `natural_key_hash` (OCR, `str(row.get(c, ''))`). `chamber` explicite : la valeur de la ligne
    prime ('house'/'senate'), sinon l'argument — jamais codé en dur. Voir test d'équivalence."""
    get = row.get if hasattr(row, "get") else (lambda k, d="": row[k] if k in row else d)
    vals = []
    for c in NATURAL_KEY_FIELDS:
        if c == "chamber":
            v = get("chamber", chamber)
            if v is None or v == "" or (isinstance(v, float) and math.isnan(v)):
                v = chamber
        else:
            v = get(c, "")
        vals.append(str(v))
    return "|".join(vals)


def natural_key_hash(row, chamber="house"):
    """SHA-256 de la clé naturelle (7 champs). Source unique House/Sénat."""
    return hashlib.sha256(natural_key(row, chamber).encode("utf-8")).hexdigest()


# Coquilles d'ANNÉE de transaction dans le PTR officiel (digital), confirmées par la date de divulgation.
# Corrigées À LA LECTURE pour l'analyse : le CSV figé conserve la valeur source (et son natural_key_hash,
# qui inclut transaction_date — muter le figé casserait la clé). Clés = chaîne brute globalement unique.
KNOWN_TXN_DATE_FIXES = {
    "3031-04-30": "2021-04-30",   # Pete Sessions / IBM (doc 20018672) — divulgué 2021-05-03
    "2202-09-19": "2022-09-19",   # Virginia Foxx / NEWT (doc 20021790) — divulgué 2022-10-12
    "2220-04-07": "2022-04-07",   # Virginia Foxx / MMP (doc 20020914) — divulgué 2022-05-04
}

# Corrections OCR de transaction_date VÉRIFIÉES par re-lecture du PDF source scanné (House OCR) : le
# formulaire imprime une date LISIBLE et valide, différente de ce que notre OCR a extrait. Clé scopée
# (doc_id, ticker, date_ocr_erronée) : par ligne, car ces dates fausses sont plausibles et peuvent exister
# CORRECTEMENT ailleurs — et parce qu'un doc peut avoir un AUTRE actif partageant la même date mal lue mais
# NON vérifié (ex. doc 8218296 : DaVita vérifié à 05/28, mais Motorola même date → laissé flaggé). Read-time
# only (le figé garde la valeur source). On ne corrige PAS les coquilles du déposant (ex. le PTR imprime
# littéralement 01/35/22), ni les cellules vides, ni les scans illisibles — inventer une date (voir §2).
KNOWN_TXN_DATE_FIXES_BY_DOC = {
    ("8218338", "COST", "2021-09-31"): "2021-08-16",   # Khanna / Costco — formulaire : 08/16/21
    ("8217209", "FIX", "2020-08-16"): "2020-03-16",    # McCaul / Comfort Sys — mois 03 lu 08
    ("8218296", "DVA", "2021-08-21"): "2021-05-28",    # Harshbarger / DaVita (vente fractionnée) — 05/28/21
    ("8218082", "SQ", "2021-06-14"): "2021-05-14",     # Schrader / Square — mois 05 lu 06
}


def apply_txn_date_fixes(df):
    """Applique les corrections de `transaction_date` À LA LECTURE (sans toucher au figé) : d'abord la carte
    globale `KNOWN_TXN_DATE_FIXES` (coquilles d'année du PTR, chaînes uniques), puis la carte scopée
    `KNOWN_TXN_DATE_FIXES_BY_DOC` par `(doc_id, ticker, date)` (OCR mal lu, vérifié ligne à ligne)."""
    if "transaction_date" not in df.columns:
        return df
    df = df.copy()
    df["transaction_date"] = df["transaction_date"].replace(KNOWN_TXN_DATE_FIXES)
    if KNOWN_TXN_DATE_FIXES_BY_DOC and {"doc_id", "ticker"} <= set(df.columns):
        _doc = df["doc_id"].astype(str).str.replace(r"\.0$", "", regex=True)
        _tk = df["ticker"].fillna("").astype(str).str.strip()
        _td = df["transaction_date"].astype(str)
        df["transaction_date"] = [
            KNOWN_TXN_DATE_FIXES_BY_DOC.get((d, tk, t), cur)
            for d, tk, t, cur in zip(_doc, _tk, _td, df["transaction_date"])
        ]
    return df


def load_ticker_recovery(repo_root):
    """Carte de récupération ticker (asset_description → ticker), résolue depuis le NOM (hors Quiver, jamais
    réinjecté) et vérifiée. `data/house/ticker_recovery.json`. Renvoie {} si absente."""
    import json
    from pathlib import Path
    p = Path(repo_root) / "data" / "house" / "ticker_recovery.json"
    if not p.exists():
        return {}
    try:
        obj = json.loads(p.read_text())
        return obj.get("map", obj) if isinstance(obj, dict) else {}
    except Exception:
        return {}


def apply_ticker_recovery(df, repo_root):
    """Remplit `ticker` À LA LECTURE là où il est vide et où `asset_description` est dans la carte de
    récupération (faux négatifs du LLM = actions cotées réelles, ex NEENAH PAPER→NP). Marque
    `ticker_source='recovered'`. Le figé n'est PAS touché ; Quiver n'est jamais réinjecté (résolution
    depuis le nom, sa validation = baisse du résidu §6.2)."""
    rec = load_ticker_recovery(repo_root)
    if not rec or "ticker" not in df.columns or "asset_description" not in df.columns:
        return df
    df = df.copy()
    _blank = df["ticker"].fillna("").astype(str).str.strip() == ""
    _desc = df["asset_description"].fillna("").astype(str).str.strip()
    _hit = _blank & _desc.isin(rec)
    if _hit.any():
        df.loc[_hit, "ticker"] = _desc[_hit].map(rec)
        if "ticker_source" in df.columns:
            df.loc[_hit, "ticker_source"] = "recovered"
    return df


def add_occurrence_index(df):
    """occurrence_index = rang du lot répété intra-dépôt (préserve les lots identiques d'un même PTR,
    dédup non destructrice). Exige les colonnes doc_id + natural_key_hash."""
    df = df.copy()
    df["occurrence_index"] = df.groupby(["doc_id", "natural_key_hash"]).cumcount()
    return df


def dedup_canonical(df, sort_col="disclosure_date"):
    """Dédup canonique : garde la divulgation la plus récente par (natural_key_hash, occurrence_index).
    Retire les vrais doublons cross-dépôt, préserve les lots intra-dépôt. Reproduit `finalize`."""
    s = df.sort_values(sort_col, ascending=False, na_position="last")
    return s.drop_duplicates(["natural_key_hash", "occurrence_index"]).copy()
