#!/usr/bin/env python
"""GATE de validation OCR — test représentatif AVANT de scaler (le coûteux).

Applique le pipeline adaptatif (prompt durci + routage DPI/pages-par-appel selon densité) sur un
échantillon STRATIFIÉ sur les poids du census 547 (/tmp/ocr_test_sample.json, 38 docs : A5/B19/C14
+ 6 illisibles + 2 Yoho), puis mesure, PAR CLUSTER :
  - stabilité run-à-run (2 runs sur le dense/manuscrit) — le défaut historique (dates Khanna) ;
  - concordance Quiver (vérité-terrain) : ticker présent + (ticker,date) exact, sur les déposants couverts.
Puis PROJETTE la justesse par cluster × poids census → estimation sur les 547.

Réutilise house_ocr_multiyear (TXN_TOOL, AMOUNT_MAP, _norm_asset, _explicit_ticker, MODEL) et le
cache Quiver. N'écrit AUCUNE table du pipeline : sorties de test dans data_v1/tables/_ocr_gate/.

Usage : python test_ocr_clusters.py [--mode smoke|full] [--runs2 N]
  smoke = 3 docs minuscules (1/cluster) pour valider la plomberie sans frais ; full = les 38.
"""
import os, re, json, time, base64, argparse, statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pymupdf, pandas as pd, anthropic
import house_ocr_multiyear as ocr
import house_multiyear as hm

# ───────── prompt DURCI (identique à test_prompt_durci.py, déjà validé A/B) ─────────
HARDENED = """\
Tu lis les pages scannées d'un formulaire PTR (Periodic Transaction Report — US House of
Representatives) déposé par {member_name}, DÉPOSÉ EN {filing_year}. Reporte TOUTES les transactions
en appelant l'outil record_transactions.

STRUCTURE :
  Colonne propriétaire (gauche) : DC=Dependent Child | JT=Joint | SP=Spouse | vide=Self
  FULL ASSET NAME : nom complet tel qu'écrit (jamais de ticker inventé)
  TYPE (cases) : Purchase | Sale | Partial Sale | Exchange
  DATE OF TRANSACTION et DATE NOTIFIED : MM/DD/YY (deux dates par ligne)
  AMOUNT (cases A–K) : A=$1,001–15k B=15k–50k C=50k–100k D=100k–250k E=250k–500k F=500k–1M
    G=1M–5M H=5M–25M I=25M–50M J=>50M K=SP/DC >1M

RÈGLES CRITIQUES :
  1. Orientation : la page peut être tournée 90°/180° — lis-la droite.
  2. LIGNE D'EXEMPLE pré-imprimée « Example: Mega Corp. Common Stock » → JAMAIS une transaction, ignore-la.
  3. « Nothing to report » → aucune transaction sur cette page. Ignore couvertures/certifications.
  4. CHAQUE ligne numérotée du tableau = UNE transaction. Ne fusionne PAS deux lignes ; ne scinde PAS
     un actif sur deux lignes. Reporte les lignes répétées à l'identique (ce sont de vrais lots).
  5. TRANSCRIPTION FIDÈLE : transcris le FULL ASSET NAME EXACTEMENT, caractère par caractère. Ne devine
     pas et ne remplace JAMAIS par une société ressemblante (ex. ne confonds pas « Becton » avec
     « Blackstone », « KKR » avec « KnR », « Rooney » avec « Rooster », « 1831 » avec « 1351 »). Si une
     partie est illisible, transcris seulement ce que tu lis, sans inventer.
  6. DATES — GARDE-FOU : ce dépôt date de {filing_year}. Les transactions sont récentes : leur année est
     quasiment toujours {filing_year} ou {prev_year}. Si tu crois lire une année très différente
     (autre décennie, ou postérieure au dépôt), c'est une ERREUR de lecture des chiffres manuscrits
     — relis le chiffre attentivement (un « 1 » se confond avec « 7 », « 5 » avec « 9 », « 0 » avec « 8 »).
     Convertis MM/DD/YY → YYYY-MM-DD. Lis transaction_date ET notification_date ligne par ligne.
  7. amount_code = UNIQUEMENT la lettre cochée (A–K). Si illisible, omets le champ.
"""

PDFBASE = Path("/Users/lemairealice/Downloads/Jupiter/semaine 1/data/raw/house/ptr_pdfs")
GATE_DIR = hm.TABROOT / "_ocr_gate"


def route(n_pages):
    """Routage par densité (proxy = nb pages)."""
    if n_pages >= 5:
        return dict(dpi=300, per_call=1)      # dense → haute déf, 1 page/appel
    return dict(dpi=250, per_call=3)          # petit → 3 pages/appel


def render(path, dpi):
    d = pymupdf.open(path)
    imgs = [base64.b64encode(p.get_pixmap(dpi=dpi).tobytes("png")).decode() for p in d]
    d.close()
    return imgs


def call_vision(client, imgs, member, year, max_retries=7):
    content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b}} for b in imgs]
    content.append({"type": "text", "text": HARDENED.format(member_name=member, filing_year=year, prev_year=year - 1)})
    for attempt in range(max_retries):
        try:
            r = client.messages.create(model=ocr.MODEL, max_tokens=ocr.MAX_TOKENS, tools=[ocr.TXN_TOOL],
                                       tool_choice={"type": "tool", "name": "record_transactions"},
                                       messages=[{"role": "user", "content": content}])
            for b in r.content:
                if getattr(b, "type", None) == "tool_use" and b.name == "record_transactions":
                    return b.input.get("transactions", [])
            return []
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            if attempt < max_retries - 1:
                time.sleep(min(2 ** attempt, 45)); continue
            raise


# Cap de pages POUR LE TEST seulement : on échantillonne les gros docs pour mesurer la qualité
# (dates/tickers/stabilité) sans payer toutes les pages. Le coût plein = au scaling.
MAX_TEST_PAGES = 8

def ocr_doc(rec):
    """Rend + batch selon le routage, renvoie la liste de txns (filtre ligne-exemple)."""
    path = PDFBASE / rec["year"] / f"{rec['doc_id']}.pdf"
    r = route(rec["pages"])
    imgs = render(path, r["dpi"])[:MAX_TEST_PAGES]
    client = anthropic.Anthropic(api_key=ocr.ANTHROPIC_API_KEY)
    batches = [imgs[i:i + r["per_call"]] for i in range(0, len(imgs), r["per_call"])]
    txns = []
    for b in batches:
        txns += call_vision(client, b, rec["member"], int(rec["year"]))
    # filtre ligne-exemple
    txns = [t for t in txns if not ocr._EXAMPLE_RE.search(str(t.get("asset_description", "")))]
    return txns


# ───────── vérité-terrain : dict ticker global (digital) + Quiver par membre ─────────
def build_ticker_dict():
    d = {}
    for y in range(2020, 2027):
        p = hm.TABROOT / str(y) / f"06_house_{y}_transactions.csv"
        if not p.exists():
            continue
        e = pd.read_csv(p, dtype=str)
        e = e[e["ticker"].notna() & (e["ticker"].str.strip() != "")]
        for _, row in e.iterrows():
            n = ocr._norm_asset(row["asset_description"])
            if n:
                d.setdefault(n, row["ticker"].upper())
    return d


def resolve_ticker(desc, tdict):
    t = ocr._explicit_ticker(desc)
    if t:
        return t.upper()
    return tdict.get(ocr._norm_asset(desc))


def load_quiver():
    q = pd.read_csv(hm.TABROOT / "_quiver_house_cache.csv", dtype=str)
    q["traded_d"] = pd.to_datetime(q["traded"], errors="coerce").dt.strftime("%Y-%m-%d")
    return q


def last_name(n):
    n = str(n).replace('"', "").split("(")[0].strip()
    return n.split()[-1].lower() if n.split() else n.lower()


def canon(t, tdict):
    """Clé canonique d'une txn OCR pour stabilité + matching."""
    return (ocr._norm_asset(t.get("asset_description", "")),
            str(t.get("transaction_date") or ""),
            (t.get("amount_code") or "").upper(),
            (t.get("transaction_type") or ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="full", choices=["smoke", "full"])
    args = ap.parse_args()
    if not ocr.ANTHROPIC_API_KEY:
        raise SystemExit("ANTHROPIC_API_KEY manquante")
    GATE_DIR.mkdir(parents=True, exist_ok=True)

    sample = pd.DataFrame(json.load(open("/tmp/ocr_test_sample.json")))
    sample["pages"] = pd.to_numeric(sample["pages"], errors="coerce").fillna(1).astype(int)
    if args.mode == "smoke":
        # 1 doc minuscule par cluster pour valider la plomberie
        smoke_ids = ["9115811", "8216969", "8217005"]  # Harshbarger 1p / Fleischmann 2p / Kelly 1p
        sample = sample[sample["doc_id"].isin(smoke_ids)]
    print(f"GATE OCR — mode={args.mode} — {len(sample)} docs, {int(sample['pages'].sum())} pages\n")

    tdict = build_ticker_dict()
    quiver = load_quiver()
    print(f"dict ticker digital: {len(tdict)} entrées | Quiver cache: {len(quiver)} txns\n")

    # qui rejoue 2x (stabilité) : tout C + dense-B représentatif + illisibles ; 1x sinon
    def need_two(r):
        if r["cluster"] == "C_manuscrit" or r["tag"].startswith("EDGE-illisible"):
            return True
        if r["cluster"] == "B_tape_tourne" and r["pages"] >= 5 and r["tag"] in ("B-dense-Khanna", "B-dense-McCaul", "B-dense-Harsh"):
            return True
        return False

    jobs = []
    for _, r in sample.iterrows():
        rec = r.to_dict()
        jobs.append((rec, 1))
        if need_two(rec):
            jobs.append((rec, 2))

    print(f"{len(jobs)} runs OCR au total (dont {sum(1 for _,k in jobs if k==2)} seconds-runs stabilité)\n")

    results = {}  # doc_id -> {run1:[...], run2:[...]}
    def work(rec, run):
        return rec, run, ocr_doc(rec)
    with ThreadPoolExecutor(max_workers=ocr.CONCURRENCY) as ex:
        futs = [ex.submit(work, rec, run) for rec, run in jobs]
        done = 0
        for fut in as_completed(futs):
            rec, run, txns = fut.result()
            results.setdefault(rec["doc_id"], {"rec": rec})[f"run{run}"] = txns
            done += 1
            print(f"  [{done}/{len(jobs)}] {rec['tag']:16s} {rec['year']}/{rec['doc_id']} {rec['member'][:22]:22s} run{run}: {len(txns)} txns")

    # dump brut pour debug
    json.dump({did: {"rec": d["rec"], "run1": d.get("run1"), "run2": d.get("run2")} for did, d in results.items()},
              open(GATE_DIR / "gate_raw.json", "w"), ensure_ascii=False, indent=1)

    # ───────── métriques par doc ─────────
    rows = []
    for did, d in results.items():
        rec = d["rec"]; r1 = d.get("run1", []); r2 = d.get("run2")
        n1 = len(r1)
        # stabilité
        if r2 is not None:
            s1 = {canon(t, tdict) for t in r1}; s2 = {canon(t, tdict) for t in r2}
            inter = len(s1 & s2); uni = len(s1 | s2)
            stab = inter / uni if uni else 1.0
            # stabilité dates seules (le défaut Khanna)
            d1 = sorted(str(t.get("transaction_date") or "") for t in r1)
            d2 = sorted(str(t.get("transaction_date") or "") for t in r2)
            date_stab = sum(a == b for a, b in zip(d1, d2)) / max(len(d1), len(d2), 1)
        else:
            stab, date_stab = None, None
        # Quiver — FENÊTRÉ par année de dépôt {year-1, year} (sinon faux zéros hors-période)
        ln = last_name(rec["member"])
        yr = int(rec["year"]); win = {str(yr), str(yr - 1)}
        qsub = quiver[quiver["Name"].apply(last_name) == ln]
        qwin = qsub[qsub["traded_d"].str[:4].isin(win)]
        our = [(resolve_ticker(t.get("asset_description", ""), tdict), str(t.get("transaction_date") or ""), t)
               for t in r1]
        n_tick = sum(1 for tk, _, _ in our if tk)
        has_gt = len(qwin) > 0                       # vérité-terrain Quiver disponible pour CETTE période ?
        if has_gt and n_tick:
            qtickers = set(qsub["Ticker"].dropna().str.upper())                 # tickers du membre (toutes dates)
            qtd = set(zip(qwin["Ticker"].dropna().str.upper(), qwin["traded_d"].dropna()))  # (ticker,date) en fenêtre
            prec_tick = sum(1 for tk, _, _ in our if tk and tk in qtickers) / n_tick   # nos tickers connus de Quiver
            prec_td = sum(1 for tk, dt, _ in our if tk and (tk, dt) in qtd) / n_tick    # (ticker,date) exact en fenêtre
            our_td = set((tk, dt) for tk, dt, _ in our if tk and dt)
            recall_td = (sum(1 for x in qtd if x in our_td) / len(qtd)) if qtd else None  # info (niveau membre-année)
        else:
            prec_tick = prec_td = recall_td = None
        rows.append({"cluster": rec["cluster"], "tag": rec["tag"], "year": rec["year"], "doc_id": did,
                     "member": rec["member"], "pages": rec["pages"], "n_txn": n1,
                     "n_ticker_resolu": n_tick, "stab_jaccard": stab, "stab_dates": date_stab,
                     "quiver_win": len(qwin), "has_gt": has_gt, "prec_ticker": prec_tick,
                     "prec_ticker_date": prec_td, "recall_td": recall_td})
    res = pd.DataFrame(rows).sort_values(["cluster", "tag", "doc_id"])
    res.to_csv(GATE_DIR / "gate_per_doc.csv", index=False)

    # ───────── synthèse par cluster + projection ─────────
    print("\n" + "=" * 78 + "\nRÉSULTATS PAR DOC\n" + "=" * 78)
    cols = ["cluster", "tag", "year", "doc_id", "member", "pages", "n_txn", "n_ticker_resolu",
            "stab_jaccard", "stab_dates", "quiver_win", "has_gt", "prec_ticker", "prec_ticker_date", "recall_td"]
    with pd.option_context("display.max_rows", None, "display.width", 200):
        print(res[cols].to_string(index=False))

    def agg(s):
        v = [x for x in s if x is not None and pd.notna(x)]
        return round(statistics.mean(v), 3) if v else None
    WEIGHTS = {"A_tape_droit": 0.135, "B_tape_tourne": 0.589, "C_manuscrit": 0.276}
    print("\n" + "=" * 78 + "\nSYNTHÈSE PAR CLUSTER (et projection census)\n" + "=" * 78)
    summ = []
    for cl, g in res.groupby("cluster"):
        row = {"cluster": cl, "poids_census": WEIGHTS.get(cl), "n_docs": len(g),
               "n_gt": int(g["has_gt"].sum()), "stab_jaccard": agg(g["stab_jaccard"]),
               "stab_dates": agg(g["stab_dates"]), "prec_ticker": agg(g["prec_ticker"]),
               "prec_ticker_date": agg(g["prec_ticker_date"]), "recall_td": agg(g["recall_td"])}
        summ.append(row)
    sdf = pd.DataFrame(summ)
    print(sdf.to_string(index=False))
    sdf.to_csv(GATE_DIR / "gate_by_cluster.csv", index=False)

    # projection pondérée (sur clusters mesurés)
    def proj(metric):
        num = den = 0
        for _, r in sdf.iterrows():
            if r[metric] is not None and r["poids_census"]:
                num += r[metric] * r["poids_census"]; den += r["poids_census"]
        return round(num / den, 3) if den else None
    print(f"\nPROJECTION pondérée sur 547 :")
    print(f"  précision (ticker,date) attendue : {proj('prec_ticker_date')}")
    print(f"  stabilité dates attendue         : {proj('stab_dates')}")
    print(f"\nSorties : {GATE_DIR}/gate_per_doc.csv + gate_by_cluster.csv")


if __name__ == "__main__":
    main()
