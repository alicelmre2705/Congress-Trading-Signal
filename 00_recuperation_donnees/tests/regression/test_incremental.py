#!/usr/bin/env python
"""PREUVE de mise à jour incrémentale (exigence Ramify S2) : « 2ᵉ run = 0 appel Vision ».

Le pipeline OCR est resumable via un cache versionné par (prompt_sha, model). On prouve ici, SANS
aucun appel API, que :
  1. un cache `status="ok"` valide court-circuite l'extraction AVANT toute instanciation du client
     Anthropic (donc 0 coût au re-run) ;
  2. `prompt_sha` est déterministe (même prompt → même sha) et sensible (prompt/tag modifié → sha
     différent → cache invalidé proprement) ;
  3. un cache `status="partial_error"` n'est PAS servi tel quel : il déclenche une nouvelle tentative
     (reprise au batch), donc l'extraction retente bien les batches KO.

Lançable en script (`python tests/regression/test_incremental.py`) ou via `pytest`.
"""
import sys
import json
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENGINE = REPO / "data" / "house"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO))


def _production_extractor():
    """Le VRAI extracteur de production (constantes House) — comme tests/regression/test_vision_sha."""
    import house.ocr as ho
    from common.vision_ocr import VisionExtractor
    return VisionExtractor(ho.MODEL, ho.OCR_PROMPT, ho.TXN_TOOL, ho.PIPELINE_TAG)


def test_cache_hit_no_api():
    """Cache `ok` valide → transactions servies du cache, client Anthropic JAMAIS instancié."""
    ve = _production_extractor()
    import anthropic
    orig = anthropic.Anthropic
    n_inst = {"count": 0}

    class _Boom:
        def __init__(self, *a, **k):
            n_inst["count"] += 1
            raise AssertionError("Client Anthropic instancié sur un cache hit → re-OCR payant !")

    anthropic.Anthropic = _Boom
    try:
        with tempfile.TemporaryDirectory() as d:
            cache_dir = Path(d)
            doc_id = "INCR_TEST_OK"
            cached = {"doc_id": doc_id, "member": "X", "model": ve.model,
                      "prompt_sha": ve.prompt_sha, "status": "ok",
                      "transactions": [{"ticker": "AAPL"}, {"ticker": "MSFT"}]}
            (cache_dir / f"{doc_id}.json").write_text(json.dumps(cached))
            txns, obj = ve.extract_cached(["FAKE_B64"], doc_id, cache_dir, {}, member="X")
        assert n_inst["count"] == 0, "0 instanciation de client attendue"
        assert [t["ticker"] for t in txns] == ["AAPL", "MSFT"]
        assert obj["prompt_sha"] == ve.prompt_sha
    finally:
        anthropic.Anthropic = orig


def test_prompt_sha_stable_and_sensitive():
    """prompt_sha déterministe + sensible au prompt et au pipeline_tag (invalidation propre)."""
    from common.vision_ocr import VisionExtractor
    tool = {"name": "record_transactions", "input_schema": {"type": "object"}}
    a = VisionExtractor("m", "PROMPT", tool, "tag")
    b = VisionExtractor("m", "PROMPT", tool, "tag")
    assert a.prompt_sha == b.prompt_sha, "même entrée → même sha (déterministe)"
    assert VisionExtractor("m", "PROMPT v2", tool, "tag").prompt_sha != a.prompt_sha
    assert VisionExtractor("m", "PROMPT", tool, "tag2").prompt_sha != a.prompt_sha
    assert len(a.prompt_sha) == 12


def test_partial_error_not_served():
    """Cache `partial_error` → l'extraction RETENTE (n'est pas servie du cache) : ici le client est
    patché pour lever, donc extract_cached doit lever (= il a bien tenté de retravailler)."""
    ve = _production_extractor()
    import anthropic
    orig = anthropic.Anthropic

    class _Sentinel(Exception):
        pass

    def _boom(*a, **k):
        raise _Sentinel()

    anthropic.Anthropic = _boom
    try:
        with tempfile.TemporaryDirectory() as d:
            cache_dir = Path(d)
            doc_id = "INCR_TEST_PARTIAL"
            cached = {"doc_id": doc_id, "member": "X", "model": ve.model,
                      "prompt_sha": ve.prompt_sha, "status": "partial_error",
                      "batches": [], "transactions": []}
            (cache_dir / f"{doc_id}.json").write_text(json.dumps(cached))
            retried = False
            try:
                ve.extract_cached(["FAKE_B64"], doc_id, cache_dir, {}, member="X")
            except _Sentinel:
                retried = True
            assert retried, "partial_error doit déclencher une nouvelle tentative (pas servi du cache)"
    finally:
        anthropic.Anthropic = orig


def main():
    tests = [test_cache_hit_no_api, test_prompt_sha_stable_and_sensitive, test_partial_error_not_served]
    ok = True
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
        except AssertionError as e:
            ok = False
            print(f"  ❌ {t.__name__} : {e}")
    print("\nRÉSULTAT :", "✅ MISE À JOUR INCRÉMENTALE PROUVÉE (2ᵉ run = 0 appel Vision)"
          if ok else "❌ ÉCHEC")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
