"""Résolution ticker nom→symbole pour le Sénat — portage de la passe House (parité).

La House remonte la couverture ticker de ~46 % à ~90 % via TROIS étapes que le Sénat n'avait
jamais reçues (cf. audit de parité 2026-06-25) :
  1. ticker explicite embarqué dans la description « … (AAPL) » ;
  2. **dictionnaire nom→ticker** construit depuis les lignes DÉJÀ tickées (l'électronique imprime
     le symbole ; le papier non) → on propage aux lignes sans symbole ;
  3. **passe LLM** (Claude, tool_use forcé, filtre `is_equity`) sur le reliquat coté, cache versionné.

Aucun Quiver injecté. Le LLM met `null` pour tout ce qui n'est pas une action/ETF coté US
(obligation, muni, Treasury, fonds privé, participation non cotée) → ces lignes restent sans ticker,
flaggées `ticker_source="none"` (légitime, pas une perte). Logique reprise telle quelle de
`0 HOUSE/toutes_annees/house_ocr_multiyear.py` (fonctions `_norm_asset`, `_map_tickers_batch`,
`llm_resolve_tickers`), adaptée au Sénat : on cible « ticker vide ET description présente » (l'OCR
Sénat taggait toutes ses lignes `explicit` même sans symbole — on corrige ce label au passage).
"""
import os
import re
import json
import time
import hashlib
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent        # <repo>/senate
REPO = HERE.parent                             # racine du dépôt
CACHE_PATH = REPO / "data" / "senate" / "ticker_llm_cache.json"

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8_000

# Normalisation du nom d'actif (clé de dictionnaire) — repris de house_ocr_multiyear.py
_SUFFIX_RE = re.compile(r"\b(CMN|COM|COMMON STOCK|COMMON|CLASS [A-Z]|CL [A-Z]|INCORPORATED|INC|CORPORATION|CORP|"
                        r"COMPANY|CO|HOLDINGS|HLDGS|LLC|L\.?P\.?|LTD|PLC|THE|SYS|SYSTEMS|SER|TR|TRUST|FUND|FUNDS|ETF)\b")
_EXPLICIT_TICKER_RE = re.compile(r"[-(]\s*([A-Z][A-Z0-9.]{0,5})\)?\s*$")
_OCR_FIX = {"METILIFE": "METLIFE", "ATT": "AT T"}
_VALID_TICKER = re.compile(r"^[A-Z][A-Z.]{0,5}$")
# Les descriptions eFD/OCR du Sénat sont verbeuses : « Nom  Company: …  Description: …  Rate/Coupon… ».
# On coupe au premier double-espace + mot-clé de méta pour garder le NOM seul (clé + prompt plus nets).
_TRIM_RE = re.compile(r"\s{2,}(company:|description:|rate/coupon|matures:|comment).*$", re.I | re.S)


def _clean_name(s):
    return _TRIM_RE.sub("", str(s)).strip()


def _norm_asset(s):
    s = _clean_name(s).upper()
    s = _EXPLICIT_TICKER_RE.sub("", s)
    s = re.sub(r"[^A-Z0-9 &]", " ", s)
    s = _SUFFIX_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    for bad, good in _OCR_FIX.items():
        s = re.sub(rf"\b{bad}\b", good, s)
    return s


def _explicit_ticker(desc):
    m = _EXPLICIT_TICKER_RE.search(_clean_name(desc))
    if not m:
        return None
    t = m.group(1).strip(".")
    return t if 1 <= len(t) <= 5 else None


# --------------------------------------------------------------------- passe LLM
_TICKER_TOOL = {
    "name": "map_tickers",
    "description": "Renvoie le symbole boursier US (ticker) pour chaque nom de titre fourni.",
    "input_schema": {"type": "object", "properties": {"mappings": {"type": "array", "items": {
        "type": "object", "properties": {
            "name": {"type": "string", "description": "Le nom fourni, recopié à l'identique."},
            "ticker": {"type": ["string", "null"], "description": "Ticker US en MAJUSCULES (ex. GIS, MET, AAPL). null si ce n'est pas une action/ETF cotée US."},
            "is_equity": {"type": "boolean", "description": "true si action ordinaire ou ETF coté US."},
        }, "required": ["name", "ticker", "is_equity"]}}}, "required": ["mappings"]},
}
_TICKER_PROMPT = (
    "Tu reçois des noms de titres financiers issus de déclarations de transactions du Congrès US "
    "(formulaires PTR du Sénat). Pour CHAQUE nom, donne le ticker boursier US s'il s'agit d'une action "
    "ordinaire ou d'un ETF coté aux États-Unis. Mets ticker=null si c'est une obligation, une option, un "
    "bon du Trésor, une obligation municipale, un fonds non coté, un titre privé, ou si tu n'es pas sûr. "
    "Ne devine jamais un ticker au hasard : dans le doute, null. Recopie 'name' à l'identique.\n\nNoms :\n{names}"
)
_PROMPT_SHA = hashlib.sha256((_TICKER_PROMPT + json.dumps(_TICKER_TOOL, sort_keys=True) + MODEL).encode()).hexdigest()[:16]


def _api_key():
    try:
        from dotenv import load_dotenv
        load_dotenv(REPO / ".env")
        if not os.getenv("ANTHROPIC_API_KEY"):
            load_dotenv()
    except Exception:
        pass
    return os.getenv("ANTHROPIC_API_KEY", "")


def _load_cache(path):
    if path.exists():
        obj = json.loads(path.read_text(encoding="utf-8"))
        if obj.get("prompt_sha") == _PROMPT_SHA and obj.get("model") == MODEL:
            return obj.get("mappings", {})
    return {}


def _save_cache(path, mappings):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"model": MODEL, "prompt_sha": _PROMPT_SHA, "mappings": mappings},
                               ensure_ascii=False, indent=1), encoding="utf-8")


def _map_tickers_batch(cli, names, max_retries=4):
    import anthropic
    listing = "\n".join(f"- {n}" for n in names)
    last = None
    for attempt in range(max_retries):
        try:
            resp = cli.messages.create(model=MODEL, max_tokens=MAX_TOKENS, tools=[_TICKER_TOOL],
                                       tool_choice={"type": "tool", "name": "map_tickers"},
                                       messages=[{"role": "user", "content": _TICKER_PROMPT.format(names=listing)}])
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use" and block.name == "map_tickers":
                    return block.input.get("mappings", [])
            return []
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            last = e
            if attempt < max_retries - 1:
                time.sleep(min(2 ** attempt, 20)); continue
            raise
    raise RuntimeError(f"map_tickers échec : {last}")


def llm_resolve_tickers(df, cache_path=CACHE_PATH, verbose=True):
    """Remplit le ticker des lignes sans symbole via la passe LLM (cache global versionné).
    Cible « ticker vide ET asset_description présent ». Met `ticker_source="llm"` sur les résolus."""
    if df.empty or "ticker" not in df.columns:
        return df
    miss = df["ticker"].isna() & df["asset_description"].notna()
    names = sorted({_clean_name(d) for d in df.loc[miss, "asset_description"].dropna() if _clean_name(d)})
    if not names:
        return df
    cache = _load_cache(cache_path)
    todo = [n for n in names if n not in cache]
    if todo:
        import anthropic
        cli = anthropic.Anthropic(api_key=_api_key())
        try:
            for i in range(0, len(todo), 60):
                batch = todo[i:i + 60]
                for m in _map_tickers_batch(cli, batch):
                    tk = (m.get("ticker") or "").upper().strip(".")
                    cache[m.get("name", "")] = tk if (m.get("is_equity") and _VALID_TICKER.match(tk)) else ""
                for n in batch:
                    cache.setdefault(n, "")
                if verbose:
                    print(f"    passe LLM ticker : {min(i + 60, len(todo))}/{len(todo)} noms…")
        except Exception as e:                       # crédit API épuisé / réseau : on garde l'acquis
            print(f"    [passe LLM interrompue : {type(e).__name__} — acquis conservé]")
        _save_cache(cache_path, cache)
    key = df["asset_description"].map(lambda d: cache.get(_clean_name(d), "") if pd.notna(d) else "")
    fill = miss & key.astype(bool)
    df.loc[fill, "ticker"] = key[fill].str.upper()
    df.loc[fill, "ticker_source"] = "llm"
    return df


# --------------------------------------------------------------------- orchestration
def resolve_tickers(df, cache_path=CACHE_PATH, verbose=True):
    """Pipeline complet : normalise la vacuité du ticker, corrige le label OCR, puis applique
    explicite → dictionnaire → LLM. Idempotent (re-run = 0 appel si cache à jour). Ne touche
    qu'à `ticker` / `ticker_source` ; n'ajoute ni ne supprime aucune ligne."""
    df = df.copy()
    s = df["ticker"].astype("string").str.strip()
    empty = s.isna() | s.str.upper().isin(["", "NAN", "NONE", "--", "<NA>"])
    df["ticker"] = s.mask(empty).str.upper()
    if "ticker_source" not in df.columns:
        df["ticker_source"] = pd.NA
    # corrige le label hérité : toute ligne sans ticker = 'none' (l'OCR Sénat taggait 'explicit')
    df.loc[df["ticker"].isna(), "ticker_source"] = "none"
    has_src = df["ticker_source"].astype("string")
    df.loc[df["ticker"].notna() & (has_src.isna() | has_src.isin(["", "none"])), "ticker_source"] = "explicit"

    desc = df["asset_description"].astype("string")
    n0 = int(df["ticker"].notna().sum())

    # NB : pas d'extraction de ticker « (XXX) » en fin de description (étape House) — au Sénat les
    # parenthèses finales sont des codes d'État (« (DE) », « (NY) ») et non des tickers ; le symbole
    # explicite est déjà capté en amont (colonne Ticker eFD + recover_ticker). On garde dict + LLM.

    # 1) dictionnaire nom→ticker depuis les lignes DÉJÀ tickées
    have = df[df["ticker"].notna() & desc.notna()].copy()
    have["norm"] = have["asset_description"].map(_norm_asset)
    name_to_ticker = (have[have["norm"] != ""].groupby("norm")["ticker"]
                      .agg(lambda x: x.astype(str).str.upper().mode().iat[0]).to_dict())

    miss = df["ticker"].isna() & desc.notna()
    dic = df.loc[miss, "asset_description"].map(lambda d: name_to_ticker.get(_norm_asset(d)))
    idx = dic[dic.notna()].index
    df.loc[idx, "ticker"] = dic[dic.notna()].astype(str).str.upper()
    df.loc[idx, "ticker_source"] = "elec_dict"
    n_dic = len(idx)

    # 2) passe LLM sur le reliquat coté
    before_llm = int(df["ticker"].notna().sum())
    df = llm_resolve_tickers(df, cache_path=cache_path, verbose=verbose)
    n_llm = int(df["ticker"].notna().sum()) - before_llm

    if verbose:
        n1 = int(df["ticker"].notna().sum())
        print(f"  résolution ticker : {n0} → {n1} (+{n1 - n0}) "
              f"| dict +{n_dic} · llm +{n_llm} sur {len(df)} lignes")
    return df
