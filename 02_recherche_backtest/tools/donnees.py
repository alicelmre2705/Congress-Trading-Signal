"""Chargement de la lignée « titre » : table clean, prix, calendrier, coupes, facteurs.

Code extrait des cellules d'ouverture du notebook 16 (§1) — mêmes filtres, mêmes garde-fous,
mêmes constantes. Une seule différence : les chemins sont ancrés sur ce fichier
(`Path(__file__)`), jamais codés en absolu.
"""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[2]          # …/Jupiter
DOSSIER = RACINE / "02_recherche_backtest"
# La table COURANTE (produite par le pipeline, step 7) — et la V1 du 04/07, archivée, sur laquelle
# TOUTES les ancres publiées (FICHE_M3, carte, notebooks) restent adossées (cf. NOTE_DIFF_TABLE_CLEAN,
# branche presentation).
CLEAN = RACINE / "00_recuperation_donnees" / "data" / "clean" / "transactions_backtest_2014_2026.csv"
CLEAN_V1 = (RACINE / "00_recuperation_donnees" / "_archive" / "data_clean"
            / "transactions_backtest_2014_2026_v20260704.csv")
PX = DOSSIER / "cache" / "prices_v2"
FF_CSV = DOSSIER / "cache" / "ff_factors.csv"

# les trois constantes de M3 — fenêtre du signal, taille d'univers, plafond de position
W3, TOPN, CAP = 756, 150, 0.10
ETF_SECT = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
FUSION = {"GOOGL": "GOOG", "BRK-A": "BRK-B", "FOXA": "FOX", "NWSA": "NWS"}  # classes d'actions = une société


def charger(verbose=True, table=None):
    """Charge tout le contexte de la lignée titre et le rend en un seul objet `D`.

    `table` : None → la table CLEAN courante (pipeline) ; "v1" → la table archivée du 04/07,
    celle des ancres publiées ; ou un chemin explicite.

    Attributs : df (le flux, 113 369 opérations), cal, spy, r_spy, PXV, PXV_ACTIONS,
    NFIRST/NLAST, vivant(tk, i), coupes (calendrier conforme, ≥ ⌈1/c⌉ titres des deux côtés),
    coupes_tout, i_start, FF, ordre_d/I_de (index trié sur la divulgation).
    """
    chemin = {None: CLEAN, "v1": CLEAN_V1}.get(table, Path(table) if table else CLEAN)
    # colonnes voulues ∩ colonnes présentes : la v1 porte committee_membership inline, la table
    # courante l'a normalisée en annexe (NOTE_DIFF_TABLE_CLEAN, branche presentation) — tools n'en a pas besoin.
    voulues = ["bioguide_id", "member_name", "ticker_yahoo", "direction", "transaction_date",
               "disclosure_date", "amount_midpoint", "asset_class", "chamber",
               "committee_membership", "committees_key_flag", "sector_gics", "flag_late_filing",
               "party", "etf_proxy"]
    entete = pd.read_csv(chemin, nrows=0).columns
    df0 = pd.read_csv(chemin, usecols=[c for c in voulues if c in entete],
                      parse_dates=["transaction_date", "disclosure_date"])
    a = df0[df0.asset_class == "stock"]                                                  # actions seules
    b = a[(a.transaction_date.dt.year >= 2014) & (a.transaction_date.dt.year <= 2026)]   # fenêtre canonique
    df = (b.rename(columns={"ticker_yahoo": "tk", "direction": "op",
                            "transaction_date": "tau", "amount_midpoint": "A"})
            .sort_values("tau").reset_index(drop=True))
    assert df[["tk", "A"]].notna().all().all(), "ticker ou montant manquant dans la table clean"

    spy = pd.read_csv(PX / "SPY.csv", parse_dates=["Date"]).set_index("Date")["close"].sort_index()
    cal = spy.index
    r_spy = spy.pct_change()

    # prix : titres du flux + les 11 SPDR, avec les garde-fous du dépôt (< 0,10 $, saut > 300 %)
    PXV, LAST = {}, {}
    for tk in sorted(set(df.tk.unique()) | set(ETF_SECT)):
        f = PX / f"{tk}.csv"
        if not f.exists():
            continue
        try:
            s = pd.read_csv(f, parse_dates=["Date"]).set_index("Date")["close"].sort_index().dropna()
        except Exception:
            continue
        if len(s) < 2 or s.min() < 0.10:
            continue
        v = s.pct_change().dropna()
        if len(v) and v.abs().max() > 3.0:
            continue
        LAST[tk] = s.index[-1]
        PXV[tk] = s.reindex(cal).ffill().to_numpy()
    PXV_ACTIONS = set(df.tk.unique()) & set(PXV)

    df = df[df.tk.isin(PXV)].reset_index(drop=True)
    df["i0"] = cal.searchsorted(df.tau.values, side="left")               # exécution à τ
    df["ide"] = cal.searchsorted(df.disclosure_date.values, side="left")  # exécution à δ — celle de M3
    df = df[df.i0 < len(cal)].reset_index(drop=True)
    df["sgn"] = np.where(df.op == "buy", 1.0, -1.0)
    # taille du dépôt = nb d'opérations du même élu au même jour de divulgation (filtre θ de M4)
    df["taille_depot"] = df.groupby(["bioguide_id", "ide"]).tk.transform("size")

    NLAST = {tk: cal.searchsorted(d, side="right") - 1 for tk, d in LAST.items()}
    NFIRST = {tk: int(np.argmax(~np.isnan(PXV[tk]))) for tk in PXV}

    def vivant(tk, i):
        # le titre cote DÉJÀ et cote ENCORE (dernier cours à moins de 4 jours)
        return NFIRST[tk] <= i and NLAST[tk] >= i - 4

    # coupes mensuelles (dernier jour coté), puis règle de démarrage : première coupe où le
    # plafond a une solution (≥ ⌈1/c⌉ titres) POUR LES DEUX partis — critère structurel, §4.1 du nb 16
    DEBUT = pd.Timestamp("2014-01-31")
    coupes_tout = [cal.searchsorted(d, side="right") - 1 for d in pd.date_range(DEBUT, cal[-1], freq="ME")]
    coupes_tout = sorted(set(i for i in coupes_tout if 21 <= i < len(cal) - 1))

    ordre_d = np.argsort(df.ide.values, kind="stable")
    I_de = df.ide.values[ordre_d]

    D = SimpleNamespace(df=df, cal=cal, spy=spy, r_spy=r_spy, PXV=PXV, PXV_ACTIONS=PXV_ACTIONS,
                        NFIRST=NFIRST, NLAST=NLAST, vivant=vivant, ordre_d=ordre_d, I_de=I_de,
                        coupes_tout=coupes_tout, coupes=None, i_start=None,
                        FF=pd.read_csv(FF_CSV, parse_dates=["Date"]).set_index("Date"))

    from . import moteur  # ici pour éviter l'import circulaire au chargement du paquet
    import math
    seuil_deg = math.ceil(1 / CAP)
    i_start = next(i for i in coupes_tout
                   if min(len(moteur.poids_M3(D, i, p)) for p in ("Democrat", "Republican")) >= seuil_deg)
    D.i_start = i_start
    D.coupes = [i for i in coupes_tout if i >= i_start]

    if verbose:
        print(f"flux {len(df):,} opérations · {df.bioguide_id.nunique()} membres · "
              f"{df.tk.nunique():,} titres · calendrier {len(cal):,} j · "
              f"{len(D.coupes)} coupes dès {cal[i_start].date()}")
    return D
