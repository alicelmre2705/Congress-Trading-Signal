"""Chargement de la famille membre : table clean, prix, calendrier — contexte M.

Code extrait des cellules d'ouverture de copier_les_membres/tables_membres_tickers (§0),
aux chemins ancrés (Path(__file__)) près et aux colonnes du pipeline près : la génération 2
CONSOMME owner_n, member_name_canon et la table annexe des commissions au lieu de les refaire
(elles n'existaient pas quand les notebooks ont été écrits — absorbées par le pipeline le 11/08).

⚠️ Le garde-fou prix garde l'ORDRE HISTORIQUE de la famille membre : reindex(cal).ffill()
PUIS les seuils (< 0,10 $, saut > 300 %/j) — tools.donnees (famille titre) teste les seuils
sur la série brute AVANT alignement. (Vérifié le 12/08 : les deux définitions donnent des
statuts IDENTIQUES sur les 4 607 tickers.)

Depuis le 2026-08-12, la table clean du pipeline est DÉJÀ fenêtrée (2013-2026, étape E) et
couverte-prix (étape F, référentiel data/reference/couverture_prix_*.csv) : les filtres
ci-dessous deviennent des garde-fous à ZÉRO effet sur la courante — conservés parce qu'ils
restent nécessaires sur table="v1" et qu'ils protègent contre une dérive du cache local.
"""
import glob
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from ..donnees import RACINE, DOSSIER, CLEAN, CLEAN_V1

BRUT = RACINE / "00_recuperation_donnees" / "data" / "clean" / "transactions_brut_2014_2026.csv"
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
    committee_membership joint depuis la table annexe sur la courante), dfb (𝒯^brut : le
    périmètre fenêtré AVANT le filtre prix — lu dans la table BRUTE du pipeline sur la
    courante, verdicts ∅ et F), prices (dict de Series alignées ffill sur cal), cal, spy,
    r_spy, need / missing / corrompus, n0.
    """
    chemin = {None: CLEAN, "v1": CLEAN_V1}.get(table, Path(table) if table else CLEAN)
    brut = pd.read_csv(chemin, low_memory=False)
    n0 = len(brut)
    v1 = "member_name_canon" not in brut.columns

    def _preparer(b, v1_):
        b = (b.drop(columns=["ticker"])
              .rename(columns={"ticker_yahoo": "ticker", "direction": "op",
                               "transaction_date": "traded", "amount_midpoint": "size_usd"}))
        # le nom : canonique (une seule graphie par bioguide_id) — colonne pipeline sur la courante
        if v1_:
            b = b.rename(columns={"member_name": "name"})
            canon = b.groupby("bioguide_id")["name"].transform(_mode)
            b["name"] = canon.where(canon.notna(), b["name"])
            b["owner_n"] = b["owner"].map(_OWNER_V1).fillna("autre/inconnu")
        else:
            b["name"] = b["member_name_canon"]
            # complément local : deux libellés longtemps absents d'OWNER_N côté pipeline
            # (« Dependent Child », « Joint Tenancy ») — sans effet depuis le correctif du 12/08
            trous = b["owner_n"].eq("autre/inconnu")
            b.loc[trous, "owner_n"] = (b.loc[trous, "owner"].map(_OWNER_V1)
                                       .fillna("autre/inconnu"))
        b["traded"] = pd.to_datetime(b["traded"], errors="coerce")
        b = b[b["traded"].dt.year.between(2013, 2026)].reset_index(drop=True)
        # commissions : inline sur la v1 ; sur la courante, jointure de la table annexe du pipeline
        if "committee_membership" not in b.columns and COMMISSIONS.exists():
            annexe = pd.read_csv(COMMISSIONS)
            b = b.merge(annexe[["bioguide_id", "congress", "committee_membership"]],
                        on=["bioguide_id", "congress"], how="left")
        return b

    propre = _preparer(brut, v1)

    # 𝒯^brut : depuis le 12/08 la clean est déjà couverte-prix (étape F du pipeline) — le
    # périmètre « fenêtré avant prix » se lit donc dans la table BRUTE (verdicts ∅ et F).
    if not v1 and BRUT.exists():
        b0 = pd.read_csv(BRUT, low_memory=False)
        b0 = b0[b0["exclusion_etape"].fillna("").isin(["", "F"])].drop(
            columns=["exclusion_etape", "exclusion_motif"])
        dfb = _preparer(b0, False)
    else:
        dfb = propre                                      # v1 : la clean d'époque EST le 𝒯^brut

    df = propre[["bioguide_id", "name", "ticker", "op", "traded", "size_usd"]].copy()

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
    dfx = propre[propre["ticker"].isin(need)].reset_index(drop=True)
    assert len(dfx) == len(df), "dfx doit porter exactement le périmètre exploitable de df"

    M = SimpleNamespace(df=df, dfx=dfx, dfb=dfb, prices=prices, cal=cal, spy=spy, r_spy=r_spy,
                        need=need, missing=missing, corrompus=corrompus, n0=n0, n_jetes=n_jetes,
                        v1=v1)
    if verbose:
        print(f"𝒯^brut (fenêtré, avant prix — table brute) : {len(dfb):,} trades | "
              f"{dfb.bioguide_id.nunique()} membres | {dfb.ticker.nunique():,} tickers")
        print(f"clean (exploitable) : {len(df):,} trades | tickers avec prix {len(need):,} | "
              f"sans prix {len(missing)} | corrompus {len(corrompus)} | jetés au chargement {n_jetes}")
    return M
