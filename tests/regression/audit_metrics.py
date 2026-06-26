#!/usr/bin/env python
"""Audit des métriques — recompute TOUTES les métriques clés des deux chambres depuis `data/`.

Source unique de vérité chiffrée (pour la doc et le rapport) : aucune valeur codée en dur, tout est
recalculé depuis les tables FINAL. Asserte les invariants porteurs (totaux, identité). Le reste est
imprimé pour relecture vs la documentation.

    .venv/bin/python tests/regression/audit_metrics.py
"""
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]


def _load(chamber):
    pat = (REPO / "data" / chamber / "tables" if chamber == "house" else REPO / "data" / chamber)
    glob = f"*/06_{chamber}_*_FINAL.csv"
    files = sorted(pat.glob(glob))
    return pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False) for f in files], ignore_index=True)


def _pct(n, d):
    return f"{100*n/d:.1f}%" if d else "—"


def report(chamber, prov_elec, prov_ocr):
    df = _load(chamber)
    n = len(df)
    dig = (df["provenance"] == prov_elec).sum()
    ocr = (df["provenance"] == prov_ocr).sum()
    bios = df[df["bioguide_id"].str.strip() != ""]["bioguide_id"].nunique()
    names = df["declarant_name"].nunique()
    sans_bio = (df["bioguide_id"].str.strip() == "").sum()
    has_tk = (df["ticker"].str.strip() != "").sum()
    sec = df["sector_gics"].str.strip() != "" if "sector_gics" in df.columns else pd.Series([False] * n)
    fields = 12 if "sector_gics" in df.columns else 10
    print(f"\n=== {chamber.upper()} (FINAL {n}) ===")
    print(f"  digital {dig} + OCR {ocr} = {dig+ocr}  (== {n} ? {dig+ocr==n})")
    print(f"  identité : {bios} bioguides / {names} noms · sans bioguide {sans_bio} ({_pct(n-sans_bio,n)} rattachées)")
    print(f"  ticker rempli : {has_tk} ({_pct(has_tk,n)})")
    print(f"  secteur GICS rempli : {int(sec.sum())} ({_pct(int(sec.sum()),n)}) · champs garantis : {fields}/12")
    if "date_confidence" in df.columns:
        ocr_df = df[df["provenance"] == prov_ocr]
        pl = (ocr_df["date_confidence"] == "plausible").sum()
        im = (ocr_df["date_confidence"] == "implausible").sum()
        print(f"  date_confidence (lignes OCR) : plausible {pl} ({_pct(pl,len(ocr_df))}) · implausible {im}")
    assert dig + ocr == n, f"{chamber}: digital+OCR != FINAL"
    return {"n": n, "dig": dig, "ocr": ocr, "bios": bios, "names": names, "sans_bio": sans_bio,
            "ticker_pct": round(100*has_tk/n, 1), "sector_n": int(sec.sum()), "fields": fields}


def main():
    h = report("house", "house-pdf-electronic", "house-pdf-ocr")
    s = report("senate", "senate-efd-electronic", "senate-efd-ocr")
    # invariants porteurs
    assert h["n"] == 81646 and h["dig"] == 32676 and h["ocr"] == 48970, "House totaux"
    assert s["n"] == 8841 and s["dig"] == 7161 and s["ocr"] == 1680, "Sénat totaux"
    assert h["sans_bio"] == 4 and s["sans_bio"] == 0, "sans-bioguide attendus"
    assert h["bios"] == 256 and h["names"] == 275, "House déposants"
    assert s["bios"] == 64 and s["names"] == 67, "Sénat déposants"
    print("\nRÉSULTAT : ✅ invariants OK (totaux, identité, déposants) — métriques ci-dessus = source du rapport")


if __name__ == "__main__":
    main()
