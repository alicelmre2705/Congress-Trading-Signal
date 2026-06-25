#!/usr/bin/env python
"""
OCR multi-années — PTR House SCANNÉS (non lisibles), backlog 2020→2026.

Porte la logique de Q1_2025/notebook_v1_house_2025q1_ocr.ipynb (Claude Vision `claude-sonnet-4-6`,
tool_use `record_transactions`, cache versionné par prompt_sha+model) et la généralise au backlog.
Réutilise house_multiyear pour le référentiel / match_bioguide / cache Quiver.

PDF scannés lus depuis data_v1/pdfs (embarqués). Cache OCR : data_v1/ocr_cache/{année}/{doc_id}.json (resumable).
Sorties : data_v1/tables/{année}/06b_house_{année}_ocr_transactions.csv + 06c_ocr_failures.csv
          + 06_house_{année}_FINAL.csv (digital + OCR) + 06d_ocr_quiver_comparison.csv
"""
import os, re, json, time, base64, hashlib, argparse
from io import BytesIO
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import pymupdf
import anthropic
from PIL import Image

import house_multiyear as hm   # référentiel, match_bioguide, resolve_pdf_path, fetch_quiver, TABROOT

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

MODEL = "claude-sonnet-4-6"
DPI = 200
MAX_IMG_PER_CALL = 3
MAX_TOKENS = 16_000
ROT_DETECT_DPI = 110    # basse résolution pour la pré-passe d'orientation (bon marché, suffisant)
# PDF traités en parallèle. Le palier API limite les OUTPUT tokens/min : Niveau 1 = 8K (throttle),
# Niveau 2 = 90K pour Sonnet 4.x → marge confortable. À 8 en parallèle on reste sous 90K/min ;
# les retries renforcés absorbent les 429 ponctuels. Monter encore si tu passes Niveau 3/4.
CONCURRENCY = 8

OCR_CACHE_ROOT = hm.OUTDIR / "ocr_cache"

# ── Politique de clusters OCR (cf. cross-validation Quiver du cluster C) ──────────────────────
# Le cluster C (manuscrit) est une CATÉGORIE CONSERVÉE (tracée au census + cache) mais NON EXÉCUTÉE
# par défaut : dates OCR manuscrites peu fiables, et la perte Quiver-corroborée — réelle — est
# ultra-concentrée. Cross-val : ~195-203 trades Quiver distincts (filers C) absents de notre digital
# (le brut 267 était gonflé ~25 % par les doublons natifs de Quiver), dont ~99 % sur 3 déposants
# quasi sans aucune trace digitale. 17/30 filers C = 0 trade Quiver (perte corroborée nulle).
# Donc : on n'exécute pas C en bloc, MAIS on récupère en ciblé les 3 filers à forte perte.
CLUSTERS_NON_EXECUTES = {"C_manuscrit"}
FILERS_C_A_RECUPERER = {"S001180", "L000564", "H001086"}  # Schrader, Lamborn, Harshbarger (≈99 % de la perte dure)

# ───────────────────────── Constantes OCR (port cellule 7) ─────────────────────────
AMOUNT_MAP = {
    "A": ("$1,001 - $15,000", 8_000.0), "B": ("$15,001 - $50,000", 32_500.0),
    "C": ("$50,001 - $100,000", 75_000.0), "D": ("$100,001 - $250,000", 175_000.0),
    "E": ("$250,001 - $500,000", 375_000.0), "F": ("$500,001 - $1,000,000", 750_000.0),
    "G": ("$1,000,001 - $5,000,000", 3_000_000.0), "H": ("$5,000,001 - $25,000,000", 15_000_000.0),
    "I": ("$25,000,001 - $50,000,000", 37_500_000.0), "J": ("Over $50,000,000", 75_000_000.0),
    "K": ("SP/DC over $1,000,000", 1_000_001.0),
}
OCR_PROMPT = """\
Tu lis les pages scannées d'un formulaire PTR (Periodic Transaction Report — US House of
Representatives) déposé par {member_name}. Reporte TOUTES les transactions financières en
appelant l'outil record_transactions.

STRUCTURE DU FORMULAIRE :
  Colonne propriétaire (gauche, étroite) : DC = Dependent Child | JT = Joint | SP = Spouse | vide = Self
  FULL ASSET NAME : nom complet de l'actif tel qu'écrit (n'invente pas de ticker)
  TYPE OF TRANSACTION (cases à cocher) : Purchase | Sale | Partial Sale | Exchange
  DATE OF TRANSACTION et DATE NOTIFIED OF TRANSACTION : format MM/DD/YY (deux dates distinctes par ligne)
  AMOUNT OF TRANSACTION (cases A–K, une seule cochée par ligne) :
    A=$1,001–15k  B=15k–50k  C=50k–100k  D=100k–250k  E=250k–500k  F=500k–1M
    G=1M–5M  H=5M–25M  I=25M–50M  J=>50M  K=SP/DC >1M

RÈGLES CRITIQUES :
  1. Le formulaire peut être scanné à 90° ou 180° — lis-le dans son orientation correcte.
  2. LIGNE D'EXEMPLE PRÉ-IMPRIMÉE — À IGNORER ABSOLUMENT. Chaque formulaire vierge contient une
     ligne modèle imprimée « Example: Mega Corp. Common Stock » (souvent accompagnée de la mention
     « Provide full name, not ticker symbol »). Ce N'EST JAMAIS une transaction : ne la reporte pas.
  3. « Nothing to report for <mois> » dans la colonne FULL ASSET NAME → aucune transaction sur cette page.
  4. Ignore les pages de couverture / certification sans table de transactions.
  5. Reporte CHAQUE ligne dont une case TYPE est cochée, Y COMPRIS des lignes strictement identiques
     répétées (même actif, même date, même montant, même propriétaire) : ce sont des transactions
     réelles distinctes, jamais des doublons à fusionner.
  6. DATES — GARDE-FOU : ce dépôt date de {filing_year}. L'année de TOUTE transaction doit être
     {filing_year} ou {prev_year} — quasi-certain. Toute autre année est une ERREUR de lecture
     (sur un formulaire tourné 90°, « 4 » ressemble à « 1 », « 3 » à « 8 »). Corrige vers
     {filing_year} ou {prev_year} selon le contexte.
     Convertis MM/DD/YY → YYYY-MM-DD. Lis transaction_date ET notification_date ligne par ligne.
  7. amount_code = UNIQUEMENT la lettre de la case cochée (A–K). Si illisible, omets le champ.
"""
TXN_TOOL = {
    "name": "record_transactions",
    "description": ("Enregistre la liste complète des transactions lues sur les pages fournies. "
                    "Tableau vide si aucune transaction (ex: page 'Nothing to report' ou page de couverture)."),
    "input_schema": {"type": "object", "properties": {"transactions": {"type": "array", "items": {
        "type": "object", "properties": {
            "asset_description": {"type": "string"},
            "transaction_type": {"type": "string", "enum": ["Purchase", "Sale", "Partial Sale", "Exchange"]},
            "transaction_date": {"type": ["string", "null"]},
            "notification_date": {"type": ["string", "null"]},
            "amount_code": {"type": "string", "enum": list("ABCDEFGHIJK")},
            "owner": {"type": "string", "enum": ["Self", "Spouse", "Joint", "Dependent Child"]},
        }, "required": ["asset_description", "transaction_type", "owner"], "additionalProperties": False}}},
        "required": ["transactions"]},
}
PROMPT_SHA = hashlib.sha256((OCR_PROMPT + json.dumps(TXN_TOOL, sort_keys=True)).encode()).hexdigest()[:12]

OWNER_MAP = {"Self": "SELF", "Spouse": "Spouse", "Joint": "Joint Tenancy", "Dependent Child": "Dependent Child"}
_EXAMPLE_RE = re.compile(r"example.*mega\s*corp|mega\s*corp.*common\s*stock", re.I)


# ───────────────────────── Passe LLM nom→ticker (port de 2025_test) ─────────────────────────
# Les lignes OCR sans ticker (ticker_source == "none") sont souvent de grandes valeurs cotées que
# l'électronique n'a jamais tradées (General Mills, MetLife, Colgate…) → le dict électronique plafonne
# (~46 %). On demande à Claude de mapper ces NOMS UNIQUES → ticker (null si non coté). Sortie structurée
# forcée + cache GLOBAL versionné (model + prompt_sha) → re-run sans changement = gratuit. Quiver non utilisé ici.
TICKER_LLM_CACHE = hm.OUTDIR / "ticker_llm_cache.json"
_TICKER_TOOL = {
    "name": "map_tickers",
    "description": "Renvoie le symbole boursier US (ticker) pour chaque nom de titre fourni.",
    "input_schema": {"type": "object", "properties": {"mappings": {"type": "array", "items": {
        "type": "object", "properties": {
            "name": {"type": "string", "description": "Le nom fourni, recopié à l'identique."},
            "ticker": {"type": ["string", "null"], "description": "Ticker US en MAJUSCULES (ex. GIS, MET, AAPL). null si ce n'est pas une action/ETF cotée US."},
            "is_equity": {"type": "boolean", "description": "true si action ordinaire ou ETF coté US."},
        }, "required": ["name", "ticker", "is_equity"]}}}, "required": ["mappings"]},
}
_TICKER_PROMPT = (
    "Tu reçois des noms de titres financiers issus de déclarations de transactions du Congrès US "
    "(formulaires PTR). Pour CHAQUE nom, donne le ticker boursier US s'il s'agit d'une action ordinaire "
    "ou d'un ETF coté aux États-Unis. Mets ticker=null si c'est une obligation, une option, un bon du "
    "Trésor, un fonds non coté, un titre privé, ou si tu n'es pas sûr. Ne devine jamais un ticker au "
    "hasard : dans le doute, null. Recopie 'name' à l'identique.\n\nNoms :\n{names}"
)
_TICKER_PROMPT_SHA = hashlib.sha256((_TICKER_PROMPT + json.dumps(_TICKER_TOOL, sort_keys=True) + MODEL).encode()).hexdigest()[:16]
_VALID_TICKER = re.compile(r"^[A-Z][A-Z.]{0,5}$")

def _load_ticker_cache():
    if TICKER_LLM_CACHE.exists():
        obj = json.loads(TICKER_LLM_CACHE.read_text(encoding="utf-8"))
        if obj.get("prompt_sha") == _TICKER_PROMPT_SHA and obj.get("model") == MODEL:
            return obj.get("mappings", {})
    return {}

def _save_ticker_cache(mappings):
    TICKER_LLM_CACHE.write_text(json.dumps(
        {"model": MODEL, "prompt_sha": _TICKER_PROMPT_SHA, "mappings": mappings},
        ensure_ascii=False, indent=1), encoding="utf-8")

def _map_tickers_batch(cli, names, max_retries=4):
    listing = "\n".join(f"- {n}" for n in names)
    last = None
    for attempt in range(max_retries):
        try:
            resp = cli.messages.create(model=MODEL, max_tokens=MAX_TOKENS, tools=[_TICKER_TOOL],
                                       tool_choice={"type": "tool", "name": "map_tickers"},
                                       messages=[{"role": "user", "content": _TICKER_PROMPT.format(names=listing)}])
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use" and block.name == "map_tickers":
                    return block.input.get("mappings", [])
            return []
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            last = e
            if attempt < max_retries - 1:
                time.sleep(min(2 ** attempt, 20)); continue
            raise
    raise RuntimeError(f"map_tickers échec : {last}")

def llm_resolve_tickers(df):
    """Remplit le ticker des lignes 'none' via la passe LLM (cache global versionné)."""
    if df.empty or "ticker_source" not in df.columns:
        return df
    missing = sorted(df.loc[df["ticker_source"].eq("none"), "asset_description"].dropna().unique())
    if not missing:
        return df
    cache = _load_ticker_cache()
    todo = [n for n in missing if n not in cache]
    if todo:
        cli = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        try:
            for i in range(0, len(todo), 60):
                batch = todo[i:i + 60]
                for m in _map_tickers_batch(cli, batch):
                    tk = (m.get("ticker") or "").upper().strip(".")
                    cache[m.get("name", "")] = tk if (m.get("is_equity") and _VALID_TICKER.match(tk)) else ""
                for n in batch:
                    cache.setdefault(n, "")
        except Exception as e:                          # ex. crédit API épuisé : on garde l'acquis, dégradation gracieuse
            print(f"  [passe LLM ticker interrompue : {type(e).__name__} — tickers dict conservés]")
        _save_ticker_cache(cache)
    fill = df["ticker_source"].eq("none") & df["asset_description"].map(lambda d: bool(cache.get(d, "")))
    df.loc[fill, "ticker"] = df.loc[fill, "asset_description"].map(lambda d: cache.get(d, ""))
    df.loc[fill, "ticker_source"] = "llm"
    return df


# ───────────────────────── Redressement des scans tournés (deskew) ─────────────────────────
# 525/547 scans sont couchés (census : rotated90/180/mixed) avec page.rotation=0 et canevas portrait
# → aucun signal métadonnée. On envoyait l'image COUCHÉE au modèle, d'où les confusions de chiffres de
# date (« 4 » lu « 1 » sur formulaire tourné). On détecte l'angle (pré-passe Vision bon marché) puis on
# redresse géométriquement AVANT l'extraction. Tesseract/cv2 indisponibles (venv autonome) → on s'appuie
# sur Vision + PIL, déjà embarqués.
ROT_CANDIDATES = [0, 90, 180, 270]   # angles horaires testés
# Demander au modèle « de combien tourner » est une tâche spatiale peu fiable (il répond ~toujours 90).
# On lui montre la MÊME page aux 4 rotations et on lui fait CHOISIR celle qui est droite — une tâche de
# reconnaissance, bien plus robuste. Le numéro choisi → l'angle horaire correspondant.
ROT_PROMPT = ("Ci-dessus la MÊME page scannée d'un formulaire « UNITED STATES HOUSE OF REPRESENTATIVES — "
              "Periodic Transaction Report », montrée à 4 rotations (Image 1 à 4). UNE SEULE est droite : "
              "le titre est horizontal en haut et tout le texte se lit de gauche à droite. Donne le NUMÉRO "
              "(1, 2, 3 ou 4) de l'image parfaitement à l'endroit. Réponds par un seul chiffre.")


def detect_rotation(client, img_b64, retries=4):
    """Pré-passe Vision robuste : montre la page (img_b64, basse DPI) aux 4 rotations et fait choisir au
    modèle celle qui est droite → renvoie l'angle horaire à appliquer. 0 par défaut (dégradation gracieuse
    si l'appel échoue) — ne lève jamais, pour ne pas casser un run OCR de 70 docs."""
    cands = [rotate_b64_png(img_b64, a) for a in ROT_CANDIDATES]
    content = []
    for i, c in enumerate(cands, 1):
        content.append({"type": "text", "text": f"Image {i} :"})
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": c}})
    content.append({"type": "text", "text": ROT_PROMPT})
    for a in range(retries):
        try:
            r = client.messages.create(model=MODEL, max_tokens=8,
                                       messages=[{"role": "user", "content": content}])
            txt = "".join(getattr(b, "text", "") for b in r.content)
            m = re.search(r"[1-4]", txt)
            return ROT_CANDIDATES[int(m.group()) - 1] if m else 0
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError):
            if a < retries - 1:
                time.sleep(min(2 ** a, 30)); continue
            return 0
    return 0


def rotate_b64_png(img_b64, angle):
    """Tourne une image PNG b64 de `angle` degrés HORAIRES (PIL.rotate est anti-horaire → -angle)."""
    if angle % 360 == 0:
        return img_b64
    im = Image.open(BytesIO(base64.b64decode(img_b64)))
    im = im.rotate(-angle, expand=True)
    buf = BytesIO(); im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ───────────────────────── Extraction Claude Vision (port cellule 9) ─────────────────────────
def pdf_to_b64_images(pdf_path, dpi=DPI, client=None, deskew=False):
    """Rend les pages en PNG b64. Si deskew + client : détecte et redresse CHAQUE page (montage
    4-rotations, basse DPI) — par page car les docs 'mixed' ont des pages d'orientations différentes.
    Renvoie (images, angles) si deskew, sinon images."""
    doc = pymupdf.open(pdf_path)
    out, angles = [], []
    for page in doc:
        full = base64.b64encode(page.get_pixmap(dpi=dpi).tobytes("png")).decode()
        if deskew and client is not None:
            low = base64.b64encode(page.get_pixmap(dpi=ROT_DETECT_DPI).tobytes("png")).decode()
            ang = detect_rotation(client, low)
            out.append(rotate_b64_png(full, ang)); angles.append(ang)
        else:
            out.append(full)
    doc.close()
    return (out, angles) if deskew else out

class OcrError(Exception):
    pass

def _call_vision_tool(client, images_b64, member_name, filing_year, max_retries=7):
    content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b}}
               for b in images_b64]
    content.append({"type": "text", "text": OCR_PROMPT.format(
        member_name=member_name, filing_year=filing_year, prev_year=filing_year - 1)})
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS, tools=[TXN_TOOL],
                                          tool_choice={"type": "tool", "name": "record_transactions"},
                                          messages=[{"role": "user", "content": content}])
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use" and block.name == "record_transactions":
                    return block.input.get("transactions", [])
            raise OcrError(f"aucun bloc tool_use (stop_reason={resp.stop_reason})")
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            last_err = e
            status = getattr(e, "status_code", None)
            retriable = isinstance(e, (anthropic.RateLimitError, anthropic.APIConnectionError)) or status in (500, 502, 503, 529)
            if retriable and attempt < max_retries - 1:
                time.sleep(min(2 ** attempt, 45)); continue
            raise OcrError(f"appel API échoué : {type(e).__name__} {status} {e}") from e
    raise OcrError(f"échec après {max_retries} tentatives : {last_err}")

def extract_from_pdf(pdf_path, doc_id, member_name, cache_dir, year, force=False):
    """Extraction avec cache versionné et REPRISE AU NIVEAU BATCH : un PDF partiellement traité ne
    re-paie QUE ses batches en erreur ; les batches déjà 'ok' (et leurs transactions) sont conservés."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{doc_id}.json"
    prev = None
    if cache_file.exists() and not force:
        try:
            prev = json.loads(cache_file.read_text())
        except json.JSONDecodeError:
            prev = None
        if isinstance(prev, dict) and prev.get("prompt_sha") == PROMPT_SHA and prev.get("model") == MODEL:
            if prev.get("status") != "partial_error":
                return prev["transactions"], prev          # complet → réutilisé tel quel (0 appel)
        else:
            prev = None                                     # cache incompatible → tout refaire

    images = pdf_to_b64_images(pdf_path)
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    batches = [images[i:i + MAX_IMG_PER_CALL] for i in range(0, len(images), MAX_IMG_PER_CALL)]

    # Reprise : garder les batches 'ok' du cache, ne refaire que les autres
    if prev and prev.get("status") == "partial_error" and prev.get("batches"):
        prev_log = {b["batch"]: b for b in prev["batches"]}
        kept_log = [b for b in prev["batches"] if b.get("status") == "ok"]
        # base de txns = union des batches ok (ancien format : top-level ; nouveau : par batch)
        if kept_log and all("transactions" in b for b in kept_log):
            all_txns = [t for b in kept_log for t in b["transactions"]]
        else:
            all_txns = list(prev.get("transactions", []))
        todo = [i for i in range(len(batches)) if prev_log.get(i, {}).get("status") != "ok"]
    else:
        kept_log, all_txns, todo = [], [], list(range(len(batches)))

    new_log, status = [], "ok"
    for n, idx in enumerate(todo):
        try:
            txns = _call_vision_tool(client, batches[idx], member_name, int(year))
            all_txns.extend(txns)
            new_log.append({"batch": idx, "pages": len(batches[idx]), "status": "ok", "n": len(txns), "transactions": txns})
        except OcrError as e:
            status = "partial_error"
            new_log.append({"batch": idx, "pages": len(batches[idx]), "status": "error", "error": str(e)[:200]})
        if n < len(todo) - 1:
            time.sleep(0.3)

    batch_log = sorted(kept_log + new_log, key=lambda b: b["batch"])
    if any(b.get("status") == "error" for b in batch_log):
        status = "partial_error"
    cache_obj = {"doc_id": doc_id, "member": member_name, "model": MODEL, "prompt_sha": PROMPT_SHA,
                 "dpi": DPI, "n_pages": len(images), "created_utc": pd.Timestamp.now("UTC").isoformat(),
                 "status": "nothing_to_report" if (status == "ok" and not all_txns) else status,
                 "batches": batch_log, "transactions": all_txns}
    cache_file.write_text(json.dumps(cache_obj, ensure_ascii=False, indent=2))
    return all_txns, cache_obj


# ───────────────────────── Normalisation + enrichissement (port cellules 16, 21) ─────────────
def natural_key_hash(row):
    key = "|".join(["house", str(row.get("declarant_name", "")), str(row.get("transaction_date", "")),
                    str(row.get("asset_description", "")), str(row.get("operation_type", "")),
                    str(row.get("amount_range", "")), str(row.get("owner", ""))])
    return hashlib.sha256(key.encode()).hexdigest()

# Fenêtre légale STOCK Act : un PTR se dépose dans les ~45 j suivant la transaction. On garde 75 j de
# marge (dépôts tardifs / amendements). Une transaction APRÈS le dépôt, ou > 75 j avant, est quasi
# certainement un misread d'année/mois → date aberrante. Indépendant de Quiver (survit en table finale).
DATE_WINDOW_DAYS = 75

def date_confidence(transaction_date, disclosure_date):
    """'plausible' | 'implausible' selon le délai légal dépôt-transaction. 'implausible' = date à jeter
    (n'attrape QUE les aberrations type confusion d'année ; les misreads jour/mois restent 'plausible')."""
    t = pd.to_datetime(transaction_date, errors="coerce")
    d = pd.to_datetime(disclosure_date, errors="coerce")
    if pd.isna(t) or pd.isna(d):
        return "implausible"
    lag = (d - t).days
    return "plausible" if 0 <= lag <= DATE_WINDOW_DAYS else "implausible"

def normalize(txn, meta, year):
    code = (txn.get("amount_code") or "").upper()
    amount_range, amount_mid = AMOUNT_MAP.get(code, ("", None))
    owner_raw = txn.get("owner") or "Self"
    disclosure = meta.get("disclosure_date", "") or txn.get("notification_date")
    r = {"bioguide_id": None, "declarant_name": meta["declarant_name"], "chamber": "house", "party": None,
         "state_district": meta.get("state_district", ""), "committee_membership": None, "committees_key_flag": None,
         "transaction_date": txn.get("transaction_date"),
         "disclosure_date": disclosure,
         "date_confidence": date_confidence(txn.get("transaction_date"), disclosure),
         "ticker": None, "asset_description": txn.get("asset_description", ""), "asset_type": None,
         "operation_type": txn.get("transaction_type", ""), "amount_range": amount_range,
         "amount_midpoint": amount_mid, "amount_split_flag": False,
         "owner": OWNER_MAP.get(owner_raw, "SELF"), "doc_id": meta["doc_id"],
         "source_url": meta.get("url_pdf", hm.HOUSE_PDF_URL.format(year=year, doc_id=meta["doc_id"])),
         "natural_key_hash": None, "provenance": "house-pdf-ocr"}
    r["natural_key_hash"] = natural_key_hash(r)
    return r

_SUFFIX_RE = re.compile(r"\b(CMN|COM|COMMON STOCK|COMMON|CLASS [A-Z]|CL [A-Z]|INCORPORATED|INC|CORPORATION|CORP|"
                        r"COMPANY|CO|HOLDINGS|HLDGS|LLC|L\.?P\.?|LTD|PLC|THE|SYS|SYSTEMS|SER|TR|TRUST|FUND|FUNDS|ETF)\b")
_EXPLICIT_TICKER_RE = re.compile(r"[-(]\s*([A-Z][A-Z0-9.]{0,5})\)?\s*$")
_OCR_FIX = {"METILIFE": "METLIFE", "ATT": "AT T"}

def _norm_asset(s):
    s = str(s).upper(); s = _EXPLICIT_TICKER_RE.sub("", s); s = re.sub(r"[^A-Z0-9 &]", " ", s)
    s = _SUFFIX_RE.sub(" ", s); s = re.sub(r"\s+", " ", s).strip()
    for bad, good in _OCR_FIX.items():
        s = re.sub(rf"\b{bad}\b", good, s)
    return s

def _explicit_ticker(desc):
    m = _EXPLICIT_TICKER_RE.search(str(desc))
    if not m:
        return None
    t = m.group(1).strip(".")
    return t if 1 <= len(t) <= 5 else None

def _infer_asset_type(desc):
    d = str(desc).upper()
    if re.search(r"TREASURY|T-?BILL|T-?BOND|T-?NOTE|GOVT|GOVERNMENT|MUNICIPAL|\bMUNI\b|\bISD\b|SCHOOL DIST", d): return "Gov Security"
    if re.search(r"LINKED TO|NOTES? LINKED|STRUCTURED|BASKET OF", d): return "Other"
    if re.search(r"\bETF\b|\bFUND\b|FUNDS|INDEX|SPDR|ISHARES|VANGUARD|AMPLIFY|GLOBAL X|SELECT SECTOR|\bTR\b|TRUST", d): return "Mutual Fund"
    if re.search(r"\bBOND\b|\bNOTE\b|DEBENTURE|\bBILL\b", d): return "Corporate Bond"
    if re.search(r"CMN|COM|COMMON|\bINC\b|CORP|CLASS|\bCO\b|HOLDINGS|\bLLC\b|\bLP\b|\bPLC\b|COMPANY", d): return "Stock"
    return None

SCHEMA_COLS = ["bioguide_id", "declarant_name", "chamber", "party", "state_district",
               "committee_membership", "committees_key_flag", "transaction_date", "disclosure_date",
               "date_confidence", "ticker", "asset_description", "asset_type", "operation_type", "amount_range",
               "amount_midpoint", "amount_split_flag", "owner", "doc_id", "source_url", "natural_key_hash"]


# ───────────────────────── Orchestration par année ─────────────────────────
def run_ocr_year(year, force=False):
    ydir = hm.TABROOT / str(year)
    man = pd.read_csv(ydir / "04_download_manifest.csv", dtype={"doc_id": str})
    ptr = pd.read_csv(ydir / "03_ptr_index.csv", dtype={"doc_id": str})
    scanned = man[man["bucket"] == "non_lisible"][["doc_id"]].merge(ptr, on="doc_id", how="left")
    # Le cluster C (CLUSTERS_NON_EXECUTES) est CONSERVÉ comme catégorie mais NON EXÉCUTÉ par défaut.
    # On garde une EXCEPTION : les docs des filers prioritaires (FILERS_C_A_RECUPERER) restent exécutés,
    # car ils portent ~99 % de la perte Quiver-corroborée (cf. cross-validation). Tout reste tracé au census.
    census_path = hm.TABROOT / "_scan_census_547.csv"
    if census_path.exists():
        cen = pd.read_csv(census_path, dtype={"doc_id": str})
        non_exec_ids = set(cen.loc[cen["cluster"].isin(CLUSTERS_NON_EXECUTES), "doc_id"])
        # exception : on n'exclut PAS les docs des filers à récupérer (résolus via le déclarant du PTR)
        if FILERS_C_A_RECUPERER and "last" in scanned.columns:
            hm.build_reference()
            keep = scanned["doc_id"].isin(non_exec_ids) & scanned.apply(
                lambda r: hm.match_bioguide(r.get("last", ""), r.get("first", "")) in FILERS_C_A_RECUPERER, axis=1)
            non_exec_ids -= set(scanned.loc[keep, "doc_id"])
        n_before = len(scanned)
        scanned = scanned[~scanned["doc_id"].isin(non_exec_ids)].reset_index(drop=True)
        if n_before != len(scanned):
            print(f"  Cluster C non exécuté : {n_before - len(scanned)} docs écartés (catégorie conservée au census)")
    cache_dir = OCR_CACHE_ROOT / str(year)
    print(f"\n===== OCR {year} : {len(scanned)} PDF scannés (A+B + filers C prioritaires) =====")
    if scanned.empty:
        return None

    meta_lookup = {r["doc_id"]: r.to_dict() for _, r in scanned.iterrows()}
    raw_results, failures = [], []

    def _work(doc_id, member):
        path = hm.resolve_pdf_path(year, doc_id)
        if path is None:
            return doc_id, member, [], {"status": "pdf_manquant", "batches": []}
        txns, cache_obj = extract_from_pdf(path, doc_id, member, cache_dir, year, force=force)
        return doc_id, member, txns, cache_obj

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(_work, r["doc_id"], r["declarant_name"]): r["doc_id"] for _, r in scanned.iterrows()}
        done = 0
        for fut in as_completed(futs):
            doc_id, member, txns, cache_obj = fut.result()
            done += 1
            raw_results.append({"doc_id": doc_id, "declarant_name": member, "transactions": txns})
            for bl in cache_obj.get("batches", []):
                if bl.get("status") == "error":
                    failures.append({"doc_id": doc_id, "declarant_name": member,
                                     "batch": bl["batch"], "reason": bl.get("error", "")})
            if cache_obj.get("status") == "pdf_manquant":
                failures.append({"doc_id": doc_id, "declarant_name": member, "batch": -1, "reason": "pdf_manquant"})
            if done % 20 == 0 or done == len(scanned):
                print(f"  {done}/{len(scanned)} PDF traités…")

    pd.DataFrame(failures, columns=["doc_id", "declarant_name", "batch", "reason"]).to_csv(
        ydir / "06c_ocr_failures.csv", index=False)

    # normalisation + filtre ligne-exemple
    rows, n_example = [], 0
    for entry in raw_results:
        meta = meta_lookup.get(entry["doc_id"], {"doc_id": entry["doc_id"], "declarant_name": entry["declarant_name"]})
        for txn in entry["transactions"]:
            if _EXAMPLE_RE.search(str(txn.get("asset_description", ""))):
                n_example += 1; continue
            rows.append(normalize(txn, meta, year))
    df = pd.DataFrame(rows)
    n_txn = len(df)
    print(f"  → {n_txn} transactions OCR ({n_example} ligne-exemple écartée) | {len(failures)} échec(s) batch")
    if df.empty:
        return {"year": year, "n_scanned": len(scanned), "n_ocr_txns": 0, "n_failures": len(failures)}

    # enrichissement ticker (dict du DIGITAL de l'année) + asset_type
    dig_path = ydir / f"06_house_{year}_transactions.csv"
    name_to_ticker = {}
    if dig_path.exists():
        elec = pd.read_csv(dig_path, dtype=str)
        elec_tk = elec[elec["ticker"].notna() & (elec["ticker"].str.strip() != "")].copy()
        elec_tk["norm"] = elec_tk["asset_description"].map(_norm_asset)
        name_to_ticker = (elec_tk[elec_tk["norm"] != ""].groupby("norm")["ticker"]
                          .agg(lambda s: s.str.upper().mode().iat[0]).to_dict())
    def _resolve(desc):
        t = _explicit_ticker(desc)
        if t: return t.upper(), "explicit"
        t = name_to_ticker.get(_norm_asset(desc))
        if t: return t, "elec_dict"
        return None, "none"
    res = df["asset_description"].map(_resolve)
    df["ticker"] = [r[0] for r in res]
    df["ticker_source"] = [r[1] for r in res]
    df["asset_type"] = df["asset_description"].map(_infer_asset_type)
    # passe LLM nom→ticker (récupère les cotées absentes du dict électronique : ~46 % → ~90 %)
    df = llm_resolve_tickers(df)

    # enrichissement bioguide / parti / commissions via match_bioguide
    df["bioguide_id"] = df["doc_id"].map(
        lambda d: hm.match_bioguide(meta_lookup[d].get("last", ""), meta_lookup[d].get("first", "")) if d in meta_lookup else None)
    df["party"] = df["bioguide_id"].map(lambda b: hm.ref_universe["party"].get(b) if b else None)
    df["committee_membership"] = df["bioguide_id"].map(
        lambda b: "; ".join(sorted(hm.bio_to_committees.get(b, []))) if b else None)
    df["committees_key_flag"] = df["bioguide_id"].map(
        lambda b: bool(hm.ref_house_key is not None and b in hm.ref_house_key.index) if b else None)

    out = df.reindex(columns=SCHEMA_COLS + ["ticker_source", "provenance"])
    out.to_csv(ydir / f"06b_house_{year}_ocr_transactions.csv", index=False)
    print(f"  → 06b_house_{year}_ocr_transactions.csv | ticker résolu {df['ticker'].notna().sum()}/{n_txn} | "
          f"déclarants {df['declarant_name'].nunique()}")

    # table FINALE digitale + OCR (dédup inter-sources uniquement)
    if dig_path.exists():
        dmain = pd.read_csv(dig_path, dtype={"doc_id": str}); dmain["provenance"] = "house-pdf-electronic"
        collide = out["natural_key_hash"].isin(set(dmain["natural_key_hash"].dropna()))
        comb = pd.concat([dmain, out[~collide]], ignore_index=True)
        comb.to_csv(ydir / f"06_house_{year}_FINAL.csv", index=False)
        print(f"  → 06_house_{year}_FINAL.csv : {len(comb)} lignes ({len(dmain)} digital + {int((~collide).sum())} OCR)")

    return {"year": year, "n_scanned": len(scanned), "n_ocr_txns": n_txn, "n_failures": len(failures),
            "n_declarants": int(df["declarant_name"].nunique())}


def validate_ocr_quiver(year):
    """OCR vs Quiver pour les déposants papier (clé : recouvrement et comptage par déclarant)."""
    ydir = hm.TABROOT / str(year)
    p = ydir / f"06b_house_{year}_ocr_transactions.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p, dtype={"doc_id": str})
    q = hm.fetch_quiver()
    if q is None or df.empty:
        return None
    q = q.copy(); q["_filed"] = pd.to_datetime(q["filed"], errors="coerce")
    q = q[(q["_filed"] >= pd.Timestamp(f"{year}-01-01")) & (q["_filed"] <= pd.Timestamp(f"{year}-12-31"))]
    cmp = (df.groupby("bioguide_id").agg(name=("declarant_name", "first"), docs=("doc_id", "nunique"),
                                         n_ocr=("doc_id", "count")).reset_index())
    cmp["n_quiver"] = cmp["bioguide_id"].map(q.groupby("BioGuideID").size()).fillna(0).astype(int)
    cmp["delta"] = cmp["n_ocr"] - cmp["n_quiver"]
    cmp["verdict"] = cmp.apply(lambda r: "quiver_sans_donnee" if r["n_quiver"] == 0
                               else ("ocr>=quiver" if r["delta"] >= 0
                                     else ("concordant" if abs(r["delta"]) <= max(5, 0.15 * r["n_quiver"]) else "ocr_souscompte")), axis=1)
    cmp = cmp.sort_values("n_ocr", ascending=False)
    cmp.to_csv(ydir / f"06d_ocr_quiver_comparison.csv", index=False)
    return dict(cmp["verdict"].value_counts())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2020")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-quiver", action="store_true")
    args = ap.parse_args()
    if not ANTHROPIC_API_KEY:
        raise SystemExit("ANTHROPIC_API_KEY manquante dans .env")
    print("Référentiel (match_bioguide)…")
    hm.build_reference()
    for y in [int(x) for x in args.years.split(",") if x.strip()]:
        s = run_ocr_year(y, force=args.force)
        if s and not args.no_quiver:
            v = validate_ocr_quiver(y)
            print(f"  Quiver (déposants papier) {y} : {v}")


if __name__ == "__main__":
    main()
