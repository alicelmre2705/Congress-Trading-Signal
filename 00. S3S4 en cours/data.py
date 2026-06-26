"""S3S4 / data — journal des transactions du Congrès depuis Quiver (2014+), LECTURE SEULE.

Charge les deux caches Quiver embarqués (House + Sénat ; colonnes différentes), normalise, et renvoie
un journal unifié des transactions (achats ET ventes). Aucune écriture hors `00. S3S4 en cours/`.

Caches lus (jamais modifiés) :
  - data/house/tables/_quiver_house_cache.csv        (cols: ..., traded, filed, District)
  - data/senate/reference/_quiver_senate_cache.csv   (cols: ..., Traded, Filed, State)

Colonnes de sortie : chamber, bioguide, name, ticker (yfinance-ready), op (buy/sell/exch),
traded, filed, size_usd (borne basse fourchette $), party.
"""
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
HOUSE_CACHE = REPO / "data" / "house" / "tables" / "_quiver_house_cache.csv"
SENATE_CACHE = REPO / "data" / "senate" / "reference" / "_quiver_senate_cache.csv"

# Bornes basses des fourchettes STOCK Act ($). Sert à « nettoyer » Trade_Size_USD (qq valeurs aberrantes).
MIN_BRACKET = 1001.0


def _norm_op(x: str) -> str:
    s = str(x).lower()
    if "purchase" in s:
        return "buy"
    if "sale" in s:
        return "sell"
    if "exchange" in s:
        return "exch"
    return "other"


def _norm_ticker(t):
    """Garde les tickers cotés propres ; convertit le point en tiret pour yfinance (BRK.B→BRK-B).
    Rejette le bruit (ex. '3.MONTH, MATURE')."""
    if not isinstance(t, str):
        return None
    s = t.strip().upper()
    if re.fullmatch(r"[A-Z]{1,5}", s):
        return s
    if re.fullmatch(r"[A-Z]{1,4}\.[A-Z]", s):
        return s.replace(".", "-")
    return None


def _load_one(path: Path, chamber: str) -> pd.DataFrame:
    d = pd.read_csv(path, dtype=str)
    # noms de colonnes harmonisés (House: traded/filed/District ; Sénat: Traded/Filed/State)
    ren = {"Traded": "traded", "Filed": "filed", "District": "state_dist", "State": "state_dist"}
    d = d.rename(columns={k: v for k, v in ren.items() if k in d.columns})
    out = pd.DataFrame({
        "chamber": chamber,
        "bioguide": d.get("BioGuideID"),
        "name": d.get("Name"),
        "ticker": d.get("Ticker").map(_norm_ticker),
        "op": d.get("Transaction").map(_norm_op),
        "traded": pd.to_datetime(d.get("traded"), errors="coerce"),
        "filed": pd.to_datetime(d.get("filed"), errors="coerce"),
        "size_usd": pd.to_numeric(d.get("Trade_Size_USD"), errors="coerce").clip(lower=MIN_BRACKET),
        "party": d.get("Party"),
    })
    return out


def load_transactions(min_year: int = 2014, max_year: int = 2026) -> pd.DataFrame:
    """Journal unifié House+Sénat, filtré sur les `filed` valides dans [min_year, max_year]."""
    df = pd.concat([_load_one(HOUSE_CACHE, "house"), _load_one(SENATE_CACHE, "senate")],
                   ignore_index=True)
    df = df[df["filed"].notna() & df["traded"].notna()]
    df = df[(df["filed"].dt.year >= min_year) & (df["filed"].dt.year <= max_year)]
    return df.reset_index(drop=True)


def buy_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Achats tickés = signaux d'entrée (long)."""
    b = df[(df["op"] == "buy") & df["ticker"].notna()].copy()
    return b.reset_index(drop=True)


def _summary():
    df = load_transactions()
    b = buy_signals(df)
    print(f"Transactions Quiver 2014-2026 : {len(df):,}".replace(",", " "))
    print(f"  par chambre : {df['chamber'].value_counts().to_dict()}")
    print(f"  par op : {df['op'].value_counts().to_dict()}")
    print(f"  filed : {df['filed'].min().date()} → {df['filed'].max().date()}")
    print(f"\nSignaux d'ACHAT tickés : {len(b):,}".replace(",", " "))
    print(f"  tickers distincts : {b['ticker'].nunique()}")
    print(f"  membres distincts : {b['bioguide'].nunique()}")
    print(f"  top 5 membres (achats) : {b['name'].value_counts().head(5).to_dict()}")
    print(f"  size_usd (borne basse) médiane : {b['size_usd'].median():,.0f} $".replace(",", " "))
    print(f"  achats/an (filed) : {b.groupby(b['filed'].dt.year).size().to_dict()}")


if __name__ == "__main__":
    _summary()
