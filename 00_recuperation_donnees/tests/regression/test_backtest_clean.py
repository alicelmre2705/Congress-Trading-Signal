"""Filet « zéro changement » du nettoyage backtest (common/backtest_clean.py — step 7 du pipeline).

Reconstruit les trois tables (brute + clean + gated) 100 % hors-ligne depuis les FINAL figées,
et compare au manifest : comptes de l'entonnoir, dimensions, et sha256 du rendu CSV de chacune.
C'est le seul step du pipeline entièrement rejouable sans réseau — il est donc testé de bout en bout.

  python tests/regression/test_backtest_clean.py           # vérifie (doit afficher ZÉRO ÉCART)
  python tests/regression/test_backtest_clean.py --build   # re-fige le manifest (après un changement VOULU)
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

MANIFEST = Path(__file__).with_name("backtest_clean_manifest.json")


def _sha(df):
    return hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()


def snapshot():
    from common.backtest_clean import build_tables, commissions_table
    brut, clean, gated, funnel = build_tables(corrections=True, verbose=False)
    com = commissions_table()
    return {
        "funnel": {str(k): int(v) for k, v in funnel.items()},
        "brut": {"shape": list(brut.shape), "sha256": _sha(brut)},
        "clean": {"shape": list(clean.shape), "sha256": _sha(clean)},
        "gated": {"shape": list(gated.shape), "sha256": _sha(gated)},
        "commissions": {"shape": list(com.shape), "sha256": _sha(com)},
    }


def main():
    snap = snapshot()
    if "--build" in sys.argv:
        MANIFEST.write_text(json.dumps(snap, indent=2, ensure_ascii=False))
        print(f"Manifest figé : {MANIFEST.name}")
        for t in ("brut", "clean", "gated"):
            print(f"  {t:5s} {snap[t]['shape']}  sha {snap[t]['sha256'][:16]}…")
        return
    ref = json.loads(MANIFEST.read_text())
    ecarts = []
    if snap["funnel"] != ref["funnel"]:
        ecarts.append(f"entonnoir : {ref['funnel']} → {snap['funnel']}")
    for t in ("brut", "clean", "gated", "commissions"):
        if snap[t] != ref[t]:
            ecarts.append(f"{t} : shape {ref[t]['shape']}→{snap[t]['shape']} "
                          f"sha {ref[t]['sha256'][:12]}→{snap[t]['sha256'][:12]}")
    if ecarts:
        print("❌ ÉCARTS :")
        for e in ecarts:
            print("  ", e)
        sys.exit(1)
    print(f"Nettoyage backtest : brut {ref['brut']['shape']} · clean {ref['clean']['shape']} · "
          f"gated {ref['gated']['shape']}")
    print("RÉSULTAT : ✅ ZÉRO ÉCART")


if __name__ == "__main__":
    main()
