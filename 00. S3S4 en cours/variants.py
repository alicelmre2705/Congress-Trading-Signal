"""S3S4 / variants — filtres & pondérations alternatives (conviction, dé-concentration par membre).

Sert à tester équitablement l'hypothèse « conviction » sans la caricaturer par le size brut (où une
poignée de méga-trades écrase tout).
"""
import numpy as np
import pandas as pd


def conviction_mask(buys: pd.DataFrame, window_days: int = 30, min_members: int = 2) -> pd.Series:
    """True si le ticker a été acheté par ≥ min_members membres DISTINCTS dans ±window_days autour du
    `filed` de l'achat (signal de consensus / cluster)."""
    mask = pd.Series(False, index=buys.index)
    W = np.timedelta64(window_days, "D")
    for _, g in buys.groupby("ticker"):
        g = g.sort_values("filed")
        f = g["filed"].values
        mem = g["bioguide"].values
        idx = g.index.values
        for i in range(len(g)):
            j0 = np.searchsorted(f, f[i] - W, side="left")
            j1 = np.searchsorted(f, f[i] + W, side="right")
            if len(set(mem[j0:j1])) >= min_members:
                mask.iloc[mask.index.get_loc(idx[i])] = True
    return mask


def member_dampen_raw(positions: pd.DataFrame) -> np.ndarray:
    """Poids brut = 1/√(nb d'achats du membre) → atténue les déposants prolifiques (Khanna, McCaul)
    pour que le portefeuille ne soit pas piloté par 2-3 personnes."""
    cnt = positions["bioguide"].map(positions["bioguide"].value_counts())
    return (1.0 / np.sqrt(cnt.values.astype(float)))
