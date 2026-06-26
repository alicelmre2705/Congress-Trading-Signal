#!/usr/bin/env python
"""Recalcule les tables de concordance Quiver FRAÎCHES sur le FINAL actuel (les 07/06d du disque
étaient périmées, pré-rebuild OCR). Écrit par année 07_quiver_comparison.csv (FINAL vs Quiver) +
06d_ocr_quiver_comparison.csv (OCR vs Quiver), et un récap global 00_concordance_finale.csv
(cov%, accord sens/montant, vrais-absents). Source de vérité du rapport superviseur. LECTURE des
PDF non requise (offline ; cache Quiver local)."""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, ".")
import house.digital as hm
from congress_core import quiver as qv

TABLES = Path("data/house/tables")
YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]


def paper_bios(year):
    """bioguides ayant ≥1 PTR scanné (non_lisible) cette année → écart Quiver attendu (papier)."""
    man = pd.read_csv(TABLES / str(year) / "04_download_manifest.csv", dtype=str)
    ptr = pd.read_csv(TABLES / str(year) / "03_ptr_index.csv", dtype=str)
    scanned = man[man["bucket"] == "non_lisible"][["doc_id"]].merge(ptr, on="doc_id", how="left")
    bios = scanned.apply(lambda r: hm.match_bioguide(r.get("last", ""), r.get("first", "")), axis=1)
    return set(bios.dropna())


def main():
    hm.build_reference()
    q = pd.read_csv(TABLES / "_quiver_house_cache.csv")
    recap = []
    for y in YEARS:
        ws, we = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31")
        final = pd.read_csv(TABLES / str(y) / f"06_house_{y}_FINAL.csv", dtype=str)
        pb = paper_bios(y)

        # FINAL vs Quiver (clé House brute) → 07_quiver_comparison.csv
        cmp, real_miss, stats = qv.validate_quiver_house(final, q, ws, we, pb)
        cmp.to_csv(TABLES / str(y) / f"07_quiver_comparison.csv")
        real_miss.to_csv(TABLES / str(y) / f"07b_quiver_truly_absent.csv", index=False)

        # accord de champs via reconcile (renomme colonnes Quiver)
        qy = q.copy()
        qy["filed"] = pd.to_datetime(qy["filed"], errors="coerce")
        qy = qy[(qy["filed"] >= ws) & (qy["filed"] <= we)].rename(columns={"traded": "Traded", "filed": "Filed"})
        rec = qv.reconcile(final, qy)
        fa = rec["field_agreement"].set_index("field")["agreement_pct"]

        # OCR vs Quiver → 06d
        ocr = pd.read_csv(TABLES / str(y) / f"06b_house_{y}_ocr_transactions.csv", dtype=str)
        qd = q.copy(); qd["_f"] = pd.to_datetime(qd["filed"], errors="coerce")
        qd = qd[(qd["_f"] >= ws) & (qd["_f"] <= we)]
        ocr_cmp = (ocr.groupby("bioguide_id").agg(name=("declarant_name", "first"),
                   docs=("doc_id", "nunique"), n_ocr=("doc_id", "count")).reset_index())
        ocr_cmp["n_quiver"] = ocr_cmp["bioguide_id"].map(qd.groupby("BioGuideID").size()).fillna(0).astype(int)
        ocr_cmp["delta"] = ocr_cmp["n_ocr"] - ocr_cmp["n_quiver"]
        ocr_cmp.sort_values("n_ocr", ascending=False).to_csv(
            TABLES / str(y) / f"06d_ocr_quiver_comparison.csv", index=False)

        recap.append({"annee": y, "final": len(final), "quiver": stats["quiver_total"],
                      "cov_pct": stats["coverage_of_quiver_pct"], "matched": stats["set_matched"],
                      "only_quiver": stats["set_only_quiver"], "only_ours": stats["set_only_ours"],
                      "sense_pct": fa.get("sense"), "amount_pct": fa.get("amount_bucket"),
                      # BRUT : only-Quiver pour déclarants sans papier cette année (inclut artefacts
                      # ticker / amendements / dates ±1j ; ≠ « vraiment absent » qui est le résidu curé).
                      "only_q_digital_brut": stats["n_real_missing_trades"]})
        print(f"  {y}: cov {stats['coverage_of_quiver_pct']}% | sens {fa.get('sense')}% | "
              f"montant {fa.get('amount_bucket')}% | only-Q digital (brut) {stats['n_real_missing_trades']}")

    df = pd.DataFrame(recap)
    df.to_csv(TABLES / "00_concordance_finale.csv", index=False)
    tot_m = df["matched"].sum(); tot_q = df["matched"].sum() + df["only_quiver"].sum()
    print(f"\n  GLOBAL cov = {100*tot_m/tot_q:.1f}% | only-Q digital brut total = {df['only_q_digital_brut'].sum()} | "
          f"→ data/house/tables/00_concordance_finale.csv")


if __name__ == "__main__":
    main()
