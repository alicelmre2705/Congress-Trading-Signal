#!/usr/bin/env python
"""Phase 9a — reconstruction ADDITIVE après re-OCR des 40 partial_error (cluster C, 0 txn avant).

Pour les docs nouvellement complétés (cache status=ok), on normalise + enrichit EXACTEMENT comme
house.ocr.run_ocr_year (ticker explicite/dict/LLM, identité, asset_type, date_confidence) et on
APPEND au 06b existant (lignes existantes intactes), puis on rebâtit 06_FINAL. Purement additif.
"""
import sys, json, glob
from pathlib import Path
import pandas as pd
sys.path.insert(0, ".")
import house.ocr as ho
import house.digital as hm

TABLES = Path("data/house/tables")
CACHE = Path("data/house/ocr_cache")
YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]

# Les 40 doc_ids EXACTEMENT re-OCR-isés (partial_error → complétés). Restreindre à ceux-là :
# sinon on capte tous les docs C ok-mais-exclus du 06b par la politique cluster (≠ « juste les 40 »).
import re as _re
_OUT = Path("/private/tmp/claude-501/-Users-lemairealice-Downloads-Jupiter/"
            "b553b801-a9d1-4b57-94de-b1668197a892/tasks/b98lgwayc.output")
TARGET = set(_re.findall(r"\b([89]\d{6})\b", _OUT.read_text())) if _OUT.exists() else set()


def completed_docs():
    """Cache 'ok' AVEC transactions, restreint aux 40 doc_ids ciblés (partial_error re-OCR-isés)."""
    by_year = {}
    for f in glob.glob(str(CACHE / "*" / "*.json")):
        o = json.load(open(f))
        if o["doc_id"] in TARGET and o.get("status") == "ok" and o.get("transactions"):
            by_year.setdefault(int(Path(f).parent.name), {})[o["doc_id"]] = o
    return by_year


def main():
    hm.build_reference()
    cache_by_year = completed_docs()
    total_new = 0
    for year in YEARS:
        b06 = TABLES / str(year) / f"06b_house_{year}_ocr_transactions.csv"
        existing = pd.read_csv(b06, dtype=str)
        have = set(existing["doc_id"])
        # docs complétés de l'année ABSENTS du 06b actuel = les nouveaux à ajouter
        ptr = pd.read_csv(TABLES / str(year) / "03_ptr_index.csv", dtype=str)
        meta_lookup = {r["doc_id"]: r.to_dict() for _, r in ptr.iterrows()}
        new_docs = [d for d in cache_by_year.get(year, {}) if d not in have and d in meta_lookup]
        if not new_docs:
            continue
        rows = []
        for d in new_docs:
            for txn in cache_by_year[year][d]["transactions"]:
                if ho._EXAMPLE_RE.search(str(txn.get("asset_description", ""))):
                    continue
                rows.append(ho.normalize(txn, meta_lookup[d], year))
        if not rows:
            continue
        df = pd.DataFrame(rows)

        # — enrichissement IDENTIQUE à run_ocr_year —
        dig = pd.read_csv(TABLES / str(year) / f"06_house_{year}_transactions.csv", dtype=str)
        dig_tk = dig[dig["ticker"].notna() & (dig["ticker"].str.strip() != "")].copy()
        dig_tk["norm"] = dig_tk["asset_description"].map(ho._norm_asset)
        name_to_ticker = (dig_tk[dig_tk["norm"] != ""].groupby("norm")["ticker"]
                          .agg(lambda s: s.str.upper().mode().iat[0]).to_dict())

        def _resolve(desc):
            t = ho._explicit_ticker(desc)
            if t:
                return t.upper(), "explicit"
            t = name_to_ticker.get(ho._norm_asset(desc))
            if t:
                return t, "elec_dict"
            return None, "none"
        res = df["asset_description"].map(_resolve)
        df["ticker"] = [r[0] for r in res]
        df["ticker_source"] = [r[1] for r in res]
        df["asset_type"] = df["asset_description"].map(ho._infer_asset_type)
        df = ho.llm_resolve_tickers(df)
        df["bioguide_id"] = df["doc_id"].map(
            lambda d: hm.match_bioguide(meta_lookup[d].get("last", ""), meta_lookup[d].get("first", "")))
        df["party"] = df["bioguide_id"].map(lambda b: hm.ref_universe["party"].get(b) if b else None)
        df["committee_membership"] = df["bioguide_id"].map(
            lambda b: "; ".join(sorted(hm.bio_to_committees.get(b, []))) if b else None)
        df["committees_key_flag"] = df["bioguide_id"].map(
            lambda b: bool(hm.ref_house_key is not None and b in hm.ref_house_key.index) if b else None)

        new = df.reindex(columns=ho.SCHEMA_COLS + ["ticker_source", "provenance"])
        merged = pd.concat([existing, new], ignore_index=True)
        merged.to_csv(b06, index=False)

        # rebuild 06_FINAL = digital + OCR complet (dédup collision avec digital)
        dmain = pd.read_csv(TABLES / str(year) / f"06_house_{year}_transactions.csv", dtype=str)
        dmain["provenance"] = "house-pdf-electronic"
        collide = merged["natural_key_hash"].isin(set(dmain["natural_key_hash"].dropna()))
        comb = pd.concat([dmain, merged[~collide]], ignore_index=True)
        comb.to_csv(TABLES / str(year) / f"06_house_{year}_FINAL.csv", index=False)

        total_new += len(new)
        print(f"  {year}: +{len(new_docs)} docs / +{len(new)} txns OCR → 06b {len(existing)}→{len(merged)} | "
              f"FINAL {len(comb)} | bioguide {new['bioguide_id'].notna().sum()}/{len(new)} | "
              f"ticker {new['ticker'].notna().sum()}/{len(new)}")
    print(f"\nTOTAL ajouté : {total_new} transactions OCR (manuscrit récupéré)")


if __name__ == "__main__":
    main()
