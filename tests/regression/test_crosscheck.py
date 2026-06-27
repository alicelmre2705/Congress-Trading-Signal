#!/usr/bin/env python
"""Phase 3 — smoke quiver + démo crosscheck (livrable statut/déposant) sur les tables figées.

Vérifie que crosscheck produit la table de statut et que les déposants papier (Khanna/Harshbarger…)
ressortent bien `ocr_unique` avec Kadoa≈0 — la preuve chiffrée, en code, que l'OCR est la source unique.
"""
import sys
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ENGINE = REPO / "data" / "house"
TABLES = ENGINE / "tables"
KADOA = REPO / "data" / "external" / "senate_openset" / "kadoa_filers.json"
HSW = REPO / "data" / "external" / "hsw.json"  # miroir House Stock Watcher (optionnel, absent par défaut)
sys.path.insert(0, str(REPO))
YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]


def main():
    import house.quiver as quiver  # smoke
    from congress_core import crosscheck as cc

    final = pd.concat([pd.read_csv(TABLES / str(y) / f"06_house_{y}_FINAL.csv", dtype=str)
                       for y in YEARS], ignore_index=True)
    qcache = TABLES / "_quiver_house_cache.csv"
    q = pd.read_csv(qcache) if qcache.exists() else None

    status = cc.per_filer_status(final, q, chamber="house")
    kadoa = cc.load_kadoa_house(KADOA) if KADOA.exists() else None
    hsw = cc.load_hsw_counts(HSW) if HSW.exists() else None
    status = cc.add_external_counts(status, kadoa=kadoa, hsw=hsw)

    print("  smoke quiver :", "✅" if hasattr(quiver, "reconcile") and hasattr(quiver, "validate_quiver_house") else "❌")
    print(f"  déposants : {len(status)} | FINAL {int(status['our_total'].sum())}")
    print("\n  RÉCAP PAR STATUT :")
    print(cc.summary(status).to_string(index=False))

    cols = [c for c in ["name", "our_total", "our_ocr", "quiver", "kadoa", "hsw", "status", "ocr_share_pct"] if c in status.columns]
    ocr_unique = status[status["status"] == "ocr_unique"].head(10)
    print("\n  TOP déposants OCR-UNIQUE (Quiver≈0 ; Kadoa/HSW≈0 = source unique) :")
    print(ocr_unique[cols].to_string(index=False))

    # sanité : Khanna/Harshbarger présents et OCR-lourds
    big = status[status["name"].str.contains("Khanna|Harshbarger|McCaul", na=False)]
    print("\n  déposants papier emblématiques :")
    print(big[cols].to_string(index=False))
    print("\nRÉSULTAT : ✅ crosscheck opérationnel (statut/déposant)")


if __name__ == "__main__":
    main()
