#!/usr/bin/env python
"""senate.ocr_engine — moteur OCR des PTR Sénat SCANNÉS (papier), Claude Vision.

Moteur figé porté tel quel du pilote Q1 (logique inchangée — c'est elle qui a produit le golden OCR).
On lit les rapports papier déjà cachés (data/senate/reports/{uuid}.html), on récupère les images
.gif (efd-media-public.senate.gov — serveur public, hors barrière CSRF), on les cache en local, puis
on les passe à Claude Vision (tool_use `record_transactions`). Cache OCR versionné par prompt_sha +
modèle (re-run = 0 appel si inchangé). Les chemins par défaut pointent `data/senate/` ; l'orchestrateur
multi-années `senate.ocr` les surcharge au besoin (monkeypatch REPORTS/MEDIA/OCR_CACHE).

Adapté au formulaire Sénat « PERIODIC DISCLOSURE OF FINANCIAL TRANSACTIONS » (≠ House) :
  - propriétaire = préfixe entre parenthèses (SP)/(DC)/(JT) dans le nom de l'actif, sinon Self ;
  - types : Purchase / Sale / Exchange (le papier ne distingue pas Full/Partial) ;
  - montant : colonnes à cocher en fourchettes $ explicites (pas de lettres A–K sur le formulaire) ;
  - une seule date de transaction par ligne ;
  - ligne-exemple pré-imprimée « (DC) Microsoft (stock) » à IGNORER.

Sortie : 06b_senate_{année}_ocr_transactions.csv sous data/senate/ (provenance=senate-efd-ocr),
au schéma complet (identité ré-attachée via senate.identity). La fusion digital+OCR et la
validation Quiver sont faites par senate.fusion / senate.digital.
"""
import os
import re
import io
import json
import time
import base64
import hashlib
from pathlib import Path

import requests
import pandas as pd
from PIL import Image
import anthropic

from senate.identity import (load_reference, make_matcher, recover_ticker,
                             strip_accents, norm, SCHEMA)

HERE = Path(__file__).resolve().parent       # <repo>/senate
OUT = HERE.parent / "data" / "senate"         # données Sénat (parité data/house)
TAB = OUT                                      # tables directement sous data/senate
REPORTS = OUT / "reports"
MEDIA = REPORTS / "media"        # cache local des images .gif (offline après 1er run)
OCR_CACHE = OUT / "ocr_cache"    # cache des extractions Vision (versionné prompt_sha+model)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8_000
MAX_IMG_PER_CALL = 3
LONG_EDGE = 1568                 # Anthropic plafonne le bord long ~1568 px → inutile d'envoyer plus
GIF_RE = re.compile(r'https://efd-media-public\.senate\.gov/media/[^\s"\']+\.gif')
EFD_PAPER = "https://efdsearch.senate.gov/search/view/paper/{uuid}/"
UA = {"User-Agent": "congress-trading-research/1.0 (poli, sans evasion)"}

# Les 4 PTR papier Q1 2025 (tous Sénateur Richard Blumenthal, déposés via Elias Law Group).
# uuid -> (declarant_name, disclosure_date = date de réception par le Secrétaire du Sénat).
PAPERS = {
    "d7d35e4a-545e-4215-a318-f90031461bc3": ("Richard Blumenthal", "2025-01-21"),
    "14607985-10ba-44a3-bd64-9840e003b06e": ("Richard Blumenthal", "2025-02-10"),
    "4fbbf6be-25c1-4589-bda0-95b5295c4107": ("Richard Blumenthal", "2025-03-04"),
    "8e8ae815-6d8b-4330-8aa0-da89ab2e2ca0": ("Richard Blumenthal", "2025-03-17"),
}

# Fourchettes Sénat : mêmes bornes que l'électronique (« $1,001 - $15,000 », midpoint (lo+hi)/2).
AMOUNT_MAP = {
    "A": ("$1,001 - $15,000", 8000.5),       "B": ("$15,001 - $50,000", 32500.5),
    "C": ("$50,001 - $100,000", 75000.5),    "D": ("$100,001 - $250,000", 175000.5),
    "E": ("$250,001 - $500,000", 375000.5),  "F": ("$500,001 - $1,000,000", 750000.5),
    "G": ("$1,000,001 - $5,000,000", 3000000.5), "H": ("$5,000,001 - $25,000,000", 15000000.5),
    "I": ("$25,000,001 - $50,000,000", 37500000.5), "J": ("Over $50,000,000", 50000000.0),
}
OWNER_MAP = {"Self": "Self", "Spouse": "Spouse", "Joint": "Joint", "Dependent Child": "Child"}
# Lignes-exemple pré-imprimées (filet de sécurité si le modèle les reporte malgré le prompt)
EXAMPLE_RE = re.compile(r"\bexample\b|mega\s*corp|ibm\s*corp|microsoft\s*\(\s*stock\s*\)", re.I)

OCR_PROMPT = """\
Tu lis les pages scannées d'un formulaire « PERIODIC DISCLOSURE OF FINANCIAL TRANSACTIONS »
(Periodic Transaction Report — Sénat des États-Unis) déposé par {member_name}. Reporte TOUTES
les transactions financières en appelant l'outil record_transactions.

PÉRIODE DU RAPPORT : toutes les transactions de ce dépôt sont datées entre {win_start} et
{win_end} (un PTR est déposé peu après la transaction). Le JOUR et le MOIS que tu lis sont
fiables ; si l'ANNÉE que tu lis place une date HORS de cette plage, c'est une mauvaise lecture
du chiffre de l'année : corrige l'année pour que la date retombe dans la plage.

STRUCTURE DU FORMULAIRE :
  Colonne « Identification of Assets » : nom complet de l'actif. Le PROPRIÉTAIRE est un préfixe
    entre parenthèses au début du nom : (S)=Spouse, (DC)=Dependent Child, (J)=Joint ; aucun
    préfixe = Self. Retire ce préfixe de asset_description et renseigne le champ owner.
  COMPTES IMBRIQUÉS : une ligne qui se termine par « : » SANS case cochée ni date est un EN-TÊTE
    de compte (ex. « (S) Peter L Malkin Family 9 LLC: »), PAS une transaction. Ne la reporte pas
    seule : rattache son nom en préfixe aux transactions indentées en dessous, au format
    « Compte: Actif » (ex. « Peter L Malkin Family 9 LLC: MH Four Winds LLC »).
  « Transaction Type(s) » : trois colonnes à cocher → Purchase | Sale | Exchange.
  « Transaction Date (Mo. Day. Yr.) » : une seule date par ligne, format MM/DD/YY.
  « Amount of Transaction ($) » : une seule case cochée par ligne parmi des fourchettes en dollars,
    de gauche à droite :
      A=$1,001–15k  B=15k–50k  C=50k–100k  D=100k–250k  E=250k–500k  F=500k–1M
      G=1M–5M  H=5M–25M  I=25M–50M  J=>50M  → renvoie la LETTRE de la colonne cochée.

RÈGLES CRITIQUES :
  1. Le formulaire peut être scanné à 90° ou 180° — lis-le dans son orientation correcte.
  2. LIGNES D'EXEMPLE PRÉ-IMPRIMÉES — À IGNORER ABSOLUMENT. Le formulaire vierge contient des lignes
     modèles dans la zone « Example » : « IBM Corp. (stock) NYSE » et « (DC) Microsoft (stock)
     NASDAQ/OTC » (dates en « /1X »). Ce ne sont JAMAIS des transactions réelles.
  3. Ignore la lettre d'accompagnement (cabinet d'avocats), les pages de couverture et de
     certification qui ne contiennent pas de table de transactions.
  4. Reporte CHAQUE ligne dont une case Transaction Type est cochée, Y COMPRIS des lignes
     strictement identiques répétées (même actif, même date, même montant, même propriétaire) :
     ce sont des transactions réelles distinctes, jamais des doublons à fusionner.
  5. Transcris fidèlement le nom de l'actif tel qu'écrit. N'invente jamais ; ne devine pas.
  6. Convertis MM/DD/YY → YYYY-MM-DD en respectant la PÉRIODE DU RAPPORT ci-dessus.
  7. ticker : uniquement si un symbole boursier est explicitement imprimé ; sinon null.
  8. amount_code = UNIQUEMENT la lettre A–J de la colonne cochée. Si illisible, omets le champ.
"""

TXN_TOOL = {
    "name": "record_transactions",
    "description": ("Enregistre la liste complète des transactions lues sur les pages fournies. "
                    "Tableau vide si aucune (lettre d'accompagnement, page de couverture, ou "
                    "'Nothing to report')."),
    "input_schema": {"type": "object", "properties": {"transactions": {"type": "array", "items": {
        "type": "object", "properties": {
            "asset_description": {"type": "string"},
            "ticker": {"type": ["string", "null"]},
            "transaction_type": {"type": "string", "enum": ["Purchase", "Sale", "Exchange"]},
            "transaction_date": {"type": ["string", "null"]},
            "amount_code": {"type": "string", "enum": list("ABCDEFGHIJ")},
            "owner": {"type": "string", "enum": ["Self", "Spouse", "Joint", "Dependent Child"]},
        }, "required": ["asset_description", "transaction_type", "owner"],
        "additionalProperties": False}}},
        "required": ["transactions"]},
}
PROMPT_SHA = hashlib.sha256((OCR_PROMPT + json.dumps(TXN_TOOL, sort_keys=True)).encode()).hexdigest()[:12]


# --------------------------------------------------------------------------- secrets locaux
def _api_key():
    k = os.environ.get("ANTHROPIC_API_KEY")
    envf = HERE / ".env"
    if not k and envf.exists():
        for line in open(envf):
            if line.startswith("ANTHROPIC_API_KEY="):
                k = line.split("=", 1)[1].strip() or None
    return k


# --------------------------------------------------------------------------- images
def report_gif_urls(uuid):
    html = (REPORTS / f"{uuid}.html").read_text(encoding="utf-8", errors="replace")
    return GIF_RE.findall(html)


def _image_b64(url):
    """Récupère un .gif (cache disque local d'abord), redimensionne ≤ LONG_EDGE, renvoie PNG base64."""
    MEDIA.mkdir(parents=True, exist_ok=True)
    cache = MEDIA / url.rsplit("/", 1)[-1]
    if cache.exists():
        data = cache.read_bytes()
    else:
        r = requests.get(url, headers=UA, timeout=60)
        r.raise_for_status()
        data = r.content
        cache.write_bytes(data)             # offline-capable après 1er téléchargement
    img = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = img.size
    if max(w, h) > LONG_EDGE:
        s = LONG_EDGE / max(w, h)
        img = img.resize((round(w * s), round(h * s)))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


class OcrError(Exception):
    pass


def _call_vision(client, images_b64, member, win_start, win_end, max_retries=6):
    content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b}}
               for b in images_b64]
    content.append({"type": "text", "text": OCR_PROMPT.format(
        member_name=member, win_start=win_start, win_end=win_end)})
    last = None
    for attempt in range(max_retries):
        try:
            resp = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS, tools=[TXN_TOOL],
                                          tool_choice={"type": "tool", "name": "record_transactions"},
                                          messages=[{"role": "user", "content": content}])
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use" and block.name == "record_transactions":
                    return block.input.get("transactions", [])
            raise OcrError(f"aucun bloc tool_use (stop={resp.stop_reason})")
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            last = e
            status = getattr(e, "status_code", None)
            retriable = isinstance(e, (anthropic.RateLimitError, anthropic.APIConnectionError)) or status in (500, 502, 503, 529)
            if retriable and attempt < max_retries - 1:
                time.sleep(min(2 ** attempt, 45)); continue
            raise OcrError(f"API {type(e).__name__} {status}: {e}") from e
    raise OcrError(f"échec après {max_retries} tentatives : {last}")


def extract_report(uuid, member, disclosure, force=False):
    """Extraction Vision avec cache versionné (prompt_sha+model). Renvoie (transactions, cache_obj).

    `disclosure` (date de dépôt) borne la plage de dates plausibles passée au garde-fou du prompt :
    un PTR est déposé peu après la transaction → fenêtre [disclosure − 80 j, disclosure + 5 j]."""
    OCR_CACHE.mkdir(parents=True, exist_ok=True)
    cache_file = OCR_CACHE / f"{uuid}.json"
    if cache_file.exists() and not force:
        try:
            prev = json.loads(cache_file.read_text())
        except json.JSONDecodeError:
            prev = None
        if (isinstance(prev, dict) and prev.get("prompt_sha") == PROMPT_SHA
                and prev.get("model") == MODEL and prev.get("status") != "partial_error"):
            return prev["transactions"], prev

    disc = pd.Timestamp(disclosure)
    win_start = (disc - pd.Timedelta(days=80)).date().isoformat()
    win_end = (disc + pd.Timedelta(days=5)).date().isoformat()
    images = [_image_b64(u) for u in report_gif_urls(uuid)]
    client = anthropic.Anthropic(api_key=_api_key())
    batches = [images[i:i + MAX_IMG_PER_CALL] for i in range(0, len(images), MAX_IMG_PER_CALL)]
    all_txns, log, status = [], [], "ok"
    for bi, batch in enumerate(batches):
        try:
            txns = _call_vision(client, batch, member, win_start, win_end)
            all_txns.extend(txns)
            log.append({"batch": bi, "pages": len(batch), "status": "ok", "n": len(txns)})
        except OcrError as e:
            status = "partial_error"
            log.append({"batch": bi, "pages": len(batch), "status": "error", "error": str(e)[:200]})
        time.sleep(0.3)
    obj = {"doc_id": uuid, "member": member, "model": MODEL, "prompt_sha": PROMPT_SHA,
           "n_pages": len(images), "created_utc": pd.Timestamp.now("UTC").isoformat(),
           "status": "nothing_to_report" if status == "ok" and not all_txns else status,
           "batches": log, "transactions": all_txns}
    cache_file.write_text(json.dumps(obj, ensure_ascii=False, indent=2))
    return all_txns, obj


# --------------------------------------------------------------------------- normalisation
def _infer_asset_type(desc):
    d = str(desc).upper()
    if re.search(r"MUNICIPAL|\bMUNI\b|SCHOOL DIST|\bISD\b|TREASURY|T-?BILL|T-?NOTE|T-?BOND|GO BOND", d):
        return "Municipal Security"
    if re.search(r"\bBOND\b|\bNOTE\b|DEBENTURE|SR NT|\bNT\b", d):
        return "Corporate Bond"
    if re.search(r"\bLLC\b|\bL\.?P\.?\b|\bLP\b|PARTNERS|FUND|TRUST|HOLDINGS", d):
        return "Other"
    if re.search(r"COMMON|\bSTOCK\b|\bINC\b|CORP|\bCO\b|CLASS [A-Z]|\bPLC\b|\bNV\b|\bSA\b|\bADR\b", d):
        return "Stock"
    return None


def _fix_year(date_str, disclosure):
    """Filet déterministe : si la date lue tombe hors fenêtre PTR plausible, on corrige l'ANNÉE
    (le jour/mois lus sont fiables). Évite les millésimes aberrants (2023, 2027) sur scans abîmés."""
    if not date_str:
        return date_str
    d = pd.to_datetime(date_str, errors="coerce")
    if pd.isna(d):
        return date_str
    disc = pd.Timestamp(disclosure)
    lo, hi = disc - pd.Timedelta(days=90), disc + pd.Timedelta(days=10)
    if lo <= d <= hi:
        return d.date().isoformat()
    for y in (disc.year, disc.year - 1):
        try:
            cand = d.replace(year=y)
        except ValueError:
            continue
        if lo <= cand <= hi:
            return cand.date().isoformat()
    return d.date().isoformat()        # rien ne colle → on garde la lecture (visible en QA)


def normalize(txn, uuid, member, disclosure_date):
    code = (txn.get("amount_code") or "").upper()
    amount_range, amount_mid = AMOUNT_MAP.get(code, ("", None))
    desc = (txn.get("asset_description") or "").strip()
    # filet : retire un préfixe propriétaire résiduel « (S)/(SP)/(DC)/(J)/(JT) » oublié par le modèle
    m = re.match(r"^\(\s*(S|SP|DC|J|JT)\s*\)\s*(.*)$", desc, re.I)
    if m:
        desc = m.group(2).strip()
    tick = (txn.get("ticker") or "").strip().upper() or None
    return {
        "chamber": "senate", "declarant_name": member,
        "transaction_date": _fix_year(txn.get("transaction_date"), disclosure_date),
        "disclosure_date": disclosure_date,
        "ticker": tick, "asset_description": desc, "asset_type": _infer_asset_type(desc),
        "operation_type": txn.get("transaction_type", ""),
        "amount_range": amount_range, "amount_midpoint": amount_mid,
        "owner": OWNER_MAP.get(txn.get("owner", "Self"), "Self"),
        "doc_id": uuid, "source_url": EFD_PAPER.format(uuid=uuid),
        "provenance": "senate-efd-ocr",
    }


def _natural_key(r):
    raw = "|".join(str(r[c]) for c in ["chamber", "declarant_name", "transaction_date",
                                       "asset_description", "operation_type", "amount_range", "owner"])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main(force=False):
    if not _api_key():
        raise SystemExit("ANTHROPIC_API_KEY manquante (voir .env / .env.example)")
    print(f"=== OCR Sénat papier Q1 2025 — {len(PAPERS)} PTR (prompt_sha={PROMPT_SHA}) ===")

    rows, n_example, failures = [], 0, []
    for uuid, (member, disc) in PAPERS.items():
        txns, obj = extract_report(uuid, member, disc, force=force)
        kept = 0
        for t in txns:
            if EXAMPLE_RE.search(str(t.get("asset_description", ""))):
                n_example += 1
                continue
            rows.append(normalize(t, uuid, member, disc))
            kept += 1
        for b in obj.get("batches", []):
            if b.get("status") == "error":
                failures.append({"doc_id": uuid, "declarant_name": member, "batch": b["batch"],
                                 "reason": b.get("error", "")})
        print(f"  {uuid[:8]} {member:20} pages={obj['n_pages']:2} → {kept:3} txns "
              f"[{obj['status']}]")

    pd.DataFrame(failures, columns=["doc_id", "declarant_name", "batch", "reason"]).to_csv(
        TAB / "06c_ocr_failures.csv", index=False)

    df = pd.DataFrame(rows)
    if df.empty:
        print("Aucune transaction OCR.")
        return df
    print(f"  → {len(df)} transactions OCR ({n_example} ligne-exemple écartée, {len(failures)} échec batch)")

    # natural_key_hash + occurrence_index (lots répétés intra-rapport préservés)
    df["natural_key_hash"] = df.apply(_natural_key, axis=1)
    df["occurrence_index"] = df.groupby(["doc_id", "natural_key_hash"]).cumcount()
    df["amount_split_flag"] = False

    # ticker : symbole explicite imprimé, sinon « le nom EST un ticker », sinon none (titres privés)
    def _resolve(desc, tick):
        if tick:
            return tick, "explicit"
        rec = recover_ticker(desc)
        if rec:
            return rec, "asset_name"
        return None, "none"
    res = [_resolve(d, t) for d, t in zip(df["asset_description"], df["ticker"])]
    df["ticker"] = [r[0] for r in res]
    df["ticker_source"] = [r[1] for r in res]

    # identité (bioguide) via le matcher partagé du dossier
    ref, name_exact, name_by_last, current_bios, bio_to_committees, key_flag = load_reference()
    match = make_matcher(ref, name_exact, name_by_last, current_bios)
    df["bioguide_id"] = df["declarant_name"].map(match)
    df["party"] = df["bioguide_id"].map(lambda b: ref.get(b, {}).get("party"))
    df["state_district"] = df["bioguide_id"].map(lambda b: ref.get(b, {}).get("state"))
    df["committee_membership"] = df["bioguide_id"].map(
        lambda b: "; ".join(sorted(bio_to_committees.get(b, []))) if b else "")
    df["committees_key_flag"] = df["bioguide_id"].map(lambda b: bool(key_flag.get(b, False)))

    df = df.reindex(columns=SCHEMA)
    df.to_csv(TAB / "06b_senate_2025q1_ocr_transactions.csv", index=False)
    matched = df["bioguide_id"].notna().sum()
    print(f"  → 06b_senate_2025q1_ocr_transactions.csv : {len(df)} lignes | "
          f"identité {matched}/{len(df)} | ticker {int(df['ticker'].notna().sum())}/{len(df)} | "
          f"lots répétés {int((df['occurrence_index'] > 0).sum())}")
    return df


if __name__ == "__main__":
    import sys
    main(force="--force" in sys.argv)
