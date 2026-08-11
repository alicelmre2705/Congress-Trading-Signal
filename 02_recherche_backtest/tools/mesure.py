"""La boîte à outils de mesure de la lignée titre — extraite du notebook 16 (§5).

⚠️ Convention : α = Jensen (rendements EN EXCÈS du taux sans risque des deux côtés),
annualisé ×252 arithmétique ; « excès » = moyenne des écarts d'années civiles au SPY.
La lignée « membre » (05b/07/09/12) régresse le rendement brut et annualise en géométrique :
ses chiffres ne sont pas comparables à ceux-ci.

Chaque run passé à `bilan` laisse son nom dans ESSAIS — le compteur de multiplicité :
tout essai compte, tout essai se publie (FICHE_M3, annexe D).
"""
import numpy as np
import pandas as pd
from scipy import stats

FACS = ["Mkt-RF", "SMB", "HML", "Mom"]
ESSAIS = []          # le compteur de multiplicité — ne jamais le remettre à zéro en cours d'étude


def bilan(D, Vx, nom):
    ESSAIS.append(nom)
    rx = Vx.pct_change().dropna()
    ax = pd.DataFrame({"s": rx.groupby(rx.index.year).apply(lambda z: float((1 + z).prod() - 1)),
                       "m": D.r_spy.reindex(rx.index).fillna(0).groupby(rx.index.year)
                                 .apply(lambda z: float((1 + z).prod() - 1))})
    xx = (ax.s - ax.m).values
    dd = pd.DataFrame({"p": rx, "m": D.r_spy.reindex(rx.index)}).join(D.FF[["RF"]]).dropna()
    yy, XX = (dd.p - dd.RF).values, (dd.m - dd.RF).values
    b, a = np.polyfit(XX, yy, 1)
    ee = yy - (a + b * XX)
    return {"run": nom, "excès %/an": 100 * xx.mean(),
            "t": xx.mean() / (xx.std(ddof=1) / np.sqrt(len(xx))),
            "α %/an": 252 * a * 100, "t_α": a / (ee.std(ddof=2) / np.sqrt(len(yy))), "β": b,
            "NAV": Vx.iloc[-1], "ann. gagnantes": f"{int((xx > 0).sum())}/{len(xx)}"}


def bilan_ic(D, Vx, nom):
    # bilan() + l'intervalle de confiance de Student de l'excès annuel moyen
    rx = Vx.pct_change().dropna()
    ax = pd.DataFrame({"s": rx.groupby(rx.index.year).apply(lambda z: float((1 + z).prod() - 1)),
                       "m": D.r_spy.reindex(rx.index).fillna(0).groupby(rx.index.year)
                                 .apply(lambda z: float((1 + z).prod() - 1))})
    xx = (ax.s - ax.m).values
    n, se = len(xx), xx.std(ddof=1) / np.sqrt(len(xx))
    q = float(stats.t.ppf(0.975, n - 1))
    b = dict(bilan(D, Vx, nom))
    b.update({"n ans": n, "IC bas": 100 * (xx.mean() - q * se), "IC haut": 100 * (xx.mean() + q * se)})
    return b


def facteurs(D, Vx, nom, cols=FACS):
    # OLS multi-facteurs, erreurs-types analytiques ; α annualisé ×252
    r = Vx.pct_change().dropna().rename("r")
    d = pd.DataFrame(r).join(D.FF, how="inner").dropna()
    y = (d.r - d.RF).values
    X = np.column_stack([np.ones(len(d))] + [d[c].values for c in cols])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    s2 = float(e @ e) / (len(y) - X.shape[1])
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    o = {"run": nom, "α %/an": 252 * 100 * b[0], "t_α": b[0] / se[0]}
    for j, c in enumerate(cols, 1):
        o[c] = b[j]
        o["t " + c] = b[j] / se[j]
    o["n j"] = len(y)
    return o


def annuel(D, Vx):
    rx = Vx.pct_change().dropna()
    s = rx.groupby(rx.index.year).apply(lambda z: float((1 + z).prod() - 1))
    m = D.r_spy.reindex(rx.index).fillna(0).groupby(rx.index.year).apply(lambda z: float((1 + z).prod() - 1))
    return (100 * s).round(1), (100 * m).round(1), (100 * (s - m)).round(1)


def cagr(s, i0=None):
    s = s.dropna()
    if i0 is not None:
        s = s[s.index >= i0]
    return (s.iloc[-1] / s.iloc[0]) ** (252 / len(s)) - 1


def conc(w):
    # w : une Series de poids EN POURCENTS, triée décroissante → (top1, top5, N_eff)
    p = (w / w.sum()).values
    return round(float(w.iloc[0]), 1), round(float(w.head(5).sum()), 1), round(1 / float(np.sum(p ** 2)), 1)


def roll_ab(D, span, fenetre=252):
    r = span.pct_change().dropna()
    d = pd.DataFrame({"y": r, "m": D.r_spy.reindex(r.index)}).join(D.FF[["RF"]]).dropna()
    y, x = d.y - d.RF, d.m - d.RF
    beta = y.rolling(fenetre).cov(x) / x.rolling(fenetre).var()
    alpha = (y.rolling(fenetre).mean() - beta * x.rolling(fenetre).mean()) * 252 * 100
    return alpha.dropna(), beta.dropna(), y, x
