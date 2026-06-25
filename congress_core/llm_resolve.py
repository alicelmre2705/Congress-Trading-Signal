"""Résolveur LLM générique à cache versionné — factorise le motif identique derrière la passe
nom→ticker (house_ocr) et ticker→GICS (sector_enrich).

`VersionedLLMCache` : JSON {model, prompt_sha, mappings}, invalidé si (model, prompt_sha) changent.
`map_batch` : appel tool_use forcé + backoff. Dégradation gracieuse (crédit épuisé → on garde l'acquis).
Inclut les constantes House nom→ticker (port verbatim de house_ocr_multiyear).
"""
import re
import json
import time
import hashlib
from pathlib import Path


class VersionedLLMCache:
    """Cache disque versionné par (model, prompt_sha). `load()` ne renvoie les mappings que si la
    version concorde (sinon {} → on recalcule). Port de _load/_save_ticker_cache."""

    def __init__(self, path, model, prompt_sha):
        self.path = Path(path)
        self.model = model
        self.prompt_sha = prompt_sha

    def load(self) -> dict:
        if self.path.exists():
            obj = json.loads(self.path.read_text(encoding="utf-8"))
            if obj.get("prompt_sha") == self.prompt_sha and obj.get("model") == self.model:
                return obj.get("mappings", {})
        return {}

    def save(self, mappings: dict) -> None:
        self.path.write_text(json.dumps(
            {"model": self.model, "prompt_sha": self.prompt_sha, "mappings": mappings},
            ensure_ascii=False, indent=1), encoding="utf-8")


def map_batch(client, tool, prompt, model, max_tokens=16_000, max_retries=4):
    """Un appel tool_use forcé renvoyant `tool['name'].<liste>`. Backoff sur 429/5xx. Port de
    _map_tickers_batch (le prompt est déjà formaté par le caller)."""
    import anthropic
    last = None
    for attempt in range(max_retries):
        try:
            resp = client.messages.create(model=model, max_tokens=max_tokens, tools=[tool],
                                          tool_choice={"type": "tool", "name": tool["name"]},
                                          messages=[{"role": "user", "content": prompt}])
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use" and block.name == tool["name"]:
                    return block.input
            return {}
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            last = e
            if attempt < max_retries - 1:
                time.sleep(min(2 ** attempt, 20))
                continue
            raise
    raise RuntimeError(f"map_batch échec : {last}")


# ───────────────────────── Passe House nom→ticker (port verbatim) ─────────────────────────────
TICKER_TOOL = {
    "name": "map_tickers",
    "description": "Renvoie le symbole boursier US (ticker) pour chaque nom de titre fourni.",
    "input_schema": {"type": "object", "properties": {"mappings": {"type": "array", "items": {
        "type": "object", "properties": {
            "name": {"type": "string", "description": "Le nom fourni, recopié à l'identique."},
            "ticker": {"type": ["string", "null"], "description": "Ticker US en MAJUSCULES (ex. GIS, MET, AAPL). null si ce n'est pas une action/ETF cotée US."},
            "is_equity": {"type": "boolean", "description": "true si action ordinaire ou ETF coté US."},
        }, "required": ["name", "ticker", "is_equity"]}}}, "required": ["mappings"]},
}
TICKER_PROMPT = (
    "Tu reçois des noms de titres financiers issus de déclarations de transactions du Congrès US "
    "(formulaires PTR). Pour CHAQUE nom, donne le ticker boursier US s'il s'agit d'une action ordinaire "
    "ou d'un ETF coté aux États-Unis. Mets ticker=null si c'est une obligation, une option, un bon du "
    "Trésor, un fonds non coté, un titre privé, ou si tu n'es pas sûr. Ne devine jamais un ticker au "
    "hasard : dans le doute, null. Recopie 'name' à l'identique.\n\nNoms :\n{names}"
)
_VALID_TICKER = re.compile(r"^[A-Z][A-Z.]{0,5}$")


def ticker_prompt_sha(model):
    return hashlib.sha256((TICKER_PROMPT + json.dumps(TICKER_TOOL, sort_keys=True) + model).encode()).hexdigest()[:16]


def resolve_names_to_tickers(df, model, cache_path, batch_size=60):
    """Remplit le ticker des lignes `ticker_source == 'none'` via le LLM (cache versionné global).
    Dégradation gracieuse si l'API échoue. Port de house_ocr_multiyear.llm_resolve_tickers."""
    import anthropic
    if df.empty or "ticker_source" not in df.columns:
        return df
    missing = sorted(df.loc[df["ticker_source"].eq("none"), "asset_description"].dropna().unique())
    if not missing:
        return df
    cache_obj = VersionedLLMCache(cache_path, model, ticker_prompt_sha(model))
    cache = cache_obj.load()
    todo = [n for n in missing if n not in cache]
    if todo:
        cli = anthropic.Anthropic()
        try:
            for i in range(0, len(todo), batch_size):
                batch = todo[i:i + batch_size]
                listing = "\n".join(f"- {n}" for n in batch)
                out = map_batch(cli, TICKER_TOOL, TICKER_PROMPT.format(names=listing), model)
                for m in out.get("mappings", []):
                    tk = (m.get("ticker") or "").upper().strip(".")
                    cache[m.get("name", "")] = tk if (m.get("is_equity") and _VALID_TICKER.match(tk)) else ""
                for n in batch:
                    cache.setdefault(n, "")
        except Exception as e:
            print(f"  [passe LLM ticker interrompue : {type(e).__name__} — tickers dict conservés]")
        cache_obj.save(cache)
    fill = df["ticker_source"].eq("none") & df["asset_description"].map(lambda d: bool(cache.get(d, "")))
    df.loc[fill, "ticker"] = df.loc[fill, "asset_description"].map(lambda d: cache.get(d, ""))
    df.loc[fill, "ticker_source"] = "llm"
    return df
