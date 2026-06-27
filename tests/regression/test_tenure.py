#!/usr/bin/env python
"""Reproduction de `years_in_office` : recompute la colonne depuis (bioguide_id, transaction_date)
+ le référentiel embarqué (offline) et la compare à la valeur figée des FINAL. Même esprit que
test_senate_repro : prouve la métadonnée sans re-jouer le pipeline, et garantit qu'elle est
déterministe à partir des entrées gelées.
"""
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from congress_core import reference, enrich_tenure  # noqa: E402

COL = enrich_tenure.COLUMN


def main():
    refs, total, mism, files = {}, 0, 0, 0
    for chamber, year, path in enrich_tenure.final_files(REPO):
        if chamber not in refs:
            refs[chamber] = reference.load_reference(REPO / "data" / chamber / "reference",
                                                    chamber=chamber, live=False)
        df = pd.read_csv(path, dtype=str)
        files += 1
        if COL not in df.columns:
            print(f"  ❌ {chamber} {year} : colonne {COL} absente")
            mism += 1
            continue
        recomputed = reference.add_years_in_office(df.drop(columns=[COL]), refs[chamber])[COL]
        stored = pd.to_numeric(df[COL], errors="coerce").astype("Float64")
        recomp = pd.to_numeric(pd.Series(recomputed), errors="coerce").astype("Float64")
        neq = (stored != recomp) & ~(stored.isna() & recomp.isna())
        n = int(neq.sum())
        total += len(df)
        mism += n
        if n:
            print(f"  ❌ {chamber} {year} : {n}/{len(df)} écarts")
    ok = (mism == 0) and (files == 14)
    print(f"\n{files} fichiers FINAL, {total} lignes vérifiées, {mism} écarts")
    print("RÉSULTAT :", "✅ years_in_office REPRODUIT (zéro écart, 14 FINAL)"
          if ok else "❌ ÉCART / fichiers manquants")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
