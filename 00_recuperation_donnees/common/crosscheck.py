"""Triangulation & statut de validation par déposant — livrable « qu'a-t-on validé ou pas ».

Constat NUANCÉ (cf. validation 3-scopes, common/quiver_scopes.py) : Quiver POSSÈDE le papier AU HOUSE
(Rohit Khanna ≈ 29 000 lignes Quiver) → l'OCR House y est validé en EXTERNE (~75 % au scope `ocr`). C'est
AU SÉNAT que Quiver est aveugle au papier (Blumenthal, Feinstein = 0 ligne), surtout parce que l'OCR y
est du NON-COTÉ (munis/obligations, hors périmètre actions de Quiver) → là, et là seulement, notre OCR
est la SOURCE UNIQUE. Ce module n'attribue `ocr_unique` que lorsque Quiver≈0 (donc Khanna, vu par Quiver,
sort `quiver_validable`) :

  - `per_filer_status(final_df, quiver_df)` : statut par déposant (bioguide), axe principal Quiver.
  - `add_external_counts(...)` : ajoute Kadoa (résumé House) + House Stock Watcher par nom (best-effort).

Statuts : `quiver_validable` (Quiver le couvre) · `ocr_unique` (on l'a SURTOUT via OCR, Quiver≈0,
aucune source externe) · `digital` (digital, peu/pas d'OCR).
"""
import re
import json
from pathlib import Path

import pandas as pd


def _norm_name(s):
    s = re.sub(r"[^a-z ]", " ", str(s).lower())
    return re.sub(r"\s+", " ", s).strip()


def per_filer_status(final_df, quiver_df, chamber="house"):
    """Table de statut par déposant : nos comptes (digital/OCR) vs Quiver (par bioguide), + verdict."""
    f = final_df.copy()
    prov_ocr = f"{chamber}-pdf-ocr" if chamber == "house" else f"{chamber}-efd-ocr"
    f["_ocr"] = (f.get("provenance", "") == prov_ocr)
    g = f.groupby("bioguide_id").agg(
        name=("declarant_name", "first"),
        our_total=("doc_id", "size"),
        our_ocr=("_ocr", "sum"),
        n_docs=("doc_id", "nunique"),
    ).reset_index()
    g["our_digital"] = g["our_total"] - g["our_ocr"]

    if quiver_df is not None and len(quiver_df):
        qcol = "BioGuideID"
        qcount = quiver_df.groupby(qcol).size()
        g["quiver"] = g["bioguide_id"].map(qcount).fillna(0).astype(int)
    else:
        g["quiver"] = 0

    def _status(r):
        if r["quiver"] > 0:
            return "quiver_validable"
        if r["our_ocr"] > 0 and r["our_ocr"] >= 0.5 * r["our_total"]:
            return "ocr_unique"       # surtout papier + Quiver aveugle → source unique
        return "digital"
    g["status"] = g.apply(_status, axis=1)
    g["ocr_share_pct"] = (100 * g["our_ocr"] / g["our_total"]).round().astype(int)
    return g.sort_values("our_total", ascending=False).reset_index(drop=True)


def load_kadoa_house(path):
    """Résumé déposant Kadoa (House) : full_name → trade_count. Fichier archivé semaine 1."""
    data = json.loads(Path(path).read_text())
    out = {}
    for x in data:
        if x.get("chamber") == "house" and x.get("full_name"):
            out[_norm_name(x["full_name"])] = x.get("trade_count")
    return out


def load_hsw_counts(path):
    """House Stock Watcher (miroir JSON) : representative → nb de transactions. Best-effort par nom."""
    data = json.loads(Path(path).read_text())
    cnt = {}
    for t in data:
        nm = _norm_name(t.get("representative", ""))
        if nm:
            cnt[nm] = cnt.get(nm, 0) + 1
    return cnt


def add_external_counts(status_df, kadoa=None, hsw=None):
    """Ajoute les comptes Kadoa / HSW par appariement de NOM (best-effort). Colonnes informatives :
    si une ligne OCR-unique a kadoa=hsw=0, c'est la preuve chiffrée que notre OCR est la seule source."""
    s = status_df.copy()
    s["_nk"] = s["name"].map(_norm_name)
    if kadoa is not None:
        s["kadoa"] = s["_nk"].map(lambda n: kadoa.get(n, 0))
    if hsw is not None:
        s["hsw"] = s["_nk"].map(lambda n: hsw.get(n, 0))
    return s.drop(columns="_nk")


def summary(status_df):
    """Récap : combien de déposants/transactions par statut (le résumé superviseur)."""
    by = status_df.groupby("status").agg(
        deposants=("bioguide_id", "size"),
        transactions=("our_total", "sum"),
        dont_ocr=("our_ocr", "sum"),
    ).reset_index()
    return by


# ─────────────────────────────────────────────────────────────────────────────
#  Corroboration LIGNE À LIGNE (transaction par transaction) contre une collecte
#  publique tierce. Deux collectes indépendantes re-lisant les mêmes sources
#  officielles : senate-stock-watcher (Sénat) et house-stock-watcher (House).
#  La concordance mesure la ROBUSTESSE de notre lecture (pas la complétude vs un
#  univers tiers). Clé d'appariement = déposant · ticker · sens · date (montant
#  hors clé — la loi ne donne qu'une tranche). On rapporte aussi le sous-ensemble
#  `asset_type == "Stock"`, seul directement comparable à notre table backtest
#  (qui filtre les fonds mutuels et ETF exotiques).
# ─────────────────────────────────────────────────────────────────────────────
from datetime import date as _date

_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def _key_norm(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower())


def _name_keys(fullname):
    """Clés-nom robustes {dernier mot, deux derniers mots}, suffixes (Jr./III) retirés.
    Gère les noms composés (Van Hollen) et les formats « Prénom Nom, Suffixe »."""
    toks = [_key_norm(x) for x in str(fullname).split(",")[0].split()]
    toks = [x for x in toks if x and x not in _SUFFIXES]
    keys = set()
    if toks:
        keys.add(toks[-1])
    if len(toks) >= 2:
        keys.add(toks[-2] + toks[-1])
    return frozenset(keys)


def _tick_ok(t):
    return bool(re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,5}", t or ""))


def _sens(t):
    t = (t or "").lower()
    return "buy" if t.startswith("purchase") else "sell" if t.startswith("sale") \
        else "exch" if t.startswith("exchange") else "?"


def _pdate(s):
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s or "")
    if m:
        return _date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s or "")
    if m:
        return _date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def _ssw_ticker(raw):
    """SSW encapsule le symbole dans un lien HTML : <a ...q?s=AAPL>AAPL</a> → AAPL."""
    if not raw or raw.strip() == "--":
        return ""
    m = re.search(r"q\?s=([A-Za-z0-9.\-]+)", raw) or re.search(r">([A-Za-z0-9.\-]+)</a>", raw)
    return (m.group(1) if m else raw).strip().upper()


def load_ssw_lines(path):
    """senate-stock-watcher (`ssw_all_daily_summaries.json`) → lignes normalisées.
    Renvoie une liste de dicts {name, ticker, sens, date, is_stock}."""
    out = []
    for f in json.loads(Path(path).read_text()):
        keys = _name_keys(f.get("last_name", ""))
        for t in f.get("transactions", []):
            tk = _ssw_ticker(t.get("ticker", ""))
            if not _tick_ok(tk):
                continue
            out.append(dict(name=keys, ticker=tk, sens=_sens(t.get("type", "")),
                            date=_pdate(t.get("transaction_date", "")),
                            is_stock=(t.get("asset_type", "") == "Stock")))
    return out


def load_hsw_lines(path):
    """house-stock-watcher (`hsw_all_transactions.json`) → lignes normalisées (même schéma)."""
    out = []
    for t in json.loads(Path(path).read_text()):
        tk = (t.get("ticker") or "").strip().upper()
        if not _tick_ok(tk):
            continue
        out.append(dict(name=_name_keys(t.get("representative", "")), ticker=tk,
                        sens=_sens(t.get("type", "")), date=_pdate(t.get("transaction_date", "")),
                        is_stock=(t.get("asset_type", "") == "Stock")))
    return out


def corroboration_lignes(backtest_df, tp_lines, chamber):
    """Appariement ligne à ligne d'une collecte tierce (`tp_lines`, cf. load_*_lines) contre
    NOTRE table de recherche (`backtest_df`, colonnes member_name/chamber/ticker/ticker_yahoo/
    direction/transaction_date), restreinte à `chamber`.

    Clé stricte = (nom, ticker, sens, date). On indexe notre table par ticker ET ticker_yahoo
    (renommages) et par chaque clé-nom du membre. Renvoie un dict de taux + le résidu (DataFrame)
    des lignes « Stock » non retrouvées, pour inspection.
    """
    sub = backtest_df[backtest_df["chamber"] == chamber]
    by_nts, by_nt = {}, {}                          # (nk,ticker,sens)->set(dates) ; (nk,ticker)->1
    for m_name, tk, tky, dr, td in zip(sub["member_name"], sub["ticker"], sub["ticker_yahoo"],
                                       sub["direction"], sub["transaction_date"]):
        d = _pdate(str(td))
        for nk in _name_keys(m_name):
            for t in {str(tk).upper(), str(tky).upper()}:
                if not t or t == "NAN":
                    continue
                by_nts.setdefault((nk, t, dr), set()).add(d)
                by_nt[(nk, t)] = 1

    def hit_exact(x):
        return any(x["date"] in by_nts.get((nk, x["ticker"], x["sens"]), ()) for nk in x["name"])

    def hit_loose(x):                               # titre+personne, date/sens libres
        return any((nk, x["ticker"]) in by_nt for nk in x["name"])

    ps = [x for x in tp_lines if x["sens"] in ("buy", "sell")]
    stock = [x for x in ps if x["is_stock"]]

    def rates(items):
        n = len(items)
        e = sum(hit_exact(x) for x in items)
        loo = sum(hit_loose(x) for x in items)
        return dict(n=n, exact=e, pct_exact=round(100 * e / n, 1) if n else 0.0,
                    loose=loo, pct_loose=round(100 * loo / n, 1) if n else 0.0)

    residu = [x for x in stock if not hit_loose(x)]
    return dict(
        chamber=chamber,
        tout_cote=rates(ps),                        # actions + ETF + fonds (fonds filtrés chez nous)
        actions=rates(stock),                       # asset_type == Stock : le périmètre comparable
        n_echanges=sum(1 for x in tp_lines if x["sens"] == "exch"),
        residu=pd.DataFrame([dict(ticker=x["ticker"], sens=x["sens"], date=x["date"]) for x in residu]),
    )
