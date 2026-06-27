"""Quiver — vérification externe (jamais réinjectée). Fetch + clé d'appariement + reconcile.

Quiver = vérification UNIQUEMENT. La construction de clé diffère par chambre (piège #2) :
- House (validate_quiver) : `bioguide | ticker.upper() | transaction_date BRUT | operation_type[:4]`.
- Sénat (reconcile) : `bioguide × norm_ticker × Traded.date() × norm_sense`.
On NE fusionne PAS les clés : House garde sa sémantique exacte (reproduit 07), Sénat la sienne (07c-f).
"""
import re
import pandas as pd

QUIVER_URL = "https://api.quiverquant.com/beta/bulk/congresstrading"


# ───────────────────────── Normalisation d'appariement (canonique, port validate_quiver_sample) ──
def norm_ticker(t):
    if not isinstance(t, str):
        return ""
    t = t.upper().strip()
    if t in ("", "NAN", "NONE", "--"):
        return ""
    t = re.sub(r"\s+(PUT|CALL)$", "", t)
    return t.replace(".", "_").replace("-", "_")


def norm_sense(s):
    """Granularité 3-voies pour l'appariement (≠ operation_type 5-voies stocké). Port verbatim."""
    s = str(s).strip().lower()
    if s.startswith("p"):
        return "Purchase"
    if s.startswith("s"):
        return "Sale"
    if s.startswith("e"):
        return "Exchange"
    return s or "?"


def low_bound(rng):
    """Borne basse de la fourchette $ (= Quiver Trade_Size_USD). Port de _low_bound."""
    m = re.search(r"\$([\d,]+)", str(rng))
    return int(m.group(1).replace(",", "")) if m else None


# ───────────────────────── Fetch (cache-first) ───────────────────────────────────────────────
def fetch_quiver(chamber="house", cache_path=None, token=None, session=None):
    """Charge le cache transaction-level si présent ; sinon live (filtré chambre). Port de
    house_multiyear.fetch_quiver (House) généralisé. Renvoie un DataFrame ou None."""
    from pathlib import Path
    if cache_path and Path(cache_path).exists():
        return pd.read_csv(cache_path)
    if not token:
        import os
        token = os.environ.get("QUIVER_API_KEY") or os.environ.get("QUIVER_API_TOKEN")
    if not token:
        return None
    import requests
    sess = session or requests.Session()
    q = pd.DataFrame(sess.get(QUIVER_URL, headers={"Authorization": f"Bearer {token}"}, timeout=180).json())
    if chamber == "house":
        q = q[q["Chamber"].str.contains("Rep", na=False)].copy()
        q = q.rename(columns={"Filed": "filed", "Traded": "traded"})
        q["disclosure_year"] = pd.to_datetime(q["filed"], errors="coerce").dt.year
    else:
        q = q[q["Chamber"].astype(str).str.strip().str.lower() == "senate"].copy()
    return q


# ───────────────────────── Validation House (clé BRUTE, reproduit 07) — port verbatim ────────
def validate_quiver_house(df, q, win_start, win_end, paper_bios):
    """Validation honnête House : (1) comptes par déclarant PER-LOT (Quiver brut) ; (2) recouvrement
    transaction-niveau (clé bioguide|ticker|date|type[:4]), invariant à la dédup. Renvoie (cmp_df,
    real_missing_df, stats). Port FIDÈLE de house_multiyear.validate_quiver (n'écrit rien)."""
    q = q.copy()
    q["_filed"] = pd.to_datetime(q["filed"], errors="coerce")
    q = q[(q["_filed"] >= win_start) & (q["_filed"] <= win_end)].copy()
    q["_ticker"] = q["Ticker"].astype(str).str.upper().str.strip()
    q["_op4"] = q["Transaction"].astype(str).str.strip().str[:4]
    q["_td"] = pd.to_datetime(q["traded"], errors="coerce").dt.strftime("%Y-%m-%d")

    our_name = df.drop_duplicates("bioguide_id").set_index("bioguide_id")["declarant_name"]
    q_name = q.drop_duplicates("BioGuideID").set_index("BioGuideID")["Name"]

    cmp = pd.DataFrame({"nous": df.groupby("bioguide_id").size()}).join(
        pd.DataFrame({"quiver": q.groupby("BioGuideID").size()}), how="outer").fillna(0).astype(int)
    cmp["delta"] = cmp["nous"] - cmp["quiver"]
    cmp["name"] = cmp.index.map(lambda b: our_name.get(b) or q_name.get(b, b))
    cmp["a_du_papier"] = cmp.index.isin(paper_bios)

    def verdict(row):
        if row["nous"] == 0 and row["quiver"] > 0:
            return "manquant_papier" if row["a_du_papier"] else "manquant_a_revoir"
        if row["delta"] == 0:
            return "concordant"
        if row["quiver"] == 0:
            return "quiver_sans_donnee"
        if row["delta"] > 0:
            return "nous_plus"
        return "quiver_plus_papier" if row["a_du_papier"] else "quiver_plus_a_revoir"
    cmp["verdict"] = cmp.apply(verdict, axis=1)
    cmp = cmp[["name", "nous", "quiver", "delta", "a_du_papier", "verdict"]].sort_values("nous", ascending=False)

    ours = df[df["ticker"].notna() & df["bioguide_id"].notna()].copy()
    ours["_k"] = (ours["bioguide_id"].astype(str) + "|" + ours["ticker"].astype(str).str.upper()
                  + "|" + ours["transaction_date"].astype(str) + "|" + ours["operation_type"].astype(str).str[:4])
    qk = q[q["BioGuideID"].notna() & q["_ticker"].ne("NAN") & q["_ticker"].ne("")].copy()
    qk["_k"] = (qk["BioGuideID"].astype(str) + "|" + qk["_ticker"] + "|" + qk["_td"] + "|" + qk["_op4"])
    our_keys, q_keys = set(ours["_k"]), set(qk["_k"])
    matched = our_keys & q_keys
    only_ours = our_keys - q_keys
    only_q = q_keys - our_keys
    cov = (len(matched) / len(q_keys) * 100) if q_keys else float("nan")

    miss = qk[qk["_k"].isin(only_q)].copy()
    miss["a_du_papier"] = miss["BioGuideID"].isin(paper_bios)
    real_miss = miss[~miss["a_du_papier"]]
    real_miss_out = real_miss[["BioGuideID", "Name", "_ticker", "_td", "Transaction"]].rename(
        columns={"_ticker": "ticker", "_td": "traded"})

    vc = dict(cmp["verdict"].value_counts())
    stats = {"quiver_total": len(q), "quiver_declarants": int(q["BioGuideID"].nunique()),
             "verdicts": vc, "n_declarants_compared": len(cmp),
             "set_matched": len(matched), "set_only_ours": len(only_ours), "set_only_quiver": len(only_q),
             "coverage_of_quiver_pct": round(cov, 1), "n_real_missing_trades": len(real_miss),
             "real_missing_declarants": sorted(real_miss["Name"].dropna().unique().tolist())[:20]}
    return cmp, real_miss_out, stats


# ───────────────────────── Reconcile canonique (Sénat-style, audit riche) — port verbatim ────
def reconcile(df, qwin):
    """Réconciliation transaction-niveau (clé bioguide×norm_ticker×Traded.date×norm_sense) + accords
    sens/date/montant + deltas. Port VERBATIM de validate_quiver_sample.reconcile (07c-07f)."""
    d = df.copy()
    d["tk"] = d["ticker"].map(norm_ticker)
    d["sense"] = d["operation_type"].map(norm_sense)
    d["d"] = pd.to_datetime(d["transaction_date"], errors="coerce").dt.date
    d["lb"] = d["amount_range"].map(low_bound)

    q = qwin.copy()
    _n_q_raw = len(q)
    q = q.drop_duplicates(subset=["BioGuideID", "Ticker", "Traded", "Transaction"], keep="first")
    _n_q_dups = _n_q_raw - len(q)
    q["tk"] = q["Ticker"].map(norm_ticker)
    q["sense"] = q["Transaction"].map(norm_sense)
    q["dt"] = pd.to_datetime(q["Traded"], errors="coerce").dt.date
    q["fd"] = pd.to_datetime(q["Filed"], errors="coerce").dt.date
    q["qlb"] = pd.to_numeric(q["Trade_Size_USD"], errors="coerce")

    common = set(d["bioguide_id"].dropna()) & set(q["BioGuideID"].dropna())
    o = d[d["bioguide_id"].isin(common) & (d["tk"] != "")]
    qo = q[q["BioGuideID"].isin(common) & (q["tk"] != "")]

    ours_k = set(zip(o["bioguide_id"], o["tk"], o["d"], o["sense"]))
    quiv_k = set(zip(qo["BioGuideID"], qo["tk"], qo["dt"], qo["sense"]))
    quiv_k_filed = set(zip(qo["BioGuideID"], qo["tk"], qo["fd"], qo["sense"]))
    matched, onlyq, onlyo = ours_k & quiv_k, quiv_k - ours_k, ours_k - quiv_k
    cov = round(100 * len(matched) / len(quiv_k), 1) if quiv_k else None
    txn_reco = pd.DataFrame([
        {"metric": "common_members", "value": len(common)},
        {"metric": "quiver_amendment_dups", "value": _n_q_dups},
        {"metric": "ours_tickerizable", "value": len(ours_k)},
        {"metric": "quiver", "value": len(quiv_k)},
        {"metric": "matched", "value": len(matched)},
        {"metric": "only_quiver", "value": len(onlyq)},
        {"metric": "only_ours", "value": len(onlyo)},
        {"metric": "coverage_pct", "value": cov},
    ])
    only_quiver_txn = pd.DataFrame(sorted(onlyq), columns=["bioguide", "ticker", "date", "sense"])

    rows = []
    for b in sorted(common, key=lambda b: -(d["bioguide_id"] == b).sum()):
        ot = set(o[o["bioguide_id"] == b]["tk"]) - {""}
        qt = set(qo[qo["BioGuideID"] == b]["tk"]) - {""}
        nm = d[d["bioguide_id"] == b]["declarant_name"].iloc[0]
        rows.append({"bioguide": b, "name": nm, "n_tk_nous": len(ot), "n_tk_quiver": len(qt),
                     "inter": len(ot & qt), "nous_seul": len(ot - qt), "quiver_seul": len(qt - ot),
                     "quiver_seul_list": ",".join(sorted(qt - ot))})
    ticker_per_member = pd.DataFrame(rows)

    om = o[["bioguide_id", "tk", "d", "sense", "lb"]]
    qm = qo[["BioGuideID", "tk", "dt", "sense", "qlb"]].rename(
        columns={"BioGuideID": "bioguide_id", "dt": "d", "sense": "sense_q"})
    j = om.merge(qm, on=["bioguide_id", "tk", "d"])
    sense_agree = round(100 * (j["sense"] == j["sense_q"]).mean(), 1) if len(j) else None
    amt_agree = round(100 * (j["lb"] == j["qlb"]).mean(), 1) if len(j) else None
    date_traded = round(100 * len(matched) / len(quiv_k), 1) if quiv_k else None
    date_filed = round(100 * len(ours_k & quiv_k_filed) / len(quiv_k), 1) if quiv_k else None
    field_agreement = pd.DataFrame([
        {"field": "sense", "agreement_pct": sense_agree, "n_pairs": len(j)},
        {"field": "date_traded", "agreement_pct": date_traded, "n_pairs": len(quiv_k)},
        {"field": "date_filed", "agreement_pct": date_filed, "n_pairs": len(quiv_k)},
        {"field": "amount_bucket", "agreement_pct": amt_agree, "n_pairs": len(j)},
    ])

    nous = d.groupby("bioguide_id").size()
    quiv = q.groupby("BioGuideID").size()
    bios = sorted(set(nous.index) | set(quiv.index), key=lambda b: -int(nous.get(b, 0)))
    drows = []
    for b in bios:
        n, qv = int(nous.get(b, 0)), int(quiv.get(b, 0))
        sub = d[d["bioguide_id"] == b]
        nm = (sub["declarant_name"].iloc[0] if n else q[q["BioGuideID"] == b]["Name"].iloc[0])
        ocr = int((sub["provenance"] == "house-pdf-ocr").sum()) if "provenance" in sub else 0
        drows.append({"bioguide": b, "name": nm, "nous": n, "quiver": qv, "delta": n - qv,
                      "no_ticker": int((sub["tk"] == "").sum()), "ocr": ocr})
    deltas = pd.DataFrame(drows)

    return {"txn_reco": txn_reco, "only_quiver_txn": only_quiver_txn,
            "ticker_per_member": ticker_per_member, "field_agreement": field_agreement, "deltas": deltas}
