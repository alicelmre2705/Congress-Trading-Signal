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


def member_scores(buys: pd.DataFrame, com: pd.Series, year: int,
                  ucb_c: float = 0.5, min_trades: int = 10) -> pd.DataFrame:
    """Scores des membres sur les données ≤ `year` (achats avec colonne `car` = rendement par trade).
    score = Sharpe rétréci + UCB1 (exploration). Renvoie un DataFrame trié par score décroissant."""
    past = buys[(buys["filed"].dt.year <= year) & buys["car"].notna()]
    g = past.groupby("bioguide")
    n = g.size()
    elig = n[n >= min_trades].index
    if not len(elig):
        return pd.DataFrame(columns=["bioguide", "n", "sharpe_brut", "shrunk", "ucb", "score", "key"])
    # moyenne de groupe des Sharpe bruts (cible du rétrécissement)
    raw = {b: (past[past.bioguide == b]["car"].mean() / (past[past.bioguide == b]["car"].std(ddof=1) + 1e-9))
           for b in elig}
    grp_mean = float(np.nanmean(list(raw.values())))
    N = int(n[elig].sum())
    rows = []
    for b in elig:
        arr = past[past.bioguide == b]["car"].values
        sh = shrunk_sharpe(arr, grp_mean)
        ni = len(arr)
        ucb = ucb_c * np.sqrt(np.log(N) / ni)
        rows.append({"bioguide": b, "name": past[past.bioguide == b]["name"].iloc[0],
                     "n": ni, "sharpe_brut": raw[b], "shrunk": sh, "ucb": ucb,
                     "score": sh + ucb, "key": is_key(b, com)})
    return pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)


def select_K(buys: pd.DataFrame, com: pd.Series, year: int, K: int,
             ucb_c: float = 0.5, key_frac: float = 0.5) -> list:
    """Top-K par score, en imposant ≥ key_frac·K membres de commission clé (règle Ramify)."""
    sc = member_scores(buys, com, year, ucb_c=ucb_c)
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
