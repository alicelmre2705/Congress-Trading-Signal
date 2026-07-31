#!/usr/bin/env python
"""Classifie les PTR House SCANNÉS (bucket `non_lisible`) en TAPÉ vs MANUSCRIT via Claude Vision,
pour ÉTENDRE le census de clusters (`_scan_census.csv`) aux années pré-2020 et appliquer le MÊME
gating `C_manuscrit` qu'en 2020-2026 (cf. `house/ocr.py:run_ocr_year`).

Motivation : le census 2020-2026 (`_scan_census_547.csv`) fut curé À LA MAIN ; les scans 2014-2019
n'avaient aucune classification → tous OCR-isés (manuscrits inclus), incohérent avec la politique
2020-2026 qui écarte les manuscrits (dates peu fiables, corroboration Quiver ~35 %).

Sortie : append au census des lignes {doc_id, year, member, pages, entry_style, cluster} — colonnes
minimales lues par le gating (`cluster` + `doc_id`). Cache versionné (`prompt_sha`+`model`) → re-run = 0 coût.

Usage : python -m house.classify_scans --years 2014-2019
"""
import argparse
import base64
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

import house.digital as hm   # resolve_pdf_path, TABROOT, OUTDIR, .env chargé à l'import

MODEL = "claude-sonnet-4-6"          # parité pipeline
DPI = 200
CONCURRENCY = 8
CACHE_ROOT = hm.OUTDIR / "classify_cache"
CENSUS_OLD = hm.TABROOT / "_scan_census_547.csv"   # 547 lignes 2020-2026, JAMAIS modifiées
CENSUS_NEW = hm.TABROOT / "_scan_census.csv"       # census étendu 2014-2026

CLASSIFY_PROMPT = (
    "Voici une page scannée d'un formulaire PTR (Periodic Transaction Report) de la Chambre des "
    "représentants US. Détermine si les DONNÉES DE TRANSACTION saisies (noms d'actifs, dates, "
    "montants dans le tableau) ont été écrites À LA MAIN ou TAPÉES à la machine/ordinateur.\n"
    "ATTENTION — le scan est très souvent DE TRAVERS, INCLINÉ ou TOURNÉ de 90° ou 180°. Un texte "
    "TAPÉ reste TAPÉ même penché ou tourné : ne le prends pas pour du manuscrit. Réponds MANUSCRIT "
    "UNIQUEMENT si tu vois clairement de l'ÉCRITURE À LA MAIN (traits irréguliers, cursive, ou "
    "capitales tracées à la main dont la forme varie d'une lettre à l'autre). Des caractères "
    "RÉGULIERS et IDENTIQUES à chaque occurrence = TAPÉ. Le texte pré-imprimé du formulaire "
    "(titres, en-têtes, cases A–K) est toujours tapé et ne compte pas : juge seulement les valeurs "
    "SAISIES. En cas de doute, réponds TAPE.\n"
    "Réponds par UN SEUL MOT : MANUSCRIT ou TAPE."
)
_PROMPT_SHA = hashlib.sha256((CLASSIFY_PROMPT + MODEL).encode()).hexdigest()[:12]


def _render_page1(pdf_path, dpi=DPI):
    """Rend la page 1 en PNG b64 + renvoie le nombre de pages."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    n = doc.page_count
    b64 = base64.b64encode(doc[0].get_pixmap(dpi=dpi).tobytes("png")).decode()
    doc.close()
    return b64, n


def classify_one(year, doc_id, force=False):
    """Retourne (cluster, entry_style, pages). Cache disque versionné → 0 appel si déjà vu."""
    cache_dir = CACHE_ROOT / str(year)
    cache_file = cache_dir / f"{doc_id}.json"
    if cache_file.exists() and not force:
        try:
            prev = json.loads(cache_file.read_text())
            if prev.get("prompt_sha") == _PROMPT_SHA and prev.get("model") == MODEL:
                return prev["cluster"], prev["entry_style"], prev.get("pages")
        except json.JSONDecodeError:
            pass
    path = hm.resolve_pdf_path(year, doc_id)
    if path is None:
        return None, None, None
    b64, pages = _render_page1(path)

    import anthropic
    client = anthropic.Anthropic()
    content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
               {"type": "text", "text": CLASSIFY_PROMPT}]
    label = "TAPE"
    for attempt in range(6):
        try:
            r = client.messages.create(model=MODEL, max_tokens=8,
                                       messages=[{"role": "user", "content": content}])
            txt = "".join(getattr(b, "text", "") for b in r.content).upper()
            label = "MANUSCRIT" if "MANUSCRIT" in txt else "TAPE"
            break
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError):
            if attempt < 5:
                time.sleep(min(2 ** attempt, 30))
                continue
    cluster = "C_manuscrit" if label == "MANUSCRIT" else "B_tape_tourne"   # tapé = exécuté (A/B non distingués)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps({"doc_id": doc_id, "year": int(year), "model": MODEL,
                                      "prompt_sha": _PROMPT_SHA, "entry_style": label,
                                      "cluster": cluster, "pages": pages}, ensure_ascii=False))
    return cluster, label, pages


def _scanned_docs(year):
    """doc_ids scannés (bucket non_lisible) + nom du déposant (via 03_ptr_index)."""
    ydir = hm.TABROOT / str(year)
    man = pd.read_csv(ydir / "04_download_manifest.csv", dtype=str)
    scanned = man[man["bucket"] == "non_lisible"][["doc_id"]]
    idx = pd.read_csv(ydir / "03_ptr_index.csv", dtype=str)[["doc_id", "declarant_name"]]
    return scanned.merge(idx, on="doc_id", how="left")


def _parse_years(spec):
    spec = spec.strip()
    if "-" in spec and "," not in spec:
        a, b = spec.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in spec.split(",") if x.strip()]


def main():
    ap = argparse.ArgumentParser(description="Classification tapé/manuscrit des scans House → census.")
    ap.add_argument("--years", default="2014-2019")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    years = _parse_years(args.years)

    tasks, meta = [], {}
    for y in years:
        docs = _scanned_docs(y)
        for _, r in docs.iterrows():
            tasks.append((y, r["doc_id"]))
            meta[(y, r["doc_id"])] = r.get("declarant_name", "")
    print(f"À classifier : {len(tasks)} scans sur {years}")

    rows, n_hand, n_type, n_miss = [], 0, 0, 0
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(classify_one, y, d, args.force): (y, d) for (y, d) in tasks}
        done = 0
        for fut in as_completed(futs):
            y, d = futs[fut]
            cluster, style, pages = fut.result()
            done += 1
            if cluster is None:
                n_miss += 1
            else:
                rows.append({"doc_id": d, "year": y, "member": meta[(y, d)], "pages": pages,
                             "entry_style": style, "cluster": cluster})
                n_hand += (cluster == "C_manuscrit")
                n_type += (cluster != "C_manuscrit")
            if done % 100 == 0 or done == len(tasks):
                print(f"  {done}/{len(tasks)} (manuscrit {n_hand} · tapé {n_type} · pdf absent {n_miss})")

    new = pd.DataFrame(rows)
    # census étendu = 547 lignes 2020-2026 INCHANGÉES + nouvelles lignes 2014-2019
    old = pd.read_csv(CENSUS_OLD, dtype=str)
    combined = pd.concat([old, new.reindex(columns=old.columns)], ignore_index=True)
    combined.to_csv(CENSUS_NEW, index=False)
    print(f"\n→ {CENSUS_NEW.name} : {len(combined)} lignes ({len(old)} anciennes + {len(new)} neuves)")
    print("  répartition cluster (nouvelles) :", new["cluster"].value_counts().to_dict())
    print("  par année :")
    print(new.groupby(["year", "cluster"]).size().to_string())


if __name__ == "__main__":
    main()
