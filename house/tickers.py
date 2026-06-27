"""Normalisation / récupération de ticker + inférence de type d'actif — copies EXACTES des moteurs.

Réunit les variantes éparpillées (House OCR `_norm_asset`/`_explicit_ticker`/`_infer_asset_type`,
Sénat `recover_ticker`, regex de parsing House digital). `infer_asset_type` prend `chamber` car les
tables de mots-clés diffèrent (House : Mutual Fund/Gov Security ; Sénat : Municipal Security).
"""
import re

# ── Regex de parsing (House digital) ──────────────────────────────────────────────────────────
TICKER_RE = re.compile(r"\(([A-Za-z][A-Za-z0-9.\-]{0,5})\)")
EXCH_TICKER_RE = re.compile(r"(?:NYSE|NASDAQ|NYSEARCA|BATS|AMEX|CBOE)[:\s]+([A-Za-z]{1,5})\b", re.IGNORECASE)

# ── « Le nom EST un ticker » (Sénat eFD : colonne Asset Name = « LLY », « CRWD PUT ») ──────────
TICK_RE = re.compile(r"^([A-Z]{1,5})(?:\.[A-Z])?(?:\s+(?:PUT|CALL))?$")

# ── Symbole explicite en fin de description + normalisation pour lookup dict (House OCR) ────────
_SUFFIX_RE = re.compile(
    r"\b(CMN|COM|COMMON STOCK|COMMON|CLASS [A-Z]|CL [A-Z]|INCORPORATED|INC|CORPORATION|CORP|"
    r"COMPANY|CO|HOLDINGS|HLDGS|LLC|L\.?P\.?|LTD|PLC|THE|SYS|SYSTEMS|SER|TR|TRUST|FUND|FUNDS|ETF)\b")
_EXPLICIT_TICKER_RE = re.compile(r"[-(]\s*([A-Z][A-Z0-9.]{0,5})\)?\s*$")
_OCR_FIX = {"METILIFE": "METLIFE", "ATT": "AT T"}


def recover_ticker(desc):
    """« Le nom EST un ticker » (Sénat). Copie EXACTE de senate_finalize.recover_ticker."""
    if not isinstance(desc, str):
        return None
    m = TICK_RE.match(desc.strip())
    return m.group(1) if m else None


def explicit_ticker(desc):
    """Symbole explicite « … - AAPL » / « … (AAPL) » en fin de description. Copie de _explicit_ticker."""
    m = _EXPLICIT_TICKER_RE.search(str(desc))
    if not m:
        return None
    t = m.group(1).strip(".")
    return t if 1 <= len(t) <= 5 else None


def norm_asset(s):
    """Normalise une description pour le lookup dict nom→ticker. Copie EXACTE de _norm_asset."""
    s = str(s).upper()
    s = _EXPLICIT_TICKER_RE.sub("", s)
    s = re.sub(r"[^A-Z0-9 &]", " ", s)
    s = _SUFFIX_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    for bad, good in _OCR_FIX.items():
        s = re.sub(rf"\b{bad}\b", good, s)
    return s


def _infer_asset_type_house(desc):
    d = str(desc).upper()
    if re.search(r"TREASURY|T-?BILL|T-?BOND|T-?NOTE|GOVT|GOVERNMENT|MUNICIPAL|\bMUNI\b|\bISD\b|SCHOOL DIST", d):
        return "Gov Security"
    if re.search(r"LINKED TO|NOTES? LINKED|STRUCTURED|BASKET OF", d):
        return "Other"
    if re.search(r"\bETF\b|\bFUND\b|FUNDS|INDEX|SPDR|ISHARES|VANGUARD|AMPLIFY|GLOBAL X|SELECT SECTOR|\bTR\b|TRUST", d):
        return "Mutual Fund"
    if re.search(r"\bBOND\b|\bNOTE\b|DEBENTURE|\bBILL\b", d):
        return "Corporate Bond"
    if re.search(r"CMN|COM|COMMON|\bINC\b|CORP|CLASS|\bCO\b|HOLDINGS|\bLLC\b|\bLP\b|\bPLC\b|COMPANY", d):
        return "Stock"
    return None


def _infer_asset_type_senate(desc):
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


def infer_asset_type(desc, chamber="house"):
    """Type d'actif inféré de la description. Tables de mots-clés EXACTES par chambre."""
    return _infer_asset_type_senate(desc) if chamber == "senate" else _infer_asset_type_house(desc)
