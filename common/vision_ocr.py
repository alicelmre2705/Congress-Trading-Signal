"""Moteur OCR Claude Vision — chambre-agnostique : rendu image, deskew, appel tool_use, cache versionné.

Le prompt et le tool sont passés PAR LE CALLER (chaque chambre possède ses octets exacts) → la
classe calcule `prompt_sha = sha256(prompt + json.dumps(tool, sort_keys=True) + pipeline_tag)[:12]`
EXACTEMENT comme les moteurs d'origine. Préserver ces octets = cache OCR valide (pas de re-OCR payant).
Porte house_ocr_multiyear (deskew + reprise au batch) et la version SHA1 de l'image (senat_ocr_multiyear,
pas la `senate_ocr._image_b64` à collision de basename).
"""
import io
import json
import time
import base64
import hashlib
from pathlib import Path

import pandas as pd


class OcrError(Exception):
    pass


# ───────────────────────── Rendu image + deskew (port house_ocr_multiyear) ────────────────────
ROT_CANDIDATES = [0, 90, 180, 270]
ROT_PROMPT = ("Ci-dessus la MÊME page scannée d'un formulaire « UNITED STATES HOUSE OF REPRESENTATIVES — "
              "Periodic Transaction Report », montrée à 4 rotations (Image 1 à 4). UNE SEULE est droite : "
              "le titre est horizontal en haut et tout le texte se lit de gauche à droite. Donne le NUMÉRO "
              "(1, 2, 3 ou 4) de l'image parfaitement à l'endroit. Réponds par un seul chiffre.")


def rotate_b64_png(img_b64, angle):
    """Tourne une image PNG b64 de `angle` degrés HORAIRES (PIL.rotate anti-horaire → -angle)."""
    from PIL import Image
    if angle % 360 == 0:
        return img_b64
    im = Image.open(io.BytesIO(base64.b64decode(img_b64)))
    im = im.rotate(-angle, expand=True)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def detect_rotation(client, img_b64, model, retries=4):
    """Pré-passe Vision : montre la page aux 4 rotations, fait CHOISIR la droite → angle horaire.
    Ne lève jamais (0 par défaut) pour ne pas casser un run. Port de house_ocr_multiyear.detect_rotation."""
    import anthropic
    import re
    cands = [rotate_b64_png(img_b64, a) for a in ROT_CANDIDATES]
    content = []
    for i, c in enumerate(cands, 1):
        content.append({"type": "text", "text": f"Image {i} :"})
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": c}})
    content.append({"type": "text", "text": ROT_PROMPT})
    for a in range(retries):
        try:
            r = client.messages.create(model=model, max_tokens=8,
                                       messages=[{"role": "user", "content": content}])
            txt = "".join(getattr(b, "text", "") for b in r.content)
            m = re.search(r"[1-4]", txt)
            return ROT_CANDIDATES[int(m.group()) - 1] if m else 0
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError):
            if a < retries - 1:
                time.sleep(min(2 ** a, 30))
                continue
            return 0
    return 0


def pdf_to_b64_images(pdf_path, dpi=200, client=None, model=None, deskew=False, rot_detect_dpi=110):
    """Rend les pages PNG b64. Si deskew : détecte+redresse chaque page (docs 'mixed'). Port verbatim."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    out, angles = [], []
    for page in doc:
        full = base64.b64encode(page.get_pixmap(dpi=dpi).tobytes("png")).decode()
        if deskew and client is not None:
            low = base64.b64encode(page.get_pixmap(dpi=rot_detect_dpi).tobytes("png")).decode()
            ang = detect_rotation(client, low, model)
            out.append(rotate_b64_png(full, ang))
            angles.append(ang)
        else:
            out.append(full)
    doc.close()
    return (out, angles) if deskew else out


def image_b64_from_url(url, media_dir, long_edge=1568):
    """Récupère une image (cache disque clé = SHA1 de l'URL → pas de collision de basename), la
    redimensionne ≤ long_edge, renvoie PNG b64. Version SÛRE (senat_ocr_multiyear._image_b64_safe)."""
    import requests
    from PIL import Image
    media_dir = Path(media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    cache = media_dir / (hashlib.sha1(url.encode()).hexdigest() + ".gif")
    if cache.exists():
        data = cache.read_bytes()
    else:
        r = requests.get(url, headers={"User-Agent": "congress-trading-research/1.0 (poli, sans evasion)"},
                         timeout=60)
        r.raise_for_status()
        data = r.content
        cache.write_bytes(data)
    img = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = img.size
    if max(w, h) > long_edge:
        s = long_edge / max(w, h)
        img = img.resize((round(w * s), round(h * s)))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ───────────────────────── Extracteur Vision versionné (port _call_vision_tool + extract_from_pdf) ──
class VisionExtractor:
    """Appel `record_transactions` (tool_use forcé) + cache versionné par (prompt_sha, model) avec
    REPRISE au batch. `prompt`/`tool`/`pipeline_tag` viennent du caller (octets exacts par chambre)."""

    def __init__(self, model, prompt, tool, pipeline_tag="", max_tokens=16_000, max_img_per_call=3):
        self.model = model
        self.prompt = prompt
        self.tool = tool
        self.pipeline_tag = pipeline_tag
        self.max_tokens = max_tokens
        self.max_img_per_call = max_img_per_call

    @property
    def prompt_sha(self):
        return hashlib.sha256(
            (self.prompt + json.dumps(self.tool, sort_keys=True) + self.pipeline_tag).encode()
        ).hexdigest()[:12]

    def _call(self, client, images_b64, fmt, max_retries=7):
        import anthropic
        content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b}}
                   for b in images_b64]
        content.append({"type": "text", "text": self.prompt.format(**fmt)})
        last = None
        for attempt in range(max_retries):
            try:
                resp = client.messages.create(
                    model=self.model, max_tokens=self.max_tokens, tools=[self.tool],
                    tool_choice={"type": "tool", "name": self.tool["name"]},
                    messages=[{"role": "user", "content": content}])
                for block in resp.content:
                    if getattr(block, "type", None) == "tool_use" and block.name == self.tool["name"]:
                        return block.input.get("transactions", [])
                raise OcrError(f"aucun bloc tool_use (stop={resp.stop_reason})")
            except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
                last = e
                status = getattr(e, "status_code", None)
                retriable = isinstance(e, (anthropic.RateLimitError, anthropic.APIConnectionError)) or status in (500, 502, 503, 529)
                if retriable and attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 45))
                    continue
                raise OcrError(f"API {type(e).__name__} {status}: {e}") from e
        raise OcrError(f"échec après {max_retries} tentatives : {last}")

    def extract_cached(self, images, doc_id, cache_dir, fmt, member="", dpi=None, force=False):
        """Cache versionné + reprise au batch (un PDF partiel ne re-paie que ses batches KO). `images`
        = liste de PNG b64 déjà rendus (deskew appliqué en amont). Port de extract_from_pdf."""
        import anthropic
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{doc_id}.json"
        prev = None
        if cache_file.exists() and not force:
            try:
                prev = json.loads(cache_file.read_text())
            except json.JSONDecodeError:
                prev = None
            if isinstance(prev, dict) and prev.get("prompt_sha") == self.prompt_sha and prev.get("model") == self.model:
                if prev.get("status") != "partial_error":
                    return prev["transactions"], prev
            else:
                prev = None

        client = anthropic.Anthropic()
        batches = [images[i:i + self.max_img_per_call] for i in range(0, len(images), self.max_img_per_call)]
        if prev and prev.get("status") == "partial_error" and prev.get("batches"):
            prev_log = {b["batch"]: b for b in prev["batches"]}
            kept_log = [b for b in prev["batches"] if b.get("status") == "ok"]
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
                txns = self._call(client, batches[idx], fmt)
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
        obj = {"doc_id": doc_id, "member": member, "model": self.model, "prompt_sha": self.prompt_sha,
               "dpi": dpi, "n_pages": len(images), "created_utc": pd.Timestamp.now("UTC").isoformat(),
               "status": "nothing_to_report" if (status == "ok" and not all_txns) else status,
               "batches": batch_log, "transactions": all_txns}
        cache_file.write_text(json.dumps(obj, ensure_ascii=False, indent=2))
        return all_txns, obj
