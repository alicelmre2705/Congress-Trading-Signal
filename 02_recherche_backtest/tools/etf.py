"""La version ETF : carte titre → SPDR, carte DATÉE (bascules d'indice), agrégation des poids.

Extrait du notebook 16 (§9 et §18). La carte datée rend à chaque titre le secteur qu'il avait :
l'immobilier était dans XLF avant le 16/09/2016, la communication dans XLK ou XLY avant le
21/09/2018 — dates de bascule d'INDICE (sources SEC primaires), pas de cotation.
"""
import json

import numpy as np
import pandas as pd

from .donnees import DOSSIER, FUSION
from . import moteur

BASC_RE = pd.Timestamp("2016-09-16")   # XLF cesse de porter l'immobilier
BASC_CS = pd.Timestamp("2018-09-21")   # XLK et XLY cessent de porter la communication

IND_VERS_BRANCHE = {                   # l'industrie dit d'où le titre VENAIT
    "Telecom Services": "XLK", "Internet Content & Information": "XLK",
    "Electronic Gaming & Multimedia": "XLK",
    "Entertainment": "XLY", "Advertising Agencies": "XLY",
    "Broadcasting": "XLY", "Publishing": "XLY",
}
# les sociétés disparues (yfinance muet) : attribution nominative, opposable — nb 16, §18
MANUEL_CS = {
    "LVLT": "XLK", "CHL": "XLK", "FTR": "XLK", "CNSL": "XLK", "BT": "XLK", "NTT": "XLK",
    "ZAYO": "XLK", "ORAN": "XLK", "WIN": "XLK", "TLSYY": "XLK", "JCS": "XLK", "DCM": "XLK",
    "IQNT": "XLK", "VODPD": "XLK",
    "YNDX": "XLK", "TWTR": "XLK", "LNKD": "XLK", "ATVI": "XLK", "YHOO": "XLK", "IACI": "XLK",
    "JCOM": "XLK", "ZNGA": "XLK", "RNWK": "XLK", "ISDR": "XLK",
    "VIAC": "XLY", "SNI": "XLY", "DISH": "XLY", "TWX": "XLY", "CMCSK": "XLY", "MSG": "XLY",
    "TGNA": "XLY", "GCI": "XLY", "VIAB": "XLY", "LTRPA": "XLY", "LMCK": "XLY", "LMCA": "XLY",
    "MDCA": "XLY", "WPPGY": "XLY", "IPG": "XLY", "LSXMA": "XLY", "LSXMK": "XLY", "TIME": "XLY",
    "DTV": "XLY", "LGF-A": "XLY", "SJR": "XLY",
}
# des fonds, pas des actions — jamais réattribués (nb 16 §18, FICHE_M3 annexe D)
HORS_CARTE = ["EDR", "FDN", "IXP", "PNQI", "VOX", "VNQ", "IYR", "SCHH"]


def carte_simple(D):
    """titre (classes fusionnées) → SPDR : le mode de etf_proxy — la carte du nb 13 §12.3."""
    tkm = D.df.tk.map(lambda t: FUSION.get(t, t))
    return D.df.assign(tkm=tkm).groupby("tkm").etf_proxy.agg(lambda s: s.mode().iat[0])


def carte_datee(D):
    """Rend (CARTE, carte_hist) — carte_hist(i1) = la carte applicable à la coupe i1."""
    CARTE = carte_simple(D)
    fine = DOSSIER / "cache" / "sector_fine_v1" / "industry.json"
    IND = {k: (v.get("industry") or None)
           for k, v in json.load(open(fine, encoding="utf-8")).items()}
    cs = [t for t in CARTE.index[CARTE == "XLC"] if t not in HORS_CARTE]
    br = pd.Series({t: (IND_VERS_BRANCHE.get(IND.get(t)) or MANUEL_CS.get(t)) for t in cs}).dropna()
    re_ = [t for t in CARTE.index[CARTE == "XLRE"] if t not in HORS_CARTE]

    def carte_hist(i1):
        d = D.cal[i1]
        if d >= BASC_CS:
            return CARTE
        c = CARTE.copy()
        if d < BASC_RE:
            c.loc[re_] = "XLF"
        c.loc[br.index] = br.values
        return c

    return CARTE, carte_hist


def poids_agrege(D, i1, parti=None, carte=None, cap_sect=None, **kw):
    """M3 EN ENTIER, puis chaque ligne est remplacée par son ETF et les POIDS sont sommés.

    La spécification « seul l'instrument change » (variante C du nb 13). parti=None = l'unique.
    """
    w = moteur.poids_M3(D, i1, parti, **kw)
    if not w:
        return {}
    s = pd.Series(w)
    cle = carte.reindex(s.index)
    assert not cle.isna().any(), f"coupe {i1} : titres sans instrument — {list(s.index[cle.isna()])}"
    s = s.groupby(cle.values).sum()
    viv = [t for t in s.index
           if t in D.PXV and np.isfinite(D.PXV[t][i1 + 1]) and D.vivant(t, i1)]
    if not viv or s[viv].sum() <= 0:
        return {}
    s = s[viv] / s[viv].sum()
    if cap_sect is not None:
        s = moteur.cap_poids(s, cap_sect)
    return s.to_dict()


def cibles_etf(D, parti=None, carte_hist=None, **kw):
    """Un jeu de poids sectoriels par coupe, à la carte DATÉE (carte_hist(i) par coupe)."""
    return {i: poids_agrege(D, i, parti, carte=carte_hist(i), **kw) for i in D.coupes[:-1]}
