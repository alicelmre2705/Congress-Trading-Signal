#!/usr/bin/env python
"""Re-joue UNIQUEMENT la validation Quiver (honnête, per-lot + set-overlap) sur les tables 06
déjà produites, sans re-parser les PDF. Régénère 07/07b par année + 00_year_status.csv."""
import pandas as pd
import house_multiyear as hm

print("Référentiel (pour match_bioguide des PTR papier)…")
hm.build_reference()

YEARS = ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]
rows = []
for y in YEARS:
    yd = hm.TABROOT / y
    df = pd.read_csv(yd / f"06_house_{y}_transactions.csv", dtype={"doc_id": str})
    man = pd.read_csv(yd / "04_download_manifest.csv", dtype={"doc_id": str})
    ptr = pd.read_csv(yd / "03_ptr_index.csv", dtype={"doc_id": str})
    ws, we = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31")
    qv = hm.validate_quiver(df, man, ptr, int(y), ws, we, yd)
    nlis = int((man["bucket"] == "lisible").sum())
    nnon = int((man["bucket"] == "non_lisible").sum())
    print(f"{y}: txns {len(df)} | recouvrement Quiver {qv['coverage_of_quiver_pct']}% "
          f"(matched {qv['set_matched']} / only-Q {qv['set_only_quiver']} / only-nous {qv['set_only_ours']}) "
          f"| vrais trades manqués (digital) {qv['n_real_missing_trades']}")
    v = qv["verdicts"]
    rows.append({"year": y, "n_ptr": len(ptr), "n_lisible": nlis, "n_non_lisible": nnon,
                 "n_txns_digital": len(df), "n_declarants": int(df["declarant_name"].nunique()),
                 "quiver_coverage_pct": qv["coverage_of_quiver_pct"],
                 "set_matched": qv["set_matched"], "set_only_quiver": qv["set_only_quiver"],
                 "set_only_nous": qv["set_only_ours"],
                 "vrais_trades_manques": qv["n_real_missing_trades"],
                 "decl_concordant": v.get("concordant", 0), "decl_nous_plus": v.get("nous_plus", 0),
                 "decl_quiver_vide": v.get("quiver_sans_donnee", 0),
                 "decl_manquant_papier": v.get("manquant_papier", 0)})

status = pd.DataFrame(rows)
status.to_csv(hm.TABROOT / "00_year_status.csv", index=False)
print("\n→ 00_year_status.csv")
print(status.to_string(index=False))
