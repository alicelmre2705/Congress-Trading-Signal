#!/usr/bin/env python
"""Cache prix v2 pour la recherche — construit sur `ticker_yahoo` de la table canonique.

- Symboles : renommages/fusions DÉJÀ appliqués par la table (data/reference/ticker_renames.csv).
- Resumable : un CSV présent et non vide n'est pas re-téléchargé ; les échecs sont RE-tentés à
  chaque run (pas de liste noire définitive — leçon de l'audit : MMC/DENN/FI étaient des échecs
  transitoires bloqués à vie par l'ancien failed_tickers.txt).
- Échecs classés dans failed_v2.csv : delisting_attendu (référentiel) vs inattendu (à re-tenter).

Usage : .venv/bin/python build_prices_v2.py
"""
import logging
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

for noisy in ("yfinance", "urllib3", "peewee"):
    logging.getLogger(noisy).setLevel(logging.CRITICAL)

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CLEAN = REPO / "00_S1S2_donnees" / "data" / "clean" / "transactions_backtest_2014_2026.csv"
RENAMES = REPO / "00_S1S2_donnees" / "data" / "reference" / "ticker_renames.csv"
OUT = HERE / "cache" / "prices_v2"
OUT.mkdir(parents=True, exist_ok=True)

BENCH = ["SPY", "RSP", "QQQ", "XLE", "XLB", "XLI", "XLY", "XLP", "XLV", "XLF", "XLK", "XLC", "XLU", "XLRE"]
START = "2012-01-01"

df = pd.read_csv(CLEAN, dtype=str, usecols=["ticker_yahoo"])
tickers = sorted(set(df["ticker_yahoo"].dropna()) - {""}) + [b for b in BENCH]
tickers = list(dict.fromkeys(tickers))
ren = pd.read_csv(RENAMES, dtype=str)
delisted = set(ren.loc[ren["type"].isin(["rachat_delisting", "faillite_delisting"]), "ticker_ancien"])

print(f"{len(tickers)} symboles à couvrir → {OUT}")
ok = skip = 0
fails = []
for i, tk in enumerate(tickers, 1):
    dest = OUT / f"{tk}.csv"
    if dest.exists() and dest.stat().st_size > 200:
        skip += 1
        continue
    got = False
    for attempt in range(3):
        try:
            h = yf.Ticker(tk).history(start=START, auto_adjust=True)
            if len(h) >= 30:
                out = h["Close"].rename("close").reset_index()
                out["Date"] = pd.to_datetime(out["Date"]).dt.date
                out.to_csv(dest, index=False)
                ok += 1
                got = True
                break
            # série vide/trop courte : delisté chez Yahoo → pas la peine d'insister
            break
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    if not got:
        fails.append({"ticker": tk, "classe": "delisting_attendu" if tk in delisted else "inattendu"})
    if i % 250 == 0:
        print(f"  {i}/{len(tickers)} | ok {ok} | déjà {skip} | échecs {len(fails)}", flush=True)
    time.sleep(0.25)

pd.DataFrame(fails).to_csv(OUT / "failed_v2.csv", index=False)
n_att = sum(1 for f in fails if f["classe"] == "delisting_attendu")
print(f"\nTERMINÉ : {ok} téléchargés + {skip} déjà présents | échecs {len(fails)} "
      f"(dont {n_att} délistages attendus, {len(fails) - n_att} inattendus → re-tenter au prochain run)")
