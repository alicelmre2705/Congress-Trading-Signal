"""S3S4 / selection — sélection ANNUELLE ROLLING des K congressmen (cœur de la stratégie Ramify).

Spéc Ramify : fin d'année Y, parmi les éligibles (≥10 trades), classer par **Sharpe RÉTRÉCI vers la
moyenne du groupe** (Mauboussin — pénalise les petits échantillons / la chance), avec une touche
d'**exploration UCB1** ; prendre **K∈{4,6,8,10}** dont **≥ la moitié en commission clé**
(Finance / Defense / Intelligence) ; suivre LEURS achats l'année **Y+1** ; rebalancer chaque année.

Pur (pas d'I/O prix) : le caller fournit `buys` avec une colonne `car` (rendement anormal par trade,
ex. CAR 12 mois vs SPY via `evaluate.car_event`) — c'est la « série de trades » à évaluer.
Réutilise `portfolio`/`evaluate` côté caller (notebook 03).
"""
import glob
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# Commissions clés Ramify (matché sur le libellé de committee_membership des tables FINAL).
KEY_PATTERNS = ("Financial Services", "Committee on Finance", "Ways and Means", "Banking",  # Finance
                "Armed Services",                                                            # Defense
                "Intelligence")                                                              # Intelligence


def load_committees() -> pd.Series:
    """bioguide → libellé concaténé des commissions (depuis les 14 tables FINAL House+Sénat)."""
    fs = (glob.glob(os.path.join(REPO, "data/house/tables/*/06_house_*_FINAL.csv")) +
          glob.glob(os.path.join(REPO, "data/senate/*/06_senate_*_FINAL.csv")))
    fin = pd.concat([pd.read_csv(f, dtype=str, usecols=["bioguide_id", "committee_membership"])
                     for f in fs], ignore_index=True).dropna()
    return fin.groupby("bioguide_id")["committee_membership"].agg(lambda s: " ; ".join(s.unique()))


def is_key(bio, com: pd.Series) -> bool:
    """Le membre siège-t-il dans au moins une commission Finance/Defense/Intelligence ?"""
    txt = com.get(bio, "") or ""
    return any(p in txt for p in KEY_PATTERNS)


def shrunk_sharpe(returns: np.ndarray, grp_mean: float, k: int = 10) -> float:
    """Sharpe de la série de trades RÉTRÉCI vers la moyenne du groupe (Mauboussin / James-Stein).
    Poids `w = n/(n+k)` : peu de trades → on croit surtout à la moyenne du groupe (anti-chance)."""
    r = returns[~np.isnan(returns)]
    n = len(r)
    if n < 2:
        return grp_mean
    sr = r.mean() / (r.std(ddof=1) + 1e-9)
    w = n / (n + k)
    return w * sr + (1 - w) * grp_mean


def member_scores(buys: pd.DataFrame, com: pd.Series, year: int, ucb_c: float = 0.5,
                  min_trades: int = 10, ret_col: str = "tret", exit_col: str = "exit_d") -> pd.DataFrame:
    """Scores des membres sur les trades CLÔTURÉS au 31/12/`year` (sortie ≤ fin d'année → aucun look-ahead :
    on ne note un trade que quand son issue est connue). `ret_col` = rendement RÉALISÉ par trade
    (entrée→sortie, cf. `with_realized`) = la « série de trades » du brief. score = Sharpe rétréci
    (Mauboussin) + UCB1 (exploration, Sutton & Barto). DataFrame trié par score décroissant."""
    cutoff = pd.Timestamp(year, 12, 31)
    past = buys[(buys[exit_col] <= cutoff) & buys[ret_col].notna()]
    g = past.groupby("bioguide")[ret_col]
    n = g.size()
    elig = n[n >= min_trades].index
    if not len(elig):
        return pd.DataFrame(columns=["bioguide", "name", "n", "sharpe_brut", "shrunk", "ucb", "score", "key"])
    mean, std = g.mean(), g.std(ddof=1)
    raw = (mean / (std + 1e-9)).reindex(elig)                 # Sharpe brut par membre
    grp_mean = float(raw.mean())                             # cible du rétrécissement (moyenne du groupe)
    N = int(n[elig].sum())
    name_of = past.drop_duplicates("bioguide").set_index("bioguide")["name"]
    rows = []
    for b in elig:
        arr = past.loc[past.bioguide == b, ret_col].values
        ni = len(arr)
        rows.append({"bioguide": b, "name": name_of.get(b, b), "n": ni,
                     "sharpe_brut": float(raw[b]), "shrunk": shrunk_sharpe(arr, grp_mean),
                     "ucb": ucb_c * np.sqrt(np.log(N) / ni), "key": is_key(b, com)})
    out = pd.DataFrame(rows)
    out["score"] = out["shrunk"] + out["ucb"]
    return out.sort_values("score", ascending=False).reset_index(drop=True)


def select_K(buys: pd.DataFrame, com: pd.Series, year: int, K: int,
             ucb_c: float = 0.5, key_frac: float = 0.5, ret_col: str = "tret") -> list:
    """Top-K par score, en imposant ≥ key_frac·K membres de commission clé (règle Ramify)."""
    sc = member_scores(buys, com, year, ucb_c=ucb_c, ret_col=ret_col)
    if not len(sc):
        return []
    need_key = int(np.ceil(key_frac * K))
    chosen, keys = [], 0
    # 1) on remplit en privilégiant le score, mais on garantit le quota de commissions clés
    for _, r in sc.iterrows():
        if len(chosen) >= K:
            break
        remaining = K - len(chosen)
        if (not r["key"]) and (K - keys) <= need_key and remaining <= (need_key - keys):
            continue  # garder de la place pour atteindre le quota clé
        chosen.append(r["bioguide"]); keys += int(r["key"])
    # 2) compléter le quota clé si pas atteint
    if keys < need_key:
        for _, r in sc[sc["key"]].iterrows():
            if keys >= need_key or len(chosen) >= K:
                break
            if r["bioguide"] not in chosen:
                chosen.append(r["bioguide"]); keys += 1
    return chosen[:K]


def selections_by_year(buys, com, K, start=2015, end=2025, **kw) -> dict:
    """{Y: liste des K sélectionnés sur données ≤Y} → s'applique aux achats de l'année Y+1."""
    return {y: select_K(buys, com, y, K, **kw) for y in range(start, end + 1)}


def with_realized(buys: pd.DataFrame, df_all: pd.DataFrame, panel: pd.DataFrame,
                  spy: pd.Series, horizon_months: int = 12) -> pd.DataFrame:
    """Renvoie une copie de `buys` enrichie de la « série de trades » du brief : `tret` (rendement ANORMAL
    réalisé entrée `filed`+1 → sortie vente/+`horizon_months`, vs SPY) et `exit_d` (date de sortie, pour
    filtrer les trades clôturés sans look-ahead). Sert à scorer la sélection sur ce que la stratégie
    réalise vraiment (et non un proxy CAR fixe)."""
    import portfolio
    import evaluate
    pos = portfolio.build_positions(buys, df_all, horizon_months=horizon_months)
    tr = evaluate.trade_returns(pos, panel, spy, lag_days=1)
    out = buys.copy()
    out["tret"] = tr["abn"].values
    out["exit_d"] = pos["exit"].values
    out["win"] = out["tret"] > 0
    return out


def sector_breadth(buys: pd.DataFrame, sector_map: dict, window_days: int = 90) -> pd.Series:
    """Pour chaque achat : nombre de membres DISTINCTS ayant acheté le MÊME secteur sur la fenêtre
    glissante causale [filed-`window_days`, filed]. Mesure la *breadth* sectorielle (Grinold-Kahn) —
    sert à la V2 pilotée par breadth (SUPP_C). `sector_map` : ticker → secteur (ou ETF). 0 si non mappé."""
    b = buys.copy()
    b["_sec"] = b["ticker"].map(sector_map)
    out = pd.Series(0.0, index=buys.index)
    for _sec, g in b.dropna(subset=["_sec"]).groupby("_sec"):
        g = g.sort_values("filed")
        filed = g["filed"].values
        bios = g["bioguide"].values
        idx = g.index.values
        lo = 0
        for i in range(len(g)):
            while filed[i] - filed[lo] > np.timedelta64(window_days, "D"):
                lo += 1
            out.loc[idx[i]] = len(set(bios[lo:i + 1]))
    return out


def gate_buys(buys: pd.DataFrame, selections: dict) -> pd.DataFrame:
    """Ne garde que les achats dont le membre était SÉLECTIONNÉ pour l'année de leur `filed`
    (sélection faite sur l'année précédente). C'est la stratégie rolling, sans look-ahead."""
    keep = []
    for r in buys.itertuples(index=False):
        sel = selections.get(r.filed.year - 1)
        keep.append(bool(sel) and r.bioguide in sel)
    return buys[pd.Series(keep, index=buys.index)].copy()


# ───────────── V2 : substitution action → ETF sectoriel ─────────────
def ticker_to_etf() -> dict:
    """ticker → ETF SPDR sectoriel, via `sector_gics` des tables FINAL + GICS_TO_ETF de congress_core."""
    import sys
    sys.path.insert(0, REPO)
    from congress_core.sector_enrich import GICS_TO_ETF
    fs = (glob.glob(os.path.join(REPO, "data/house/tables/*/06_house_*_FINAL.csv")) +
          glob.glob(os.path.join(REPO, "data/senate/*/06_senate_*_FINAL.csv")))
    fin = pd.concat([pd.read_csv(f, dtype=str, usecols=["ticker", "sector_gics"]) for f in fs],
                    ignore_index=True).dropna()
    sec = fin.groupby("ticker")["sector_gics"].agg(lambda s: s.value_counts().index[0])
    return {t: GICS_TO_ETF.get(g) for t, g in sec.items() if GICS_TO_ETF.get(g)}


def to_v2(positions: pd.DataFrame, t2e: dict) -> pd.DataFrame:
    """Remplace le ticker de chaque position par son ETF sectoriel (logique d'entrée/sortie inchangée)."""
    p = positions.copy()
    p["ticker"] = p["ticker"].map(t2e)
    return p.dropna(subset=["ticker"])
