#!/usr/bin/env python
"""A2-House — dédup `(nk, occ)` + secteur GICS→ETF sur les FINAL House toutes_annees (parité Sénat).

Les `06_house_{an}_FINAL.csv` (digital+OCR déjà fusionné, **déjà** dotés de `date_confidence` +
`ticker_source`) n'ont pas `sector_gics`/`etf_proxy`, et la fusion House laisse passer des **doublons
exacts** sur `(natural_key_hash, occurrence_index)` (elle ne déduplique que OCR-vs-digital sur
`natural_key_hash`). Ce script, sur le corpus choisi, en une passe :
  1. retire les doublons `(nk, occ)` (parité avec la fusion Sénat `merge_ocr.py`) ;
  2. ajoute `sector_gics`/`etf_proxy`/`sector_source` via `sector_enrich.enrich_sectors` (module Q1, éprouvé) ;
  3. préserve toutes les autres colonnes (dont `date_confidence`, `ticker_source`) ; n'ajoute/supprime
     aucune AUTRE ligne.

`--out-dir` écrit ailleurs que la donnée réelle (validation cheap sans rien muter). Sans `--out-dir`,
réécrit en place — à réserver au **run complet quand House est figé** (les FINAL sont régénérés par
`house_ocr_multiyear`, donc cet enrichissement doit être le dernier passage).

Usage :
  validation : python finalize_house_sector.py --years 2024 --out-dir /chemin/scratch
  run gelé   : python finalize_house_sector.py --years 2020,2021,2022,2023,2024,2025,2026
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
Q1 = HERE.parent / "2025_test"            # sector_enrich.py (module Q1 figé) + cache secteur partagé
sys.path.insert(0, str(Q1))
DATA = HERE / "data_v1" / "tables"

import sector_enrich as se                # noqa: E402

DEDUP_KEY = ["natural_key_hash", "occurrence_index"]


def _reorder(df):
    """Insère sector_gics/etf_proxy après asset_type, sector_source après ticker_source."""
    cols = [c for c in df.columns if c not in ("sector_gics", "etf_proxy", "sector_source", "_year")]
    out = []
    for c in cols:
        out.append(c)
        if c == "asset_type":
            out += ["sector_gics", "etf_proxy"]
        if c == "ticker_source":
            out.append("sector_source")
    # filets si les colonnes d'ancrage manquent
    for extra in ("sector_gics", "etf_proxy", "sector_source"):
        if extra not in out and extra in df.columns:
            out.append(extra)
    return df.reindex(columns=out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2020,2021,2022,2023,2024,2025,2026")
    ap.add_argument("--out-dir", default=None,
                    help="répertoire de sortie (défaut = donnée réelle). Validation : passer un scratch.")
    ap.add_argument("--no-llm", action="store_true",
                    help="secteur via yfinance seul (skip repli LLM) — validation cheap, ~0 token.")
    args = ap.parse_args()
    years = [int(y) for y in args.years.split(",") if y.strip()]
    out_root = Path(args.out_dir) if args.out_dir else DATA
    in_place = args.out_dir is None
    print(f"=== A2-House : dédup + secteur | années {years} | sortie {'EN PLACE' if in_place else out_root} ===")
    if in_place:
        print("  ⚠️ écriture EN PLACE sur la donnée réelle (réservé au run figé).")

    # --- Étape 1 : lecture + dédup (nk,occ) par année ---
    frames, meta = [], {}
    for y in years:
        f = DATA / str(y) / f"06_house_{y}_FINAL.csv"
        if not f.exists():
            print(f"  {y}: FINAL absent → ignoré"); continue
        df = pd.read_csv(f, dtype=str)
        n0 = len(df)
        df = df.drop_duplicates(DEDUP_KEY, keep="first").reset_index(drop=True)
        df["_year"] = y
        frames.append(df)
        meta[y] = {"n_before": n0, "n_after": len(df), "dups": n0 - len(df),
                   "tk_pct": round(100 * df["ticker"].notna().mean(), 1) if len(df) else 0.0}
    if not frames:
        print("  Aucune table FINAL trouvée — arrêt."); return
    big = pd.concat(frames, ignore_index=True)
    print(f"Corpus : {len(big)} lignes (après dédup) / {len(frames)} années — enrichissement secteur…")

    # --- Étape 2 : secteur GICS → ETF (une passe, cache partagé Q1) ---
    big = se.enrich_sectors(big, with_llm=not args.no_llm)
    if args.no_llm:
        print("  (--no-llm : secteur yfinance seul, repli LLM sauté)")

    # --- Écriture par année + dashboard ---
    rows = []
    for y in years:
        if y not in meta:
            continue
        sub = _reorder(big[big["_year"] == y].drop(columns="_year"))
        outdir = out_root / str(y)
        outdir.mkdir(parents=True, exist_ok=True)
        sub.to_csv(outdir / f"06_house_{y}_FINAL.csv", index=False)
        m = meta[y]
        rows.append({
            "year": y, "n_before": m["n_before"], "dups_removed": m["dups"], "n_final": len(sub),
            "ticker_pct": m["tk_pct"],
            "sector_pct": round(100 * sub["sector_gics"].notna().mean(), 1),
            "date_implausible": int((sub["date_confidence"] == "implausible").sum()) if "date_confidence" in sub else None,
        })
        print(f"  {y}: {m['n_before']:6}→{len(sub):6} (−{m['dups']} doublons) | "
              f"ticker {m['tk_pct']:.0f}% | secteur {rows[-1]['sector_pct']:.0f}%")

    dash = pd.DataFrame(rows)
    dash.to_csv(out_root / "00_final_sector_status.csv", index=False)
    n_sec = int(big["sector_gics"].notna().sum())
    print("\n=== 00_final_sector_status.csv ===")
    print(dash.to_string(index=False))
    print(f"\nTOTAL {len(big)} lignes | doublons retirés {dash['dups_removed'].sum()} | "
          f"secteur {round(100*n_sec/len(big),1)}% ({n_sec}/{len(big)}) | "
          f"sources secteur={big['sector_source'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
