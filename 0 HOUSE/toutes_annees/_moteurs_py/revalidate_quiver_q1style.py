#!/usr/bin/env python
"""Validation Quiver au STANDARD Q1 2025 (qui sortait 99,9% / 0 vraiment-absent), appliquée aux
tables digitales 2020→2026. Réplique exactement la méthodo des cellules 7a-7c du notebook Q1 :
  7a : Quiver House dans la fenêtre année + DÉDUP amendements (BioGuideID|Ticker|Traded|Transaction)
  7b : comparaison DIGITAL-vs-DIGITAL (exclut les déposants papier des deux côtés), delta par déclarant
  7c : niveau transaction (clé bioguide|ticker|date|op[:4]) + cross-check 'ticker raté' (on a le
       membre+date mais ticker NULL) vs 'vraiment absent'.
Sortie : data_v1/tables/{année}/07_quiver_q1style.csv + récap console + 07c_truly_absent_{année}.csv
"""
import pandas as pd
import house_multiyear as hm

print("Référentiel (match_bioguide pour les déposants papier)…")
hm.build_reference()
QH = pd.read_csv(hm.TABROOT / "_quiver_house_cache.csv")
QH["_filed"] = pd.to_datetime(QH["filed"], errors="coerce")
QH["_traded"] = pd.to_datetime(QH["traded"], errors="coerce")

YEARS = ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]
rows = []
for y in YEARS:
    yd = hm.TABROOT / y
    df = pd.read_csv(yd / f"06_house_{y}_transactions.csv", dtype={"doc_id": str})
    man = pd.read_csv(yd / "04_download_manifest.csv", dtype={"doc_id": str})
    ptr = pd.read_csv(yd / "03_ptr_index.csv", dtype={"doc_id": str})
    ws, we = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31")

    # 7a : Quiver House année + dédup amendements
    q = QH[(QH["_filed"] >= ws) & (QH["_filed"] <= we)].copy()
    n_before = len(q)
    q = q.drop_duplicates(subset=["BioGuideID", "Ticker", "traded", "Transaction"])
    n_dupes = n_before - len(q)
    q["_ticker"] = q["Ticker"].astype(str).str.upper().str.strip()
    q["_op"] = q["Transaction"].astype(str).str.strip()
    q["_td"] = q["_traded"].dt.strftime("%Y-%m-%d")

    # déposants papier (à exclure des deux côtés)
    paper = man[man["bucket"] == "non_lisible"][["doc_id"]].merge(ptr[["doc_id", "last", "first"]], on="doc_id", how="left")
    paper["bio"] = paper.apply(lambda r: hm.match_bioguide(r["last"], r["first"]), axis=1)
    paper_bios = set(paper["bio"].dropna())

    df_elec = df[~df["bioguide_id"].isin(paper_bios)].copy()
    q_elec = q[~q["BioGuideID"].isin(paper_bios)].copy()

    # 7b : delta par déclarant (digital vs digital)
    cmp = (pd.DataFrame({"nous": df_elec.groupby("bioguide_id").size()})
           .join(pd.DataFrame({"quiver": q_elec.groupby("BioGuideID").size()}), how="outer").fillna(0).astype(int))
    cmp["delta"] = cmp["nous"] - cmp["quiver"]
    cmp.to_csv(yd / "07_quiver_q1style.csv")
    n_decl = len(cmp)
    n_eq = int((cmp["delta"] == 0).sum())
    n_plus = int((cmp["delta"] > 0).sum())
    n_minus = int((cmp["delta"] < 0).sum())

    # 7c : niveau transaction + cross-check ticker raté
    nk = df_elec[df_elec["ticker"].notna() & df_elec["bioguide_id"].notna()].copy()
    nk["_k"] = (nk["bioguide_id"].astype(str) + "|" + nk["ticker"].astype(str).str.upper()
                + "|" + nk["transaction_date"].astype(str) + "|" + nk["operation_type"].astype(str).str[:4])
    qk = q_elec[q_elec["BioGuideID"].notna() & q_elec["_ticker"].ne("NAN") & q_elec["_ticker"].ne("")].copy()
    qk["_k"] = (qk["BioGuideID"].astype(str) + "|" + qk["_ticker"] + "|" + qk["_td"] + "|" + qk["_op"].str[:4])
    only_q = set(qk["_k"]) - set(nk["_k"])
    matched = set(nk["_k"]) & set(qk["_k"])
    qmiss = qk[qk["_k"].isin(only_q)].copy()
    our_bio_date = set(df_elec[df_elec["bioguide_id"].notna()].apply(
        lambda r: f"{r['bioguide_id']}|{r['transaction_date']}", axis=1))
    qmiss["_bd"] = qmiss["BioGuideID"].astype(str) + "|" + qmiss["_td"]
    qmiss["ticker_rate"] = qmiss["_bd"].isin(our_bio_date)
    n_missed = int(qmiss["ticker_rate"].sum())          # présent chez nous, ticker non extrait
    truly = qmiss[~qmiss["ticker_rate"]]
    n_absent = len(truly)                                # vraiment absent
    truly[["BioGuideID", "Name", "_ticker", "_td", "Transaction"]].to_csv(yd / f"07c_truly_absent_{y}.csv", index=False)

    print(f"{y}: déclarants élec {n_decl} | delta=0 {n_eq} | nous>Q {n_plus} | Q>nous {n_minus} "
          f"|| trades: matched {len(matched)} | only-Q {len(only_q)} (ticker-raté {n_missed} / VRAIMENT absent {n_absent})  "
          f"[Quiver dédup -{n_dupes}]")
    rows.append({"year": y, "decl_elec": n_decl, "delta0": n_eq, "nous_plus": n_plus, "quiver_plus": n_minus,
                 "matched": len(matched), "only_quiver": len(only_q), "ticker_rate": n_missed, "truly_absent": n_absent})

st = pd.DataFrame(rows)
st.to_csv(hm.TABROOT / "00_quiver_q1style_status.csv", index=False)
print("\n=== RÉCAP standard-Q1 ===")
print(st.to_string(index=False))
print(f"\nTOTAL vraiment-absents sur 6 ans : {st['truly_absent'].sum()}  (Q1 2025 = 0)")
