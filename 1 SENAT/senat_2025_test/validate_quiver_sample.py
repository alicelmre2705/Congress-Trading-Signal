#!/usr/bin/env python
"""Validation EXHAUSTIVE de la correspondance Sénat ↔ Quiver — module canonique + CLI.

Deux usages :
  - importé par `senate_finalize.py` : `reconcile(df, qwin)` renvoie les tables d'aspects
    (couverture txn, ticker par sénateur, accord sens/date/montant, deltas) → 07c/07d/07e/07f.
  - en CLI (`python validate_quiver_sample.py`) : lit les CSV existants, filtre les délégués,
    appelle `reconcile`, imprime le récit des 7 aspects et écrit `tables/audit/*.csv`.

LECTURE SEULE côté données : ne modifie jamais la table de prod. Conçu pour être rejoué à
l'identique année par année lors du passage multi-années (la clé d'appariement éprouvée ici —
`transaction_date ↔ Quiver Traded`, montant par bucket borne-basse — y est directement réutilisable).
"""
import re
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "data_v1_senate"
TAB = OUT / "tables"
AUDIT = TAB / "audit"

WIN_START = pd.Timestamp("2025-01-01")
WIN_END = pd.Timestamp("2025-03-31")


def norm_ticker(t):
    if not isinstance(t, str):
        return ""
    t = t.upper().strip()
    if t in ("", "NAN", "NONE", "--"):
        return ""
    # AHL-C / AHL.C → AHL_C ; on retire un éventuel suffixe option pour la clé instrument
    t = re.sub(r"\s+(PUT|CALL)$", "", t)
    return t.replace(".", "_").replace("-", "_")


def norm_sense(s):
    """Granularité réduite pour l'appariement : Purchase / Sale / Exchange."""
    s = str(s).strip().lower()
    if s.startswith("p"):
        return "Purchase"
    if s.startswith("s"):
        return "Sale"
    if s.startswith("e"):
        return "Exchange"
    return s or "?"


def _low_bound(rng):
    """Borne basse de la fourchette de montant. Quiver Trade_Size_USD = cette borne basse."""
    m = re.search(r"\$([\d,]+)", str(rng))
    return int(m.group(1).replace(",", "")) if m else None


def reconcile(df, qwin):
    """Réconcilie notre table `df` (FINAL) avec `qwin` (Quiver Sénat, fenêtre Filed, déjà filtré
    sur les vrais sénateurs côté appelant). Renvoie un dict de DataFrames d'audit.

    Appariement : `transaction_date ↔ Quiver Traded` ; montant par bucket borne-basse.
    Restreint aux sénateurs communs et aux actifs tickérisables (Quiver ne peut apparier ni une
    obligation ni un actif sans ticker)."""
    d = df.copy()
    d["tk"] = d["ticker"].map(norm_ticker)
    d["sense"] = d["operation_type"].map(norm_sense)
    d["d"] = pd.to_datetime(d["transaction_date"], errors="coerce").dt.date
    d["lb"] = d["amount_range"].map(_low_bound)

    q = qwin.copy()
    q["tk"] = q["Ticker"].map(norm_ticker)
    q["sense"] = q["Transaction"].map(norm_sense)
    q["dt"] = pd.to_datetime(q["Traded"], errors="coerce").dt.date
    q["fd"] = pd.to_datetime(q["Filed"], errors="coerce").dt.date
    q["qlb"] = pd.to_numeric(q["Trade_Size_USD"], errors="coerce")

    common = set(d["bioguide_id"].dropna()) & set(q["BioGuideID"].dropna())
    o = d[d["bioguide_id"].isin(common) & (d["tk"] != "")]
    qo = q[q["BioGuideID"].isin(common) & (q["tk"] != "")]

    # --- Aspect 2 : couverture transaction-niveau (clé bioguide×ticker×date(Traded)×sens) ---
    ours_k = set(zip(o["bioguide_id"], o["tk"], o["d"], o["sense"]))
    quiv_k = set(zip(qo["BioGuideID"], qo["tk"], qo["dt"], qo["sense"]))
    quiv_k_filed = set(zip(qo["BioGuideID"], qo["tk"], qo["fd"], qo["sense"]))
    matched, onlyq, onlyo = ours_k & quiv_k, quiv_k - ours_k, ours_k - quiv_k
    cov = round(100 * len(matched) / len(quiv_k), 1) if quiv_k else None
    txn_reco = pd.DataFrame([
        {"metric": "common_senators", "value": len(common)},
        {"metric": "ours_tickerizable", "value": len(ours_k)},
        {"metric": "quiver", "value": len(quiv_k)},
        {"metric": "matched", "value": len(matched)},
        {"metric": "only_quiver", "value": len(onlyq)},
        {"metric": "only_ours", "value": len(onlyo)},
        {"metric": "coverage_pct", "value": cov},
    ])
    only_quiver_txn = pd.DataFrame(sorted(onlyq), columns=["bioguide", "ticker", "date", "sense"])

    # --- Aspect 3 : correspondance ticker par sénateur ---
    rows = []
    for b in sorted(common, key=lambda b: -(d["bioguide_id"] == b).sum()):
        ot = set(o[o["bioguide_id"] == b]["tk"]) - {""}
        qt = set(qo[qo["BioGuideID"] == b]["tk"]) - {""}
        nm = d[d["bioguide_id"] == b]["declarant_name"].iloc[0]
        rows.append({"bioguide": b, "name": nm, "n_tk_nous": len(ot), "n_tk_quiver": len(qt),
                     "inter": len(ot & qt), "nous_seul": len(ot - qt), "quiver_seul": len(qt - ot),
                     "quiver_seul_list": ",".join(sorted(qt - ot))})
    ticker_per_sen = pd.DataFrame(rows)

    # --- Aspects 4/5/6 : accord sens, date (Traded vs Filed), montant (bucket) ---
    om = o[["bioguide_id", "tk", "d", "sense", "lb"]]
    qm = qo[["BioGuideID", "tk", "dt", "sense", "qlb"]].rename(
        columns={"BioGuideID": "bioguide_id", "dt": "d", "sense": "sense_q"})
    j = om.merge(qm, on=["bioguide_id", "tk", "d"])
    sense_agree = round(100 * (j["sense"] == j["sense_q"]).mean(), 1) if len(j) else None
    amt_agree = round(100 * (j["lb"] == j["qlb"]).mean(), 1) if len(j) else None
    date_traded = round(100 * len(matched) / len(quiv_k), 1) if quiv_k else None
    date_filed = round(100 * len(ours_k & quiv_k_filed) / len(quiv_k), 1) if quiv_k else None
    field_agreement = pd.DataFrame([
        {"field": "sense", "agreement_pct": sense_agree, "n_pairs": len(j),
         "note": "désaccords = artefact merge option-vs-action même jour (cf. AUDIT_SENAT.md)"},
        {"field": "date_traded", "agreement_pct": date_traded, "n_pairs": len(quiv_k),
         "note": "appariement sur Quiver Traded = vraie date de trade"},
        {"field": "date_filed", "agreement_pct": date_filed, "n_pairs": len(quiv_k),
         "note": "Filed ≠ date de trade → ne pas apparier dessus"},
        {"field": "amount_bucket", "agreement_pct": amt_agree, "n_pairs": len(j),
         "note": "Quiver Trade_Size_USD = borne basse exacte de la fourchette"},
    ])

    # --- Aspect 7 : deltas par sénateur (catégorisation) ---
    nous = d.groupby("bioguide_id").size()
    quiv = q.groupby("BioGuideID").size()
    bios = sorted(set(nous.index) | set(quiv.index), key=lambda b: -int(nous.get(b, 0)))
    drows = []
    for b in bios:
        n, qv = int(nous.get(b, 0)), int(quiv.get(b, 0))
        sub = d[d["bioguide_id"] == b]
        nm = (sub["declarant_name"].iloc[0] if n else q[q["BioGuideID"] == b]["Name"].iloc[0])
        ocr = int((sub["provenance"] == "senate-efd-ocr").sum()) if "provenance" in sub else 0
        drows.append({"bioguide": b, "name": nm, "nous": n, "quiver": qv, "delta": n - qv,
                      "no_ticker": int((sub["tk"] == "").sum()), "ocr": ocr})
    deltas = pd.DataFrame(drows)

    return {"txn_reco": txn_reco, "only_quiver_txn": only_quiver_txn,
            "ticker_per_sen": ticker_per_sen, "field_agreement": field_agreement, "deltas": deltas}


def _load_inputs():
    """CLI : charge notre FINAL + le cache Quiver, filtre la fenêtre et les vrais sénateurs."""
    df = pd.read_csv(OUT / "senate_2025q1_FINAL.csv", dtype=str)
    q = pd.read_csv(TAB / "_quiver_senate_cache.csv")
    q["Filed"] = pd.to_datetime(q["Filed"], errors="coerce")
    qwin = q[(q["Filed"] >= WIN_START) & (q["Filed"] <= WIN_END)].copy()
    # filtre délégués (même logique que senate_finalize) via le référentiel
    try:
        from senate_finalize import load_reference
        ref = load_reference()[0]
        senate_bios = {b for b, v in ref.items() if v["chamber"] == "senate"}
        before = qwin["BioGuideID"].nunique()
        qwin = qwin[qwin["BioGuideID"].isin(senate_bios)]
        dropped = before - qwin["BioGuideID"].nunique()
        if dropped:
            print(f"(CLI) {dropped} déposant(s) hors-chambre exclu(s) du côté Quiver.")
    except Exception as e:
        print("(CLI) filtre délégués non appliqué :", e)
    return df, qwin


def main():
    AUDIT.mkdir(parents=True, exist_ok=True)
    df, qwin = _load_inputs()
    print(f"NOUS  : {len(df)} txns / {df['bioguide_id'].nunique()} sénateurs")
    print(f"QUIVER: {len(qwin)} txns (Filed Q1, sénateurs) / {qwin['BioGuideID'].nunique()} sénateurs")

    rec = reconcile(df, qwin)
    for name, key in [("07c_txn_reconciliation", "txn_reco"),
                      ("07d_field_agreement", "field_agreement"),
                      ("ticker_par_senateur", "ticker_per_sen"),
                      ("only_quiver_txn", "only_quiver_txn"),
                      ("deltas_par_senateur", "deltas")]:
        rec[key].to_csv(AUDIT / f"{name}.csv", index=False)

    m = rec["txn_reco"].set_index("metric")["value"]
    fa = rec["field_agreement"].set_index("field")["agreement_pct"]
    print("\n=== Couverture transaction-niveau ===")
    print(rec["txn_reco"].to_string(index=False))
    print(f"\n>>> COUVERTURE Quiver = {m['coverage_pct']}%  | only_quiver = {int(m['only_quiver'])}")
    print("\n=== Accord par champ ===")
    print(rec["field_agreement"].to_string(index=False))
    print("\n=== Ticker par sénateur (Σ quiver_seul doit être 0) ===")
    print(rec["ticker_per_sen"].to_string(index=False))
    print(f"\nΣ quiver_seul = {rec['ticker_per_sen']['quiver_seul'].sum()}")
    print("\n=== Deltas (Σ doit boucler ; tous positifs hors délégués) ===")
    print(rec["deltas"].to_string(index=False))
    print(f"\nΣ delta = {rec['deltas']['delta'].sum()} | "
          f"sens={fa['sense']}% date(Traded)={fa['date_traded']}% "
          f"date(Filed)={fa['date_filed']}% montant={fa['amount_bucket']}%")
    print("\nArtefacts d'audit →", AUDIT)


if __name__ == "__main__":
    main()
