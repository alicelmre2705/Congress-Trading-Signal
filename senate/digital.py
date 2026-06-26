#!/usr/bin/env python
"""Pipeline Sénat DIGITAL multi-années (eFD direct) — 2020 → 2026, sur le modèle House toutes_annees.

Pour chaque année : scraping eFD des PTR électroniques (cache HTML disque), parsing, identité +
enrichissement ticker + reclassement options + dédup non destructrice (via `enrich` de
senate_finalize), puis **validation Quiver par an** (couverture transaction-niveau via `reconcile`,
comparaison par sénateur, deltas). Agrège un dashboard `00_year_status.csv`.

DIGITAL SEUL : les rapports `paper` sont comptés (backlog) mais pas OCR-isés (chantier séparé ;
Quiver est de toute façon aveugle au papier). Réutilise le code Q1 figé (`senat_2025_test/`) :
identité, enrichissement, validation — source unique, zéro duplication de logique métier.

Principes : agrément accepté une fois, PAUSE poli, AUCUNE évasion, cache HTML (reprise gratuite),
arrêt propre si l'eFD bloque. Quiver = vérification externe (cache local), jamais réinjecté.

Usage : python senat_multiyear.py --years 2020,2021,2022,2023,2024,2025,2026
"""
import io
import re
import sys
import time
import argparse
from pathlib import Path
from collections import Counter

import requests
import pandas as pd

HERE = Path(__file__).resolve().parent        # <repo>/senate
from senate.identity import load_reference, make_matcher, enrich, SCHEMA
from senate import quiver_audit as vq

DATA = HERE.parent / "data" / "senate"         # données Sénat (parité data/house)
REPORTS = DATA / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)
QUIVER_CACHE = DATA / "reference" / "_quiver_senate_cache.csv"

EFD_BASE = "https://efdsearch.senate.gov"
EFD_HOME = f"{EFD_BASE}/search/home/"
EFD_SEARCH = f"{EFD_BASE}/search/"
EFD_DATA = f"{EFD_BASE}/search/report/data/"
EFD_PTR = f"{EFD_BASE}/search/view/ptr/{{uuid}}/"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "congress-trading-research/1.0 (poli, sans evasion)",
                        "Accept-Language": "en-US,en;q=0.9"})
PAUSE = 1.5
PTR_LINK_RE = re.compile(r'/search/view/(ptr|paper)/([0-9a-f\-]+)/', re.IGNORECASE)
DATE_RE = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')


# ----------------------------------------------------------------- scraping (poli, caché)
def accept_agreement():
    r = SESSION.get(EFD_HOME, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Accès eFD refusé (HTTP {r.status_code}) — arrêt propre.")
    token = SESSION.cookies.get("csrftoken", "")
    SESSION.post(EFD_HOME, data={"prohibition_agreement": "1", "csrfmiddlewaretoken": token},
                 headers={"Referer": EFD_HOME, "X-CSRFToken": token}, timeout=60)
    return "sessionid" in SESSION.cookies or "csrftoken" in SESSION.cookies


def fetch_ptr_list(win_start, win_end):
    token = SESSION.cookies.get("csrftoken", "")
    headers = {"Referer": EFD_SEARCH, "X-CSRFToken": token, "X-Requested-With": "XMLHttpRequest"}
    rows, start, length = [], 0, 100
    while True:
        payload = {"draw": "1", "start": str(start), "length": str(length),
                   "search[value]": "", "search[regex]": "false",
                   "order[0][column]": "4", "order[0][dir]": "desc",
                   "report_types": "[11]", "filer_types": "[]",
                   "submitted_start_date": f"{win_start} 00:00:00",
                   "submitted_end_date": f"{win_end} 23:59:59",
                   "candidate_state": "", "senator_state": "", "office_id": "",
                   "first_name": "", "last_name": ""}
        r = SESSION.post(EFD_DATA, data=payload, headers=headers, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"Recherche eFD bloquée (HTTP {r.status_code}) — arrêt propre.")
        j = r.json()
        data = j.get("data", [])
        if not data:
            break
        for cells in data:
            blob = " ".join(str(c) for c in cells)
            link = PTR_LINK_RE.search(blob)
            dates = DATE_RE.findall(blob)
            first = re.sub(r"<[^>]+>", "", str(cells[0])).strip() if len(cells) > 0 else ""
            last = re.sub(r"<[^>]+>", "", str(cells[1])).strip() if len(cells) > 1 else ""
            rows.append({"declarant_name": f"{first} {last}".strip(),
                         "kind": link.group(1).lower() if link else None,
                         "report_uuid": link.group(2) if link else None,
                         "disclosure_date": dates[-1] if dates else None})
        start += length
        total = j.get("recordsTotal", len(rows))
        time.sleep(PAUSE)
        if start >= total:
            break
    df = pd.DataFrame(rows)
    if len(df):
        df["disclosure_date"] = pd.to_datetime(df["disclosure_date"], errors="coerce")
        ws, we = pd.to_datetime(win_start), pd.to_datetime(win_end)
        df = df[(df["disclosure_date"] >= ws) & (df["disclosure_date"] <= we)]
    return df


def fetch_report(uuid):
    url = EFD_PTR.format(uuid=uuid)
    cache = REPORTS / f"{uuid}.html"
    if cache.exists():
        return url, cache.read_text(encoding="utf-8", errors="replace")
    r = SESSION.get(url, headers={"Referer": EFD_SEARCH}, timeout=60)
    time.sleep(PAUSE)
    if r.status_code != 200:
        return url, ""
    cache.write_text(r.text, encoding="utf-8")
    return url, r.text


# ----------------------------------------------------------------- parser (version complète)
def amount_midpoint(a):
    nums = [int(x.replace(",", "")) for x in re.findall(r'\$([\d,]+)', str(a))]
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2
    if len(nums) == 1:
        return float(nums[0])
    return None


def norm_op(t):
    t = str(t).strip().lower()
    if t.startswith("p"): return "Purchase"
    if "exchange" in t:   return "Exchange"
    if "partial" in t:    return "Sale (Partial)"
    if "full" in t:       return "Sale (Full)"
    if t.startswith("s"): return "Sale"
    return str(t).strip()


def _find_col(df, *keys):
    for c in df.columns:
        cl = str(c).strip().lower()
        if all(k in cl for k in keys):
            return c
    return None


def parse_electronic(html):
    """HTML d'un PTR électronique → liste de transactions (owner + asset_type inclus)."""
    try:
        tables = pd.read_html(io.StringIO(html))
    except ValueError:
        return []
    txn = None
    for t in tables:
        cols = " ".join(str(c).lower() for c in t.columns)
        if "ticker" in cols or ("asset" in cols and "name" in cols):
            txn = t
            break
    if txn is None:
        return []
    c_date = _find_col(txn, "transaction", "date") or _find_col(txn, "date")
    c_owner = _find_col(txn, "owner")
    c_tick = _find_col(txn, "ticker")
    c_asset = _find_col(txn, "asset", "name") or _find_col(txn, "asset")
    c_atype = _find_col(txn, "asset", "type")
    c_op = _find_col(txn, "transaction", "type")
    if not c_op:
        for c in txn.columns:
            cl = str(c).strip().lower()
            if cl == "type" or ("type" in cl and "asset" not in cl and "date" not in cl):
                c_op = c
                break
    c_amt = _find_col(txn, "amount")
    rows = []
    for _, r in txn.iterrows():
        tick = str(r[c_tick]).strip() if c_tick else None
        if tick in ("--", "nan", "", "None"):
            tick = None
        rows.append({"transaction_date": str(r[c_date]).strip() if c_date else None,
                     "owner": str(r[c_owner]).strip() if c_owner else None,
                     "ticker": tick,
                     "asset_description": str(r[c_asset]).strip() if c_asset else None,
                     "asset_type": str(r[c_atype]).strip() if c_atype else None,
                     "operation_type": norm_op(r[c_op]) if c_op else None,
                     "amount_range": str(r[c_amt]).strip() if c_amt else None,
                     "amount_midpoint": amount_midpoint(r[c_amt]) if c_amt else None})
    return rows


# ----------------------------------------------------------------- traitement par année
def run_year(year, ref, bio_to_committees, key_flag, match, quiver_df, senate_bios):
    ws, we = f"01/01/{year}", f"12/31/{year}"
    filings = fetch_ptr_list(ws, we)
    if not len(filings):
        print(f"  {year}: aucun dépôt.")
        return None
    elec = filings[filings["kind"] == "ptr"]
    n_paper = int((filings["kind"] == "paper").sum())

    rows, fails = [], []
    for _, f in elec.iterrows():
        if not f["report_uuid"]:
            continue
        url, html = fetch_report(f["report_uuid"])
        if not html:
            fails.append({"doc_id": f["report_uuid"], "raison": "fetch_fail"})
            continue
        txns = parse_electronic(html)
        if not txns:
            fails.append({"doc_id": f["report_uuid"], "raison": "parse_empty"})
            continue
        for t in txns:
            t.update({"doc_id": f["report_uuid"], "source_url": url,
                      "declarant_name": f["declarant_name"],
                      "disclosure_date": f["disclosure_date"].date() if pd.notna(f["disclosure_date"]) else None,
                      "provenance": "senate-efd-electronic"})
            rows.append(t)

    raw = pd.DataFrame(rows)
    df = enrich(raw, ref, bio_to_committees, key_flag, match)

    ydir = DATA / str(year)
    ydir.mkdir(parents=True, exist_ok=True)
    df.to_csv(ydir / f"06_senate_{year}_transactions.csv", index=False)
    pd.DataFrame(fails, columns=["doc_id", "raison"]).to_csv(ydir / "05_parse_failures.csv", index=False)

    # --- validation Quiver de l'année ---
    qy = quiver_df[(quiver_df["Filed"].dt.year == year) & (quiver_df["BioGuideID"].isin(senate_bios))].copy()
    rec = vq.reconcile(df, qy)
    rec["txn_reco"].to_csv(ydir / "07c_quiver_txn_reconciliation.csv", index=False)
    rec["field_agreement"].to_csv(ydir / "07d_quiver_field_agreement.csv", index=False)
    rec["ticker_per_sen"].to_csv(ydir / "07e_quiver_ticker_per_senator.csv", index=False)
    rec["only_quiver_txn"].to_csv(ydir / "07f_quiver_only_quiver_txn.csv", index=False)

    # comparaison par sénateur (07) + verdict, à partir des deltas de reconcile
    cmp = rec["deltas"].copy()
    def verdict(r):
        if r["nous"] == 0:
            return "quiver_seul"
        if r["delta"] == 0:
            return "concordant"
        if r["quiver"] == 0:
            return "quiver_sans_donnee"
        return "nous_plus" if r["delta"] > 0 else "quiver_plus_a_verifier"
    cmp["verdict"] = cmp.apply(verdict, axis=1)
    cmp.to_csv(ydir / "07_quiver_comparison.csv", index=False)

    m = rec["txn_reco"].set_index("metric")["value"]
    fa = rec["field_agreement"].set_index("field")["agreement_pct"]
    tk_cov = round(100 * df["ticker"].notna().mean(), 1) if len(df) else 0.0
    vc = Counter(cmp["verdict"])
    status = {
        "year": year, "n_ptr_elec": int(len(elec)), "n_ptr_paper": n_paper,
        "n_parse_fail": len(fails), "n_txns": int(len(df)),
        "n_senateurs": int(df["bioguide_id"].nunique()),
        "ticker_pct": tk_cov, "quiver_txns": int(qy.shape[0]),
        "coverage_pct": m.get("coverage_pct"), "only_quiver": int(m.get("only_quiver", 0)),
        "delta_total": int(cmp["delta"].sum()),
        "concordant": vc.get("concordant", 0), "nous_plus": vc.get("nous_plus", 0),
        "quiver_sans_donnee": vc.get("quiver_sans_donnee", 0),
        "sens_pct": fa.get("sense"), "date_traded_pct": fa.get("date_traded"),
        "montant_pct": fa.get("amount_bucket"),
    }
    print(f"  {year}: PTR élec={len(elec):3d} (papier {n_paper}) | txns={len(df):4d} | "
          f"sén={df['bioguide_id'].nunique():2d} | ticker={tk_cov:.0f}% | "
          f"couverture Quiver={m.get('coverage_pct')}% only_q={int(m.get('only_quiver',0))} | "
          f"Δ={int(cmp['delta'].sum())} | fails={len(fails)}")
    return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2020,2021,2022,2023,2024,2025,2026")
    args = ap.parse_args()
    years = [int(y) for y in args.years.split(",") if y.strip()]

    print("=== Sénat DIGITAL multi-années ===")
    ref, name_exact, name_by_last, current_bios, bio_to_committees, key_flag = load_reference()
    match = make_matcher(ref, name_exact, name_by_last, current_bios)
    senate_bios = {b for b, v in ref.items() if v["chamber"] == "senate"}
    print(f"Référentiel : {len(ref)} législateurs ({len(senate_bios)} sénateurs)")

    quiver_df = pd.read_csv(QUIVER_CACHE)
    quiver_df["Filed"] = pd.to_datetime(quiver_df["Filed"], errors="coerce")
    quiver_df["Traded"] = pd.to_datetime(quiver_df["Traded"], errors="coerce")
    print(f"Cache Quiver Sénat : {len(quiver_df)} lignes (2014→2026)\n")

    if not accept_agreement():
        print("Agrément incertain — arrêt.")
        return
    print("Session eFD ouverte.\n")

    statuses = []
    for y in years:
        try:
            st = run_year(y, ref, bio_to_committees, key_flag, match, quiver_df, senate_bios)
            if st:
                statuses.append(st)
        except Exception as e:
            print(f"  {y}: ARRÊT propre — {e}")
            break

    if statuses:
        dash = pd.DataFrame(statuses)
        # met à jour le dashboard global (conserve les années non recalculées)
        path = DATA / "00_year_status.csv"
        if path.exists():
            old = pd.read_csv(path)
            old = old[~old["year"].isin(dash["year"])]
            dash = pd.concat([old, dash], ignore_index=True).sort_values("year")
        dash.to_csv(path, index=False)
        print("\n=== 00_year_status.csv ===")
        print(dash.to_string(index=False))
        print(f"\nTOTAL txns digital {min(years)}→{max(years)} : {dash['n_txns'].sum()} "
              f"| only_quiver cumulé : {dash['only_quiver'].sum()}")


if __name__ == "__main__":
    main()
