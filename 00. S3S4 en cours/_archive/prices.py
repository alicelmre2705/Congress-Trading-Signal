"""S3S4 / prices — prix ajustés (yfinance) + benchmark SPY + facteurs Fama-French, avec CACHE disque.

Tout est mis en cache sous `00. S3S4 en cours/cache/` → un 2ᵉ run ne re-télécharge rien. Les tickers
introuvables (délistés) sont marqués pour **borner le biais de survivorship**.
"""
import time
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
PX_DIR = CACHE / "prices"
FAIL_FILE = CACHE / "failed_tickers.txt"
FACT_FILE = CACHE / "ff_factors.csv"
SPY_FILE = PX_DIR / "SPY.csv"


def _failed() -> set:
    return set(FAIL_FILE.read_text().split()) if FAIL_FILE.exists() else set()


def ensure_prices(tickers, start="2013-06-01", end="2026-06-26", batch=60):
    """Télécharge (yfinance, auto_adjust) les tickers absents du cache, 1 CSV/ticker. Résumable."""
    import yfinance as yf
    PX_DIR.mkdir(parents=True, exist_ok=True)
    failed = _failed()
    todo = [t for t in dict.fromkeys(tickers)
            if not (PX_DIR / f"{t}.csv").exists() and t not in failed]
    if not todo:
        return
    print(f"  prix à télécharger : {len(todo)} (cache : {len(list(PX_DIR.glob('*.csv')))} déjà là)")
    new_fail = []
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        try:
            data = yf.download(chunk, start=start, end=end, auto_adjust=True,
                               progress=False, threads=True, group_by="ticker")
        except Exception as e:
            print(f"    batch {i//batch} KO ({str(e)[:60]}) — réessai unitaire")
            data = None
        for t in chunk:
            s = None
            try:
                if data is not None and isinstance(data.columns, pd.MultiIndex) and t in data.columns.levels[0]:
                    s = data[t]["Close"].dropna()
                elif data is not None and "Close" in getattr(data, "columns", []):
                    s = data["Close"].dropna()
            except Exception:
                s = None
            if s is None or len(s) < 20:
                new_fail.append(t)
            else:
                s.rename("close").to_csv(PX_DIR / f"{t}.csv")
        time.sleep(0.4)
    if new_fail:
        with open(FAIL_FILE, "a") as f:
            f.write("\n".join(new_fail) + "\n")
        print(f"  introuvables (délistés/échec) : {len(new_fail)}")


def load_panel(tickers) -> pd.DataFrame:
    """Panneau (dates × tickers) des cours ajustés présents en cache."""
    cols = {}
    for t in dict.fromkeys(tickers):
        p = PX_DIR / f"{t}.csv"
        if p.exists():
            s = pd.read_csv(p, index_col=0, parse_dates=True)["close"]
            cols[t] = s
    if not cols:
        raise RuntimeError("Aucun prix en cache — lance ensure_prices d'abord.")
    return pd.DataFrame(cols).sort_index()


def get_spy(start="2013-06-01", end="2026-06-26") -> pd.Series:
    import yfinance as yf
    if not SPY_FILE.exists():
        PX_DIR.mkdir(parents=True, exist_ok=True)
        s = yf.download("SPY", start=start, end=end, auto_adjust=True, progress=False)["Close"].dropna()
        s = s.iloc[:, 0] if isinstance(s, pd.DataFrame) else s
        s.rename("close").to_csv(SPY_FILE)
    return pd.read_csv(SPY_FILE, index_col=0, parse_dates=True)["close"]


def get_factors() -> pd.DataFrame:
    """Facteurs quotidiens Fama-French (Mkt-RF, SMB, HML, RF) + momentum (Mom), via Ken French."""
    if FACT_FILE.exists():
        return pd.read_csv(FACT_FILE, index_col=0, parse_dates=True)
    import pandas_datareader.data as web
    ff = web.DataReader("F-F_Research_Data_Factors_daily", "famafrench", start="2013-01-01")[0] / 100.0
    try:
        mom = web.DataReader("F-F_Momentum_Factor_daily", "famafrench", start="2013-01-01")[0] / 100.0
        mom.columns = ["Mom"]
        ff = ff.join(mom)
    except Exception:
        pass
    ff.index = ff.index.to_timestamp() if hasattr(ff.index, "to_timestamp") else pd.to_datetime(ff.index)
    CACHE.mkdir(parents=True, exist_ok=True)
    ff.to_csv(FACT_FILE)
    return ff


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE))
    import data
    b = data.buy_signals(data.load_transactions())
    top = b["ticker"].value_counts()
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    universe = list(top.head(K).index)
    print(f"Univers : top-{K} tickers ({top.head(K).sum()/len(b)*100:.1f}% des achats)")
    ensure_prices(universe)
    get_spy()
    panel = load_panel(universe)
    fac = get_factors()
    got = panel.shape[1]
    print(f"\nPrix en cache : {got}/{K} tickers | délistés/échec : {len(_failed())}")
    print(f"  panel : {panel.shape[0]} jours, {panel.index.min().date()} → {panel.index.max().date()}")
    print(f"  facteurs FF : {list(fac.columns)} ({fac.index.min().date()} → {fac.index.max().date()})")
    print(f"  SPY : {len(get_spy())} jours")
