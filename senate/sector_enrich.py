#!/usr/bin/env python
"""senate.sector_enrich — adaptateur fin : DÉLÈGUE à congress_core.sector_enrich.

La logique secteur (yfinance → repli LLM → overrides manuels → GICS→ETF SPDR) est désormais UNIQUE,
dans `congress_core/sector_enrich.py`. Prouvé (Palier 2, cf. docs/RAPPORT_V2_ARCHI.md) : le cœur
reproduit les colonnes `sector_gics`/`etf_proxy`/`sector_source` du Sénat À L'OCTET, hors-ligne, depuis
le même cache (`MANUAL_OVERRIDES`, `_norm_ticker`, `GICS_TO_ETF` étaient déjà identiques entre les deux).

Ici on ne garde que le **spécifique Sénat** : le chemin de cache + la signature locale, pour que
`senate.fusion` reste inchangé (`se.enrich_sectors(big)`).
"""
from pathlib import Path

from congress_core.sector_enrich import (  # noqa: F401  — source unique partagée
    enrich_sectors as _enrich,
    resolve_sectors as _resolve,
    build_audit as _build_audit,
    GICS_TO_ETF,
    GICS_SECTORS,
    MANUAL_OVERRIDES,
)

# Cache secteur Sénat — inchangé (data/senate/sector_cache.json).
SECTOR_CACHE = Path(__file__).resolve().parent.parent / "data" / "senate" / "sector_cache.json"


def enrich_sectors(df, with_llm=True, audit_all=True):
    """Ajoute sector_gics / etf_proxy / sector_source (délègue au cœur, cache Sénat)."""
    return _enrich(df, SECTOR_CACHE, with_llm=with_llm, audit_all=audit_all)


def resolve_sectors(tickers, with_llm=True, audit_all=True):
    return _resolve(tickers, SECTOR_CACHE, with_llm=with_llm, audit_all=audit_all)


def build_audit(df):
    return _build_audit(df, SECTOR_CACHE)
