#!/usr/bin/env python
"""
Acquisition House — télécharge l'index annuel du Clerk + les PDF des PTR, EN LOCAL.

Contrat : `house/digital.py` lit les PDF déjà présents (`resolve_pdf_path` → `data/house/pdfs/{year}/`)
et l'index (`data/house/index/{year}FD.xml`). Pour 2020-2026 ces ressources sont embarquées ; pour
étendre à 2014-2019 il faut d'abord les acquérir. Ce module fait UNIQUEMENT cette acquisition
(idempotente) ; `digital.py`/`ocr.py` tournent ensuite INCHANGÉS.

- Source index  : https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip  (→ {year}FD.xml)
- Source PDF    : HOUSE_PDF_URL (réutilisé depuis house.digital)
- Idempotent    : ne re-télécharge jamais un fichier déjà présent → 0 impact sur 2020-2026 (index +
                  547 scannés déjà là) et reprise gratuite après interruption.
- Politesse     : User-Agent du dépôt, pause entre requêtes, 404 tolérés (loggés, le manifeste
                  aval les marquera `absent`).

Usage :
  python -m house.acquire --years 2014,2015,2016,2017,2018,2019
  python -m house.acquire --years 2014-2019
"""
import argparse
import io
import time
import zipfile

import pandas as pd
import requests

# Réutilise les constantes/fonctions existantes (source unique, aucun doublon)
from house.digital import INDEX_DIR, PDF_DIR, HOUSE_PDF_URL, SESSION, load_ptr_index

INDEX_ZIP_URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"
PAUSE = 0.4          # s entre PDF (politesse)
RETRIES = 3


def _get(url, timeout=90):
    """GET avec petites reprises sur erreurs transitoires. Retourne la réponse (peut être != 200)."""
    last = None
    for attempt in range(RETRIES):
        try:
            r = SESSION.get(url, timeout=timeout)
            # 5xx = transitoire → retry ; 200/404 = terminal
            if r.status_code < 500:
                return r
            last = r
        except requests.RequestException as e:
            last = e
        time.sleep(1.5 * (attempt + 1))
    if isinstance(last, requests.Response):
        return last
    raise last


def download_index(year):
    """Télécharge + extrait `{year}FD.xml` → data/house/index/. Idempotent (skip si présent)."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    dest = INDEX_DIR / f"{year}FD.xml"
    if dest.exists():
        print(f"  index {year} : déjà présent ({dest.name}) — skip")
        return dest
    r = _get(INDEX_ZIP_URL.format(year=year))
    if r.status_code != 200:
        raise RuntimeError(f"Index {year} indisponible (HTTP {r.status_code}) — {INDEX_ZIP_URL.format(year=year)}")
    z = zipfile.ZipFile(io.BytesIO(r.content))
    xml_names = [n for n in z.namelist() if n.lower().endswith(".xml")]
    if not xml_names:
        raise RuntimeError(f"Index {year} : aucun .xml dans l'archive ({z.namelist()})")
    dest.write_bytes(z.read(xml_names[0]))
    print(f"  index {year} : téléchargé → {dest.name} ({dest.stat().st_size // 1024} Ko)")
    return dest


def download_pdfs(year):
    """Télécharge tous les PDF des PTR (FilingType=P, fenêtre année civile) → data/house/pdfs/{year}/.
    Idempotent (skip si le fichier existe). Écrit un log 00_download_log.csv."""
    download_index(year)  # garantit l'index présent
    win_start = pd.Timestamp(f"{year}-01-01")
    win_end = pd.Timestamp(f"{year}-12-31")
    ptr_index, _ft = load_ptr_index(year, win_start, win_end)
    ydir = PDF_DIR / str(year)
    ydir.mkdir(parents=True, exist_ok=True)

    n = len(ptr_index)
    print(f"  PDF {year} : {n} PTR à vérifier/télécharger …")
    log, got, skipped, missing = [], 0, 0, 0
    for i, (_, r) in enumerate(ptr_index.iterrows(), 1):
        doc_id = str(r["doc_id"])
        dest = ydir / f"{doc_id}.pdf"
        url = HOUSE_PDF_URL.format(year=year, doc_id=doc_id)
        if dest.exists() and dest.stat().st_size > 0:
            skipped += 1
            log.append({"doc_id": doc_id, "http_status": "cache", "bytes": dest.stat().st_size})
            continue
        resp = _get(url)
        status = resp.status_code
        if status == 200 and resp.content:
            dest.write_bytes(resp.content)
            got += 1
            log.append({"doc_id": doc_id, "http_status": 200, "bytes": len(resp.content)})
        else:
            missing += 1
            log.append({"doc_id": doc_id, "http_status": status, "bytes": 0})
        if i % 100 == 0:
            print(f"    … {i}/{n} (téléchargés {got}, en cache {skipped}, absents {missing})")
        time.sleep(PAUSE)
    pd.DataFrame(log).to_csv(ydir / "00_download_log.csv", index=False)
    print(f"  PDF {year} : téléchargés {got} | déjà en cache {skipped} | absents/404 {missing} "
          f"→ {ydir}/00_download_log.csv")
    return {"year": year, "n_ptr": n, "downloaded": got, "cached": skipped, "missing": missing}


def _parse_years(spec):
    spec = spec.strip()
    if "-" in spec and "," not in spec:
        a, b = spec.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in spec.split(",") if x.strip()]


def main():
    ap = argparse.ArgumentParser(description="Acquisition House : index {year}FD.xml + PDF des PTR.")
    ap.add_argument("--years", default="2014-2019", help="ex: 2014-2019 ou 2014,2015 ou 2015")
    args = ap.parse_args()
    summary = []
    for y in _parse_years(args.years):
        print(f"\n===== ACQUISITION {y} =====")
        summary.append(download_pdfs(y))
    print("\n=== RÉCAP ACQUISITION ===")
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == "__main__":
    main()
