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

from common import reference, enrich_tenure  # noqa: E402

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
    # 13 années (2014-2026) × 2 chambres depuis l'extension pré-2020 (la valeur 14 datait
    # de la fenêtre 2020-2026 et faisait échouer le test alors que les lignes étaient justes).
    EXPECTED_FILES = 26
    ok = (mism == 0) and (files == EXPECTED_FILES)
    print(f"\n{files} fichiers FINAL (attendus : {EXPECTED_FILES}), {total} lignes vérifiées, {mism} écarts")
    print("RÉSULTAT :", f"✅ years_in_office REPRODUIT (zéro écart, {EXPECTED_FILES} FINAL)"
          if ok else "❌ ÉCART / fichiers manquants")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
