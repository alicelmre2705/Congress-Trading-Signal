#!/usr/bin/env python
"""PREUVE Phase 2 (identité) — priorité #1.

Partie A — fidélité du port : le matcher de house.identity == house_multiyear.match_bioguide
ORIGINAL sur TOUTES les paires (last, first) des index PTR (même référentiel live). Doit être 100 %.

Partie B — reproduction des bioguides figés : pour chaque doc des tables 06/06b, on relit (last, first)
dans 03_ptr_index, on recompute le bioguide et on le compare au bioguide_id stocké. Doit être ~100 %
(tout écart = dérive de millésime du référentiel, à expliquer).

    .venv/bin/python tests/regression/test_identity.py
"""
import sys
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ENGINE = REPO / "data" / "house"
TABLES = ENGINE / "tables"
REF_DIR = ENGINE / "reference"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO))
YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]


def main():
    import house.digital as hm
    hm.build_reference()  # référentiel live → globals + hm.match_bioguide (l'original)

    from congress_core.reference import load_reference
    from house.identity import make_matcher
    ref = load_reference(REF_DIR, chamber="house", live=True)
    match = make_matcher(ref)
    print(f"  référentiel cœur : {len(ref.ref_universe)} | source {ref.source}")

    # index doc_id → (last, first)
    doc2lf = {}
    pairs = set()
    for y in YEARS:
        p = TABLES / str(y) / f"03_ptr_index.csv"
        if not p.exists():
            continue
        idx = pd.read_csv(p, dtype=str)
        for _, r in idx.iterrows():
            lf = (r.get("last") or "", r.get("first") or "")
            doc2lf[str(r["doc_id"])] = lf
            pairs.add(lf)

    # ---- Partie A : fidélité du port ----
    bad_a = 0
    for last, first in pairs:
        if match(last, first) != hm.match_bioguide(last, first):
            bad_a += 1
            if bad_a <= 5:
                print(f"   ❌ port: ({last!r},{first!r}) cœur={match(last,first)} orig={hm.match_bioguide(last,first)}")
    print(f"  Partie A (port == original) : {len(pairs)-bad_a}/{len(pairs)} "
          + ("✅" if bad_a == 0 else f"❌ {bad_a}"))

    # ---- Partie B : reproduction des bioguides figés ----
    ok = tot = 0
    drift = []
    for y in YEARS:
        for pat in [f"{y}/06_house_{y}_transactions.csv", f"{y}/06b_house_{y}_ocr_transactions.csv"]:
            p = TABLES / pat
            if not p.exists():
                continue
            df = pd.read_csv(p, dtype=str)
            seen = df.drop_duplicates("doc_id")[["doc_id", "bioguide_id"]]
            for _, r in seen.iterrows():
                d = str(r["doc_id"])
                if d not in doc2lf:
                    continue
                tot += 1
                got = match(*doc2lf[d])
                stored = r["bioguide_id"] if pd.notna(r["bioguide_id"]) else None
                if (got or None) == (stored or None):
                    ok += 1
                elif len(drift) < 8:
                    drift.append((d, doc2lf[d], stored, got))
    print(f"  Partie B (repro bioguides figés, par doc) : {ok}/{tot} "
          + ("✅" if ok == tot else f"⚠ {tot-ok} dérives"))
    for d, lf, stored, got in drift:
        print(f"      doc {d} {lf} stocké={stored} recomp={got}")

    fail = bad_a > 0
    print("\nRÉSULTAT :", "✅ MATCHER = PORT FIDÈLE" if not fail else "❌ PORT INFIDÈLE")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
