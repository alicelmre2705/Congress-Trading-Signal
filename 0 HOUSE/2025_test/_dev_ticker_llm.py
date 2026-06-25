# -*- coding: utf-8 -*-
"""DEV : valide la passe LLM nom→ticker + l'audit Quiver avant portage dans le notebook.
Écrit le cache (réutilisé ensuite par le notebook = pas de double appel API). Ne touche pas
06b/FINAL. À supprimer après portage."""
import hashlib
import json
import re
import time
from pathlib import Path

import anthropic
import pandas as pd
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
TABLE_DIR = BASE_DIR / "data_v1/tables"
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 16_000
TICKER_LLM_CACHE = BASE_DIR / "data_v1/ticker_llm_cache.json"

client = anthropic.Anthropic()

# ---- Tool + prompt (DOIVENT rester identiques à la cellule notebook pour partager le cache) ----
_TICKER_TOOL = {
    "name": "map_tickers",
    "description": "Renvoie le symbole boursier US (ticker) pour chaque nom de titre fourni.",
    "input_schema": {
        "type": "object",
        "properties": {
            "mappings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Le nom fourni, recopié à l'identique."},
                        "ticker": {"type": ["string", "null"], "description": "Ticker US en MAJUSCULES (ex. GIS, MET, AAPL). null si ce n'est pas une action/ETF cotée en bourse US."},
                        "is_equity": {"type": "boolean", "description": "true si action ordinaire ou ETF coté US."},
                    },
                    "required": ["name", "ticker", "is_equity"],
                },
            }
        },
        "required": ["mappings"],
    },
}
_TICKER_PROMPT = (
    "Tu reçois des noms de titres financiers issus de déclarations de transactions du Congrès US "
    "(formulaires PTR). Pour CHAQUE nom, donne le ticker boursier US s'il s'agit d'une action "
    "ordinaire ou d'un ETF coté aux États-Unis. Mets ticker=null si c'est une obligation, une option, "
    "un bon du Trésor, un fonds non coté, un titre privé, ou si tu n'es pas sûr. Ne devine jamais un "
    "ticker au hasard : dans le doute, null. Recopie 'name' à l'identique.\n\nNoms :\n{names}"
)
_TICKER_PROMPT_SHA = hashlib.sha256(
    (_TICKER_PROMPT + json.dumps(_TICKER_TOOL, sort_keys=True) + MODEL).encode()
).hexdigest()[:16]
_VALID_TICKER = re.compile(r"^[A-Z][A-Z.]{0,5}$")


def _load_cache():
    if TICKER_LLM_CACHE.exists():
        obj = json.loads(TICKER_LLM_CACHE.read_text(encoding="utf-8"))
        if obj.get("prompt_sha") == _TICKER_PROMPT_SHA and obj.get("model") == MODEL:
            return obj.get("mappings", {})
    return {}


def _save_cache(mappings):
    TICKER_LLM_CACHE.write_text(
        json.dumps({"model": MODEL, "prompt_sha": _TICKER_PROMPT_SHA, "mappings": mappings},
                   ensure_ascii=False, indent=1), encoding="utf-8")


def _map_batch(names, max_retries=4):
    listing = "\n".join(f"- {n}" for n in names)
    last = None
    for attempt in range(max_retries):
        try:
            resp = client.messages.create(
                model=MODEL, max_tokens=MAX_TOKENS,
                tools=[_TICKER_TOOL], tool_choice={"type": "tool", "name": "map_tickers"},
                messages=[{"role": "user", "content": _TICKER_PROMPT.format(names=listing)}],
            )
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


# ---- Normalisation pour l'audit (rapproche asset_description OCR ↔ company Quiver) ----
_SUF = re.compile(r"\b(CMN|COM|COMMON STOCK|COMMON|CLASS [A-Z]|CL [A-Z]|INCORPORATED|INC|CORPORATION|"
                  r"CORP|COMPANY|CO|HOLDINGS|HLDGS|LLC|L\.?P\.?|LTD|PLC|THE|SYS|SYSTEMS|GROUP|GRP)\b")
def _norm(s):
    s = re.sub(r"\([^)]*\)", " ", str(s).upper())
    s = re.sub(r"[^A-Z0-9 &]", " ", s)
    s = _SUF.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    o = pd.read_csv(TABLE_DIR / "06b_house_2025q1_ocr_transactions.csv", dtype=str)
    mask = o["ticker_source"].eq("none")
    names = sorted(o.loc[mask, "asset_description"].dropna().unique())
    print(f"Noms uniques sans ticker : {len(names)} (sur {int(mask.sum())} lignes none)")
    print("Échantillon :", names[:8])

    cache = _load_cache()
    todo = [n for n in names if n not in cache]
    print(f"cache : {len(names)-len(todo)} hits | API à faire : {len(todo)}")

    BATCH = 60
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        for m in _map_batch(batch):
            nm = m.get("name", "")
            tk = (m.get("ticker") or "").upper().strip(".")
            cache[nm] = tk if (m.get("is_equity") and _VALID_TICKER.match(tk)) else ""
        for n in batch:
            cache.setdefault(n, "")
        print(f"  batch {i//BATCH+1}: +{len(batch)} ({min(i+BATCH,len(todo))}/{len(todo)})")
    _save_cache(cache)

    filled = {n: t for n, t in cache.items() if t}
    print(f"\n→ {len(filled)}/{len(names)} noms résolus par le LLM ({100*len(filled)/max(len(names),1):.0f}%)")
    # nouvelle couverture simulée sur 06b
    new_tk = o.apply(lambda r: (r["ticker"] if r["ticker_source"] != "none"
                                else cache.get(r["asset_description"], "")) or "", axis=1)
    cov = (new_tk.str.strip() != "").sum()
    print(f"Couverture 06b simulée : {cov}/{len(o)} ({100*cov/len(o):.0f}%)  [avant : 540/1167 = 46%]")
    print("Exemples résolus :", dict(list(filled.items())[:10]))

    # ---- AUDIT vs Quiver (precision) ----
    q = pd.read_csv(BASE_DIR / "data_v1/external/quiver_congress_trading_2025.csv", dtype=str)
    q = q[q["chamber"].str.lower() == "house"].copy()
    q["norm"] = q["company"].map(_norm)
    # map (bioguide, norm) -> ticker majoritaire Quiver
    qmap = (q[q["ticker"].notna() & (q["ticker"].str.strip() != "")]
            .groupby(["bioguide_id", "norm"])["ticker"]
            .agg(lambda s: s.str.upper().mode().iat[0]).to_dict())
    rows = []
    for _, r in o[mask].iterrows():
        llm = cache.get(r["asset_description"], "")
        if not llm:
            continue
        key = (r.get("bioguide_id"), _norm(r["asset_description"]))
        qt = qmap.get(key)
        if qt:
            rows.append((r["asset_description"], llm, qt, llm == qt))
    if rows:
        ok = sum(1 for _, _, _, m in rows if m)
        print(f"\nAudit LLM vs Quiver : {ok}/{len(rows)} concordants ({100*ok/len(rows):.0f}%) "
              f"[sur {len(rows)} lignes LLM aussi présentes dans Quiver]")
        bad = [(a, l, qt) for a, l, qt, m in rows if not m][:8]
        if bad:
            print("Désaccords (nom | LLM | Quiver) :")
            for a, l, qt in bad:
                print(f"   {a[:45]:45} | {l:6} | {qt}")
    else:
        print("\nAudit : aucune ligne LLM rapprochable de Quiver (rare).")


if __name__ == "__main__":
    main()
