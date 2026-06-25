#!/usr/bin/env python
"""Récupère le bulk Quiver (1 appel API) et sauvegarde les transactions House au niveau
transaction dans data_v1/tables/_quiver_house_cache.csv — pour adjuger les écarts ligne à ligne
sans re-frapper l'API. Quiver = vérification externe uniquement."""
import os
from pathlib import Path
import pandas as pd
import requests
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*a, **k): return False

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")
TAB = HERE / "data_v1" / "tables"

token = os.environ.get("QUIVER_API_KEY") or os.environ.get("QUIVER_API_TOKEN")
assert token, "QUIVER_API_KEY absent"
r = requests.get("https://api.quiverquant.com/beta/bulk/congresstrading",
                 headers={"Authorization": f"Bearer {token}"}, timeout=180)
q = pd.DataFrame(r.json())
print("bulk Quiver :", len(q), "lignes |", list(q.columns)[:14])

dcol = next(c for c in ["Filed", "ReportDate", "Disclosure_Date"] if c in q.columns)
tcol = next(c for c in ["Traded", "Trade_Date", "TransactionDate"] if c in q.columns)
q["filed"] = pd.to_datetime(q[dcol], errors="coerce")
q["traded"] = pd.to_datetime(q[tcol], errors="coerce")
house = q[q["Chamber"].str.contains("Rep", na=False)].copy()
house["disclosure_year"] = house["filed"].dt.year
keep = [c for c in ["BioGuideID", "Name", "Ticker", "Transaction", "traded", "filed",
                    "disclosure_year", "Trade_Size_USD", "Range", "Party", "District"] if c in house.columns]
house = house[keep]
out = TAB / "_quiver_house_cache.csv"
house.to_csv(out, index=False)
print(f"→ {out} : {len(house)} txns House | années {sorted(house['disclosure_year'].dropna().unique().astype(int).tolist())}")
print(house["disclosure_year"].value_counts().sort_index().to_string())
