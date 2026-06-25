#!/usr/bin/env python
"""
Pipeline House — piste DIGITALE multi-années (PDF lisibles uniquement).

- Dossier AUTONOME : PDF scannés, index, YAML, baseline et cache Quiver embarqués dans data_v1/
  (aucune dépendance externe, aucun re-téléchargement).
- OCR DIFFÉRÉ ici : les PDF scannés (sans texte) sont traités par house_ocr_multiyear.py /
  notebook_ocr.ipynb ; ce module ne fait que la piste digitale + l'inventaire backlog.
- Quiver = vérification externe UNIQUEMENT (jamais réinjecté).
- `disclosure_date` = FilingDate de l'index XML (anti look-ahead). Axe « année » = année de divulgation.

La logique de parsing est portée fidèlement depuis notebook_v1_house_2025q1.ipynb (piste digitale).
Ce module sert de moteur de validation ; il est ensuite matérialisé en notebook transparent.
"""
import io, re, os, sys, json, time, hashlib, argparse, unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict, Counter

import requests
import pandas as pd
import pdfplumber

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*a, **k):
        return False

# ───────────────────────── Chemins & constantes (DOSSIER AUTONOME) ─────────────────────────
# Ancrage par marqueur : BASE_DIR = le dossier qui contient data_v1/ (peu importe d'où on lance).
# Aucune dépendance à 'semaine 1' : PDF/index/YAML/baseline/Quiver sont embarqués dans data_v1/.
HERE = Path(__file__).resolve().parent           # <repo>/house
REPO = HERE.parent                                # racine du dépôt
OUTDIR = REPO / "data" / "house"                  # données (Phase 7 : data/house/)
BASE_DIR = OUTDIR
load_dotenv(REPO / ".env")
if not os.getenv("ANTHROPIC_API_KEY"):
    load_dotenv()  # repli : .env ailleurs dans l'arbre
TABROOT = OUTDIR / "tables"
TABROOT.mkdir(parents=True, exist_ok=True)

# Données embarquées localement
PDF_DIR   = OUTDIR / "pdfs"                              # 547 PDF scannés (pour le run OCR)
INDEX_DIR = OUTDIR / "index"                            # {year}FD.xml
REF_DIR   = OUTDIR / "reference"                        # YAML législateurs/comités (+ baseline)
BASELINE  = REF_DIR / "baseline_house_transactions.csv" # cross-check semaine1 (optionnel)
# Alias rétro-compatibles (le reste du module et les notebooks les réutilisent tels quels)
SEM1_PDF, SEM1_INDEX, SEM1_PARSE, SEM1_REF = PDF_DIR, INDEX_DIR, BASELINE, REF_DIR
HOUSE_DIR = BASE_DIR

HOUSE_PDF_URL = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc_id}.pdf"
LEG_CURRENT    = "https://unitedstates.github.io/congress-legislators/legislators-current.json"
LEG_HISTORICAL = "https://unitedstates.github.io/congress-legislators/legislators-historical.json"
COMMITTEES     = "https://unitedstates.github.io/congress-legislators/committees-current.json"
COMMITTEE_MEMBERSHIP = "https://unitedstates.github.io/congress-legislators/committee-membership-current.json"
QUIVER_URL = "https://api.quiverquant.com/beta/bulk/congresstrading"

HEADERS = {"User-Agent": "congress-trading-research/1.0 (poli, sans evasion)"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

KEY_COMMITTEES = ["Financial Services", "Armed Services", "Intelligence"]

# Globaux peuplés par build_reference (comme dans le notebook)
ref_universe = None
name_exact = {}
name_by_last = defaultdict(list)
bio_to_committees = defaultdict(set)
ref_house_key = None


# ───────────────────────── Normalisation noms ─────────────────────────
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))

def norm(s: str) -> str:
    s = strip_accents(s or "").lower()
    s = re.sub(r"[^a-z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ───────────────────────── Référentiel identité ─────────────────────────
def _load_people():
    """current + historical. Live d'abord ; repli sur les YAML embarqués (data_v1/reference)."""
    try:
        cur = SESSION.get(LEG_CURRENT, timeout=30).json()
        try:
            hist = SESSION.get(LEG_HISTORICAL, timeout=60).json()
        except Exception:
            hist = []
        return cur, hist, "live"
    except Exception as e:
        import yaml
        cur = yaml.safe_load(open(SEM1_REF / "legislators-current.yaml"))
        try:
            hist = yaml.safe_load(open(SEM1_REF / "legislators-historical.yaml"))
        except Exception:
            hist = []
        return cur, hist, f"local-yaml ({e})"

def _load_committees():
    try:
        committees = SESSION.get(COMMITTEES, timeout=30).json()
        membership = SESSION.get(COMMITTEE_MEMBERSHIP, timeout=30).json()
        return committees, membership
    except Exception:
        import yaml
        committees = yaml.safe_load(open(SEM1_REF / "committees-current.yaml"))
        membership = yaml.safe_load(open(SEM1_REF / "committee-membership-current.yaml"))
        return committees, membership

def _last_term_key(p):
    terms = p.get("terms") or [{}]
    end = (terms[-1] if terms else {}).get("end", "")
    if not end:
        return -9999
    try:
        return -int(str(end)[:4])
    except ValueError:
        return 0

def build_reference():
    global ref_universe, name_exact, name_by_last, bio_to_committees, ref_house_key
    cur, hist, src = _load_people()
    people = sorted(cur + hist, key=_last_term_key)

    ref_rows = []
    name_exact = {}
    name_by_last = defaultdict(list)
    for p in people:
        bio = p.get("id", {}).get("bioguide")
        if not bio:
            continue
        nm = p.get("name", {})
        last, first = nm.get("last", ""), nm.get("first", "")
        nick, mid = nm.get("nickname", ""), nm.get("middle", "")
        full = nm.get("official_full") or f"{first} {last}".strip()
        last_term = (p.get("terms") or [{}])[-1]
        chamber = "house" if last_term.get("type") == "rep" else "senate"
        ref_rows.append({
            "bioguide_id": bio, "declarant_name": full, "last": last, "first": first,
            "party": last_term.get("party"), "chamber": chamber,
            "state": last_term.get("state"), "district": last_term.get("district"),
        })
        name_exact.setdefault((norm(last), norm(first)), bio)
        if nick:
            name_exact.setdefault((norm(last), norm(nick)), bio)
        if mid:
            name_exact.setdefault((norm(last), norm(mid)), bio)
        full_first = full.split()[0] if full.split() else ""
        if full_first and norm(full_first) != norm(first):
            name_exact.setdefault((norm(last), norm(full_first)), bio)
        name_by_last[norm(last)].append(bio)
        if " " in last:
            lw = last.split()[-1]
            name_exact.setdefault((norm(lw), norm(first)), bio)
            if mid:
                name_exact.setdefault((norm(lw), norm(mid)), bio)
            if full_first and norm(full_first) != norm(first):
                name_exact.setdefault((norm(lw), norm(full_first)), bio)
            name_by_last[norm(lw)].append(bio)

    ref_universe = pd.DataFrame(ref_rows).drop_duplicates("bioguide_id").set_index("bioguide_id")

    committees, membership = _load_committees()
    code_to_name = {c["thomas_id"]: c["name"] for c in committees if "thomas_id" in c}
    bio_to_committees = defaultdict(set)
    for code, members in membership.items():
        cname = code_to_name.get(code, code)
        for mem in members:
            if mem.get("bioguide"):
                bio_to_committees[mem["bioguide"]].add(cname)

    def committee_category(bio):
        cs = bio_to_committees.get(bio, set())
        for key in KEY_COMMITTEES:
            if any(key in cn for cn in cs):
                return key
        return None

    ref_house = ref_universe[ref_universe["chamber"] == "house"].copy()
    ref_house["committee_category"] = [committee_category(b) for b in ref_house.index]
    ref_house_key = ref_house[ref_house["committee_category"].notna()].copy()
    print(f"  référentiel : {len(ref_universe)} législateurs (source: {src}) | "
          f"House commission clé : {len(ref_house_key)}")


# ───────────────────────── Patterns de parsing (port cellule 16) ─────────────────────────
TXN_RE = re.compile(
    r'(?P<type>\bP|\bS|\bE)(?:\s*\((?P<sub>partial|full)\))?\s+'
    r'(?P<txn>\d{1,2}/\d{1,2}/\d{4})\s+'
    r'(?P<notif>\d{1,2}/\d{1,2}/\d{4})\s+'
    r'(?P<amount>\$[\d,]+\s*-\s*\$[\d,]+|Over\s+\$[\d,]+|\$[\d,]+\+?)',
    re.IGNORECASE)
SKIP_RE = re.compile(
    r'^\s*(F\s|S\s+O:|S\s+S:|F\s+S:|F\s+O:|L:|D:|C:|G:|Filing ID|\*\s*For|I CERTIFY|'
    r'Digitally|ID\s+Owner|Transaction|Type$|Date|Notification|Amount|Cap\.|Gains|\$200|'
    r'Name:|Status:|State/District:|P\s*T\s*R|Clerk of|I\s*V\s*D|I\s*P\s*O|Yes\s+No|'
    # lignes d'annotation des PDF pré-2021 (rendues en casse mixte) à exclure des descriptions
    r'Filing\s*Status|Subholding|Description\s*:|Location\s*:|Asset\s*Class|Initial\s*Public|'
    r'Certification|nmlk|For the complete|'
    r'C\s+S|^T$|^F$|^F I$|Putnam)', re.IGNORECASE)
NOTE_CONT_RE  = re.compile(r'(shares|/share|@\s*\$|sold @)', re.IGNORECASE)
# Tolérant à la casse : les PDF pré-2021 ont un encodage de police qui rend des majuscules
# en minuscules (ex. [sT] au lieu de [ST], (aos) au lieu de (AOS)).
TICKER_RE     = re.compile(r'\(([A-Za-z][A-Za-z0-9.\-]{0,5})\)')
EXCH_TICKER_RE= re.compile(r'(?:NYSE|NASDAQ|NYSEARCA|BATS|AMEX|CBOE)[:\s]+([A-Za-z]{1,5})\b', re.IGNORECASE)
ATYPE_RE      = re.compile(r'\[([A-Za-z]{2})\]')
_SUB_WORDS    = {"full", "partial"}  # éviter de prendre "(full)" pour un ticker
OWNER_RE      = re.compile(r'^(JT|SP|DC)\s+', re.IGNORECASE)
_SPLIT_AMOUNT_RE = re.compile(r'\$[\d,]+\s*-\s*$')
ATYPE_NAMES = {"ST": "Stock", "OP": "Option", "OT": "Other", "MF": "Mutual Fund",
               "GS": "Gov Security", "CO": "Corp Bond", "PE": "Private Equity",
               "OI": "Other Investment"}


# ───────────────────────── Prétraitement lignes (port cellule 18) ─────────────────────────
def _find_continuation(line):
    at_m = ATYPE_RE.search(line)
    if at_m:
        amt_m = re.search(r'\$[\d,]+', line[at_m.end():])
        if amt_m:
            pre_atype = line[:at_m.start()].strip()
            m_dash = re.match(r'^-\s*([A-Z]{2,5})$', pre_atype)
            if m_dash:
                pre_atype = f'({m_dash.group(1)})'
            return at_m.group(0), amt_m.group(0), pre_atype
    return None, None, ''

def _join_split_lines(lines):
    result, i = [], 0
    while i < len(lines):
        line = lines[i]
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
        next_next = lines[i + 2].strip() if i + 2 < len(lines) else ""
        m_txn = TXN_RE.search(line)
        m_split = _SPLIT_AMOUNT_RE.search(line.rstrip())
        if m_txn and m_split and next_line:
            asset_code, second_amount, pre_atype = _find_continuation(next_line)
            if asset_code and second_amount:
                pos = m_txn.start()
                pre = (' ' + pre_atype) if pre_atype else ''
                joined = (line[:pos].rstrip() + pre + ' ' + asset_code + ' ' +
                          line[pos:].rstrip() + ' ' + second_amount)
                result.append(joined); i += 2; continue
            if next_next and not TXN_RE.search(next_next) and not SKIP_RE.match(next_next):
                at_m2 = ATYPE_RE.search(next_next)
                if at_m2:
                    amt_m2 = re.search(r'\$[\d,]+', next_line)
                    if amt_m2:
                        pos = m_txn.start()
                        pre_text = re.sub(r'\$[\d,]+', '', next_line).strip()
                        joined = (line[:pos].rstrip() + ' ' + pre_text + ' ' +
                                  next_next.strip() + ' ' +
                                  line[pos:].rstrip() + ' ' + amt_m2.group(0))
                        result.append(joined); i += 3; continue
        result.append(line); i += 1
    return result

def _amount_midpoint(a):
    nums = [int(x.replace(',', '')) for x in re.findall(r'\$([\d,]+)', a)]
    if len(nums) >= 2: return (nums[0] + nums[1]) / 2
    if len(nums) == 1: return float(nums[0])
    return None

def _op_type(t, sub):
    t, sub = t.upper(), (sub or '').lower()
    if t == 'P': return 'Purchase'
    if t == 'E': return 'Exchange'
    if sub == 'partial': return 'Sale (Partial)'
    if sub == 'full':    return 'Sale (Full)'
    return 'Sale'

def _is_txn_start(s):
    m = TXN_RE.search(s)
    return bool(m) and (m.start() == 0 or bool(ATYPE_RE.search(s[:m.start()])))


# ───────────────────────── parse_ptr (port cellule 20) ─────────────────────────
def parse_ptr(text):
    text = text.replace('\x00', '')
    lines = [l.rstrip() for l in text.splitlines()]
    lines = _join_split_lines(lines)
    out = []
    for i, line in enumerate(lines):
        m = TXN_RE.search(line)
        if not m:
            continue
        if m.start() == 0 or ATYPE_RE.search(line[:m.start()]):
            extra_atype = None
        else:
            extra_atype = None
            signal = False
            for j in range(i + 1, min(i + 6, len(lines))):
                lj = lines[j]
                if SKIP_RE.match(lj) or TXN_RE.search(lj):
                    break
                if ATYPE_RE.search(lj):
                    extra_atype = lj; signal = True; break
                # actifs SANS code [XX] (MLP, "Limited Partner Interests") : un ticker en
                # continuation suffit à confirmer la transaction (sinon on les sautait à tort)
                if TICKER_RE.search(lj):
                    extra_atype = lj; signal = True; break
            if not signal:
                continue
        prefix = line[:m.start()].strip()
        block, k = [], i - 1
        while k >= 0 and len(block) < 4:
            prev = lines[k]
            if not prev.strip(): k -= 1; continue
            if _is_txn_start(prev) or SKIP_RE.match(prev) or NOTE_CONT_RE.search(prev): break
            block.insert(0, prev.strip()); k -= 1
        if prefix:      block.append(prefix)
        if extra_atype: block.append(extra_atype.strip())
        blk = " ".join(block)
        # ticker : ignorer les faux positifs "(partial)"/"(full)"
        tk_val = None
        for mt in TICKER_RE.finditer(blk):
            if mt.group(1).lower() not in _SUB_WORDS:
                tk_val = mt.group(1).upper(); break
        if tk_val is None:
            me = EXCH_TICKER_RE.search(blk)
            tk_val = me.group(1).upper() if me else None
        at = ATYPE_RE.search(blk)
        at_code = at.group(1).upper() if at else None
        owner_m = OWNER_RE.match(blk)
        owner_val = owner_m.group(1).upper() if owner_m else None
        if owner_m: blk = blk[owner_m.end():]
        desc = ATYPE_RE.sub("", TICKER_RE.sub("", blk)).strip(" -")
        amount_str = m.group("amount").strip()
        out.append({
            "ticker": tk_val,
            "asset_type": ATYPE_NAMES.get(at_code, at_code) if at_code else None,
            "asset_description": desc,
            "operation_type": _op_type(m.group("type"), m.group("sub")),
            "transaction_date": m.group("txn"),
            "amount_range": amount_str,
            "amount_midpoint": _amount_midpoint(amount_str),
            "amount_split_flag": bool(_SPLIT_AMOUNT_RE.search(amount_str)),
            "owner": owner_val,
        })
    return out


# ───────────────────────── match_bioguide (port cellule 25) ─────────────────────────
_TITLE_RE = re.compile(r'\b(dr|hon|rev|gen|col)\b\.?\s*', re.IGNORECASE)
_NICKNAMES = {
    "richard": "rick", "william": "bill", "james": "jim", "robert": "bob",
    "michael": "mike", "joseph": "joe", "thomas": "tom", "charles": "chuck",
    "edward": "ed", "daniel": "dan", "donald": "don", "timothy": "tim",
    "christopher": "chris", "steven": "steve", "stephen": "steve", "benjamin": "ben",
    "kenneth": "ken", "anthony": "tony", "matthew": "matt", "gregory": "greg",
    "gerald": "jerry", "lawrence": "larry", "patrick": "pat", "samuel": "sam",
    "alexander": "alex", "andrew": "andy", "nathaniel": "nate", "theodore": "ted",
    "jacob": "jake", "jonathan": "jon", "elizabeth": "lizzie",
}
# suffixes honorifiques/générationnels à retirer du nom de famille
_SUFFIX_TOKENS = {"jr", "sr", "ii", "iii", "iv", "md", "dds", "phd", "facs", "do", "esq", "mr", "mrs", "ms"}
# irréductibles : déposants dont le nom de dépôt ne se relie pas au référentiel par règle
_MANUAL_BIO = {("taylor", "nicholas"): "T000479"}  # "Nicholas V. Taylor" = Van Taylor

def match_bioguide(last, first):
    first_clean = re.sub(r'\s+', ' ', _TITLE_RE.sub(' ', first or "")).strip()
    # mots du nom de famille, ponctuation retirée, suffixes honorifiques exclus
    raw = re.sub(r'[.,]', ' ', (last or "")).split()
    last_words = [w for w in raw if norm(w) and norm(w) not in _SUFFIX_TOKENS]
    # candidats de nom : CHAQUE mot du nom composé + le nom complet nettoyé
    last_cands = []
    for w in last_words + ([" ".join(last_words)] if len(last_words) > 1 else []):
        ln = norm(w)
        if ln and ln not in last_cands:
            last_cands.append(ln)
    # override manuel (clé = mot de nom + 1er prénom)
    fn0 = norm(first_clean.split()[0]) if first_clean.split() else ""
    for lw in last_cands:
        if (lw, fn0) in _MANUAL_BIO:
            return _MANUAL_BIO[(lw, fn0)]
    seen, keys = set(), []
    for l_n in last_cands:
        for f_str in ([first_clean] + (first_clean.split() if ' ' in first_clean else [])):
            f_n = norm(f_str)
            nick = _NICKNAMES.get(f_n)
            for candidate in ([nick] if nick else []) + [f_n]:
                k = (l_n, candidate)
                if k not in seen:
                    seen.add(k); keys.append(k)
    for k in keys:
        if k in name_exact:
            return name_exact[k]
    # dernier recours : un mot de nom unique au référentiel
    for lw in last_cands:
        cands = name_by_last.get(lw, [])
        if len(cands) == 1:
            return cands[0]
    return None


# ───────────────────────── Index + manifeste par année ─────────────────────────
def load_ptr_index(year, win_start, win_end):
    """Lit l'index XML embarqué (data_v1/index), filtre FilingType=P + fenêtre disclosure."""
    xml_path = SEM1_INDEX / f"{year}FD.xml"
    root = ET.fromstring(xml_path.read_bytes())
    members = root.findall("Member") or list(root)
    rows = []
    for m in members:
        g = lambda t: (m.findtext(t) or "").strip()
        rows.append({"doc_id": g("DocID"), "last": g("Last"), "first": g("First"),
                     "filing_type": g("FilingType"), "state_district": g("StateDst"),
                     "filing_date_raw": g("FilingDate")})
    idx = pd.DataFrame(rows)
    idx["disclosure_date"] = pd.to_datetime(idx["filing_date_raw"], errors="coerce")
    idx["declarant_name"] = (idx["first"] + " " + idx["last"]).str.strip()
    ft_dist = dict(Counter(idx["filing_type"]))
    ptr = idx[(idx["filing_type"] == "P") &
              (idx["disclosure_date"] >= win_start) &
              (idx["disclosure_date"] <= win_end)].copy()
    ptr["url_pdf"] = ptr["doc_id"].apply(lambda d: HOUSE_PDF_URL.format(year=year, doc_id=d))
    return ptr, ft_dist


def resolve_pdf_path(year, doc_id):
    p = SEM1_PDF / str(year) / f"{doc_id}.pdf"
    return p if p.exists() else None

def extract_text(path):
    try:
        with pdfplumber.open(str(path)) as pdf:
            return "\n".join((pg.extract_text() or "") for pg in pdf.pages)
    except Exception:
        return ""

def n_pages(path):
    try:
        with pdfplumber.open(str(path)) as pdf:
            return len(pdf.pages)
    except Exception:
        return None

def build_manifest(year, ptr_index, ydir):
    """Lit les PDF embarqués (data_v1/pdfs) EN PLACE, extrait le texte, route lisible/non_lisible.
    Aucun déplacement de fichier (suppression du .rename() destructif de v1)."""
    doc_texts, rows = {}, []
    for _, r in ptr_index.iterrows():
        doc_id = r["doc_id"]
        path = resolve_pdf_path(year, doc_id)
        if path is None:
            doc_texts[doc_id] = ""
            rows.append({"doc_id": doc_id, "url": r["url_pdf"], "status": "missing",
                         "has_text": False, "bucket": "absent", "doc_prefix": str(doc_id)[:1]})
            continue
        text = extract_text(path).replace("\x00", "")
        has = bool(text.strip())
        doc_texts[doc_id] = text
        rows.append({"doc_id": doc_id, "url": r["url_pdf"], "status": "ok",
                     "has_text": has, "bucket": "lisible" if has else "non_lisible",
                     "doc_prefix": str(doc_id)[:1]})
    manifest = pd.DataFrame(rows)
    manifest.to_csv(ydir / "04_download_manifest.csv", index=False)
    return doc_texts, manifest


def parse_docs(doc_texts, ydir):
    parsed_rows, failures = [], []
    for doc_id, text in doc_texts.items():
        if not text.strip():
            continue
        rows = parse_ptr(text)
        if rows:
            for r in rows:
                r["doc_id"] = doc_id
                parsed_rows.append(r)
        else:
            failures.append({"doc_id": doc_id, "extrait": text.strip()[:300].replace("\n", " ")})
    pd.DataFrame(failures).to_csv(ydir / "05_parse_failures.csv", index=False)
    readable = sum(1 for t in doc_texts.values() if t.strip())
    parsed_ok = readable - len(failures)
    yield_rate = (parsed_ok / readable * 100) if readable else 0.0
    return parsed_rows, failures, readable, yield_rate


def join_identity(parsed_rows, ptr_index):
    parsed_df = pd.DataFrame(parsed_rows)
    parsed_df = parsed_df.merge(
        ptr_index[["doc_id", "declarant_name", "last", "first", "disclosure_date", "state_district"]],
        on="doc_id", how="left")
    parsed_df["bioguide_id"] = parsed_df.apply(lambda r: match_bioguide(r["last"], r["first"]), axis=1)
    parsed_df["party"] = parsed_df["bioguide_id"].map(ref_universe["party"])
    parsed_df["committee_membership"] = parsed_df["bioguide_id"].map(
        lambda b: "; ".join(sorted(bio_to_committees.get(b, []))) if b else "")
    parsed_df["committees_key_flag"] = parsed_df["bioguide_id"].map(
        lambda b: bool(ref_house_key is not None and b in ref_house_key.index) if b else False)
    parsed_df["chamber"] = "house"
    return parsed_df


SCHEMA = ["bioguide_id", "declarant_name", "chamber", "party", "state_district",
          "committee_membership", "committees_key_flag", "transaction_date", "disclosure_date",
          "ticker", "asset_description", "asset_type", "operation_type", "amount_range",
          "amount_midpoint", "amount_split_flag", "owner", "doc_id", "source_url",
          "natural_key_hash", "occurrence_index"]

def _legacy_key(r):
    # Délègue au cœur partagé (drop-in exact, prouvé par tests/regression/test_schema.py).
    from congress_core.schema import natural_key_hash
    return natural_key_hash(r, "house")

def finalize(parsed_df, year):
    """Normalise + déduplique. Dédup CANONIQUE (préserve les lots identiques intra-dépôt via
    occurrence_index ; supprime les vrais doublons cross-dépôt en gardant la divulgation la plus
    récente). Journalise legacy vs canonique."""
    df = parsed_df.copy()
    df["ticker"] = df["ticker"].str.upper()
    df["owner"] = df["owner"].fillna("SELF")
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce").dt.date
    df["disclosure_date"] = pd.to_datetime(df["disclosure_date"], errors="coerce").dt.date
    df["source_url"] = df["doc_id"].apply(lambda d: HOUSE_PDF_URL.format(year=year, doc_id=d))
    df["natural_key_hash"] = df.apply(_legacy_key, axis=1)
    df["occurrence_index"] = df.groupby(["doc_id", "natural_key_hash"]).cumcount()

    n_raw = len(df)
    n_legacy = df["natural_key_hash"].nunique()
    df_sorted = df.sort_values("disclosure_date", ascending=False, na_position="last")
    df_canon = df_sorted.drop_duplicates(["natural_key_hash", "occurrence_index"]).copy()
    df_canon = df_canon.reindex(columns=SCHEMA)
    stats = {"n_parsed": n_raw, "n_legacy_dedup": n_legacy, "n_canonical": len(df_canon),
             "n_repeats_preserved": len(df_canon) - n_legacy,
             "n_crossdoc_removed": n_raw - len(df_canon)}
    return df_canon, df, stats


# ───────────────────────── Cross-check vs baseline historique ─────────────────────────
_SEM1_CACHE = {}
def _sem1_year(year):
    if "df" not in _SEM1_CACHE:
        _SEM1_CACHE["df"] = pd.read_csv(SEM1_PARSE, dtype={"doc_id": str}, low_memory=False)
    s = _SEM1_CACHE["df"].copy()
    s["_dy"] = pd.to_datetime(s["disclosure_date"], errors="coerce").dt.year
    return s[s["_dy"] == year]

def crosscheck_semaine1(df, ptr_index, year, ydir):
    sem = _sem1_year(year)
    our_docs = set(df["doc_id"].astype(str))
    year_docs = set(ptr_index["doc_id"].astype(str))
    sem = sem[sem["doc_id"].astype(str).isin(year_docs)]
    our_by_doc = df.assign(doc_id=df["doc_id"].astype(str)).groupby("doc_id").size()
    sem_by_doc = sem.groupby("doc_id").size()
    cmp = pd.DataFrame({"nous": our_by_doc}).join(pd.DataFrame({"semaine1": sem_by_doc}), how="outer").fillna(0).astype(int)
    cmp["delta"] = cmp["nous"] - cmp["semaine1"]
    cmp = cmp.sort_values("delta")
    cmp.to_csv(ydir / "08_crosscheck_semaine1.csv")
    total = len(cmp)
    # la baseline a un parser plus faible : on attend nous >= baseline. Le vrai signal de dérive de
    # format = un doc parsé par la baseline mais où NOUS sortons 0 ligne.
    n_drift = int(((cmp["nous"] == 0) & (cmp["semaine1"] > 0)).sum())
    n_superset = int((cmp["nous"] >= cmp["semaine1"]).sum())
    return {"n_docs_compared": total, "n_drift_docs": n_drift,
            "n_superset_docs": n_superset,
            "pct_superset": (n_superset / total * 100) if total else 0.0,
            "drift_doc_ids": cmp[(cmp["nous"] == 0) & (cmp["semaine1"] > 0)].index.astype(str).tolist()[:20],
            "our_total": int(df.shape[0]), "sem1_total": int(len(sem)),
            "total_delta_pct": ((df.shape[0] - len(sem)) / len(sem) * 100) if len(sem) else float("nan")}


# ───────────────────────── Quiver (vérification externe) ─────────────────────────
_QUIVER_CACHE = {}
def fetch_quiver():
    """Charge le cache Quiver House (transaction-level, toutes années) si présent ; sinon live."""
    if "raw" in _QUIVER_CACHE:
        return _QUIVER_CACHE["raw"]
    cache = TABROOT / "_quiver_house_cache.csv"
    if cache.exists():
        q = pd.read_csv(cache)
        _QUIVER_CACHE["raw"] = q
        return q
    token = os.environ.get("QUIVER_API_KEY") or os.environ.get("QUIVER_API_TOKEN")
    if not token:
        _QUIVER_CACHE["raw"] = None
        return None
    qr = SESSION.get(QUIVER_URL, headers={"Authorization": f"Bearer {token}"}, timeout=180)
    q = pd.DataFrame(qr.json())
    q = q[q["Chamber"].str.contains("Rep", na=False)].copy()
    q = q.rename(columns={"Filed": "filed", "Traded": "traded"})
    q["disclosure_year"] = pd.to_datetime(q["filed"], errors="coerce").dt.year
    _QUIVER_CACHE["raw"] = q
    return q

def validate_quiver(df, manifest, ptr_index, year, win_start, win_end, ydir):
    """Validation Quiver HONNÊTE et invariante à la dédup :
    (1) comptes par déclarant PER-LOT (notre canonique vs Quiver BRUT, sous-comptes des deux côtés) ;
    (2) recouvrement au niveau TRANSACTION (clé bioguide|ticker|date|type) = mesure réelle des trades
        ratés, indépendante de la philosophie de dédup.
    Quiver = vérification externe uniquement."""
    qh = fetch_quiver()
    if qh is None:
        print("  ⚠ Quiver indisponible (ni cache ni clé) → validation sautée.")
        return None
    q = qh.copy()
    q["_filed"] = pd.to_datetime(q["filed"], errors="coerce")
    q = q[(q["_filed"] >= win_start) & (q["_filed"] <= win_end)].copy()
    q["_ticker"] = q["Ticker"].astype(str).str.upper().str.strip()
    q["_op4"] = q["Transaction"].astype(str).str.strip().str[:4]
    q["_td"] = pd.to_datetime(q["traded"], errors="coerce").dt.strftime("%Y-%m-%d")

    # Déclarants ayant ≥1 PTR scanné (backlog OCR) → écart attendu, pas une erreur
    paper = manifest[manifest["bucket"] == "non_lisible"][["doc_id"]].merge(
        ptr_index[["doc_id", "last", "first"]], on="doc_id", how="left")
    paper["bio"] = paper.apply(lambda r: match_bioguide(r["last"], r["first"]), axis=1)
    paper_bios = set(paper["bio"].dropna())

    our_name = df.drop_duplicates("bioguide_id").set_index("bioguide_id")["declarant_name"]
    q_name = q.drop_duplicates("BioGuideID").set_index("BioGuideID")["Name"]

    # (1) comptes par déclarant, PER-LOT (Quiver brut, pas de dédup)
    cmp = pd.DataFrame({"nous": df.groupby("bioguide_id").size()}).join(
        pd.DataFrame({"quiver": q.groupby("BioGuideID").size()}), how="outer").fillna(0).astype(int)
    cmp["delta"] = cmp["nous"] - cmp["quiver"]
    cmp["name"] = cmp.index.map(lambda b: our_name.get(b) or q_name.get(b, b))
    cmp["a_du_papier"] = cmp.index.isin(paper_bios)

    def verdict(row):
        if row["nous"] == 0 and row["quiver"] > 0:
            return "manquant_papier" if row["a_du_papier"] else "manquant_a_revoir"
        if row["delta"] == 0:
            return "concordant"
        if row["quiver"] == 0:
            return "quiver_sans_donnee"
        if row["delta"] > 0:
            return "nous_plus"
        return "quiver_plus_papier" if row["a_du_papier"] else "quiver_plus_a_revoir"
    cmp["verdict"] = cmp.apply(verdict, axis=1)
    cmp = cmp[["name", "nous", "quiver", "delta", "a_du_papier", "verdict"]].sort_values("nous", ascending=False)
    cmp.to_csv(ydir / "07_quiver_comparison.csv")

    # (2) recouvrement au niveau TRANSACTION (clé = bioguide|ticker|date|type), invariant à la dédup
    ours = df[df["ticker"].notna() & df["bioguide_id"].notna()].copy()
    ours["_k"] = (ours["bioguide_id"].astype(str) + "|" + ours["ticker"].astype(str).str.upper()
                  + "|" + ours["transaction_date"].astype(str) + "|" + ours["operation_type"].astype(str).str[:4])
    qk = q[q["BioGuideID"].notna() & q["_ticker"].ne("NAN") & q["_ticker"].ne("")].copy()
    qk["_k"] = (qk["BioGuideID"].astype(str) + "|" + qk["_ticker"] + "|" + qk["_td"] + "|" + qk["_op4"])
    our_keys, q_keys = set(ours["_k"]), set(qk["_k"])
    matched = our_keys & q_keys
    only_ours = our_keys - q_keys
    only_q = q_keys - our_keys
    cov_quiver = (len(matched) / len(q_keys) * 100) if q_keys else float("nan")  # % des trades Quiver qu'on a

    # trades Quiver absents chez nous, pour déclarants SANS PTR papier = vrais manques digital
    miss = qk[qk["_k"].isin(only_q)].copy()
    miss["a_du_papier"] = miss["BioGuideID"].isin(paper_bios)
    real_miss = miss[~miss["a_du_papier"]]
    real_miss_out = real_miss[["BioGuideID", "Name", "_ticker", "_td", "Transaction"]].rename(
        columns={"_ticker": "ticker", "_td": "traded"})
    real_miss_out.to_csv(ydir / "07b_quiver_missing_trades.csv", index=False)

    vc = dict(cmp["verdict"].value_counts())
    return {"quiver_total": len(q), "quiver_declarants": int(q["BioGuideID"].nunique()),
            "verdicts": vc, "n_declarants_compared": len(cmp),
            "set_matched": len(matched), "set_only_ours": len(only_ours), "set_only_quiver": len(only_q),
            "coverage_of_quiver_pct": round(cov_quiver, 1),
            "n_real_missing_trades": len(real_miss),
            "real_missing_declarants": sorted(real_miss["Name"].dropna().unique().tolist())[:20]}


# ───────────────────────── Orchestration par année ─────────────────────────
def run_year(year, win_start=None, win_end=None, do_quiver=True, do_crosscheck=True, tag=None):
    if win_start is None:
        win_start = pd.Timestamp(f"{year}-01-01")
    if win_end is None:
        win_end = pd.Timestamp(f"{year}-12-31")
    label = tag or str(year)
    ydir = TABROOT / label
    ydir.mkdir(parents=True, exist_ok=True)
    print(f"\n===== ANNÉE {label}  (fenêtre {win_start.date()} → {win_end.date()}) =====")

    ptr_index, ft_dist = load_ptr_index(year, win_start, win_end)
    ptr_index.to_csv(ydir / "03_ptr_index.csv", index=False)
    print(f"  PTR (FilingType=P) dans la fenêtre : {len(ptr_index)} | FilingType brut : {ft_dist}")

    doc_texts, manifest = build_manifest(year, ptr_index, ydir)
    n_lis = int((manifest["bucket"] == "lisible").sum())
    n_non = int((manifest["bucket"] == "non_lisible").sum())
    n_abs = int((manifest["bucket"] == "absent").sum())
    print(f"  PDF : {len(manifest)} | lisibles {n_lis} | non lisibles {n_non} | absents {n_abs}")
    pfx = dict(Counter(manifest["doc_prefix"]))
    print(f"  préfixe DocID : {pfx}")

    parsed_rows, failures, readable, yield_rate = parse_docs(doc_texts, ydir)
    print(f"  parse : lisibles {readable} | ≥1 ligne {readable - len(failures)} | "
          f"rendement {yield_rate:.1f}% | lignes brutes {len(parsed_rows)}")

    parsed_df = join_identity(parsed_rows, ptr_index)
    df_final, df_full, dstats = finalize(parsed_df, year)
    out_name = f"06_house_{label}_transactions.csv"
    df_final.to_csv(ydir / out_name, index=False)
    n_unmatched = int(df_final["bioguide_id"].isna().sum())
    print(f"  table finale : {len(df_final)} lignes | {df_final['declarant_name'].nunique()} déclarants | "
          f"sans bioguide {n_unmatched}")
    print(f"  dédup : parsé {dstats['n_parsed']} | legacy {dstats['n_legacy_dedup']} | "
          f"canonique {dstats['n_canonical']} (repeats préservés +{dstats['n_repeats_preserved']}, "
          f"cross-doc retirés {dstats['n_crossdoc_removed']})")

    # cross-check sur le set PRÉ-dédup (df_full) : mesure la vraie couverture du parser par doc,
    # sans confondre avec la dédup d'amendements (qui retire un doc original au profit de l'amendé).
    cc = crosscheck_semaine1(df_full, ptr_index, year, ydir) if do_crosscheck else None
    if cc:
        print(f"  cross-check semaine1 : docs {cc['n_docs_compared']} | superset {cc['n_superset_docs']} "
              f"({cc['pct_superset']:.0f}%) | DÉRIVE (sem1>0 & nous=0) : {cc['n_drift_docs']} | "
              f"total nous {cc['our_total']} vs sem1 {cc['sem1_total']}")
        if cc['n_drift_docs']:
            print(f"    ⚠ docs en dérive à inspecter : {cc['drift_doc_ids'][:10]}")

    qv = validate_quiver(df_final, manifest, ptr_index, year, win_start, win_end, ydir) if do_quiver else None
    if qv:
        print(f"  Quiver : {qv['quiver_total']} txns / {qv['quiver_declarants']} déclarants | "
              f"recouvrement trades Quiver : {qv['coverage_of_quiver_pct']}% "
              f"(matched {qv['set_matched']} | only-Quiver {qv['set_only_quiver']} | only-nous {qv['set_only_ours']})")
        print(f"    verdicts (comptes per-lot) {qv['verdicts']}")
        print(f"    ⚑ vrais trades manqués (Quiver a, nous pas, déclarant digital) : "
              f"{qv['n_real_missing_trades']} {qv['real_missing_declarants'] if qv['n_real_missing_trades'] else ''}")

    # Backlog OCR (non lisibles inventoriés, NON traités)
    backlog = manifest[manifest["bucket"] == "non_lisible"].merge(
        ptr_index[["doc_id", "declarant_name", "state_district", "disclosure_date"]],
        on="doc_id", how="left")
    backlog["year"] = label
    backlog["n_pages"] = backlog["doc_id"].apply(lambda d: n_pages(resolve_pdf_path(year, d)))
    backlog = backlog[["year", "doc_id", "declarant_name", "state_district", "disclosure_date", "n_pages"]]

    summary = {"year": label, "n_ptr": len(ptr_index), "n_lisible": n_lis, "n_non_lisible": n_non,
               "n_absent": n_abs, "n_txns_digital": len(df_final),
               "n_declarants": int(df_final["declarant_name"].nunique()),
               "yield_rate": round(yield_rate, 1), "n_unmatched": n_unmatched,
               "crosscheck": cc, "quiver": qv, "dedup": dstats}
    return summary, df_final, backlog


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2020", help="ex: 2020,2021,2022 ou '2025q1'")
    ap.add_argument("--no-quiver", action="store_true")
    ap.add_argument("--no-crosscheck", action="store_true")
    args = ap.parse_args()

    print("Construction du référentiel identité…")
    build_reference()

    summaries, backlogs = [], []
    if args.years.lower() == "2025q1":
        s, dfx, bk = run_year(2025, pd.Timestamp("2025-01-01"), pd.Timestamp("2025-03-31"),
                              do_quiver=not args.no_quiver, do_crosscheck=not args.no_crosscheck,
                              tag="2025q1")
        summaries.append(s); backlogs.append(bk)
    else:
        for y in [int(x) for x in args.years.split(",") if x.strip()]:
            s, dfx, bk = run_year(y, do_quiver=not args.no_quiver, do_crosscheck=not args.no_crosscheck)
            summaries.append(s); backlogs.append(bk)

    # 00_year_status.csv (récap)
    rows = []
    for s in summaries:
        q = s["quiver"] or {}
        v = q.get("verdicts", {}) if q else {}
        rows.append({"year": s["year"], "n_ptr": s["n_ptr"], "n_lisible": s["n_lisible"],
                     "n_non_lisible": s["n_non_lisible"], "n_txns_digital": s["n_txns_digital"],
                     "yield_rate": s["yield_rate"], "n_declarants": s["n_declarants"],
                     "quiver_coverage_pct": (q.get("coverage_of_quiver_pct") if q else None),
                     "set_matched": (q.get("set_matched") if q else None),
                     "set_only_quiver": (q.get("set_only_quiver") if q else None),
                     "set_only_nous": (q.get("set_only_ours") if q else None),
                     "vrais_trades_manques": (q.get("n_real_missing_trades", 0) if q else 0)})
    status = pd.DataFrame(rows)
    status_path = TABROOT / "00_year_status.csv"
    if status_path.exists():
        old = pd.read_csv(status_path)
        status = pd.concat([old[~old["year"].astype(str).isin(status["year"].astype(str))], status])
    status.to_csv(status_path, index=False)
    print(f"\n→ {status_path}")
    print(status.to_string(index=False))

    if backlogs:
        bk_all = pd.concat(backlogs, ignore_index=True)
        bk_path = TABROOT / "00_backlog_ocr.csv"
        if bk_path.exists():
            old = pd.read_csv(bk_path, dtype={"doc_id": str})
            bk_all = pd.concat([old[~old["year"].astype(str).isin(bk_all["year"].astype(str))], bk_all], ignore_index=True)
        bk_all.to_csv(bk_path, index=False)
        print(f"→ {bk_path} ({len(bk_all)} PDF non lisibles inventoriés)")


if __name__ == "__main__":
    main()
