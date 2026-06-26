#!/usr/bin/env python
"""Smoke-test d'intégration digital : re-génère une année dans un dossier TEMP (sans réseau) et
compare la table 06 (digital) au golden à l'octet près. Prouve que le rebranchement sur le cœur
ne change rien en bout de chaîne.

    .venv/bin/python tests/regression/smoke_digital.py 2026
"""
import sys, hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENGINE = REPO / "data" / "house"
LIVE = ENGINE / "tables"
sys.path.insert(0, str(ENGINE))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    tmp = Path(f"/tmp/regtest_digital/tables")
    tmp.mkdir(parents=True, exist_ok=True)

    import house_multiyear as hm
    hm.TABROOT = tmp                       # redirige les sorties (ne touche pas le live)
    hm.build_reference()
    hm.run_year(year, do_quiver=False, do_crosscheck=False)

    rel = f"{year}/06_house_{year}_transactions.csv"
    new, gold = tmp / rel, LIVE / rel
    same = sha(new) == sha(gold)
    print(f"\n06 digital {year} : {'✅ IDENTIQUE au golden' if same else '❌ DIFFÈRE'}")
    if not same:
        import pandas as pd
        a, b = pd.read_csv(new, dtype=str), pd.read_csv(gold, dtype=str)
        print(f"   lignes new={len(a)} golden={len(b)} | cols identiques={list(a.columns)==list(b.columns)}")
    sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()
