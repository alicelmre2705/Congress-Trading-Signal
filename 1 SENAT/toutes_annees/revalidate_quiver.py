#!/usr/bin/env python
"""Re-validation Quiver OFFLINE (sans eFD) — applique la dédup des amendements de reconcile().

Relit les tables digitales `06_senate_{an}_transactions.csv` DÉJÀ extraites + le cache Quiver local,
re-exécute `validate_quiver_sample.reconcile()` (désormais avec dédup des amendements Quiver), réécrit
`07c-f` + `07` par an, et met à jour les colonnes Quiver du dashboard `00_year_status.csv`. Ne touche NI
à l'eFD NI aux tables de transactions — seulement les artefacts de validation. Idempotent.
"""
import sys
import glob
import re
from pathlib import Path
from collections import Counter

import pandas as pd

HERE = Path(__file__).resolve().parent
Q1 = HERE.parent / "senat_2025_test"
sys.path.insert(0, str(Q1))
from senate_finalize import load_reference        # noqa: E402
import validate_quiver_sample as vq               # noqa: E402

DATA = HERE / "data"
QUIVER_CACHE = Q1 / "data_v1_senate" / "tables" / "_quiver_senate_cache.csv"


def verdict(r):
    if r["nous"] == 0:
        return "quiver_seul"
    if r["delta"] == 0:
        return "concordant"
    if r["quiver"] == 0:
        return "quiver_sans_donnee"
    return "nous_plus" if r["delta"] > 0 else "quiver_plus_a_verifier"


def main():
    ref = load_reference()[0]
    senate_bios = {b for b, v in ref.items() if v["chamber"] == "senate"}
    q = pd.read_csv(QUIVER_CACHE)
    q["Filed"] = pd.to_datetime(q["Filed"], errors="coerce")
    q["Traded"] = pd.to_datetime(q["Traded"], errors="coerce")

    status_path = DATA / "00_year_status.csv"
    old = pd.read_csv(status_path).set_index("year") if status_path.exists() else None

    years = sorted(int(re.search(r"/(\d{4})/", p).group(1))
                   for p in glob.glob(str(DATA / "20*" / "06_senate_*_transactions.csv")))
    rows = []
    for y in years:
        ydir = DATA / str(y)
        df = pd.read_csv(ydir / f"06_senate_{y}_transactions.csv", dtype=str)
        qy = q[(q["Filed"].dt.year == y) & (q["BioGuideID"].isin(senate_bios))].copy()
        rec = vq.reconcile(df, qy)
        rec["txn_reco"].to_csv(ydir / "07c_quiver_txn_reconciliation.csv", index=False)
        rec["field_agreement"].to_csv(ydir / "07d_quiver_field_agreement.csv", index=False)
        rec["ticker_per_sen"].to_csv(ydir / "07e_quiver_ticker_per_senator.csv", index=False)
        rec["only_quiver_txn"].to_csv(ydir / "07f_quiver_only_quiver_txn.csv", index=False)
        cmp = rec["deltas"].copy()
        cmp["verdict"] = cmp.apply(verdict, axis=1)
        cmp.to_csv(ydir / "07_quiver_comparison.csv", index=False)

        m = rec["txn_reco"].set_index("metric")["value"]
        fa = rec["field_agreement"].set_index("field")["agreement_pct"]
        vc = Counter(cmp["verdict"])
        base = old.loc[y].to_dict() if (old is not None and y in old.index) else {}
        base.update({
            "year": y, "n_txns": len(df), "n_senateurs": int(df["bioguide_id"].nunique()),
            "ticker_pct": round(100 * df["ticker"].notna().mean(), 1) if len(df) else 0.0,
            "quiver_txns": int(qy.shape[0]),
            "coverage_pct": m.get("coverage_pct"), "only_quiver": int(m.get("only_quiver", 0)),
            "quiver_amendment_dups": int(m.get("quiver_amendment_dups", 0)),
            "delta_total": int(cmp["delta"].sum()),
            "concordant": vc.get("concordant", 0), "nous_plus": vc.get("nous_plus", 0),
            "quiver_sans_donnee": vc.get("quiver_sans_donnee", 0),
            "sens_pct": fa.get("sense"), "date_traded_pct": fa.get("date_traded"),
            "montant_pct": fa.get("amount_bucket"),
        })
        rows.append(base)
        print(f"  {y}: txns={len(df):4} | couverture={m.get('coverage_pct')}% "
              f"only_q={int(m.get('only_quiver',0))} | amend_dups Quiver retirés={int(m.get('quiver_amendment_dups',0))} "
              f"| Δ={int(cmp['delta'].sum())}")

    dash = pd.DataFrame(rows).sort_values("year")
    dash.to_csv(status_path, index=False)
    print("\n=== 00_year_status.csv (revalidé — dédup amendements Quiver) ===")
    print(dash.to_string(index=False))
    print(f"\nTOTAL amendements Quiver dédupliqués : {int(dash['quiver_amendment_dups'].sum())} "
          f"| couverture min/max = {dash['coverage_pct'].min()}–{dash['coverage_pct'].max()}% "
          f"| only_quiver cumulé = {int(dash['only_quiver'].sum())}")


if __name__ == "__main__":
    main()
