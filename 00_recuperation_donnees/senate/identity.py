#!/usr/bin/env python
"""senate.identity — référentiel, matcher bioguide et enrichissement Sénat (logique figée).

Portage FIDÈLE des fonctions réutilisables de la finalisation Q1 (`senat_2025_test/senate_finalize.py`,
fonctions reprises telles quelles — c'est cette logique qui a produit le golden) : identité bioguide
(nettoyage suffixes/initiales/virgules + surnoms + désambiguïsation par chambre Sénat puis titulaire en
exercice), enrichissement ticker déterministe (`recover_ticker`), reclassement options, `natural_key` +
`occurrence_index` (dédup non destructrice), schéma 23 colonnes (`SENATE_DIGITAL_SCHEMA`).

Le `main()` du pilote Q1 (run + Excel) n'est PAS porté ici : ce module n'expose que le contrat
réutilisable consommé par `senate.digital` / `senate.ocr` / `senate.fusion`. Référentiel lu depuis
`data/senate/reference/` (YAML embarqués, parité House). Aucun littéral « 1 SENAT » / `data_v1_senate`.
"""
import os
import re
import json
import hashlib
import unicodedata
from collections import defaultdict, Counter
from pathlib import Path

import pandas as pd
import requests
import yaml

HERE = Path(__file__).resolve().parent       # <repo>/senate
REPO = HERE.parent                            # racine du dépôt
OUT = REPO / "data" / "senate"                # données Sénat (parité data/house)
REF = OUT / "reference"                        # référentiel + cache Quiver embarqués (autonome)

KEY_COMMITTEES = ("Finance", "Armed Services", "Intelligence", "Banking")

SCHEMA = ["bioguide_id", "declarant_name", "chamber", "party", "state_district",
          "committee_membership", "committees_key_flag", "transaction_date", "disclosure_date",
          "ticker", "asset_description", "asset_type", "operation_type", "amount_range",
          "amount_midpoint", "amount_split_flag", "owner", "doc_id", "source_url",
          "natural_key_hash", "provenance", "ticker_source", "occurrence_index"]


# --------------------------------------------------------------------------- identité
def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))


def norm(s):
    s = strip_accents(s or "").lower()
    s = re.sub(r"[^a-z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


SUFFIX = {"jr", "sr", "ii", "iii", "iv", "v"}


def split_name(declarant):
    """« First [Middle…] Last[, Suffix] » → (last, first, [middle_tokens])."""
    s = (declarant or "").split(",")[0]
    toks = [t for t in re.split(r"\s+", s.strip()) if t and norm(t) not in SUFFIX]
    if not toks:
        return "", "", []
    return toks[-1], toks[0], [norm(t) for t in toks[:-1]]


def load_reference():
    cur = yaml.safe_load(open(REF / "legislators-current.yaml"))
    his = yaml.safe_load(open(REF / "legislators-historical.yaml"))
    current_bios = {p["id"]["bioguide"] for p in cur if p.get("id", {}).get("bioguide")}

    ref, name_exact, name_by_last = {}, {}, defaultdict(list)
    for p in cur + his:
        bio = p.get("id", {}).get("bioguide")
        if not bio:
            continue
        nm = p.get("name", {})
        last, first, nick = nm.get("last", ""), nm.get("first", ""), nm.get("nickname", "")
        lt = (p.get("terms") or [{}])[-1]
        chamber = "senate" if lt.get("type") == "sen" else "house"
        ref.setdefault(bio, {"full": nm.get("official_full") or f"{first} {last}".strip(),
                             "party": lt.get("party"), "state": lt.get("state"),
                             "chamber": chamber, "first": first, "nick": nick})
        name_exact.setdefault((norm(last), norm(first)), bio)
        if nick:
            name_exact.setdefault((norm(last), norm(nick)), bio)
        name_by_last[norm(last)].append(bio)

    # commissions (flag clé)
    bio_to_committees, key_flag = defaultdict(set), {}
    try:
        committees = yaml.safe_load(open(REF / "committees-current.yaml"))
        membership = yaml.safe_load(open(REF / "committee-membership-current.yaml"))
        code_to_name = {c["thomas_id"]: c["name"] for c in committees if "thomas_id" in c}
        for code, members in membership.items():
            cname = code_to_name.get(code, code)
            for mem in members:
                if mem.get("bioguide"):
                    bio_to_committees[mem["bioguide"]].add(cname)
        key_flag = {b: any(any(k in cn for k in KEY_COMMITTEES) for cn in cs)
                    for b, cs in bio_to_committees.items()}
    except Exception as e:
        print("  commissions non chargées (flag=False) :", e)

    return ref, name_exact, name_by_last, current_bios, bio_to_committees, key_flag


# Overrides manuels : noms eFD que la résolution automatique rate (prénom en initiales collées,
# homonymie irréductible). Vérifiés à la main contre legislators-current.
_MANUAL_BIO = {("vance", "jd"): "V000137"}   # « JD Vance » (initiales collées ≠ first « J.D. »)


def make_matcher(ref, name_exact, name_by_last, current_bios):
    def match(declarant):
        last, first, middles = split_name(declarant)
        nl, nf = norm(last), norm(first)
        if (nl, nf) in _MANUAL_BIO:                     # 0) override manuel
            return _MANUAL_BIO[(nl, nf)]
        if (nl, nf) in name_exact:                      # 1) (last, first/nick) exact
            return name_exact[(nl, nf)]
        cands = name_by_last.get(nl, [])
        sen = [b for b in cands if ref[b]["chamber"] == "senate"]
        pool = sen if sen else cands                    # 2) on privilégie la chambre Sénat
        if len(pool) == 1:
            return pool[0]
        cur_pool = [b for b in pool if b in current_bios]   # 3) titulaire en exercice
        if len(cur_pool) == 1:
            return cur_pool[0]
        base = cur_pool or pool                         # 4) désambiguïsation prénom/initiale
        toks = set([nf] + middles)
        fp = [b for b in base
              if any(cf and t and (cf.startswith(t[:3]) or t.startswith(cf[:3]))
                     for cf in {norm(ref[b]["first"]), norm(ref[b]["nick"])} for t in toks)]
        return fp[0] if len(fp) == 1 else None
    return match


# --------------------------------------------------------------------------- ticker
TICK_RE = re.compile(r"^([A-Z]{1,5})(?:\.[A-Z])?(?:\s+(?:PUT|CALL))?$")


def recover_ticker(desc):
    """Récupère le symbole quand l'Asset Name *est* un ticker (« LLY », « CRWD PUT »)."""
    if not isinstance(desc, str):
        return None
    m = TICK_RE.match(desc.strip())
    return m.group(1) if m else None


# ---------------------------------------------------------------- traitement réutilisable
def natural_key(r):
    """SHA-256 stable d'une transaction (n'inclut pas le ticker — robuste à l'enrichissement)."""
    raw = "|".join(str(r[c]) for c in ["chamber", "declarant_name", "transaction_date",
                                       "asset_description", "operation_type", "amount_range", "owner"])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def enrich(raw, ref, bio_to_committees, key_flag, match):
    """Transforme une table électronique BRUTE (sortie de parse_electronic + métadonnées) en table
    au schéma final : identité bioguide, enrichissement ticker, reclassement options, natural_key +
    occurrence_index (dédup non destructrice), schéma 23 colonnes. Source unique partagée par la
    finalisation Q1 et le pipeline multi-années (`senat_multiyear.py`)."""
    df = raw.copy()
    df["chamber"] = "senate"
    # 1) identité
    df["bioguide_id"] = df["declarant_name"].map(match)
    df["party"] = df["bioguide_id"].map(lambda b: ref.get(b, {}).get("party"))
    df["state_district"] = df["bioguide_id"].map(lambda b: ref.get(b, {}).get("state"))
    df["committee_membership"] = df["bioguide_id"].map(
        lambda b: "; ".join(sorted(bio_to_committees.get(b, []))) if b else "")
    df["committees_key_flag"] = df["bioguide_id"].map(lambda b: bool(key_flag.get(b, False)))
    # 2) enrichissement ticker (déterministe, aucun Quiver injecté)
    raw_tk = df["ticker"].astype(str).str.strip().str.upper()
    has_tick = df["ticker"].notna() & ~raw_tk.isin(["--", "NAN", "NONE", ""])
    df["ticker"] = df["ticker"].where(has_tick, df["asset_description"].map(recover_ticker))
    df["ticker"] = df["ticker"].astype("string").str.upper()
    rec_final = df["asset_description"].map(recover_ticker)
    df["ticker_source"] = "none"
    df.loc[df["ticker"].notna(), "ticker_source"] = "explicit"
    df.loc[df["ticker"].notna() & (rec_final == df["ticker"]), "ticker_source"] = "asset_name"
    # 3) options (le formulaire eFD met "Stock" même pour « X CALL/PUT »)
    opt = df["asset_description"].astype(str).str.contains(
        r"\b(?:CALL|PUT)\b", case=False, regex=True, na=False)
    df.loc[opt, "asset_type"] = "Option"
    # 4) dates normalisées
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce").dt.date
    df["disclosure_date"] = pd.to_datetime(df["disclosure_date"], errors="coerce").dt.date
    # 5) natural_key + occurrence_index (lots répétés intra-rapport préservés) + dédup cross-rapport
    df["natural_key_hash"] = df.apply(natural_key, axis=1)
    df["amount_midpoint"] = pd.to_numeric(df["amount_midpoint"], errors="coerce")
    df["amount_split_flag"] = False
    df["occurrence_index"] = df.groupby(["doc_id", "natural_key_hash"]).cumcount()
    _disc = pd.to_datetime(df["disclosure_date"], errors="coerce")
    df = (df.assign(_disc=_disc).sort_values("_disc", ascending=False)
            .drop_duplicates(["natural_key_hash", "occurrence_index"], keep="first")
            .drop(columns="_disc")
            .sort_values(["declarant_name", "transaction_date"])
            .reindex(columns=SCHEMA))
    return df
