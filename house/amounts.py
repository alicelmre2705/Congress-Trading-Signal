"""Fourchettes de montant, midpoint, propriétaire, type d'opération — par chambre.

Réconcilie les copies divergentes (House OCR J=75M/midpoints .0 ; Sénat OCR J=50M/midpoints .5 ;
owner labels différents). On NE fusionne PAS : chaque chambre/mode garde sa sémantique exacte
(les midpoints et `owner` alimentent des sorties figées — cf. piège #3). Les maps sont indexées
par chambre ; le code par défaut reste celui de House (refonte House-first).
"""
import re

# ── Type d'actif (codes [XX] du formulaire House électronique) ────────────────────────────────
ATYPE_NAMES = {"ST": "Stock", "OP": "Option", "OT": "Other", "MF": "Mutual Fund",
               "GS": "Gov Security", "CO": "Corp Bond", "PE": "Private Equity",
               "OI": "Other Investment"}

# ── Fourchettes A–K → (libellé, midpoint), par chambre (copie EXACTE des moteurs OCR) ──────────
HOUSE_OCR_AMOUNT_MAP = {
    "A": ("$1,001 - $15,000", 8_000.0), "B": ("$15,001 - $50,000", 32_500.0),
    "C": ("$50,001 - $100,000", 75_000.0), "D": ("$100,001 - $250,000", 175_000.0),
    "E": ("$250,001 - $500,000", 375_000.0), "F": ("$500,001 - $1,000,000", 750_000.0),
    "G": ("$1,000,001 - $5,000,000", 3_000_000.0), "H": ("$5,000,001 - $25,000,000", 15_000_000.0),
    "I": ("$25,000,001 - $50,000,000", 37_500_000.0), "J": ("Over $50,000,000", 75_000_000.0),
    "K": ("SP/DC over $1,000,000", 1_000_001.0),
}
SENATE_OCR_AMOUNT_MAP = {
    "A": ("$1,001 - $15,000", 8000.5), "B": ("$15,001 - $50,000", 32500.5),
    "C": ("$50,001 - $100,000", 75000.5), "D": ("$100,001 - $250,000", 175000.5),
    "E": ("$250,001 - $500,000", 375000.5), "F": ("$500,001 - $1,000,000", 750000.5),
    "G": ("$1,000,001 - $5,000,000", 3000000.5), "H": ("$5,000,001 - $25,000,000", 15000000.5),
    "I": ("$25,000,001 - $50,000,000", 37500000.5), "J": ("Over $50,000,000", 50000000.0),
}
AMOUNT_MAP = {"house": HOUSE_OCR_AMOUNT_MAP, "senate": SENATE_OCR_AMOUNT_MAP}

# ── Propriétaire (normalisation par chambre — labels INTENTIONNELLEMENT différents) ────────────
HOUSE_OCR_OWNER_MAP = {"Self": "SELF", "Spouse": "Spouse",
                       "Joint": "Joint Tenancy", "Dependent Child": "Dependent Child"}
SENATE_OCR_OWNER_MAP = {"Self": "Self", "Spouse": "Spouse",
                        "Joint": "Joint", "Dependent Child": "Child"}
OWNER_MAP = {"house": HOUSE_OCR_OWNER_MAP, "senate": SENATE_OCR_OWNER_MAP}


def amount_midpoint(a):
    """Midpoint d'une fourchette « $X - $Y » (piste DIGITALE House). (lo+hi)/2, ou lo seul, ou None.
    Copie EXACTE de house_multiyear._amount_midpoint (≠ AMOUNT_MAP OCR : .5 vs .0 — voulu)."""
    nums = [int(x.replace(",", "")) for x in re.findall(r"\$([\d,]+)", str(a))]
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2
    if len(nums) == 1:
        return float(nums[0])
    return None


def operation_type_from_code(t, sub=None):
    """Type d'opération 5-voies pour le champ stocké `operation_type` (P/E/Sale[/Partial/Full]).
    Copie EXACTE de house_multiyear._op_type. NE PAS confondre avec la normalisation 3-voies
    `norm_sense` utilisée seulement pour l'appariement Quiver (cf. quiver.py, piège séparé)."""
    t, sub = str(t).upper(), (sub or "").lower()
    if t == "P":
        return "Purchase"
    if t == "E":
        return "Exchange"
    if sub == "partial":
        return "Sale (Partial)"
    if sub == "full":
        return "Sale (Full)"
    return "Sale"
