#!/usr/bin/env python
"""Phase finale A — applique l'enrichissement secteur (GICS→ETF) aux 7 FINAL House (parité 12/12).

Calque de `_rededup_house_ocr.py` : agit sur les tables FIGÉES (pas de re-run du pipeline). Pour chaque
année : charge `06_house_{an}_FINAL`, ajoute `sector_gics`/`etf_proxy`/`sector_source` via
`congress_core.sector_enrich.enrich_sectors` (cache versionné + yfinance + repli LLM pour les délistés),
réindexe sur `HOUSE_FINAL_SCHEMA` (27 col), réécrit.

Résolution des tickers en CHUNKS (sauvegarde incrémentale du cache → reprise gratuite si interrompu).
`audit_all=False` : yfinance pour tous, LLM uniquement pour ce que yfinance ne trouve pas (coût minimal).
Le cache est pré-amorcé par l'union des caches archivés (House Q1 + wip + Sénat, 1508 tickers, même
pipeline_sha) → seuls les ~1825 tickers restants sont requêtés.
"""
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
try:
    from dotenv import load_dotenv
    load_dotenv(REPO / ".env")
except Exception:
    pass

import congress_core.sector_enrich as se   # noqa: E402
from congress_core.schema import HOUSE_FINAL_SCHEMA  # noqa: E402

T = REPO / "data" / "house" / "tables"
CACHE = REPO / "data" / "house" / "sector_cache.json"
YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
CHUNK = 150


def resolve_all():
    """Résout tous les tickers House uniques, par chunks (cache sauvegardé après chaque chunk)."""
    frames = [pd.read_csv(T / str(y) / f"06_house_{y}_FINAL.csv", dtype=str, usecols=["ticker"])
              for y in YEARS]
    tk = pd.concat(frames, ignore_index=True)["ticker"].dropna()
    tickers = sorted({se._norm_ticker(t) for t in tk
                      if se._norm_ticker(t) and se._VALID_TICKER.match(se._norm_ticker(t))})
    cache = se.load_cache(CACHE)
    todo = [t for t in tickers if t not in cache]
    print(f"tickers House uniques: {len(tickers)} | déjà en cache: {len(tickers)-len(todo)} | à résoudre: {len(todo)}")
    for i in range(0, len(todo), CHUNK):
        chunk = todo[i:i + CHUNK]
        se.resolve_sectors(chunk, CACHE, with_llm=True, audit_all=False)  # sauvegarde le cache
        done = min(i + CHUNK, len(todo))
        print(f"  résolu {done}/{len(todo)} (chunk {i//CHUNK + 1})", flush=True)
    print("résolution terminée.")


def apply_years():
    """Applique le secteur à chaque FINAL (cache complet → aucune requête) + réindexe le schéma."""
    tot = filled = 0
    for y in YEARS:
        fp = T / str(y) / f"06_house_{y}_FINAL.csv"
        df = pd.read_csv(fp, dtype=str, keep_default_na=False)
        n = len(df)
        out = se.enrich_sectors(df, CACHE, with_llm=True, audit_all=False)
        out = out.reindex(columns=HOUSE_FINAL_SCHEMA)
        out.to_csv(fp, index=False)
        f = (out["sector_gics"].notna() & (out["sector_gics"].astype(str).str.strip() != "")).sum()
        tot += n
        filled += f
        print(f"  {y}: {n} lignes, secteur rempli {f} ({100*f/n:.1f}%)")
    print(f"\nFINAL House: {filled}/{tot} lignes avec secteur = {100*filled/tot:.1f}% | schéma {len(HOUSE_FINAL_SCHEMA)} col.")


if __name__ == "__main__":
    if "--apply-only" not in sys.argv:
        resolve_all()
    apply_years()
    print("RÉSULTAT : ✅ secteur House appliqué (12/12).")
