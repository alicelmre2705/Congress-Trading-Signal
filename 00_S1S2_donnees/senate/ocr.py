#!/usr/bin/env python
"""OCR papier Sénat multi-années (eFD direct) — Phase 2.

Découvre les PTR PAPIER (kind='paper') par an, puis les OCR-ise (Claude Vision) en RÉUTILISANT
tel quel le moteur figé `senat_2025_test/senate_ocr.py` (prompt générique au formulaire papier
Sénat, cache versionné, normalisation, garde-fou millésime) — on **monkeypatch seulement les
chemins** (cache/images locaux à `toutes_annees/data/`), zéro duplication de logique OCR.

DIGITAL ≠ OCR : le papier est **invalidable par Quiver** (0 vérité-terrain). Validation =
période (lettres d'accompagnement) + cohérence interne + spot-check manuel.

Modes :
  --mode index    : découvre l'index papier 2020-2026 → _paper_index_2020_2026.csv
  --mode pilote   : OCR régression Blumenthal Q1 (doit refaire 92) + quelques non-Blumenthal
  --mode full     : OCR des 130 (Phase 2b, après validation du pilote)
"""
import sys
import io
import re
import time
import base64
import hashlib
import argparse
from pathlib import Path

import requests
import pandas as pd
from PIL import Image

HERE = Path(__file__).resolve().parent        # <repo>/senate

from senate import ocr_engine as so           # moteur OCR figé (réutilisé tel quel)
from senate.identity import load_reference, make_matcher, recover_ticker, SCHEMA

DATA = HERE.parent / "data" / "senate"         # données Sénat (parité data/house)
REPORTS = DATA / "reports"
MEDIA = REPORTS / "media"
OCR_CACHE = DATA / "ocr_cache"
for d in (REPORTS, MEDIA, OCR_CACHE):
    d.mkdir(parents=True, exist_ok=True)

# >>> monkeypatch des chemins du moteur OCR vers le dossier multi-années <<<
so.REPORTS = REPORTS
so.MEDIA = MEDIA
so.OCR_CACHE = OCR_CACHE


# >>> correctif collision : les .gif sont nommés 000000010/11/12 PAR rapport → collision de
# basename entre rapports. On indexe le cache image par HASH de l'URL COMPLÈTE (unique). <<<
def _image_b64_safe(url):
    MEDIA.mkdir(parents=True, exist_ok=True)
    cache = MEDIA / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".gif")
    if cache.exists():
        data = cache.read_bytes()
    else:
        data = None
        for attempt in range(4):
            try:
                r = requests.get(url, headers=so.UA, timeout=90)
                r.raise_for_status()
                data = r.content
                cache.write_bytes(data)
                break
            except requests.RequestException:
                time.sleep(min(2 ** attempt, 30))
        if data is None:
            raise RuntimeError(f"image inaccessible après retries : {url}")
    img = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = img.size
    if max(w, h) > so.LONG_EDGE:
        s = so.LONG_EDGE / max(w, h)
        img = img.resize((round(w * s), round(h * s)))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


so._image_b64 = _image_b64_safe

EFD_BASE = "https://efdsearch.senate.gov"
EFD_HOME = f"{EFD_BASE}/search/home/"
EFD_SEARCH = f"{EFD_BASE}/search/"
EFD_DATA = f"{EFD_BASE}/search/report/data/"
EFD_PAPER = f"{EFD_BASE}/search/view/paper/{{uuid}}/"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "congress-trading-research/1.0 (poli, sans evasion)",
                        "Accept-Language": "en-US,en;q=0.9"})
PAUSE = 1.5
PTR_LINK_RE = re.compile(r'/search/view/(ptr|paper)/([0-9a-f\-]+)/', re.IGNORECASE)
DATE_RE = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')
INDEX_CSV = DATA / "tables" / "_paper_index_2020_2026.csv"


# ----------------------------------------------------------------- scraping (découverte)
def accept_agreement():
    r = SESSION.get(EFD_HOME, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Accès eFD refusé (HTTP {r.status_code}).")
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
        r.raise_for_status()
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


def fetch_paper_html(uuid):
    """Télécharge la page HTML du PTR papier (contient les URLs des images .gif) dans le cache.
    Robuste : cache valide seulement s'il contient les images ; re-agrée la session eFD si elle a
    expiré en cours de run long (page d'agrément renvoyée à la place du rapport)."""
    cache = REPORTS / f"{uuid}.html"
    if cache.exists() and "efd-media-public" in cache.read_text(encoding="utf-8", errors="replace"):
        return True
    for attempt in range(4):
        try:
            r = SESSION.get(EFD_PAPER.format(uuid=uuid), headers={"Referer": EFD_SEARCH}, timeout=90)
        except requests.RequestException:
            time.sleep(min(2 ** attempt, 30))
            continue
        time.sleep(PAUSE)
        if r.status_code == 200 and "efd-media-public" in r.text:
            cache.write_text(r.text, encoding="utf-8")
            return True
        accept_agreement()   # session probablement expirée → re-agréer et réessayer
    return False


def discover_index(years):
    if not accept_agreement():
        raise SystemExit("Agrément eFD incertain — arrêt.")
    rows = []
    for y in years:
        df = fetch_ptr_list(f"01/01/{y}", f"12/31/{y}")
        paper = df[df["kind"] == "paper"]
        for _, p in paper.iterrows():
            rows.append({"year": y, "uuid": p["report_uuid"], "member": p["declarant_name"],
                         "disclosure_date": p["disclosure_date"].date().isoformat()})
        print(f"  {y}: {len(paper)} PTR papier")
    idx = pd.DataFrame(rows)
    idx.to_csv(INDEX_CSV, index=False)
    print(f"→ {len(idx)} rapports papier → {INDEX_CSV.name}")
    return idx


# ----------------------------------------------------------------- OCR (réutilise so.*)
def ocr_one(uuid, member, disclosure, force=False):
    """Fetch HTML papier puis OCR via le moteur figé (so.extract_report, chemins patchés)."""
    if not fetch_paper_html(uuid):
        return [], {"status": "fetch_fail", "n_pages": 0, "batches": []}
    return so.extract_report(uuid, member, disclosure, force=force)


def build_table(index_df, force=False):
    rows, n_example, failures, per_doc = [], 0, [], []
    for _, r in index_df.iterrows():
        uuid, member, disc = r["uuid"], r["member"], r["disclosure_date"]
        try:
            txns, obj = ocr_one(uuid, member, disc, force=force)
        except Exception as e:
            # un rapport en échec (timeout, image, API) ne stoppe pas le run : on log et on continue
            failures.append({"doc_id": uuid, "member": member, "batch": -1, "reason": str(e)[:200]})
            per_doc.append({"uuid": uuid, "member": member, "disclosure_date": disc,
                            "n_pages": 0, "n_txns": 0, "status": "error"})
            print(f"  {str(uuid)[:8]} {str(member)[:22]:22} ERREUR: {str(e)[:80]}")
            continue
        kept = 0
        for t in txns:
            if so.EXAMPLE_RE.search(str(t.get("asset_description", ""))):
                n_example += 1
                continue
            rows.append(so.normalize(t, uuid, member, disc))
            kept += 1
        for b in obj.get("batches", []):
            if b.get("status") == "error":
                failures.append({"doc_id": uuid, "member": member, "batch": b.get("batch"),
                                 "reason": b.get("error", "")})
        per_doc.append({"uuid": uuid, "member": member, "disclosure_date": disc,
                        "n_pages": obj.get("n_pages", 0), "n_txns": kept, "status": obj.get("status")})
        print(f"  {str(uuid)[:8]} {str(member)[:22]:22} pages={obj.get('n_pages',0):2} → {kept:3} txns [{obj.get('status')}]")

    df = pd.DataFrame(rows)
    if not df.empty:
        df["natural_key_hash"] = df.apply(so._natural_key, axis=1)
        df["occurrence_index"] = df.groupby(["doc_id", "natural_key_hash"]).cumcount()
        df["amount_split_flag"] = False

        def _resolve(desc, tick):
            if tick:
                return tick, "explicit"
            rec = recover_ticker(desc)
            return (rec, "asset_name") if rec else (None, "none")
        res = [_resolve(d, t) for d, t in zip(df["asset_description"], df["ticker"])]
        df["ticker"] = [x[0] for x in res]
        df["ticker_source"] = [x[1] for x in res]

        ref, name_exact, name_by_last, current_bios, bio_to_committees, key_flag = load_reference()
        match = make_matcher(ref, name_exact, name_by_last, current_bios)
        df["bioguide_id"] = df["declarant_name"].map(match)
        df["party"] = df["bioguide_id"].map(lambda b: ref.get(b, {}).get("party"))
        df["state_district"] = df["bioguide_id"].map(lambda b: ref.get(b, {}).get("state"))
        df["committee_membership"] = df["bioguide_id"].map(
            lambda b: "; ".join(sorted(bio_to_committees.get(b, []))) if b else "")
        df["committees_key_flag"] = df["bioguide_id"].map(lambda b: bool(key_flag.get(b, False)))
        df = df.reindex(columns=SCHEMA)
    return df, pd.DataFrame(per_doc), pd.DataFrame(failures), n_example


# ----------------------------------------------------------------- QA pilote
def qa(df, per_doc):
    print("\n=== QA PILOTE ===")
    if df.empty:
        print("  (table vide)")
        return
    # dates dans la période déclarée ([disclosure-90j, disclosure+10j]) ?
    d = df.copy()
    d["td"] = pd.to_datetime(d["transaction_date"], errors="coerce")
    d["dd"] = pd.to_datetime(d["disclosure_date"], errors="coerce")
    in_win = ((d["td"] >= d["dd"] - pd.Timedelta(days=90)) & (d["td"] <= d["dd"] + pd.Timedelta(days=10)))
    print(f"  transactions : {len(df)} | identité {df['bioguide_id'].notna().sum()}/{len(df)} "
          f"| ticker {df['ticker'].notna().sum()}/{len(df)}")
    print(f"  dates dans la période déclarée : {int(in_win.sum())}/{len(df)} = {100*in_win.mean():.1f}%")
    print(f"  owner : {df['owner'].value_counts().to_dict()}")
    print(f"  amount_range vides : {int((df['amount_range'].fillna('')=='').sum())}")
    print(f"  asset_type : {df['asset_type'].value_counts(dropna=False).to_dict()}")
    print("\n  par document :")
    print(per_doc.to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["index", "pilote", "full"], default="pilote")
    ap.add_argument("--years", default="2020,2021,2022,2023,2024,2025,2026")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    years = [int(y) for y in args.years.split(",") if y.strip()]

    if not so._api_key():
        raise SystemExit("ANTHROPIC_API_KEY manquante (.env).")

    # index (toujours nécessaire)
    if args.mode == "index" or not INDEX_CSV.exists():
        idx = discover_index(years)            # appelle accept_agreement
        if args.mode == "index":
            print(idx.groupby("member").size().sort_values(ascending=False).to_string())
            return
    else:
        idx = pd.read_csv(INDEX_CSV, dtype=str)
        # l'index existe déjà mais on va fetch des rapports → il FAUT agréer la session eFD
        if not accept_agreement():
            raise SystemExit("Agrément eFD incertain — arrêt.")

    if args.mode == "pilote":
        # régression : les 4 PTR Blumenthal Q1 2025 (doit refaire 92 txns)
        reg = pd.DataFrame([{"year": 2025, "uuid": u, "member": m, "disclosure_date": d}
                            for u, (m, d) in so.PAPERS.items()])
        # généralisation : 1 rapport pour chaque déposant papier NON-Blumenthal
        nonblu = idx[~idx["member"].str.contains("BLUMENTHAL", case=False, na=False)]
        gen = nonblu.sort_values(["member", "disclosure_date"]).groupby("member", as_index=False).first()
        pilot = pd.concat([reg, gen], ignore_index=True)
        print(f"=== OCR PILOTE : {len(reg)} régression Blumenthal + {len(gen)} non-Blumenthal ===")
        df, per_doc, fails, n_ex = build_table(pilot, force=args.force)
        reg_txns = int(per_doc[per_doc["member"].str.contains("Blumenthal", case=False, na=False)]["n_txns"].sum())
        print(f"\n  RÉGRESSION Blumenthal Q1 : {reg_txns} txns (attendu 92) "
              f"{'✅' if reg_txns == 92 else '⚠️ écart'}")
        print(f"  lignes-exemple écartées : {n_ex} | échecs batch : {len(fails)}")
        qa(df, per_doc)
        df.to_csv(DATA / "_pilote_ocr.csv", index=False)
        # estimation volume exhaustif
        idx_full = pd.read_csv(INDEX_CSV)
        avg = per_doc["n_txns"].mean()
        print(f"\n  Estimation exhaustif : {len(idx_full)} rapports × ~{avg:.0f} txns/rapport "
              f"≈ {int(len(idx_full)*avg)} txns OCR")
    elif args.mode == "full":
        print(f"=== OCR EXHAUSTIF : {len(idx)} rapports ===")
        df, per_doc, fails, n_ex = build_table(idx, force=args.force)
        # écriture par année
        df["_y"] = pd.to_datetime(df["disclosure_date"], errors="coerce").dt.year
        for y, g in df.groupby("_y"):
            ydir = DATA / "tables" / str(int(y))
            ydir.mkdir(parents=True, exist_ok=True)
            g.drop(columns="_y").to_csv(ydir / f"06b_senate_{int(y)}_ocr_transactions.csv", index=False)
        fails.to_csv(DATA / "tables" / "06c_ocr_failures.csv", index=False)
        print(f"\n  → {len(df)} txns OCR, {n_ex} exemples écartés, {len(fails)} échecs batch")
        qa(df, per_doc)


if __name__ == "__main__":
    main()
