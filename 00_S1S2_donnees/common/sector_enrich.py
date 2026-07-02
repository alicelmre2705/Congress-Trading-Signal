"""Enrichissement secteur : ticker → GICS → ETF SPDR Select Sector. Copie canonique (2 copies → 1).

Identique à `0 HOUSE/2025_test/sector_enrich.py` aux chemins près : le `cache_path` est PARAMÉTRÉ
(plus de BASE_DIR/data_v1 codé en dur), pour que House (toutes_annees) et Sénat l'importent.
Hybride yfinance (factuel) + repli/audit LLM + overrides manuels (audit adversarial). Purement additif.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

import pandas as pd

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8_000

GICS_TO_ETF = {
    "Energy": "XLE", "Materials": "XLB", "Industrials": "XLI",
    "Consumer Discretionary": "XLY", "Consumer Staples": "XLP", "Health Care": "XLV",
    "Financials": "XLF", "Information Technology": "XLK", "Communication Services": "XLC",
    "Utilities": "XLU", "Real Estate": "XLRE",
}
GICS_SECTORS = tuple(GICS_TO_ETF.keys())

YF_SECTOR_TO_GICS = {
    "Technology": "Information Technology", "Financial Services": "Financials",
    "Healthcare": "Health Care", "Consumer Cyclical": "Consumer Discretionary",
    "Consumer Defensive": "Consumer Staples", "Energy": "Energy", "Industrials": "Industrials",
    "Basic Materials": "Materials", "Real Estate": "Real Estate", "Utilities": "Utilities",
    "Communication Services": "Communication Services",
}

_VALID_TICKER = re.compile(r"^[A-Z][A-Z.\-]{0,6}$")

MANUAL_OVERRIDES = {
    "FNA": "Health Care", "SMCYY": "Communication Services", "LRN": "Consumer Discretionary",
    "SHLD": "Industrials", "HURA": "Materials", "URNM": "Materials",
    "SLYG": None, "TNA": None, "SPY": None, "QQQ": None, "IVW": None, "PDBC": None, "BITB": None,
}

_SECTOR_TOOL = {
    "name": "map_sectors",
    "description": "Renvoie le secteur GICS de chaque ticker boursier US fourni.",
    "input_schema": {"type": "object", "properties": {"mappings": {"type": "array", "items": {
        "type": "object", "properties": {
            "ticker": {"type": "string", "description": "Le ticker fourni, recopié à l'identique."},
            "sector_gics": {"type": ["string", "null"], "enum": [*GICS_SECTORS, None],
                            "description": "Secteur GICS de l'émetteur. null si ce n'est pas une action/ETF cotée US ou en cas de doute."},
            "is_listed": {"type": "boolean", "description": "true si action ordinaire ou ETF coté US (y compris delisté/racheté)."},
        }, "required": ["ticker", "sector_gics", "is_listed"]}}}, "required": ["mappings"]},
}
_SECTOR_PROMPT = (
    "Tu reçois des tickers boursiers US issus de déclarations de transactions du Congrès US. "
    "Pour CHAQUE ticker, donne le secteur GICS de l'émetteur, choisi STRICTEMENT parmi : "
    + ", ".join(GICS_SECTORS) + ". "
    "Mets sector_gics=null si le ticker ne correspond pas à une action/ETF cotée US (obligation, "
    "bon du Trésor, fonds non coté, titre privé) ou si tu n'es pas sûr. Ne devine jamais au hasard. "
    "Pour un ETF, donne le secteur dominant de l'ETF. Recopie 'ticker' à l'identique.\n\nTickers :\n{tickers}"
)
_PIPELINE_SHA = hashlib.sha256(
    (_SECTOR_PROMPT + json.dumps(_SECTOR_TOOL, sort_keys=True) + MODEL
     + json.dumps(YF_SECTOR_TO_GICS, sort_keys=True) + json.dumps(GICS_TO_ETF, sort_keys=True)
     ).encode()).hexdigest()[:16]


def load_cache(cache_path) -> dict:
    cache_path = Path(cache_path)
    if cache_path.exists():
        try:
            obj = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if obj.get("pipeline_sha") == _PIPELINE_SHA and obj.get("model") == MODEL:
            return obj.get("mappings", {})
    return {}


def save_cache(cache_path, mappings: dict) -> None:
    Path(cache_path).write_text(json.dumps(
        {"model": MODEL, "pipeline_sha": _PIPELINE_SHA, "mappings": mappings},
        ensure_ascii=False, indent=1), encoding="utf-8")


def _yf_sector_one(t: str):
    import yfinance as yf
    try:
        raw = (yf.Ticker(t).info or {}).get("sector")
        return YF_SECTOR_TO_GICS.get(raw) if raw else None
    except Exception:
        return None


def resolve_yfinance(tickers, pause=0.3, retry_pause=1.2, max_passes=3) -> dict:
    out = {t: None for t in tickers}
    pending = list(tickers)
    for p in range(max_passes):
        if not pending:
            break
        delay = pause if p == 0 else retry_pause
        nxt = []
        for t in pending:
            g = _yf_sector_one(t)
            out[t] = g
            if g is None:
                nxt.append(t)
            if delay:
                time.sleep(delay)
        pending = nxt
    return out


def _map_sectors_batch(cli, tickers, max_retries=4):
    import anthropic
    listing = "\n".join(f"- {t}" for t in tickers)
    last = None
    for attempt in range(max_retries):
        try:
            resp = cli.messages.create(model=MODEL, max_tokens=MAX_TOKENS, tools=[_SECTOR_TOOL],
                                       tool_choice={"type": "tool", "name": "map_sectors"},
                                       messages=[{"role": "user", "content": _SECTOR_PROMPT.format(tickers=listing)}])
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use" and block.name == "map_sectors":
                    return block.input.get("mappings", [])
            return []
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            last = e
            if attempt < max_retries - 1:
                time.sleep(min(2 ** attempt, 20))
                continue
            raise
    raise RuntimeError(f"map_sectors échec : {last}")


def resolve_llm(tickers, batch=40) -> dict:
    import anthropic
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("  [LLM] ANTHROPIC_API_KEY absente — repli LLM désactivé")
        return {}
    cli = anthropic.Anthropic()
    out = {}
    for i in range(0, len(tickers), batch):
        chunk = tickers[i:i + batch]
        for m in _map_sectors_batch(cli, chunk):
            tk = (m.get("ticker") or "").upper().strip()
            sec = m.get("sector_gics")
            out[tk] = sec if (m.get("is_listed") and sec in GICS_TO_ETF) else None
        for t in chunk:
            out.setdefault(t, None)
    return out


def _norm_ticker(t) -> str:
    return str(t).strip().upper()


def resolve_sectors(tickers, cache_path, with_llm=True, audit_all=True) -> dict:
    tickers = sorted({_norm_ticker(t) for t in tickers if _norm_ticker(t) and _VALID_TICKER.match(_norm_ticker(t))})
    cache = load_cache(cache_path)
    todo = [t for t in tickers if t not in cache]
    if todo:
        yf_res = resolve_yfinance(todo)
        llm_targets = todo if audit_all else [t for t in todo if yf_res.get(t) is None]
        llm_res = resolve_llm(llm_targets) if (with_llm and llm_targets) else {}
        for t in todo:
            yf_g, llm_g = yf_res.get(t), llm_res.get(t)
            final = yf_g if yf_g else llm_g
            source = "yfinance" if yf_g else ("llm" if llm_g else "none")
            cache[t] = {"yf": yf_g, "llm": llm_g, "sector_gics": final, "source": source}
        save_cache(cache_path, cache)
    return cache


def enrich_sectors(df, cache_path, with_llm=True, audit_all=True):
    """Ajoute sector_gics, etf_proxy, sector_source (jointure sur ticker). Purement additif."""
    df = df.copy()
    tickers = df["ticker"].dropna().map(_norm_ticker)
    tickers = [t for t in tickers.unique() if t and t not in ("NAN", "NONE", "")]
    cache = resolve_sectors(tickers, cache_path, with_llm=with_llm, audit_all=audit_all)

    def _gics(t):
        return None if pd.isna(t) else (cache.get(_norm_ticker(t)) or {}).get("sector_gics")

    def _src(t):
        if pd.isna(t) or _norm_ticker(t) in ("", "NAN", "NONE"):
            return "none"
        return (cache.get(_norm_ticker(t)) or {}).get("source", "none")

    df["sector_gics"] = df["ticker"].map(_gics)
    df["etf_proxy"] = df["sector_gics"].map(lambda s: GICS_TO_ETF.get(s) if s else None)
    df["sector_source"] = df["ticker"].map(_src)
    for tk, sec in MANUAL_OVERRIDES.items():
        m = df["ticker"].map(lambda x: _norm_ticker(x) == tk if pd.notna(x) else False)
        if m.any():
            df.loc[m, "sector_gics"] = sec
            df.loc[m, "etf_proxy"] = GICS_TO_ETF.get(sec) if sec else None
            df.loc[m, "sector_source"] = "manual"
    return df


def build_audit(df, cache_path):
    cache = load_cache(cache_path)
    rows = []
    for t in sorted({_norm_ticker(x) for x in df["ticker"].dropna()}):
        rec = cache.get(t)
        if not rec:
            continue
        yf_g, llm_g = rec.get("yf"), rec.get("llm")
        agree = (yf_g == llm_g) if (yf_g and llm_g) else None
        rows.append({"ticker": t, "sector_gics": rec.get("sector_gics"),
                     "etf_proxy": GICS_TO_ETF.get(rec.get("sector_gics")) if rec.get("sector_gics") else None,
                     "source": rec.get("source"), "yf": yf_g, "llm": llm_g, "yf_llm_agree": agree})
    return pd.DataFrame(rows)
