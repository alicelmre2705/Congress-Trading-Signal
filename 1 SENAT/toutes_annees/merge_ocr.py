#!/usr/bin/env python
"""Fusion digital + OCR papier → table FINALE par an (Sénat toutes années).

Pour chaque année : concatène la table digitale (`06_senate_{an}_transactions.csv`) et l'OCR papier
(`06b_senate_{an}_ocr_transactions.csv` si présente), déduplique de façon NON destructrice sur
(natural_key_hash, occurrence_index), écrit `06_senate_{an}_FINAL.csv`. Produit `00_final_status.csv`
(digital + OCR + final par an). Aucune validation Quiver sur la couche OCR (Quiver-aveugle au papier).
"""
import glob
import re
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


def main():
    rows = []
    years = sorted(int(re.search(r"/(\d{4})/", p).group(1))
                   for p in glob.glob(str(DATA / "20*" / "06_senate_*_transactions.csv")))
    for y in years:
        ydir = DATA / str(y)
        dig = pd.read_csv(ydir / f"06_senate_{y}_transactions.csv", dtype=str)
        ocr_path = ydir / f"06b_senate_{y}_ocr_transactions.csv"
        if ocr_path.exists():
            ocr = pd.read_csv(ocr_path, dtype=str)
            final = pd.concat([dig, ocr.reindex(columns=dig.columns)], ignore_index=True)
            n_before = len(final)
            final = final.drop_duplicates(["natural_key_hash", "occurrence_index"], keep="first")
            n_ocr_added = len(final) - len(dig)
            n_dups = n_before - len(final)
        else:
            ocr = pd.DataFrame()
            final = dig.copy()
            n_ocr_added, n_dups = 0, 0
        final.to_csv(ydir / f"06_senate_{y}_FINAL.csv", index=False)

        midp = pd.to_numeric(final["amount_midpoint"], errors="coerce")
        rows.append({
            "year": y, "n_digital": len(dig), "n_ocr": len(ocr), "n_ocr_added": n_ocr_added,
            "n_dups_intersource": n_dups, "n_final": len(final),
            "senateurs_final": final["bioguide_id"].nunique(),
            "ticker_pct_final": round(100 * final["ticker"].notna().mean(), 1),
            "volume_final_musd": round(midp.sum() / 1e6, 1),
        })
        print(f"  {y}: digital {len(dig):4} + OCR {len(ocr):3} → FINAL {len(final):4} "
              f"(dédup inter-sources {n_dups})")

    dash = pd.DataFrame(rows)
    dash.to_csv(DATA / "00_final_status.csv", index=False)
    print("\n=== 00_final_status.csv ===")
    print(dash.to_string(index=False))
    print(f"\nTOTAL FINAL (digital + OCR) : {dash['n_final'].sum()} txns "
          f"| dont OCR papier ajouté : {dash['n_ocr_added'].sum()}")


if __name__ == "__main__":
    main()
