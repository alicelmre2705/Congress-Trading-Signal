#!/usr/bin/env python
"""PREUVE Phase 1 (amounts/tickers) : reproduction depuis les colonnes figées, sans PDF.

- amount_midpoint (digital) : amount_midpoint(amount_range) == amount_midpoint stocké (06).
- amount_midpoint (OCR)     : libellé amount_range → midpoint de HOUSE_OCR_AMOUNT_MAP == stocké (06b).
- infer_asset_type (OCR)    : infer_asset_type(asset_description,'house') == asset_type stocké (06b).
"""
import sys, math
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
TABLES = REPO / "data" / "house" / "tables"
sys.path.insert(0, str(REPO))
from congress_core.amounts import amount_midpoint, HOUSE_OCR_AMOUNT_MAP
from congress_core.tickers import infer_asset_type

YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
LABEL2MID = {label: mid for _, (label, mid) in HOUSE_OCR_AMOUNT_MAP.items()}


def _fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def _eq(a, b):
    fa, fb = _fnum(a), _fnum(b)
    if math.isnan(fa) and math.isnan(fb):
        return True
    return abs(fa - fb) < 1e-6


def main():
    bad = 0

    # 1) amount_midpoint digital (06)
    ok = tot = 0
    for y in YEARS:
        p = TABLES / str(y) / f"06_house_{y}_transactions.csv"
        if not p.exists():
            continue
        d = pd.read_csv(p, dtype=str)
        for rng, mid in zip(d["amount_range"], d["amount_midpoint"]):
            tot += 1
            ok += _eq(amount_midpoint(rng), mid)
    print(f"  amount_midpoint DIGITAL : {ok}/{tot} " + ("✅" if ok == tot else f"❌ {tot-ok}"))
    bad += tot - ok

    # 2) amount_midpoint OCR (06b) via libellé→midpoint
    ok = tot = 0
    for y in YEARS:
        p = TABLES / str(y) / f"06b_house_{y}_ocr_transactions.csv"
        if not p.exists():
            continue
        d = pd.read_csv(p, dtype=str)
        for rng, mid in zip(d["amount_range"], d["amount_midpoint"]):
            tot += 1
            expected = LABEL2MID.get(str(rng), float("nan"))
            ok += _eq(expected, mid)
    print(f"  amount_midpoint OCR     : {ok}/{tot} " + ("✅" if ok == tot else f"❌ {tot-ok}"))
    bad += tot - ok

    # 3) infer_asset_type OCR (06b)
    ok = tot = 0
    miss = []
    for y in YEARS:
        p = TABLES / str(y) / f"06b_house_{y}_ocr_transactions.csv"
        if not p.exists():
            continue
        d = pd.read_csv(p, dtype=str)
        for desc, at in zip(d["asset_description"], d["asset_type"]):
            tot += 1
            got = infer_asset_type(desc, "house")
            exp = None if (at is None or (isinstance(at, float) and math.isnan(at)) or str(at) == "nan") else at
            if (got or None) == (exp or None):
                ok += 1
            elif len(miss) < 5:
                miss.append((desc, exp, got))
    print(f"  infer_asset_type OCR    : {ok}/{tot} " + ("✅" if ok == tot else f"❌ {tot-ok}"))
    for desc, exp, got in miss:
        print(f"      ❌ '{str(desc)[:45]}' stocké={exp} recomp={got}")
    bad += tot - ok

    print("\nRÉSULTAT :", "✅ AMOUNTS/TICKERS REPRODUITS" if bad == 0 else f"❌ {bad} écarts")
    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
