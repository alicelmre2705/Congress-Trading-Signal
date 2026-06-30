"""S3S4 / portfolio — moteur event-driven, série de rendements NETTE de coûts.

Entrée : achat divulgué → ouverture à `filed` + 1 jour de bourse (sans look-ahead).
Sortie : 1ʳᵉ vente correspondante (même membre+ticker) OU `filed` + horizon H mois, au PREMIER des deux.
Portefeuille long-only rebalancé quotidiennement ; pondération equal / size (`Trade_Size_USD`) ;
coûts de transaction appliqués sur le turnover quotidien.
"""
import numpy as np
import pandas as pd


def build_positions(buys: pd.DataFrame, df_all: pd.DataFrame, horizon_months: int = 6) -> pd.DataFrame:
    """Pour chaque achat : (entrée=filed, sortie=min(vente correspondante, filed+H), raw=size/1)."""
    sells = df_all[(df_all["op"] == "sell") & df_all["ticker"].notna()]
    sell_map = {k: np.sort(g["filed"].values) for k, g in sells.groupby(["bioguide", "ticker"])}
    H = pd.DateOffset(months=horizon_months)
    rows = []
    for r in buys.itertuples(index=False):
        forced = r.filed + H
        arr = sell_map.get((r.bioguide, r.ticker))
        exit_d = forced
        if arr is not None:
            later = arr[arr > np.datetime64(r.filed)]
            if len(later):
                exit_d = min(forced, pd.Timestamp(later[0]))
        rows.append((r.bioguide, r.ticker, r.filed, exit_d, float(r.size_usd)))
    return pd.DataFrame(rows, columns=["bioguide", "ticker", "entry", "exit", "size_usd"])


def run_portfolio(positions: pd.DataFrame, panel: pd.DataFrame, weighting="size",
                  cost_bps=20.0, lag_days=1) -> dict:
    """Série quotidienne de rendements nets. `panel` = cours ajustés (jours × tickers).
    weighting: 'equal' | 'size'. cost_bps = coût ONE-WAY en points de base."""
    idx = panel.index
    tickers = list(panel.columns)
    tpos = {t: i for i, t in enumerate(tickers)}
    ret = panel.pct_change().fillna(0.0).values            # (D × N)
    D, N = ret.shape

    pos = positions[positions["ticker"].isin(tpos)].copy()
    if "raw" in pos.columns:                       # poids brut fourni par l'appelant
        raw = pos["raw"].values.astype(float)
    elif weighting == "size":
        raw = pos["size_usd"].values
    elif weighting == "sqrt_size":
        raw = np.sqrt(pos["size_usd"].values)
    else:
        raw = np.ones(len(pos))

    # entrée = 1er jour de bourse >= filed + lag ; sortie idem >= exit
    entry_i = idx.searchsorted(pos["entry"].values + np.timedelta64(lag_days, "D"), side="left")
    exit_i = idx.searchsorted(pos["exit"].values, side="left")
    tk_i = pos["ticker"].map(tpos).values

    deltas = np.zeros((D + 1, N))                          # +raw à l'entrée, -raw à la sortie
    valid = entry_i < D
    np.add.at(deltas, (entry_i[valid], tk_i[valid]), raw[valid])
    ex = np.clip(exit_i, 0, D)
    np.add.at(deltas, (ex[valid], tk_i[valid]), -raw[valid])
    held = np.cumsum(deltas[:D], axis=0)                   # poids bruts détenus par jour (D × N)
    held[held < 0] = 0.0

    tot = held.sum(axis=1, keepdims=True)
    w = np.divide(held, tot, out=np.zeros_like(held), where=tot > 0)   # poids normalisés
    w_prev = np.vstack([np.zeros((1, N)), w[:-1]])
    gross = (w_prev * ret).sum(axis=1)                     # rendement gagné = poids de la veille
    turnover = np.abs(w - w_prev).sum(axis=1)              # one-way
    cost = (cost_bps / 1e4) * turnover
    net = gross - cost

    s_gross = pd.Series(gross, index=idx)
    s_net = pd.Series(net, index=idx)
    active = tot.ravel() > 0
    return {
        "gross": s_gross, "net": s_net,
        "turnover_daily": pd.Series(turnover, index=idx),
        "n_positions": len(pos), "n_dropped_no_price": len(positions) - len(pos),
        "active_from": idx[active][0] if active.any() else None,
        "avg_holdings": float((held > 0).sum(axis=1)[active].mean()) if active.any() else 0.0,
    }


def perf_vs_spy(daily: pd.Series, spy: pd.Series) -> dict:
    """CAGR, vol, Sharpe, alpha simple vs SPY, max DD, % jours battant SPY — sur la période active."""
    daily = daily[daily.index >= daily[daily != 0].index.min()].dropna()
    spy_r = spy.pct_change().reindex(daily.index).fillna(0.0)
    yrs = (daily.index[-1] - daily.index[0]).days / 365.25
    cagr = (1 + daily).prod() ** (1 / yrs) - 1
    cagr_spy = (1 + spy_r).prod() ** (1 / yrs) - 1
    vol = daily.std() * np.sqrt(252)
    sharpe = (daily.mean() * 252) / (vol + 1e-12)
    eq = (1 + daily).cumprod()
    mdd = (eq / eq.cummax() - 1).min()
    return {
        "annees": round(yrs, 1), "CAGR": cagr, "CAGR_SPY": cagr_spy,
        "alpha_annuel_vs_SPY": cagr - cagr_spy, "vol": vol, "sharpe": sharpe,
        "max_drawdown": mdd, "pct_jours_>_SPY": float((daily > spy_r).mean()),
    }
