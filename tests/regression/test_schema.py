#!/usr/bin/env python
"""PREUVE piège #1 : congress_core.schema.natural_key_hash est un drop-in EXACT des deux moteurs.

Partie A — équivalence unitaire : on copie VERBATIM les fonctions originales (digital `_legacy_key`,
OCR `natural_key_hash`) et on prouve l'égalité sur une batterie couvrant tous les cas de valeur
manquante (présent, None, NaN, '', clé absente, unicode). C'est la preuve authentique : le CSV écrase
None/''/NaN en cellule vide, donc recompute-depuis-CSV ne peut PAS distinguer ces cas (cf. partie B).

Partie B — repro CSV : sur les lignes des tables figées dont les 7 champs-clé sont tous présents et
non vides, le hash recomputé doit égaler le hash stocké à 100 % (les lignes à champ manquant sont
couvertes par la partie A + le re-run de bout en bout).

    .venv/bin/python tests/regression/test_schema.py
"""
import sys, hashlib, math
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
TABLES = REPO / "data" / "house" / "tables"
sys.path.insert(0, str(REPO))
from congress_core.schema import natural_key_hash, NATURAL_KEY_FIELDS

YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]


# ---- copies VERBATIM des originaux (à ne pas modifier — ce sont nos références) ----
def orig_digital_legacy(r):  # house_multiyear._legacy_key
    raw = "|".join(str(x) for x in [r["chamber"], r["declarant_name"], r["transaction_date"],
                                    r["asset_description"], r["operation_type"],
                                    r["amount_range"], r["owner"]])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def orig_ocr_nkh(row):  # house_ocr_multiyear.natural_key_hash
    key = "|".join(["house", str(row.get("declarant_name", "")), str(row.get("transaction_date", "")),
                    str(row.get("asset_description", "")), str(row.get("operation_type", "")),
                    str(row.get("amount_range", "")), str(row.get("owner", ""))])
    return hashlib.sha256(key.encode()).hexdigest()


NAN = float("nan")
OCR_BATTERY = [
    {"declarant_name": "Ro Khanna", "transaction_date": "2025-01-15", "asset_description": "Apple Inc",
     "operation_type": "Purchase", "amount_range": "$1,001 - $15,000", "owner": "Spouse"},
    {"declarant_name": "Michael T. McCaul", "transaction_date": None,  # date None → "None"
     "asset_description": "LLM FAMILY INVESTMENTS LP (11.7624% INTEREST)", "operation_type": "Purchase",
     "amount_range": "", "owner": "Spouse"},                            # amount '' → ''
    {"declarant_name": "X", "transaction_date": NAN, "asset_description": "Y",   # NaN → 'nan'
     "operation_type": "Sale", "amount_range": "$1 - $2", "owner": "SELF"},
    {"declarant_name": "Énà Üml", "transaction_date": "2024-12-31", "asset_description": "Société Générale",
     "operation_type": "Sale (Partial)", "amount_range": "$15,001 - $50,000"},   # owner ABSENT → ''
]
DIGITAL_BATTERY = [
    {"chamber": "house", "declarant_name": "Nancy Pelosi", "transaction_date": "2025-02-01",
     "asset_description": "NVIDIA", "operation_type": "Purchase", "amount_range": "Over $50,000,000",
     "owner": "JT"},
    {"chamber": "house", "declarant_name": "Z", "transaction_date": NAN, "asset_description": "W",
     "operation_type": "Exchange", "amount_range": "$1 - $2", "owner": "SELF"},  # NaN → 'nan'
]


def part_a():
    bad = 0
    for row in OCR_BATTERY:
        if natural_key_hash(row, chamber="house") != orig_ocr_nkh(row):
            bad += 1
            print("   ❌ OCR battery:", row)
    for row in DIGITAL_BATTERY:
        if natural_key_hash(row, chamber="house") != orig_digital_legacy(row):
            bad += 1
            print("   ❌ DIGITAL battery:", row)
    print(f"  Partie A (équivalence unitaire vs originaux) : "
          f"{len(OCR_BATTERY)+len(DIGITAL_BATTERY)-bad}/{len(OCR_BATTERY)+len(DIGITAL_BATTERY)} "
          + ("✅" if bad == 0 else f"❌ {bad} écarts"))
    return bad == 0


def _complete(r):
    for c in NATURAL_KEY_FIELDS:
        if c == "chamber":
            continue
        v = r.get(c)
        if v is None or v == "" or (isinstance(v, float) and math.isnan(v)) or str(v).lower() == "nan":
            return False
    return True


def part_b():
    total_ok = total_bad = total_skip = 0
    for y in YEARS:
        for pat in [f"{y}/06_house_{y}_transactions.csv", f"{y}/06b_house_{y}_ocr_transactions.csv",
                    f"{y}/06_house_{y}_FINAL.csv"]:
            p = TABLES / pat
            if not p.exists():
                continue
            df = pd.read_csv(p, dtype=str)
            if "natural_key_hash" not in df.columns:
                continue
            mask = df.apply(_complete, axis=1)
            sub = df[mask]
            recomputed = sub.apply(lambda r: natural_key_hash(r, chamber="house"), axis=1)
            ok = int((recomputed == sub["natural_key_hash"].astype(str)).sum())
            total_ok += ok
            total_bad += len(sub) - ok
            total_skip += int((~mask).sum())
    print(f"  Partie B (repro CSV, lignes clé-complète) : {total_ok} ok, {total_bad} écarts, "
          f"{total_skip} ignorées (champ manquant → couvert par A)")
    return total_bad == 0


def main():
    a = part_a()
    b = part_b()
    print("\nRÉSULTAT :", "✅ natural_key_hash = DROP-IN EXACT" if (a and b) else "❌ ÉCART")
    sys.exit(0 if (a and b) else 1)


if __name__ == "__main__":
    main()
