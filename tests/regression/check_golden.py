#!/usr/bin/env python
"""Vérifie qu'un dossier de tables reproduit le golden à l'octet près (refonte « zéro changement »).

Usage :
    python tests/regression/check_golden.py             # vérifie les tables LIVE
    python tests/regression/check_golden.py <tablesdir>  # vérifie un run TEMP

Sortie : liste des fichiers OK / DIFFÉRENTS / MANQUANTS / EN TROP + agrégats têtes.
Code retour 0 si tout concorde, 1 sinon. C'est l'assertion centrale de chaque phase.
"""
import sys, json, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "golden_manifest.json"
LIVE_TABLES = Path(__file__).resolve().parents[2] / "data" / "house" / "tables"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    tables = Path(sys.argv[1]) if len(sys.argv) > 1 else LIVE_TABLES
    g = json.loads(MANIFEST.read_text())
    golden = g["files"]
    seen, diff, missing = set(), [], []
    for rel, meta in golden.items():
        p = tables / rel
        if not p.exists():
            missing.append(rel)
            continue
        seen.add(rel)
        if sha256_file(p) != meta["sha256"]:
            from io import StringIO
            now = sum(1 for _ in open(p, "rb")) - 1
            diff.append((rel, meta["rows"], now))
    extra = [p.relative_to(tables).as_posix() for p in tables.rglob("*.csv")
             if p.relative_to(tables).as_posix() not in golden]

    ok = len(seen) - len(diff)
    print(f"Golden : {g['n_files']} fichiers | dossier testé : {tables}")
    print(f"  ✅ identiques : {ok}")
    if diff:
        print(f"  ❌ DIFFÉRENTS : {len(diff)}")
        for rel, was, now in diff[:40]:
            print(f"      {rel}  (golden {was} lignes → {now})")
    if missing:
        print(f"  ⚠ MANQUANTS : {len(missing)}")
        for rel in missing[:40]:
            print(f"      {rel}")
    if extra:
        print(f"  ⚠ EN TROP : {len(extra)}")
        for rel in extra[:20]:
            print(f"      {rel}")
    fail = bool(diff or missing)
    print("RÉSULTAT :", "✅ ZÉRO ÉCART" if not fail else "❌ ÉCART DÉTECTÉ")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
