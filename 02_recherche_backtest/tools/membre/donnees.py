"""Chargement de la famille membre : table clean, prix, calendrier — contexte M.

Code extrait des cellules d'ouverture de copier_les_membres/tables_membres_tickers (§0),
aux chemins ancrés (Path(__file__)) près et aux colonnes du pipeline près : la génération 2
CONSOMME owner_n, member_name_canon et la table annexe des commissions au lieu de les refaire
(elles n'existaient pas quand les notebooks ont été écrits — absorbées par le pipeline le 11/08).

⚠️ Le garde-fou prix garde l'ORDRE HISTORIQUE de la famille membre : reindex(cal).ffill()
PUIS les seuils (< 0,10 $, saut > 300 %/j) — tools.donnees (famille titre) teste les seuils
sur la série brute AVANT alignement. Les deux périmètres n'ont pas de raison de coïncider.
"""
import glob
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from ..donnees import RACINE, DOSSIER, CLEAN, CLEAN_V1

PRICES = DOSSIER / "cache" / "prices_v2"
ANCIENNETE = DOSSIER / "anciennete_2014_2026.csv"    # bioguide_id → years_in_office (extrait versionné)
LEADERSHIP = DOSSIER / "leadership_2014_2026.csv"
COMMISSIONS = (RACINE / "00_recuperation_donnees" / "data" / "clean"
               / "commissions_membre_congres.csv")   # table annexe (bioguide_id × congress)

# repli v1 UNIQUEMENT : la table du 04/07 n'a ni owner_n ni member_name_canon
_OWNER_V1 = {"Spouse": "conjoint", "SP": "conjoint", "spouse": "conjoint",
             "SELF": "élu", "Self": "élu", "self": "élu",
             "JT": "joint", "Joint Tenancy": "joint", "Joint": "joint", "joint": "joint",
             "Dependent Child": "enfant", "DC": "enfant", "Child": "enfant",
             "dependent": "enfant", "Dependent": "enfant"}


def _mode(s):
    m = s.dropna().mode()
    return m.iloc[0] if len(m) else np.nan


def charger_membre(table=None, verbose=True):
    """Charge tout le contexte de la famille membre et le rend en un seul objet `M`.

    `table` : None → la table CLEAN courante (pipeline) ; "v1" → la table archivée du 04/07
    (celle des sorties figées historiques) ; ou un chemin explicite.

    Attributs : df (6 colonnes, périmètre exploitable), dfx (toutes colonnes, même périmètre,
    committee_membership joint depuis la table annexe sur la courante), dfb (𝒯^brut : avant le
    filtre prix), prices (dict de Series alignées ffill sur cal), cal, spy, r_spy,
    need / missing / corrompus, n0.
    """
    chemin = {None: CLEAN, "v1": CLEAN_V1}.get(table, Path(table) if table else CLEAN)
    brut = pd.read_csv(chemin, low_memory=False)
    n0 = len(brut)
    v1 = "member_name_canon" not in brut.columns

    brut = (brut.drop(columns=["ticker"])
                .rename(columns={"ticker_yahoo": "ticker", "direction": "op",
                                 "transaction_date": "traded", "amount_midpoint": "size_usd"}))
    # le nom : canonique (une seule graphie par bioguide_id) — colonne pipeline sur la courante
    if v1:
        brut = brut.rename(columns={"member_name": "name"})
        canon = brut.groupby("bioguide_id")["name"].transform(_mode)
        brut["name"] = canon.where(canon.notna(), brut["name"])
        brut["owner_n"] = brut["owner"].map(_OWNER_V1).fillna("autre/inconnu")
    else:
        brut["name"] = brut["member_name_canon"]
        # complément local : deux libellés absents d'OWNER_N côté pipeline (correctif signalé) —
        # « Dependent Child » → enfant (20 837 l.) et « Joint Tenancy » → joint (9 932 l.)
        trous = brut["owner_n"].eq("autre/inconnu")
        brut.loc[trous, "owner_n"] = (brut.loc[trous, "owner"].map(_OWNER_V1)
                                      .fillna("autre/inconnu"))
    brut["traded"] = pd.to_datetime(brut["traded"], errors="coerce")
    brut = brut[brut["traded"].dt.year.between(2013, 2026)].reset_index(drop=True)

    # commissions : inline sur la v1 ; sur la courante, jointure de la table annexe du pipeline
    if "committee_membership" not in brut.columns and COMMISSIONS.exists():
        annexe = pd.read_csv(COMMISSIONS)
        brut = brut.merge(annexe[["bioguide_id", "congress", "committee_membership"]],
                          on=["bioguide_id", "congress"], how="left")

    dfb = brut                                            # 𝒯^brut : tout le périmètre 2013-2026
    df = dfb[["bioguide_id", "name", "ticker", "op", "traded", "size_usd"]].copy()

    # prix : cache prices_v2, alignés ffill sur le calendrier SPY PUIS garde-fous (ordre membre)
    spy = (pd.read_csv(PRICES / "SPY.csv", parse_dates=["Date"])
             .set_index("Date")["close"].sort_index())
    cal = spy.index
    r_spy = spy.pct_change()

    have = {os.path.splitext(os.path.basename(p))[0]
            for p in glob.glob(str(PRICES / "*.csv"))} - {"failed_v2"}
    need = sorted(set(df["ticker"]) & have)
    missing = sorted(set(df["ticker"]) - have)
    prices = {}
    for tk in need:
        s = (pd.read_csv(PRICES / f"{tk}.csv", parse_dates=["Date"])
               .set_index("Date")["close"].sort_index())
        prices[tk] = s.reindex(cal).ffill()
    corrompus = [tk for tk in need if (len(prices[tk].dropna()) < 2
                 or prices[tk].dropna().min() < 0.10
                 or prices[tk].dropna().pct_change().abs().max() > 3.0)]  # <0,10$ ou saut >300%/j
    for tk in corrompus:
        del prices[tk]
    need = [tk for tk in need if tk not in set(corrompus)]

    n_jetes = int((~df["ticker"].isin(need)).sum())
    df = df[df["ticker"].isin(need)].reset_index(drop=True)
    dfx = dfb[dfb["ticker"].isin(need)].reset_index(drop=True)
    assert len(dfx) == len(df), "dfx doit porter exactement le périmètre exploitable de df"

    M = SimpleNamespace(df=df, dfx=dfx, dfb=dfb, prices=prices, cal=cal, spy=spy, r_spy=r_spy,
                        need=need, missing=missing, corrompus=corrompus, n0=n0, n_jetes=n_jetes,
                        v1=v1)
    if verbose:
        print(f"{n0} -> {len(dfb)} trades (fenêtre 2013-2026) | {dfb.bioguide_id.nunique()} membres "
              f"| {dfb.ticker.nunique():,} tickers")
        print(f"tickers avec prix : {len(need)} | sans prix : {len(missing)} | corrompus exclus : "
              f"{len(corrompus)} | trades jetés : {n_jetes} => {len(df)} exploitables")
    return M
