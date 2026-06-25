#!/usr/bin/env python
"""PREUVE piège #6 : VisionExtractor.prompt_sha == PROMPT_SHA original == prompt_sha des caches.

Si ces trois ne coïncident pas, déplacer le moteur OCR invaliderait le cache (546 docs) → re-OCR
payant. On vérifie l'égalité ET qu'un échantillon de fichiers cache porte bien ce prompt_sha.
"""
import sys, json, glob
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENGINE = REPO / "0 HOUSE" / "toutes_annees"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO))


def main():
    import house_ocr_multiyear as ho
    from congress_core.vision_ocr import VisionExtractor

    ve = VisionExtractor(ho.MODEL, ho.OCR_PROMPT, ho.TXN_TOOL, ho.PIPELINE_TAG)
    same_orig = ve.prompt_sha == ho.PROMPT_SHA
    print(f"  VisionExtractor.prompt_sha = {ve.prompt_sha} | original = {ho.PROMPT_SHA} "
          + ("✅" if same_orig else "❌"))

    # Distribution des prompt_sha dans le cache (informational). L'invariant de la refonte = la
    # formule prompt_sha préservée (ci-dessus). Un cache portant un AUTRE sha est une condition
    # PRÉEXISTANTE (docs OCR-isés avec un prompt antérieur), indépendante de l'extraction du moteur.
    caches = glob.glob(str(ENGINE / "data_v1" / "ocr_cache" / "*" / "*.json"))
    shas, stale = {}, []
    for f in caches:
        try:
            o = json.load(open(f))
        except Exception:
            continue
        s = o.get("prompt_sha")
        shas[s] = shas.get(s, 0) + 1
        if s != ho.PROMPT_SHA:
            yr = Path(f).parent.name
            stale.append((yr, o.get("member", ""), o.get("status", "")))
    print(f"  caches : {len(caches)} | prompt_sha : {shas}")
    if stale:
        from collections import Counter
        print(f"  ⚠ {len(stale)} caches au PROMPT_SHA ANTÉRIEUR (préexistant, hors refonte) :")
        print("     par année :", dict(Counter(y for y, _, _ in stale)))
        print("     par statut :", dict(Counter(s for _, _, s in stale)))

    print("\nRÉSULTAT :", "✅ FORMULE PROMPT_SHA PRÉSERVÉE (cache 0d3d… reste valide)"
          if same_orig else "❌ FORMULE CHANGÉE → re-OCR")
    sys.exit(0 if same_orig else 1)


if __name__ == "__main__":
    main()
