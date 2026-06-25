#!/usr/bin/env python
"""Construit le golden de non-régression House : empreinte sha256 de chaque sortie + agrégats têtes.

Le golden est le FILET de la refonte « zéro changement » : on gèle l'état actuel des tables House
(toutes les sorties CSV), puis après chaque étape de refactor on re-génère dans un dossier TEMP et on
diffe via check_golden.py. Aucun commit requis : le manifeste JSON est la référence.

Usage :
    python tests/regression/build_golden.py            # construit depuis les tables LIVE
    python tests/regression/build_golden.py <tablesdir> # depuis un dossier donné
"""
import sys, json, hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIVE_TABLES = REPO / "0 HOUSE" / "toutes_annees" / "data_v1" / "tables"
MANIFEST = Path(__file__).resolve().parent / "golden_manifest.json"
YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def count_lines(p: Path) -> int:
    # nombre de lignes de données (hors en-tête)
    with open(p, "rb") as f:
        n = sum(1 for _ in f)
    return max(0, n - 1)


def headline(tables: Path) -> dict:
    """Agrégats têtes recomputés depuis les FINAL — la vérité chiffrée du plan."""
    import csv
    tot = {"digital": 0, "ocr": 0, "final": 0}
    declarants, sans_bio = set(), 0
    per_year = {}
    for y in YEARS:
        fp = tables / str(y) / f"06_house_{y}_FINAL.csv"
        if not fp.exists():
            continue
        dig = ocr = n = 0
        with open(fp, newline="") as f:
            for r in csv.DictReader(f):
                n += 1
                prov = (r.get("provenance") or "")
                if prov == "house-pdf-electronic":
                    dig += 1
                elif prov == "house-pdf-ocr":
                    ocr += 1
                nm = r.get("declarant_name")
                if nm:
                    declarants.add(nm)
                if not (r.get("bioguide_id") or "").strip():
                    sans_bio += 1
        per_year[str(y)] = {"final": n, "digital": dig, "ocr": ocr}
        tot["digital"] += dig
        tot["ocr"] += ocr
        tot["final"] += n
    return {"total": tot, "per_year": per_year,
            "n_declarants": len(declarants), "n_sans_bioguide": sans_bio}


def build(tables: Path) -> dict:
    files = {}
    for p in sorted(tables.rglob("*.csv")):
        rel = p.relative_to(tables).as_posix()
        files[rel] = {"sha256": sha256_file(p), "rows": count_lines(p), "bytes": p.stat().st_size}
    return {"tables_dir": str(tables), "n_files": len(files), "files": files,
            "headline": headline(tables)}


def main():
    tables = Path(sys.argv[1]) if len(sys.argv) > 1 else LIVE_TABLES
    assert tables.is_dir(), f"introuvable : {tables}"
    g = build(tables)
    MANIFEST.write_text(json.dumps(g, indent=2, ensure_ascii=False))
    h = g["headline"]
    print(f"Golden écrit : {MANIFEST}")
    print(f"  fichiers gelés : {g['n_files']}")
    print(f"  FINAL : {h['total']['final']} (digital {h['total']['digital']} + OCR {h['total']['ocr']})")
    print(f"  déposants : {h['n_declarants']} | sans bioguide : {h['n_sans_bioguide']}")
    print("  par an :")
    for y, v in h["per_year"].items():
        print(f"    {y} : FINAL {v['final']:6} = digital {v['digital']:5} + OCR {v['ocr']:5}")


if __name__ == "__main__":
    main()
