#!/usr/bin/env python
"""Preuve « zéro changement » Sénat — reproduction fonction-par-fonction depuis les colonnes figées.

Comme le pipeline House, le pipeline Sénat n'est PAS re-jouable hors-ligne (le scraping eFD exige le
réseau ; seuls les artefacts figés sont embarqués). On prouve donc que le code re-logé dans `senate/`
ET le cœur `common` reproduisent À L'IDENTIQUE les colonnes des tables FINAL gelées
(`data/senate/{an}/06_senate_{an}_FINAL.csv`) — sans aucun appel API, sans re-run.

Trois invariants (sur les 8 841 lignes FINAL) :
  1. natural_key_hash  : recomputé par common.schema.natural_key_hash(., "senate")
     ET par senate.identity.natural_key → == colonne figée. (⇒ « bâti sur common ».)
  2. recover_ticker    : pour ticker_source == 'asset_name', senate.identity.recover_ticker
     (asset_description) == ticker figé.
  3. identité bioguide : senate.identity.{load_reference,make_matcher} re-rattache declarant_name
     → == bioguide_id figé (sur les lignes rattachées). Référentiel lu depuis data/senate/reference.
"""
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from common.schema import natural_key_hash as core_nkh   # noqa: E402
from senate import identity as si                               # noqa: E402

DATA = REPO / "data" / "senate"
YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
NK_FIELDS = ["chamber", "declarant_name", "transaction_date",
             "asset_description", "operation_type", "amount_range", "owner"]


def _load_all():
    frames = []
    for y in YEARS:
        fp = DATA / str(y) / f"06_senate_{y}_FINAL.csv"
        frames.append(pd.read_csv(fp, dtype=str, keep_default_na=False))
    return pd.concat(frames, ignore_index=True)


def _hash_input(r):
    """Reconstitue le dict des 7 champs TEL QU'IL A ÉTÉ HASHÉ en mémoire (le CSV est lossy).
    Seule subtilité : une `transaction_date` illisible (8 lignes OCR, date non lue) valait un float
    NaN au moment du hash → `str(NaN)` = 'nan' ; la sérialisation CSV l'a rendue vide. Les autres
    champs vides étaient des chaînes vides ('') à l'origine. Vérifié exhaustivement : 8 841/8 841."""
    row = {c: r[c] for c in NK_FIELDS}
    if row["transaction_date"] == "":
        row["transaction_date"] = "nan"
    return row


def test_natural_key_hash_core_and_senate():
    """core.natural_key_hash ET senate.identity.natural_key reproduisent chaque hash figé."""
    df = _load_all()
    n_core = n_senate = 0
    for _, r in df.iterrows():
        row = _hash_input(r)
        if core_nkh(row, "senate") == r["natural_key_hash"]:
            n_core += 1
        if si.natural_key(row) == r["natural_key_hash"]:
            n_senate += 1
    n = len(df)
    print(f"natural_key_hash : core {n_core}/{n} | senate {n_senate}/{n}")
    assert n_core == n, f"core.natural_key_hash : {n - n_core} écarts / {n}"
    assert n_senate == n, f"senate.identity.natural_key : {n - n_senate} écarts / {n}"


def test_recover_ticker_asset_name():
    """Là où ticker_source == 'asset_name', recover_ticker(asset_description) == ticker figé."""
    df = _load_all()
    sub = df[df["ticker_source"] == "asset_name"]
    ok = sum(1 for _, r in sub.iterrows()
             if (si.recover_ticker(r["asset_description"]) or "").upper() == r["ticker"].upper())
    print(f"recover_ticker (asset_name) : {ok}/{len(sub)}")
    assert ok == len(sub), f"recover_ticker : {len(sub) - ok} écarts / {len(sub)}"


def test_identity_bioguide_reproduced():
    """senate.identity re-rattache declarant_name → bioguide identique au figé (lignes rattachées)."""
    df = _load_all()
    ref, name_exact, name_by_last, current_bios, _b2c, _kf = si.load_reference()
    match = si.make_matcher(ref, name_exact, name_by_last, current_bios)
    have_bio = df[df["bioguide_id"].astype(str).str.strip().ne("")]
    names = have_bio.drop_duplicates("declarant_name")[["declarant_name", "bioguide_id"]]
    ok = sum(1 for _, r in names.iterrows() if match(r["declarant_name"]) == r["bioguide_id"])
    print(f"identité bioguide (noms distincts rattachés) : {ok}/{len(names)}")
    assert ok == len(names), f"identité : {len(names) - ok} écarts / {len(names)}"


if __name__ == "__main__":
    test_natural_key_hash_core_and_senate()
    test_recover_ticker_asset_name()
    test_identity_bioguide_reproduced()
    print("RÉSULTAT : ✅ reproduction Sénat (core + senate) — zéro écart")
