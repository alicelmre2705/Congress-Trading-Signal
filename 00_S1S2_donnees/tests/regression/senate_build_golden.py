#!/usr/bin/env python
"""Construit le golden de non-régression SÉNAT : empreinte sha256 de chaque sortie + agrégats têtes.

Filet de la restructuration Sénat « zéro changement » : on gèle l'état actuel des tables Sénat
(toutes les sorties CSV sous data/senate), puis après chaque étape (git mv, repointage, package
senate/) on re-vérifie via senate_check_golden.py. Le manifeste JSON est la référence.

Usage :
    python tests/regression/senate_build_golden.py             # depuis data/senate
    python tests/regression/senate_build_golden.py <datadir>   # depuis un dossier donné
"""
import sys, json, hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIVE_DATA = REPO / "data" / "senate" / "tables"
MANIFEST = Path(__file__).resolve().parent / "senate_golden_manifest.json"
YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def count_lines(p: Path) -> int:
    with open(p, "rb") as f:
        n = sum(1 for _ in f)
    return max(0, n - 1)


def headline(data: Path) -> dict:
    """Agrégats têtes recomputés depuis les FINAL — la vérité chiffrée Sénat (8 841)."""
    import csv
    tot = {"digital": 0, "ocr": 0, "final": 0}
    declarants, sans_bio = set(), 0
    per_year = {}
    for y in YEARS:
        fp = data / str(y) / f"06_senate_{y}_FINAL.csv"
        if not fp.exists():
            continue
        dig = ocr = n = 0
        with open(fp, newline="") as f:
            for r in csv.DictReader(f):
                n += 1
                prov = (r.get("provenance") or "")
                if prov == "senate-efd-electronic":
                    dig += 1
                elif prov == "senate-efd-ocr":
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


def build(data: Path) -> dict:
    files = {}
    for p in sorted(data.rglob("*.csv")):
        rel = p.relative_to(data).as_posix()
        files[rel] = {"sha256": sha256_file(p), "rows": count_lines(p), "bytes": p.stat().st_size}
    return {"data_dir": str(data), "n_files": len(files), "files": files,
            "headline": headline(data)}


def main():
    data = Path(sys.argv[1]) if len(sys.argv) > 1 else LIVE_DATA
    assert data.is_dir(), f"introuvable : {data}"
    g = build(data)
    MANIFEST.write_text(json.dumps(g, indent=2, ensure_ascii=False))
    h = g["headline"]
    print(f"Golden Sénat écrit : {MANIFEST}")
    print(f"  fichiers gelés : {g['n_files']}")
    print(f"  FINAL : {h['total']['final']} (digital {h['total']['digital']} + OCR {h['total']['ocr']})")
    print(f"  sénateurs : {h['n_declarants']} | sans bioguide : {h['n_sans_bioguide']}")
    print("  par an :")
    for y, v in h["per_year"].items():
        print(f"    {y} : FINAL {v['final']:6} = digital {v['digital']:5} + OCR {v['ocr']:5}")


if __name__ == "__main__":
    main()
