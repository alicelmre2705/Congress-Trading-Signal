#!/usr/bin/env python
"""A2 — Correctif dédup House (parité Sénat, NON destructeur).

L'OCR House n'avait jamais peuplé occurrence_index → impossible de distinguer le multi-trust réel
(même nk, occ 0/1/2…) des vrais doublons cross-doc. On pose occurrence_index = cumcount(doc_id, nk)
sur l'OCR PUIS on dédup sur (nk, occ) : préserve le multi-trust same-doc, retire les doublons cross-doc.

Sur les tables figées (sans re-run OCR — la politique cluster droperait C) :
- 06b : pose occ + dédup (nk, occ) → OCR 49 375 → ~48 970.
- 06_FINAL : digital INTOUCHÉ + OCR dédupliqué → ~81 646.
Idempotent (relancer ne retire rien de plus).
"""
import sys
from pathlib import Path
import pandas as pd

T = Path("data/house/tables")
YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]


def dedup_ocr(ocr):
    """Pose occ = cumcount(doc_id, nk) puis dédup (nk, occ) keep=first. Renvoie (df, n_removed)."""
    ocr = ocr.copy()
    ocr["occurrence_index"] = ocr.groupby(["doc_id", "natural_key_hash"]).cumcount()
    before = len(ocr)
    ocr = ocr.drop_duplicates(["natural_key_hash", "occurrence_index"], keep="first").reset_index(drop=True)
    return ocr, before - len(ocr)


def main():
    tot_final_before = tot_final_after = tot_ocr_after = removed = 0
    for y in YEARS:
        # 06b : OCR seul → occ + dédup
        b06 = T / str(y) / f"06b_house_{y}_ocr_transactions.csv"
        ocr_b = pd.read_csv(b06, dtype=str)
        ocr_b["occurrence_index"] = ocr_b.groupby(["doc_id", "natural_key_hash"]).cumcount()
        ocr_b = ocr_b.drop_duplicates(["natural_key_hash", "occurrence_index"], keep="first").reset_index(drop=True)
        ocr_b.to_csv(b06, index=False)
        tot_ocr_after += len(ocr_b)

        # 06_FINAL : digital INTOUCHÉ + OCR dédupliqué (même ordre de colonnes)
        ff = T / str(y) / f"06_house_{y}_FINAL.csv"
        F = pd.read_csv(ff, dtype=str)
        cols = list(F.columns)
        tot_final_before += len(F)
        dig = F[F["provenance"] == "house-pdf-electronic"]
        ocr = F[F["provenance"] == "house-pdf-ocr"]
        ocr_dd, n = dedup_ocr(ocr)
        removed += n
        comb = pd.concat([dig, ocr_dd], ignore_index=True).reindex(columns=cols)
        comb.to_csv(ff, index=False)
        tot_final_after += len(comb)
        print(f"  {y}: FINAL {len(F)}→{len(comb)} (−{n}) | OCR {len(ocr)}→{len(ocr_dd)}")

    print(f"\nFINAL {tot_final_before} → {tot_final_after} (−{removed} doublons cross-doc) | OCR → {tot_ocr_after}")
    ok = tot_final_after == 81646 and tot_ocr_after == 48970
    print("RÉSULTAT :", "✅ 81 646 / OCR 48 970 (attendu)" if ok else f"⚠ inattendu ({tot_final_after}/{tot_ocr_after})")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
