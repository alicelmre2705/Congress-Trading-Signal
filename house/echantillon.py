#!/usr/bin/env python
"""OCR sur ÉCHANTILLON représentatif par année (~70 docs) — le livrable OCR (pas le run complet des 547).

⚠️ OUTIL HORS PIPELINE : non lancé par `congress_core.pipeline:build_steps` (pilote/diagnostic ponctuel).

Sélection : data_v1/tables/_ocr_echantillon.csv (10/an, stratifié clusters A/B/C, Quiver-couvert priorisé).
Méthode : prompt DURCI (validé), routage DPI/pages-par-appel par densité, CAP de pages sur les gros docs,
cache dédié data_v1/ocr_cache_echantillon/ (n'altère PAS le cache OCR principal). Enrichissement ticker
(dict digital global + passe LLM nom→ticker) puis comparaison Quiver par cluster ET par année.

Réutilise house_ocr_multiyear (TXN_TOOL, MODEL, normalize, llm_resolve_tickers, _norm_asset, _explicit_ticker,
_infer_asset_type, _EXAMPLE_RE) et house_multiyear (resolve_pdf_path, match_bioguide, fetch_quiver, build_reference).
"""
import base64, json, hashlib, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pymupdf, pandas as pd, anthropic

import house.ocr as ocr
import house.digital as hm

# ───── prompt DURCI (validé A/B : garde-fou date, transcription fidèle, 1 ligne = 1 txn) ─────
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
  6. DATES — GARDE-FOU : ce dépôt date de {filing_year}. L'année de TOUTE transaction doit être
     {filing_year} ou {prev_year} — c'est quasi-certain. Si tu lis une autre année, c'est une ERREUR
     de lecture : relis le dernier chiffre de l'année attentivement (sur un formulaire tourné 90°,
     « 4 » ressemble à « 1 », « 3 » à « 8 »). Corrige vers {filing_year} ou {prev_year} selon le contexte.
     Convertis MM/DD/YY → YYYY-MM-DD. Lis transaction_date ET notification_date ligne par ligne.
  7. amount_code = UNIQUEMENT la lettre cochée (A–K). Si illisible, omets le champ.
"""
# PIPELINE_TAG : versionne le cache OCR. Toute modif de l'IMAGE envoyée (ici : deskew des scans
# tournés) doit changer ce tag pour invalider l'ancien cache non-redressé et forcer un re-run propre.
PIPELINE_TAG = "deskew_v1"
PROMPT_SHA = hashlib.sha256((HARDENED + json.dumps(ocr.TXN_TOOL, sort_keys=True) + ocr.MODEL + PIPELINE_TAG).encode()).hexdigest()[:12]
CACHE_DIR = hm.OUTDIR / "ocr_cache_echantillon"
MAX_PAGES = 8           # cap pour le coût sur les gros docs denses (échantillon, pas run complet)
# Tolérance d'appariement de date OCR↔Quiver. Quiver bruite la date de ±1-2 j (amendements, date de
# saisie côté QuiverQuant) : une égalité STRICTE comptait ces écarts comme des erreurs. ±3 j ferme cet
# artefact sans masquer les vrais misreads (queue à plusieurs semaines visible via date_delta_days).
DATE_TOL_DAYS = 3


def _route(n_pages):
    return (300, 1) if n_pages >= 5 else (250, 3)   # dense → DPI haut, 1 page/appel


def _render(path, dpi, cap, cli=None):
    """Rend les pages (cap max) en PNG b64. Avec cli : détecte l'orientation de CHAQUE page (basse DPI,
    montage 4-rotations) et la REDRESSE — détection page par page car 27 % des docs sont 'mixed' (pages
    d'orientations différentes). Renvoie (images, angles) avec angles = liste des angles appliqués."""
    d = pymupdf.open(path)
    pages = list(d)[:cap]
    imgs, angles = [], []
    for p in pages:
        full = base64.b64encode(p.get_pixmap(dpi=dpi).tobytes("png")).decode()
        if cli is not None:
            low = base64.b64encode(p.get_pixmap(dpi=ocr.ROT_DETECT_DPI).tobytes("png")).decode()
            ang = ocr.detect_rotation(cli, low)
        else:
            ang = 0
        imgs.append(ocr.rotate_b64_png(full, ang)); angles.append(ang)
    d.close()
    return imgs, angles


def _call(cli, imgs, member, year, retries=6):
    content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b}} for b in imgs]
    content.append({"type": "text", "text": HARDENED.format(member_name=member, filing_year=year, prev_year=year - 1)})
    for a in range(retries):
        try:
            r = cli.messages.create(model=ocr.MODEL, max_tokens=ocr.MAX_TOKENS, tools=[ocr.TXN_TOOL],
                                    tool_choice={"type": "tool", "name": "record_transactions"},
                                    messages=[{"role": "user", "content": content}])
            for b in r.content:
                if getattr(b, "type", None) == "tool_use" and b.name == "record_transactions":
                    return b.input.get("transactions", [])
            return []
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            if a < retries - 1:
                time.sleep(min(2 ** a, 45)); continue
            raise


def _ocr_doc(rec, cli):
    """OCR d'un doc de l'échantillon. Ordre : cache durci (versionné PIPELINE_TAG) → API (si crédit).
    NOTE : le repli sur le cache OCR PRINCIPAL est volontairement désactivé ici — il contient des
    extractions NON redressées (sideways), incompatibles avec le pipeline deskew. On ré-OCR à neuf.
    Ne lève jamais : si l'API échoue, renvoie [] (le doc est juste sauté)."""
    y, did = str(rec["year"]), str(rec["doc_id"])
    cf = CACHE_DIR / y / f"{did}.json"; cf.parent.mkdir(parents=True, exist_ok=True)
    if cf.exists():
        o = json.loads(cf.read_text())
        if o.get("prompt_sha") == PROMPT_SHA and o.get("model") == ocr.MODEL:
            return did, o["transactions"]
    # OCR frais, redressé (peut échouer si crédit épuisé)
    try:
        path = hm.resolve_pdf_path(y, did)
        dpi, per = _route(int(rec["pages"]))
        imgs, angles = _render(path, dpi, MAX_PAGES, cli=cli)
        batches = [imgs[i:i + per] for i in range(0, len(imgs), per)]
        txns = []
        for b in batches:
            txns += _call(cli, b, rec["member"], int(y))
        txns = [t for t in txns if not ocr._EXAMPLE_RE.search(str(t.get("asset_description", "")))]
        cf.write_text(json.dumps({"doc_id": did, "year": y, "model": ocr.MODEL, "prompt_sha": PROMPT_SHA,
                                  "rotation_deg": angles, "n_pages_ocr": min(len(imgs), MAX_PAGES),
                                  "transactions": txns}, ensure_ascii=False))
        return did, txns
    except Exception as e:
        print(f"  [skip {y}/{did} : {type(e).__name__}]")
        return did, []


def _global_ticker_dict():
    """nom normalisé → ticker depuis TOUTES les tables digitales (meilleure couverture que l'année seule)."""
    d = {}
    for y in range(2020, 2027):
        p = hm.TABROOT / str(y) / f"06_house_{y}_transactions.csv"
        if not p.exists():
            continue
        e = pd.read_csv(p, dtype=str)
        e = e[e["ticker"].notna() & (e["ticker"].str.strip() != "")]
        for _, r in e.iterrows():
            n = ocr._norm_asset(r["asset_description"])
            if n:
                d.setdefault(n, r["ticker"].upper())
    return d


def run_echantillon(verbose=True):
    """OCR + enrichissement de l'échantillon. Renvoie le DataFrame et écrit _ocr_echantillon_resultats.csv."""
    if not ocr.ANTHROPIC_API_KEY:
        raise SystemExit("ANTHROPIC_API_KEY manquante")
    hm.build_reference()
    ech = pd.read_csv(hm.TABROOT / "_ocr_echantillon.csv", dtype={"doc_id": str})

    # Le cluster C (manuscrit) est une CATÉGORIE CONSERVÉE mais NON EXÉCUTÉE (cf. ocr.CLUSTERS_NON_EXECUTES) :
    # dates OCR manuscrites peu fiables. Cet échantillon mesure la qualité A+B, donc on n'y mêle pas C.
    # La perte Quiver-corroborée de C (concentrée sur 3 filers, cf. cross-val) se récupère via le SCALER
    # complet (house_ocr_multiyear.FILERS_C_A_RECUPERER), pas via cet échantillon de mesure.
    n_all = len(ech)
    n_c = int(ech["cluster"].isin(ocr.CLUSTERS_NON_EXECUTES).sum())
    ech = ech[~ech["cluster"].isin(ocr.CLUSTERS_NON_EXECUTES)].reset_index(drop=True)
    if verbose:
        print(f"  Cluster C non exécuté (catégorie conservée) : {n_c}/{n_all} docs écartés → mesure A+B sur {len(ech)}")

    # meta par doc (declarant/last/first/state_district/disclosure_date) depuis 03_ptr_index
    meta = {}
    for y in ech["year"].unique():
        ptr = pd.read_csv(hm.TABROOT / str(y) / "03_ptr_index.csv", dtype={"doc_id": str})
        for _, r in ptr.iterrows():
            meta[r["doc_id"]] = r.to_dict()

    cli = anthropic.Anthropic(api_key=ocr.ANTHROPIC_API_KEY)
    recs = ech.to_dict("records")
    txns_by_doc = {}
    with ThreadPoolExecutor(max_workers=ocr.CONCURRENCY) as ex:
        futs = {ex.submit(_ocr_doc, rec, cli): rec["doc_id"] for rec in recs}
        done = 0
        for fut in as_completed(futs):
            try:
                did, txns = fut.result()
            except Exception as e:
                did, txns = futs[fut], []
                print(f"  [échec {did} : {type(e).__name__}]")
            txns_by_doc[did] = txns; done += 1
            if verbose and (done % 10 == 0 or done == len(recs)):
                print(f"  OCR échantillon : {done}/{len(recs)} docs")

    # normalisation (schéma 06b)
    rows = []
    for rec in recs:
        did = rec["doc_id"]; m = meta.get(did, {"doc_id": did, "declarant_name": rec["member"]})
        for t in txns_by_doc.get(did, []):
            r = ocr.normalize(t, m, int(rec["year"]))
            r["year"] = rec["year"]; r["cluster"] = rec["cluster"]
            rows.append(r)
    df = pd.DataFrame(rows)
    if df.empty:
        print("Aucune transaction OCR sur l'échantillon"); return df

    # enrichissement ticker : dict global digital → passe LLM
    tdict = _global_ticker_dict()
    def _resolve(desc):
        t = ocr._explicit_ticker(desc)
        if t: return t.upper(), "explicit"
        t = tdict.get(ocr._norm_asset(desc))
        if t: return t, "elec_dict"
        return None, "none"
    res = df["asset_description"].map(_resolve)
    df["ticker"] = [r[0] for r in res]; df["ticker_source"] = [r[1] for r in res]
    df["asset_type"] = df["asset_description"].map(ocr._infer_asset_type)
    df = ocr.llm_resolve_tickers(df)

    # bioguide
    df["bioguide_id"] = df["doc_id"].map(
        lambda d: hm.match_bioguide(meta.get(d, {}).get("last", ""), meta.get(d, {}).get("first", "")) if d in meta else None)

    df.to_csv(hm.TABROOT / "_ocr_echantillon_resultats.csv", index=False)
    if verbose:
        n_tk = int((df["ticker"].fillna("").astype(str).str.strip() != "").sum())
        print(f"\nÉchantillon OCR : {len(df)} txns | ticker {n_tk}/{len(df)} ({100*n_tk/len(df):.0f}%) "
              f"| sources {df['ticker_source'].value_counts().to_dict()}")
    return df


def _nearest_signed(our_ts, dates):
    """(date Quiver la plus proche, écart signé our-quiver en jours) ; (None, None) si indéterminé."""
    if our_ts is None or not dates:
        return None, None
    arr = pd.Series(dates)
    near = arr.iloc[(arr - our_ts).abs().values.argmin()]
    return near, int((our_ts - near).days)


def compare_quiver(df, tol=DATE_TOL_DAYS):
    """Concordance Quiver fenêtrée (par membre+année) → précision par cluster ET par année.
    prec_ticker_date tolère un écart de date <= tol jours (cf. DATE_TOL_DAYS)."""
    q = hm.fetch_quiver().copy()
    q["_tk"] = q["Ticker"].astype(str).str.upper()
    q["_ty"] = pd.to_datetime(q["traded"], errors="coerce")
    q["_yr"] = q["_ty"].dt.strftime("%Y-%m-%d").str[:4]
    per_doc = []
    for (did, y, cl), g in df.groupby(["doc_id", "year", "cluster"]):
        bio = g["bioguide_id"].iloc[0]
        our = [(str(tk).upper(), str(dt)) for tk, dt in zip(g["ticker"], g["transaction_date"]) if pd.notna(tk) and str(tk).strip()]
        n_tk = len(our)
        win = {str(int(y)), str(int(y) - 1)}
        qbio = q[q["BioGuideID"] == bio]
        qm = qbio[qbio["_yr"].isin(win)]
        has_gt = len(qm) > 0 and n_tk > 0
        if has_gt:
            qtick = set(qbio["_tk"])
            byt = {}                                          # ticker → dates Quiver fenêtrées
            for _, r in qm.iterrows():
                if pd.notna(r["_ty"]):
                    byt.setdefault(r["_tk"], []).append(r["_ty"])
            def _date_ok(tk, dt):
                ds = byt.get(tk)
                if not ds:
                    return False
                try:
                    o = pd.Timestamp(dt)
                except Exception:
                    return False
                return any(abs((o - d).days) <= tol for d in ds)
            prec_t = sum(1 for tk, _ in our if tk in qtick) / n_tk
            prec_td = sum(1 for tk, dt in our if _date_ok(tk, dt)) / n_tk
        else:
            prec_t = prec_td = None
        per_doc.append({"year": y, "cluster": cl, "doc_id": did, "n_txn": len(g), "n_ticker": n_tk,
                        "has_gt": has_gt, "prec_ticker": prec_t, "prec_ticker_date": prec_td})
    pd_df = pd.DataFrame(per_doc)
    pd_df.to_csv(hm.TABROOT / "_ocr_echantillon_quiver_doc.csv", index=False)
    return pd_df


def detailed_quiver_diff(df, tol=DATE_TOL_DAYS):
    """Diff transaction par transaction contre Quiver.
    Statuts : match | ticker_ok_date_wrong | ticker_wrong | no_gt | no_ticker.
    'match' tolère un écart de date <= tol jours (Quiver bruite ±1-2 j). date_delta_days = écart signé
    (our - quiver) à la date Quiver la plus proche pour ce ticker (toutes années → révèle les confusions
    d'année). Écrit _ocr_echantillon_diff.csv et retourne le DataFrame."""
    q = hm.fetch_quiver().copy()
    q["_tk"] = q["Ticker"].astype(str).str.upper()
    q["_ty"] = pd.to_datetime(q["traded"], errors="coerce")
    q["_yr"] = q["_ty"].dt.strftime("%Y-%m-%d").str[:4]
    rows = []
    for (did, y, cl), g in df.groupby(["doc_id", "year", "cluster"]):
        bio = g["bioguide_id"].iloc[0]
        has_bio = isinstance(bio, str) and bio.strip()
        qbio = q[q["BioGuideID"] == bio] if has_bio else q.iloc[:0]
        win = {str(int(y)), str(int(y) - 1)}
        qm = qbio[qbio["_yr"].isin(win)]
        has_gt = len(qm) > 0
        byt_win, byt_all = {}, {}      # ticker → dates Quiver (fenêtre / toutes années)
        for _, r in qm.iterrows():
            if pd.notna(r["_ty"]):
                byt_win.setdefault(r["_tk"], []).append(r["_ty"])
        for _, r in qbio.iterrows():
            if pd.notna(r["_ty"]):
                byt_all.setdefault(r["_tk"], []).append(r["_ty"])
        for _, row in g.iterrows():
            tk_raw = row.get("ticker", "")
            tk = str(tk_raw).upper().strip() if pd.notna(tk_raw) and str(tk_raw).strip() else ""
            dt_raw = row.get("transaction_date", "")
            dt = str(dt_raw) if pd.notna(dt_raw) and str(dt_raw) not in ("nan", "NaT") else ""
            our_ts = None
            if dt:
                try:
                    our_ts = pd.Timestamp(dt)
                except Exception:
                    our_ts = None
            base = {"doc_id": did, "year": y, "cluster": cl, "ticker": tk or None,
                    "transaction_date": dt or None, "asset_description": str(row.get("asset_description", "")),
                    "ticker_source": str(row.get("ticker_source", "")),
                    "quiver_date_nearest": None, "date_delta_days": None, "status": None}
            if not tk:
                base["status"] = "no_ticker"
            elif not has_gt:
                base["status"] = "no_gt"
            elif tk in byt_win and our_ts is not None and any(abs((our_ts - d).days) <= tol for d in byt_win[tk]):
                base["status"] = "match"
                near, delta = _nearest_signed(our_ts, byt_win[tk])
                base["quiver_date_nearest"] = near.strftime("%Y-%m-%d") if near is not None else dt
                base["date_delta_days"] = delta
            elif tk in byt_all:
                base["status"] = "ticker_ok_date_wrong"
                near, delta = _nearest_signed(our_ts, byt_all[tk])
                if near is not None:
                    base["quiver_date_nearest"] = near.strftime("%Y-%m-%d")
                    base["date_delta_days"] = delta
            else:
                base["status"] = "ticker_wrong"
            rows.append(base)
    cols = ["doc_id", "year", "cluster", "ticker", "transaction_date", "asset_description",
            "ticker_source", "quiver_date_nearest", "date_delta_days", "status"]
    result = pd.DataFrame(rows) if rows else pd.DataFrame(columns=cols)
    result.to_csv(hm.TABROOT / "_ocr_echantillon_diff.csv", index=False)
    return result


if __name__ == "__main__":
    df = run_echantillon()
    stats = compare_quiver(df)
    print("\n=== Concordance Quiver par cluster ===")
    print(stats.groupby("cluster")[["prec_ticker", "prec_ticker_date"]].mean().round(3).to_string())
    print("\n=== par année ===")
    print(stats.groupby("year")[["prec_ticker", "prec_ticker_date"]].mean().round(3).to_string())
