"""Triangulation & statut de validation par déposant — livrable « qu'a-t-on validé ou pas ».

Constat de l'investigation : Quiver, Kadoa, House Stock Watcher sont TOUS aveugles au papier/scanné
→ la triangulation externe ne marche que pour le DIGITAL ; le papier (Khanna, Harshbarger…) n'existe
dans aucun agrégateur → notre OCR est la SOURCE UNIQUE. Ce module matérialise ce constat :

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
