#!/usr/bin/env python
"""Fusion digital + OCR papier → table FINALE par an + enrichissement (Sénat toutes années).

Étape 1 (par an) : concatène la table digitale (`06_senate_{an}_transactions.csv`) et l'OCR papier
(`06b_senate_{an}_ocr_transactions.csv` si présente), déduplique de façon NON destructrice sur
(natural_key_hash, occurrence_index).

Étape 2 (sur le CORPUS COMPLET, en une passe — parité House/Q1, cf. audit de parité 2026-06-25) :
  - **résolution ticker** : dictionnaire nom→ticker (depuis les lignes déjà tickées) + passe LLM
    (`ticker.py`) → remonte la couverture du papier sans symbole imprimé ;
  - **secteur GICS → ETF SPDR** : `common.sector_enrich.enrich_sectors` (champs `sector_gics`, `etf_proxy`) ;
  - **flag `date_confidence`** : plausible/implausible selon la fenêtre légale (75 j), parité House.

Écrit `06_senate_{an}_FINAL.csv` (schéma 12 champs complet) + `00_final_status.csv`. Aucune validation
Quiver sur la couche OCR (Quiver-aveugle au papier) ; la validation digitale reste faite par
`senat_multiyear.py`. La résolution ne touche qu'à `ticker`/`ticker_source`/`sector_*`/`date_confidence` :
aucune ligne ajoutée ni supprimée (les amendements cross-année sont préservés).
"""
import glob
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent        # <repo>/senate
DATA = HERE.parent / "data" / "senate"         # données Sénat (parité data/house)

from senate import ticker                      # résolution ticker (parité House)
from common.sector_enrich import enrich_sectors  # secteur GICS → ETF (source unique partagée)
SECTOR_CACHE = DATA / "sector_cache.json"        # cache secteur Sénat (seul spécifique)

DATE_WINDOW_DAYS = 75   # parité House : un PTR se dépose ~45 j après la transaction (+marge)

# Schéma FINAL = 23 colonnes de base + date_confidence + sector_gics/etf_proxy/sector_source
FINAL_COLS = [
    "bioguide_id", "declarant_name", "chamber", "party", "state_district",
    "committee_membership", "committees_key_flag", "transaction_date", "disclosure_date",
    "date_confidence", "ticker", "asset_description", "asset_type", "sector_gics", "etf_proxy",
    "operation_type", "amount_range", "amount_midpoint", "amount_split_flag",
    "owner", "doc_id", "source_url", "natural_key_hash",
    "provenance", "ticker_source", "sector_source", "occurrence_index",
]


def date_confidence(transaction_date, disclosure_date):
    """'plausible' | 'implausible' | 'unknown' selon le délai légal dépôt−transaction (fenêtre 75 j)."""
    t = pd.to_datetime(transaction_date, errors="coerce")
    d = pd.to_datetime(disclosure_date, errors="coerce")
    if pd.isna(t) or pd.isna(d):
        return "unknown"
    lag = (d - t).days
    return "plausible" if 0 <= lag <= DATE_WINDOW_DAYS else "implausible"


def main():
    years = sorted(int(re.search(r"/(\d{4})/", p).group(1))
                   for p in glob.glob(str(DATA / "20*" / "06_senate_*_transactions.csv")))

    # --- Étape 1 : fusion non destructrice par année ---
    per_year, meta = {}, {}
    for y in years:
        ydir = DATA / "tables" / str(y)
        dig = pd.read_csv(ydir / f"06_senate_{y}_transactions.csv", dtype=str)
        ocr_path = ydir / f"06b_senate_{y}_ocr_transactions.csv"
        if ocr_path.exists():
            ocr = pd.read_csv(ocr_path, dtype=str)
            final = pd.concat([dig, ocr.reindex(columns=dig.columns)], ignore_index=True)
            n_before = len(final)
            final = final.drop_duplicates(["natural_key_hash", "occurrence_index"], keep="first")
            n_ocr_added, n_dups = len(final) - len(dig), n_before - len(final)
            n_ocr = len(ocr)
        else:
            final, n_ocr, n_ocr_added, n_dups = dig.copy(), 0, 0, 0
        final = final.reset_index(drop=True)
        final["_year"] = y
        per_year[y] = final
        tk0 = round(100 * final["ticker"].notna().mean(), 1) if len(final) else 0.0
        meta[y] = {"n_digital": len(dig), "n_ocr": n_ocr, "n_ocr_added": n_ocr_added,
                   "n_dups_intersource": n_dups, "n_final": len(final), "ticker_pct_avant": tk0}

    # --- Étape 2 : enrichissement sur le corpus complet (une passe : dict+LLM partagés, cache unique) ---
    big = pd.concat(per_year.values(), ignore_index=True)
    print(f"Corpus FINAL : {len(big)} lignes / {len(years)} années — enrichissement…")
    big = ticker.resolve_tickers(big)                               # ticker : dict + LLM
    big = enrich_sectors(big, SECTOR_CACHE, with_llm=True, audit_all=True)  # secteur GICS → ETF SPDR
    big["date_confidence"] = [date_confidence(t, d)                 # flag date (parité House)
                              for t, d in zip(big["transaction_date"], big["disclosure_date"])]

    # --- Validation Quiver RICHE par SCOPE (digital / OCR / les deux) — cf. common/quiver_scopes ---
    # Sénat : Quiver est AVEUGLE au papier (Blumenthal/Feinstein = 0 ligne Quiver) → le scope `ocr`
    # ressort VIDE (coverage None) = « OCR = source unique » VRAI ici (≠ House, où Quiver voit le papier
    # comme Khanna → l'OCR y est validé externe ~75 %).
    from senate import quiver as vq
    from senate.identity import load_reference as _load_ref
    from common.quiver_scopes import reconcile_scopes
    _sbios = {b for b, v in _load_ref()[0].items() if v["chamber"] == "senate"}
    _qdf = pd.read_csv(DATA / "tables" / "_quiver_senate_cache.csv")
    _qdf["Filed"] = pd.to_datetime(_qdf["Filed"], errors="coerce")
    _qdf["Traded"] = pd.to_datetime(_qdf["Traded"], errors="coerce")

    # --- Écriture par année (schéma FINAL) + dashboard ---
    rows = []
    for y in years:
        final = big[big["_year"] == y].drop(columns="_year").reindex(columns=FINAL_COLS)
        _ydir = DATA / "tables" / str(y)
        final.to_csv(_ydir / f"06_senate_{y}_FINAL.csv", index=False)
        # réconciliation Quiver 3 scopes → 07c-f (relue depuis le disque, dtype=str → cohérent golden)
        _qy = _qdf[(_qdf["Filed"].dt.year == y) & (_qdf["BioGuideID"].isin(_sbios))].copy()
        _dig = pd.read_csv(_ydir / f"06_senate_{y}_transactions.csv", dtype=str)
        _ocrp = _ydir / f"06b_senate_{y}_ocr_transactions.csv"
        _ocr = pd.read_csv(_ocrp, dtype=str) if _ocrp.exists() else _dig.iloc[0:0]
        _fin = pd.read_csv(_ydir / f"06_senate_{y}_FINAL.csv", dtype=str)
        _txn, _field, _rb = reconcile_scopes(vq.reconcile, {"digital": _dig, "ocr": _ocr, "both": _fin}, _qy)
        _txn.to_csv(_ydir / "07c_quiver_txn_reconciliation.csv", index=False)
        _field.to_csv(_ydir / "07d_quiver_field_agreement.csv", index=False)
        _rb["ticker_per_sen"].to_csv(_ydir / "07e_quiver_ticker_per_senator.csv", index=False)
        _rb["only_quiver_txn"].to_csv(_ydir / "07f_quiver_only_quiver_txn.csv", index=False)
        # 07g — décomposition par asset_type (le Sénat n'a pas de census/cluster). Montre que l'OCR Sénat
        # est surtout du NON-COTÉ (munis/obligations) hors périmètre Quiver. Cf. quiver_scopes.match_breakdown.
        from common.quiver_scopes import match_breakdown
        _ba, _ = match_breakdown(_fin, _qy, vq.norm_ticker, vq.norm_sense)
        _ba.to_csv(_ydir / "07g_quiver_match_by_asset.csv", index=False)
        midp = pd.to_numeric(final["amount_midpoint"], errors="coerce")
        m = meta[y]
        rows.append({
            "year": y, "n_digital": m["n_digital"], "n_ocr": m["n_ocr"],
            "n_ocr_added": m["n_ocr_added"], "n_dups_intersource": m["n_dups_intersource"],
            "n_final": m["n_final"], "senateurs_final": final["bioguide_id"].nunique(),
            "ticker_pct_avant": m["ticker_pct_avant"],
            "ticker_pct_final": round(100 * final["ticker"].notna().mean(), 1),
            "sector_pct_final": round(100 * final["sector_gics"].notna().mean(), 1),
            "date_implausible": int((final["date_confidence"] == "implausible").sum()),
            "volume_final_musd": round(midp.sum() / 1e6, 1),
        })
        print(f"  {y}: digital {m['n_digital']:4} + OCR {m['n_ocr']:3} → FINAL {m['n_final']:4} "
              f"| ticker {m['ticker_pct_avant']:.0f}%→{rows[-1]['ticker_pct_final']:.0f}% "
              f"| secteur {rows[-1]['sector_pct_final']:.0f}%")

    dash = pd.DataFrame(rows)
    dash.to_csv(DATA / "tables" / "00_final_status.csv", index=False)
    print("\n=== 00_final_status.csv ===")
    print(dash.to_string(index=False))
    n_tk = int(big["ticker"].notna().sum())
    print(f"\nTOTAL FINAL : {dash['n_final'].sum()} txns | dont OCR ajouté : {dash['n_ocr_added'].sum()} "
          f"| ticker global {round(100*n_tk/len(big),1)}% ({n_tk}/{len(big)}) "
          f"| secteur {round(100*big['sector_gics'].notna().mean(),1)}% "
          f"| sources={big['ticker_source'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
