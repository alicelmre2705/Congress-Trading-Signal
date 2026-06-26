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
