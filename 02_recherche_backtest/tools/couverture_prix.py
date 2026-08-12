"""Extracteur du référentiel de couverture prix — data/reference/couverture_prix_<date>.csv.

Le pipeline (common/backtest_clean.py, étape F de l'entonnoir) est 100 % hors-ligne : il ne peut
pas interroger le cache de prix de la recherche (cache/prices_v2/, non versionné). Ce script
matérialise donc la couverture en un référentiel VERSIONNÉ et DATÉ, comme ticker_renames.csv :
pour chaque ticker_yahoo du corpus (fenêtre 2013-2026), un statut —
  couvert        : une série de prix exploitable existe ;
  sans_prix      : aucun fichier dans le cache (délisté ancien, OTC, symbole exotique…) ;
  prix_corrompu  : série inexploitable (< 2 points, minimum < 0,10 $, ou saut > 300 %/j).

Les garde-fous sont CEUX de la recherche (familles membre et titre — vérifié le 2026-08-12 :
les deux définitions, série alignée ffill ou série brute, donnent des statuts IDENTIQUES sur
les 4 607 tickers). Les tickers absents du référentiel (nouveaux symboles après la date
d'extraction) ne sont PAS exclus par le pipeline : re-extraire pour les couvrir.

Usage :  cd 02_recherche_backtest && ../.venv/bin/python -m tools.couverture_prix
         (écrit data/reference/couverture_prix_<AAAAMMJJ>.csv — mettre à jour le nom de fichier
          lu par common/backtest_clean.py si la date change)
"""
import glob
import os
from datetime import date

import pandas as pd

from .donnees import RACINE, CLEAN, PX


def extraire():
    df = pd.read_csv(CLEAN, usecols=["ticker_yahoo", "transaction_date"], low_memory=False)
    annee = pd.to_datetime(df["transaction_date"], errors="coerce").dt.year
    tickers = sorted(set(df.loc[annee.between(2013, 2026), "ticker_yahoo"].dropna()))
    have = {os.path.splitext(os.path.basename(p))[0]
            for p in glob.glob(str(PX / "*.csv"))} - {"failed_v2"}

    spy = pd.read_csv(PX / "SPY.csv", parse_dates=["Date"]).set_index("Date")["close"].sort_index()
    cal = spy.index

    statut = {}
    for tk in tickers:
        if tk not in have:
            statut[tk] = "sans_prix"
            continue
        s = (pd.read_csv(PX / f"{tk}.csv", parse_dates=["Date"])
               .set_index("Date")["close"].sort_index())
        sm = s.reindex(cal).ffill().dropna()
        if len(sm) < 2 or sm.min() < 0.10 or sm.pct_change().abs().max() > 3.0:
            statut[tk] = "prix_corrompu"
        else:
            statut[tk] = "couvert"

    out = pd.DataFrame({"ticker_yahoo": list(statut), "statut_prix": list(statut.values())})
    out = out.sort_values("ticker_yahoo").reset_index(drop=True)
    dest = RACINE / "00_recuperation_donnees" / "data" / "reference" / \
        f"couverture_prix_v{date.today():%Y%m%d}.csv"
    out.to_csv(dest, index=False)
    print(f"{dest.name} : {len(out)} tickers — {dict(out.statut_prix.value_counts())}")
    return dest


if __name__ == "__main__":
    extraire()
