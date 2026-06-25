"""Enrichissement secteur : ticker -> secteur GICS -> ETF SPDR Select Sector.

Deux champs obligatoires de la table finale manquaient (`sector_gics`, `etf_proxy`).
Ce module les ajoute par jointure sur `ticker`, SANS toucher au reste du pipeline.

Source hybride (cohérent avec la culture anti-hallucination du projet) :
  1. yfinance  -> secteur factuel (source primaire), `sector_source = "yfinance"`
  2. repli LLM -> Claude (tool_use forcé) pour les tickers que yfinance ne trouve pas
                 (delistés type XLNX/CTL, préférentielles, ADR), `sector_source = "llm"`
  3. sinon     -> sector_gics = None, `sector_source = "none"` (non coté : muni, obligation,
                 fonds privé) — flaggé, pas jeté.

L'univers ETF cible est SPDR Select Sector (standard de recherche ; l'univers Ramify
sera tranché en toute fin de projet). Mapping 1:1 avec les 11 secteurs GICS.

Cache disque versionné `data_v1/sector_cache.json`, calqué sur `ticker_llm_cache.json`
(clé = model + pipeline_sha). Un re-run sans changement ne rappelle ni Yahoo ni l'API.

Utilisable :
  - importé par le notebook  : `import sector_enrich as se; df = se.enrich_sectors(df)`
  - en standalone (CLI)       : `python sector_enrich.py`  (construit le cache + enrichit
                                 06_house_2025q1_transactions_FINAL.csv + écrit 06f audit)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# --- Ancrage robuste : le module vit dans 0 HOUSE/2025_test/ ---
BASE_DIR = Path(__file__).resolve().parent
TABLE_DIR = BASE_DIR / "data_v1/tables"
SECTOR_CACHE = BASE_DIR / "data_v1/sector_cache.json"

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8_000

# ======================================================================
# Tables de correspondance statiques
# ======================================================================
# 11 secteurs GICS canoniques -> ETF SPDR Select Sector (univers de recherche)
GICS_TO_ETF = {
    "Energy": "XLE",
    "Materials": "XLB",
    "Industrials": "XLI",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Health Care": "XLV",
    "Financials": "XLF",
    "Information Technology": "XLK",
    "Communication Services": "XLC",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
}
GICS_SECTORS = tuple(GICS_TO_ETF.keys())

# Libellés yfinance (taxonomie Yahoo) -> secteur GICS canonique
YF_SECTOR_TO_GICS = {
    "Technology": "Information Technology",
    "Financial Services": "Financials",
    "Healthcare": "Health Care",
    "Consumer Cyclical": "Consumer Discretionary",
    "Consumer Defensive": "Consumer Staples",
    "Energy": "Energy",
    "Industrials": "Industrials",
    "Basic Materials": "Materials",
    "Real Estate": "Real Estate",
    "Utilities": "Utilities",
    "Communication Services": "Communication Services",
}

_VALID_TICKER = re.compile(r"^[A-Z][A-Z.\-]{0,6}$")

# Override manuel issu de l'audit adversarial (workflow audit-sector-mapping, 2026-06-25) :
# 6 tickers de la queue mono-source (repli LLM / ETF) corrigés ou flaggés. Les ETF de marché
# DIVERSIFIÉS -> None (pas de secteur GICS unique, intentionnel) ; les ETF thématiques gardent
# leur secteur dominant. sector_source devient "manual" pour la traçabilité.
MANUAL_OVERRIDES = {
    "FNA": "Health Care",               # action mal classée (était Financials)
    "SMCYY": "Communication Services",  # ADR mal classé (était Information Technology)
    "SHLD": "Industrials",              # ETF défense (ticker réattribué, ex-Sears) — secteur dominant
    "HURA": "Materials",                # ETF uranium (était Health Care)
    "SLYG": None,                       # ETF small-cap growth diversifié -> non classé
    "TNA": None,                        # ETF levier small-cap diversifié -> non classé
}

# ======================================================================
# Repli LLM (tool_use forcé) — calqué sur la passe nom->ticker (cell 22)
# ======================================================================
_SECTOR_TOOL = {
    "name": "map_sectors",
    "description": "Renvoie le secteur GICS de chaque ticker boursier US fourni.",
    "input_schema": {
        "type": "object",
        "properties": {
            "mappings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Le ticker fourni, recopié à l'identique."},
                        "sector_gics": {
                            "type": ["string", "null"],
                            "enum": [*GICS_SECTORS, None],
                            "description": "Secteur GICS de l'émetteur. null si ce n'est pas une action/ETF cotée US ou en cas de doute.",
                        },
                        "is_listed": {"type": "boolean", "description": "true si action ordinaire ou ETF coté US (y compris delisté/racheté)."},
                    },
                    "required": ["ticker", "sector_gics", "is_listed"],
                },
            }
        },
        "required": ["mappings"],
    },
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
     ).encode()
).hexdigest()[:16]


# ======================================================================
# Cache disque versionné
# ======================================================================
def load_cache() -> dict:
    """Retourne le dict {TICKER: {yf, llm, sector_gics, source}} si model+pipeline_sha concordent."""
    if SECTOR_CACHE.exists():
        try:
            obj = json.loads(SECTOR_CACHE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if obj.get("pipeline_sha") == _PIPELINE_SHA and obj.get("model") == MODEL:
            return obj.get("mappings", {})
    return {}


def save_cache(mappings: dict) -> None:
    SECTOR_CACHE.write_text(
        json.dumps({"model": MODEL, "pipeline_sha": _PIPELINE_SHA, "mappings": mappings},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )


# ======================================================================
# Résolution yfinance (source primaire, factuelle)
# ======================================================================
def _yf_sector_one(t: str):
    """Un appel yfinance -> secteur GICS canonique (None si introuvable/erreur)."""
    import yfinance as yf

    try:
        raw = (yf.Ticker(t).info or {}).get("sector")
        return YF_SECTOR_TO_GICS.get(raw) if raw else None
    except Exception:
        return None


def resolve_yfinance(tickers: list[str], pause: float = 0.3, retry_pause: float = 1.2,
                     max_passes: int = 3) -> dict:
    """ticker -> secteur GICS via yfinance, ROBUSTE au throttle de Yahoo.

    Yahoo renvoie souvent un 404 « Quote not found » sur des tickers pourtant cotés quand on
    enchaîne trop d'appels (throttle). On fait donc plusieurs passes : les None d'une passe (en
    grande partie du throttle) sont réessayés à la passe suivante avec un délai plus long. Les
    tickers vraiment non cotés / delistés restent None -> repli LLM. Tout est factuel (aucune
    invention).
    """
    out = {t: None for t in tickers}
    pending = list(tickers)
    for p in range(max_passes):
        if not pending:
            break
        delay = pause if p == 0 else retry_pause
        nxt = []
        for i, t in enumerate(pending, 1):
            g = _yf_sector_one(t)
            out[t] = g
            if g is None:
                nxt.append(t)
            if delay:
                time.sleep(delay)
            if i % 50 == 0:
                print(f"    yfinance passe {p + 1} : {i}/{len(pending)} "
                      f"({sum(v is not None for v in out.values())}/{len(tickers)} résolus)")
        print(f"  passe {p + 1} : {sum(v is not None for v in out.values())}/{len(tickers)} résolus, "
              f"{len(nxt)} à réessayer")
        pending = nxt
    return out


# ======================================================================
# Résolution LLM (repli + audit croisé)
# ======================================================================
def _map_sectors_batch(cli, tickers: list[str], max_retries: int = 4) -> list[dict]:
    import anthropic

    listing = "\n".join(f"- {t}" for t in tickers)
    last = None
    for attempt in range(max_retries):
        try:
            resp = cli.messages.create(
                model=MODEL, max_tokens=MAX_TOKENS,
                tools=[_SECTOR_TOOL], tool_choice={"type": "tool", "name": "map_sectors"},
                messages=[{"role": "user", "content": _SECTOR_PROMPT.format(tickers=listing)}],
            )
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


def resolve_llm(tickers: list[str], batch: int = 40) -> dict:
    """ticker -> secteur GICS via Claude (tool_use forcé). Retourne {} si pas de clé API."""
    import anthropic

    load_dotenv(BASE_DIR / ".env")
    if not os.getenv("ANTHROPIC_API_KEY"):
        load_dotenv()
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        print("  [LLM] ANTHROPIC_API_KEY absente — repli LLM désactivé")
        return {}
    cli = anthropic.Anthropic(api_key=key)
    out = {}
    for i in range(0, len(tickers), batch):
        chunk = tickers[i:i + batch]
        for m in _map_sectors_batch(cli, chunk):
            tk = (m.get("ticker") or "").upper().strip()
            sec = m.get("sector_gics")
            out[tk] = sec if (m.get("is_listed") and sec in GICS_TO_ETF) else None
        for t in chunk:
            out.setdefault(t, None)
        print(f"    LLM secteur {min(i + batch, len(tickers))}/{len(tickers)}")
    return out


# ======================================================================
# Orchestration : construit/complète le cache de référence
# ======================================================================
def _norm_ticker(t) -> str:
    return str(t).strip().upper()


def resolve_sectors(tickers, with_llm: bool = True, audit_all: bool = True) -> dict:
    """Construit le référentiel {TICKER: {yf, llm, sector_gics, source}} (cache versionné).

    - yfinance sur tous les tickers absents du cache (source primaire).
    - LLM : si audit_all, sur TOUS les tickers cotés (permet l'audit croisé) ; sinon
      uniquement sur le résidu yfinance-None (mode repli strict).
    - sector_gics = yf si dispo, sinon llm ; source tracée.
    """
    tickers = sorted({_norm_ticker(t) for t in tickers if _norm_ticker(t) and _VALID_TICKER.match(_norm_ticker(t))})
    cache = load_cache()
    todo = [t for t in tickers if t not in cache]
    print(f"Tickers distincts valides : {len(tickers)} | cache : {len(tickers) - len(todo)} hits | à résoudre : {len(todo)}")

    if todo:
        print("  → yfinance (source primaire)…")
        yf_res = resolve_yfinance(todo)

        # Cibles LLM : tout (audit croisé) ou seulement les trous yfinance
        llm_targets = todo if audit_all else [t for t in todo if yf_res.get(t) is None]
        llm_res = {}
        if with_llm and llm_targets:
            print(f"  → LLM ({'audit complet' if audit_all else 'repli'}) sur {len(llm_targets)} tickers…")
            llm_res = resolve_llm(llm_targets)

        for t in todo:
            yf_g = yf_res.get(t)
            llm_g = llm_res.get(t)
            final = yf_g if yf_g else llm_g
            source = "yfinance" if yf_g else ("llm" if llm_g else "none")
            cache[t] = {"yf": yf_g, "llm": llm_g, "sector_gics": final, "source": source}
        save_cache(cache)
        print(f"  cache sauvegardé : {SECTOR_CACHE.relative_to(BASE_DIR)} ({len(cache)} tickers)")

    return cache


# ======================================================================
# Application au DataFrame (le point d'insertion appelé par le notebook)
# ======================================================================
def enrich_sectors(df: pd.DataFrame, with_llm: bool = True, audit_all: bool = True) -> pd.DataFrame:
    """Ajoute sector_gics, etf_proxy, sector_source à df (jointure sur `ticker`).

    N'altère aucune colonne existante. Les lignes sans ticker (non cotées) -> None + 'none'.
    """
    df = df.copy()
    tickers = df["ticker"].dropna().map(_norm_ticker)
    tickers = [t for t in tickers.unique() if t and t not in ("NAN", "NONE", "")]
    cache = resolve_sectors(tickers, with_llm=with_llm, audit_all=audit_all)

    def _gics(t):
        if pd.isna(t):
            return None
        return (cache.get(_norm_ticker(t)) or {}).get("sector_gics")

    def _src(t):
        if pd.isna(t) or _norm_ticker(t) in ("", "NAN", "NONE"):
            return "none"
        return (cache.get(_norm_ticker(t)) or {}).get("source", "none")

    df["sector_gics"] = df["ticker"].map(_gics)
    df["etf_proxy"] = df["sector_gics"].map(lambda s: GICS_TO_ETF.get(s) if s else None)
    df["sector_source"] = df["ticker"].map(_src)

    # Couche d'override manuel (audit adversarial) : corrige/flagge la queue mono-source.
    for tk, sec in MANUAL_OVERRIDES.items():
        m = df["ticker"].map(lambda x: _norm_ticker(x) == tk if pd.notna(x) else False)
        if m.any():
            df.loc[m, "sector_gics"] = sec
            df.loc[m, "etf_proxy"] = GICS_TO_ETF.get(sec) if sec else None
            df.loc[m, "sector_source"] = "manual"
    return df


# ======================================================================
# Audit croisé yfinance ↔ LLM + couverture (table 06f)
# ======================================================================
def build_audit(df: pd.DataFrame) -> pd.DataFrame:
    """Construit la table d'audit secteur (une ligne par ticker distinct résolu)."""
    cache = load_cache()
    rows = []
    for t in sorted({_norm_ticker(x) for x in df["ticker"].dropna()}):
        rec = cache.get(t)
        if not rec:
            continue
        yf_g, llm_g = rec.get("yf"), rec.get("llm")
        agree = None
        if yf_g and llm_g:
            agree = (yf_g == llm_g)
        rows.append({
            "ticker": t, "sector_gics": rec.get("sector_gics"),
            "etf_proxy": GICS_TO_ETF.get(rec.get("sector_gics")) if rec.get("sector_gics") else None,
            "source": rec.get("source"), "yf": yf_g, "llm": llm_g, "yf_llm_agree": agree,
        })
    return pd.DataFrame(rows)


def summary(df_audit: pd.DataFrame) -> None:
    n = len(df_audit)
    by_src = df_audit["source"].value_counts().to_dict()
    inter = df_audit[df_audit["yf_llm_agree"].notna()].copy()
    inter["yf_llm_agree"] = inter["yf_llm_agree"].astype(bool)
    agree = inter["yf_llm_agree"].mean() if len(inter) else float("nan")
    print(f"\n=== Audit secteur ({n} tickers distincts) ===")
    print(f"  sources : {by_src}")
    print(f"  audit croisé yfinance↔LLM : {len(inter)} tickers comparables, accord = {agree:.1%}")
    if len(inter):
        dis = inter[~inter["yf_llm_agree"]]
        if len(dis):
            print(f"  désaccords ({len(dis)}) — extrait :")
            print(dis[["ticker", "yf", "llm"]].head(15).to_string(index=False))
    print("\n  distribution sectorielle :")
    print(df_audit["sector_gics"].value_counts(dropna=False).to_string())


# ======================================================================
# CLI standalone : construit le cache + enrichit le CSV final + écrit 06f
# ======================================================================
def main() -> None:
    final_csv = TABLE_DIR / "06_house_2025q1_transactions_FINAL.csv"
    df = pd.read_csv(final_csv, dtype={"doc_id": str})
    print(f"Chargé {final_csv.name} : {len(df)} lignes, {df['ticker'].notna().sum()} avec ticker")

    df = enrich_sectors(df)

    df.to_csv(final_csv, index=False)
    print(f"\n→ {final_csv.name} ré-écrit avec sector_gics + etf_proxy + sector_source ({len(df.columns)} colonnes)")

    audit = build_audit(df)
    audit_path = TABLE_DIR / "06f_sector_audit.csv"
    audit.to_csv(audit_path, index=False)
    print(f"→ {audit_path.name} : {len(audit)} tickers")
    summary(audit)

    cov = df["sector_gics"].notna().mean()
    print(f"\nCouverture sector_gics (lignes) : {df['sector_gics'].notna().sum()}/{len(df)} = {cov:.1%}")


if __name__ == "__main__":
    main()
