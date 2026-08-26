"""Schéma canonique + clé naturelle + dédup per-lot — source unique pour House et Sénat.

Remplace les 4-5 copies de `natural_key_hash` / `_legacy_key` / `natural_key` éparpillées dans les
moteurs, qui n'étaient PAS byte-identiques (House OCR codait 'house' en dur + `row.get(k,'')`, les
autres `str(r[c])`). Politique de valeur-manquante UNIQUE et figée ici (`_cell`), `chamber` toujours
explicite. Le test `tests/regression/test_schema.py` PROUVE que cette fonction reproduit tous les
hash figés des tables actuelles (House digital, OCR, FINAL).
"""
import hashlib
import math
import re

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


# Ratés de résolution d'identité VÉRIFIÉS contre le référentiel congress-legislators (audit 2026-07-03) :
# 3 déposants jamais rattachés (bioguide vide → membre invisible pour toute analyse par membre) et
# 1 collision d'homonyme (« Robert P Casey, Jr. » sénateur PA rattaché à C000228 = Robert Casey,
# représentant TX). Corrigés À LA LECTURE, scopés (doc_id, token du nom) — le CSV figé garde la valeur
# source. party/state_district recopiés du référentiel (stables : mandats terminés ou uniques).
KNOWN_IDENTITY_FIXES_BY_DOC = {
    # doc_id: (token_nom_attendu, bioguide_id, party, state_district)
    "9115136": ("Craig", "C001119", "Democrat", "MN02"),                                # Angela « Angie » Craig, House 2019
    "9115439": ("Craig", "C001119", "Democrat", "MN02"),
    "d729aa53-3864-4ec2-8087-62ba351859c7": ("Van Hollen", "V000128", "Democrat", "MD"),  # Chris Van Hollen, Sénat 2017
    "3d4fc7ff-d1fc-4b0a-a4a0-493a65ab9d07": ("Udall", "U000039", "Democrat", "NM"),       # Tom Udall, Sénat 2018
    "c4d18b4c-1474-49db-a057-e1fcb6d96251": ("Udall", "U000039", "Democrat", "NM"),
    "debe3c76-c386-42a7-85f9-8e15e85d490b": ("Udall", "U000039", "Democrat", "NM"),
    "1dae4e2c-0fe3-46d5-9ab3-78454252da12": ("Casey", "C001070", "Democrat", "PA"),       # Bob Casey Jr., Sénat 2017 (≠ C000228 TX)
}


def apply_identity_fixes(df):
    """Applique les corrections d'identité À LA LECTURE (sans toucher au figé) : pour chaque doc de
    `KNOWN_IDENTITY_FIXES_BY_DOC` dont le nom du déposant contient le token attendu, pose
    bioguide_id/party/state_district. Ne touche à rien d'autre (commissions/ancienneté recalculées en aval)."""
    if not {"doc_id", "bioguide_id"} <= set(df.columns):
        return df
    df = df.copy()
    _doc = df["doc_id"].astype(str).str.replace(r"\.0$", "", regex=True)
    hits = _doc.isin(KNOWN_IDENTITY_FIXES_BY_DOC)
    if not hits.any():
        return df
    name_col = "declarant_name" if "declarant_name" in df.columns else "member_name"
    for i in df.index[hits]:
        token, bio, party, sd = KNOWN_IDENTITY_FIXES_BY_DOC[_doc.at[i]]
        if token.lower() in str(df.at[i, name_col]).lower():
            df.at[i, "bioguide_id"] = bio
            if "party" in df.columns:
                df.at[i, "party"] = party
            if "state_district" in df.columns:
                df.at[i, "state_district"] = sd
    return df


# Fourchettes STOCK Act dont le parseur digital House n'a capturé que la borne BASSE (le PDF imprime la
# fourchette sur deux lignes « $15,001 - » / « $50,000 » ; TXN_RE n'a retenu que la première). La borne
# basse identifie le bracket de façon UNIQUE → reconstruction déterministe du libellé et du vrai milieu.
# Ne matche que amount_range == « $X » EXACT (borne seule) : les paliers légitimes à libellé complet
# (« SP/DC over $1,000,000 », « Over $50,000,000 ») ne sont pas touchés. Read-time only (figé conservé).
AMOUNT_LOWER_BOUND_TO_BRACKET = {
    "$1,001":      ("$1,001 - $15,000",           8_000.5),
    "$15,001":     ("$15,001 - $50,000",         32_500.5),
    "$50,001":     ("$50,001 - $100,000",        75_000.5),
    "$100,001":    ("$100,001 - $250,000",      175_000.5),
    "$250,001":    ("$250,001 - $500,000",      375_000.5),
    "$500,001":    ("$500,001 - $1,000,000",    750_000.5),
    "$1,000,001":  ("$1,000,001 - $5,000,000",  3_000_000.5),
    "$5,000,001":  ("$5,000,001 - $25,000,000", 15_000_000.5),
    "$25,000,001": ("$25,000,001 - $50,000,000", 37_500_000.5),
}


def apply_amount_range_fixes(df):
    """Répare À LA LECTURE les fourchettes tronquées à la borne basse (piste digitale House, audit
    2026-07-03 : 7 995 lignes FINAL, montant sous-estimé ×2) : amount_range reconstruit + amount_midpoint
    = vrai milieu du bracket. Ajoute `amount_range_repaired` (bool) pour la traçabilité."""
    if "amount_range" not in df.columns:
        return df
    df = df.copy()
    key = df["amount_range"].astype(str).str.strip()
    hit = key.isin(AMOUNT_LOWER_BOUND_TO_BRACKET)
    df["amount_range_repaired"] = hit
    if hit.any():
        df.loc[hit, "amount_range"] = key[hit].map(lambda k: AMOUNT_LOWER_BOUND_TO_BRACKET[k][0])
        if "amount_midpoint" in df.columns:
            df.loc[hit, "amount_midpoint"] = key[hit].map(lambda k: AMOUNT_LOWER_BOUND_TO_BRACKET[k][1])
    return df


# Symboles Yahoo Finance : les classes d'actions s'écrivent avec un TIRET (BRK-B), les PTR/Quiver
# mélangent point et tiret. NB : cette canonisation est pour l'EXPORT/le join prix — la clé
# d'appariement Quiver historique (house/quiver.py::norm_ticker, port verbatim '.'/'-'→'_') ne
# doit PAS être modifiée (elle reproduit les validations figées).
_TICKER_OK = re.compile(r"^[A-Z]{1,5}(-[A-Z])?$")


def canonical_ticker(t):
    """Canonise un ticker pour l'export backtest (format Yahoo) SANS jeter d'information.
    Renvoie (ticker_canonique, flag) ; flag ∈ {'vide','ok','classe_convertie','contient_chiffre',
    'long','autre'} — les formes suspectes sont GARDÉES et flaguées (décision en aval, pas ici).
    Les graphies 'nan'/'None' minuscules = artefacts pandas ; 'NAN' MAJUSCULE = vrai fonds coté Nuveen."""
    if t is None or not isinstance(t, str):
        return "", "vide"
    raw = t.strip()
    if raw in ("", "--") or raw in ("nan", "None", "NaN", "none"):
        return "", "vide"
    up = raw.upper()
    conv = up.replace(".", "-")
    if _TICKER_OK.fullmatch(up):
        return up, "ok"
    if _TICKER_OK.fullmatch(conv):
        return conv, "classe_convertie"
    if any(ch.isdigit() for ch in up):
        return conv, "contient_chiffre"
    if len(conv.replace("-", "")) > 5:
        return conv, "long"
    return conv, "autre"


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


# ─────────────────────── notification_date (deuxième date du PTR House) ───────────────────────
# Le formulaire PTR impose DEUX dates par ligne : *Date of Transaction* et *Date Notified of
# Transaction*. La seconde existe pour les comptes que l'élu ne pilote pas lui-même (gestion
# déléguée, trust, mandat) : elle dit quand le gérant l'a INFORMÉ. L'écart entre les deux mesure
# donc directement le contenu informationnel d'une ligne.
#
# Elle a toujours été captée (groupe `notif` des deux parseurs) et jetée. La récolter dans les
# tables figées les réécrirait toutes (golden à l'octet) → elle vit dans un référentiel annexe,
# `data/reference/notification_dates.csv`, produit par `common.notification_dates` et joint ICI,
# à la lecture. Même doctrine que les quatre familles de correctifs ci-dessus.

def load_notification_dates(repo_root):
    """Carte (doc_id, natural_key_hash) → notification_date. {} si le référentiel est absent."""
    import csv
    from pathlib import Path
    p = Path(repo_root) / "data" / "reference" / "notification_dates.csv"
    if not p.exists():
        return {}
    try:
        with p.open(newline="", encoding="utf-8") as f:
            return {(r["doc_id"], r["natural_key_hash"]): r["notification_date"]
                    for r in csv.DictReader(f) if r.get("notification_date")}
    except (OSError, KeyError):
        return {}


def apply_notification_dates(df, repo_root):
    """Ajoute `notification_date` À LA LECTURE (colonne vide si le référentiel manque).

    Le Sénat n'a pas cette date : son formulaire n'a qu'une colonne de date. Les lignes Sénat
    restent donc vides — ce n'est pas un trou de collecte, c'est l'absence du champ à la source.
    """
    if not {"doc_id", "natural_key_hash"} <= set(df.columns):
        return df
    carte = load_notification_dates(repo_root)
    df = df.copy()
    if not carte:
        df["notification_date"] = ""
        return df
    _doc = df["doc_id"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["notification_date"] = [carte.get((d, h), "")
                               for d, h in zip(_doc, df["natural_key_hash"].astype(str))]
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
