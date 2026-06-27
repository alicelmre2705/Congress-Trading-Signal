#!/usr/bin/env python
"""PHASE 0 — Census PTR Sénat 2020→2026 + probe du parser sur HTML eFD ancien.

⚠️ OUTIL HORS PIPELINE : non lancé par `congress_core.pipeline:build_steps` (exploration ponctuelle).

But : chiffrer le périmètre d'un build "toutes années" DIGITAL avant de l'engager.
  1. Census par an : nb PTR électroniques vs papier, sénateurs, déposants papier.
  2. Probe parser : `parse_electronic` tient-il sur des rapports anciens (2020/2016/2012) ?
  3. Sanity Quiver : ordre de grandeur vs cache Quiver (déjà présent).

Principes (identiques au notebook) : agrément accepté une fois, PAUSE poli, AUCUNE évasion,
cache HTML disque, arrêt propre si l'eFD bloque. Lecture seule côté données existantes.
"""
import io
import re
import time
from pathlib import Path
from collections import Counter

import requests
import pandas as pd

HERE = Path(__file__).resolve().parent        # <repo>/senate
OUT = HERE.parent / "data" / "senate"          # données Sénat (parité data/house)
REPORTS = OUT / "reports"
TAB = OUT                                       # tables directement sous data/senate
REPORTS.mkdir(parents=True, exist_ok=True)

EFD_BASE = "https://efdsearch.senate.gov"
EFD_HOME = f"{EFD_BASE}/search/home/"
EFD_SEARCH = f"{EFD_BASE}/search/"
EFD_DATA = f"{EFD_BASE}/search/report/data/"
EFD_PTR = f"{EFD_BASE}/search/view/ptr/{{uuid}}/"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "congress-trading-research/1.0 (poli, sans evasion)",
    "Accept-Language": "en-US,en;q=0.9",
})
PAUSE = 1.5

PTR_LINK_RE = re.compile(r'/search/view/(ptr|paper)/([0-9a-f\-]+)/', re.IGNORECASE)
DATE_RE = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')

CENSUS_YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
PROBE_YEARS = [2020, 2016, 2012]   # tester le format HTML ancien


# ---------------------------------------------------------------- agrément + recherche
def accept_agreement():
    r = SESSION.get(EFD_HOME, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Accès eFD refusé (HTTP {r.status_code}) — arrêt propre.")
    token = SESSION.cookies.get("csrftoken", "")
    SESSION.post(EFD_HOME, data={"prohibition_agreement": "1", "csrfmiddlewaretoken": token},
                 headers={"Referer": EFD_HOME, "X-CSRFToken": token}, timeout=60)
    return "sessionid" in SESSION.cookies or "csrftoken" in SESSION.cookies


def fetch_ptr_list(win_start, win_end):
    """Liste tous les PTR déposés dans [win_start, win_end] (MM/DD/YYYY). Paginé."""
    token = SESSION.cookies.get("csrftoken", "")
    headers = {"Referer": EFD_SEARCH, "X-CSRFToken": token, "X-Requested-With": "XMLHttpRequest"}
    rows, start, length = [], 0, 100
    while True:
        payload = {
            "draw": "1", "start": str(start), "length": str(length),
            "search[value]": "", "search[regex]": "false",
            "order[0][column]": "4", "order[0][dir]": "desc",
            "report_types": "[11]",           # 11 = Periodic Transaction Report (confirmé)
            "filer_types": "[]",
            "submitted_start_date": f"{win_start} 00:00:00",
            "submitted_end_date": f"{win_end} 23:59:59",
            "candidate_state": "", "senator_state": "", "office_id": "",
            "first_name": "", "last_name": "",
        }
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
            rows.append({"first": first, "last": last,
                         "declarant_name": f"{first} {last}".strip(),
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


# ---------------------------------------------------------------- parser (copie notebook)
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
    """Retourne (rows, columns, status) — status = ok / no_txn_table / read_error."""
    try:
        tables = pd.read_html(io.StringIO(html))
    except ValueError:
        return [], [], "read_error"
    txn = None
    for t in tables:
        cols = " ".join(str(c).lower() for c in t.columns)
        if "ticker" in cols or ("asset" in cols and "name" in cols):
            txn = t
            break
    if txn is None:
        return [], [], "no_txn_table"
    cols = list(map(str, txn.columns))
    c_date = _find_col(txn, "transaction", "date") or _find_col(txn, "date")
    c_tick = _find_col(txn, "ticker")
    c_asset = _find_col(txn, "asset", "name") or _find_col(txn, "asset")
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
        rows.append({
            "transaction_date": str(r[c_date]).strip() if c_date else None,
            "ticker": str(r[c_tick]).strip() if c_tick else None,
            "asset_description": str(r[c_asset]).strip() if c_asset else None,
            "operation_type": norm_op(r[c_op]) if c_op else None,
            "amount_range": str(r[c_amt]).strip() if c_amt else None,
            "amount_midpoint": amount_midpoint(r[c_amt]) if c_amt else None,
        })
    return rows, cols, "ok"


# ---------------------------------------------------------------- main
def main():
    print("=== PHASE 0 — agrément eFD ===")
    if not accept_agreement():
        print("Agrément incertain — arrêt.")
        return
    print("Session eFD ouverte.\n")

    # 1) CENSUS par an
    print("=== CENSUS PTR 2020→2026 (année pleine) ===")
    per_year = {}
    rows_census = []
    for y in CENSUS_YEARS:
        try:
            df = fetch_ptr_list(f"01/01/{y}", f"12/31/{y}")
        except Exception as e:
            print(f"  {y}: ARRÊT propre — {e}")
            continue
        per_year[y] = df
        elec = df[df["kind"] == "ptr"]
        paper = df[df["kind"] == "paper"]
        paper_filers = sorted(paper["declarant_name"].dropna().unique())
        rows_census.append({
            "year": y,
            "n_ptr_electronique": int((df["kind"] == "ptr").sum()),
            "n_ptr_papier": int((df["kind"] == "paper").sum()),
            "n_senateurs": int(df["declarant_name"].nunique()),
            "n_senateurs_papier": int(paper["declarant_name"].nunique()),
            "deposants_papier": "; ".join(paper_filers),
        })
        print(f"  {y}: élec={int((df['kind']=='ptr').sum()):4d}  papier={int((df['kind']=='paper').sum()):3d}  "
              f"sénateurs={df['declarant_name'].nunique():3d}  papier_sén={paper['declarant_name'].nunique()}  "
              f"{('['+'; '.join(paper_filers)+']') if paper_filers else ''}")
    census = pd.DataFrame(rows_census)
    census.to_csv(TAB / "_ptr_census_2020_2026.csv", index=False)
    if len(census):
        print(f"\n  TOTAL élec 2020→2026 = {census['n_ptr_electronique'].sum()}  "
              f"| papier = {census['n_ptr_papier'].sum()}")
    print("  → tables/_ptr_census_2020_2026.csv")

    # 2) PROBE parser sur HTML ancien
    print("\n=== PROBE parser (HTML ancien) ===")
    probe_rows = []
    for y in PROBE_YEARS:
        try:
            df = per_year[y] if y in per_year else fetch_ptr_list(f"01/01/{y}", f"12/31/{y}")
        except Exception as e:
            print(f"  {y}: liste indisponible — {e}")
            continue
        elec = df[df["kind"] == "ptr"].head(5)
        if not len(elec):
            print(f"  {y}: aucun rapport électronique trouvé")
            continue
        for _, f in elec.iterrows():
            _, html = fetch_report(f["report_uuid"])
            if not html:
                probe_rows.append({"year": y, "doc_id": f["report_uuid"], "n_txns": 0,
                                   "status": "fetch_fail", "columns": ""})
                continue
            rws, cols, status = parse_electronic(html)
            probe_rows.append({"year": y, "doc_id": f["report_uuid"], "n_txns": len(rws),
                               "status": status, "columns": " | ".join(cols)})
            print(f"  {y} {f['report_uuid'][:8]} : {status:12s} n_txns={len(rws):3d}  cols={cols}")
    probe = pd.DataFrame(probe_rows)
    probe.to_csv(TAB / "_parser_probe.csv", index=False)
    print("  → tables/_parser_probe.csv")

    # 3) SANITY Quiver
    print("\n=== SANITY vs Quiver (sénateurs/an) ===")
    qp = TAB / "_quiver_senate_cache.csv"
    if qp.exists() and len(census):
        q = pd.read_csv(qp)
        q["Filed"] = pd.to_datetime(q["Filed"], errors="coerce")
        q["fy"] = q["Filed"].dt.year
        qsen = q.groupby("fy")["BioGuideID"].nunique()
        for _, r in census.iterrows():
            print(f"  {int(r['year'])}: census sénateurs={int(r['n_senateurs']):3d}  "
                  f"| Quiver sénateurs={int(qsen.get(r['year'], 0)):3d}")

    # Récap final
    print("\n=== RÉCAP PHASE 0 ===")
    if len(census):
        print(census.to_string(index=False))
    if len(probe):
        ok = (probe["status"] == "ok").sum()
        print(f"\nProbe parser : {ok}/{len(probe)} rapports parsés OK "
              f"| statuts={dict(Counter(probe['status']))}")


if __name__ == "__main__":
    main()
