"""ANALYSE 1/6 — Information Coefficient (IC) cross-sectionnel.

QUESTION : existe-t-il de l'INFORMATION dans les trades du Congrès, indépendamment de toute
construction de portefeuille ? (Test quant standard : corrélation de rang signal ↔ rendement futur.)

MÉTHODE : panneau mensuel (ticker × mois). Pour chaque mois, on classe les tickers par un signal
(nb d'acheteurs distincts, net achats-ventes, montant net $…) et on corrèle (Spearman) avec le
rendement forward du titre à 1/3/6/12 mois. L'IC moyen sur ~140 mois mesure le pouvoir prédictif.
t-stat iid ET Newey-West (lag=horizon) pour corriger le chevauchement des fenêtres.
Entrée `filed` (date publique = INVESTISSABLE) et `traded` (date réelle = information privée, contrôle).

CONCLUSION REPRODUITE : signal FAIBLE mais réel. Le **nombre d'acheteurs distincts** (breadth) prédit
positivement (IC≈0,02 ; t_NW≈2,5 à 6 mois en `filed`, jusqu'à ~3,8 à 12 mois en `traded`). Seuls les
ACHATS informent (ventes ≈ bruit) ; le COMPTAGE bat le MONTANT $ ; ce n'est pas du beta (rang
cross-sectionnel). Mais spread quintile ~+1,5 %/an (t≈1,7), instable selon les régimes → sous le seuil
d'exploitabilité net de coûts.

Lancer : .venv/bin/python "00. S3S4 en cours/analyses/ic.py"
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))          # dossier S3S4 (data.py, prices.py)
import data, prices  # noqa: E402

HORIZONS = [1, 3, 6, 12]


def nw_tstat(x, lag):
    """t-stat de la moyenne avec erreur-type Newey-West (corrige l'autocorrélation des fenêtres)."""
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 5:
        return np.nan
    mu = x.mean()
    d = x - mu
    gamma0 = (d @ d) / n
    s = gamma0
    for k in range(1, min(lag, n - 1) + 1):
        cov = (d[k:] @ d[:-k]) / n
        s += 2 * (1 - k / (lag + 1)) * cov
    se = np.sqrt(s / n)
    return mu / se if se > 0 else np.nan


def monthly_forward_returns(panel):
    """Rendement forward h-mois par ticker, indexé fin de mois."""
    mpx = panel.resample("ME").last()
    return {h: (mpx.shift(-h) / mpx - 1.0) for h in HORIZONS}, mpx.index


def build_signals(df, date_col):
    """Signaux mensuels (ticker × mois) : nb d'acheteurs distincts, net comptage, net $, nb ventes."""
    d = df[df["ticker"].notna()].copy()
    d["m"] = d[date_col].dt.to_period("M").dt.to_timestamp("M")   # fin de mois
    buys = d[d["op"] == "buy"]
    sells = d[d["op"] == "sell"]
    sig = {}
    sig["buy_count"] = buys.groupby(["m", "ticker"])["bioguide"].nunique()
    sig["sell_count"] = sells.groupby(["m", "ticker"])["bioguide"].nunique()
    sig["net_count"] = sig["buy_count"].subtract(sig["sell_count"], fill_value=0)
    sig["net_usd"] = (buys.groupby(["m", "ticker"])["size_usd"].sum()
                      .subtract(sells.groupby(["m", "ticker"])["size_usd"].sum(), fill_value=0))
    return sig


def ic_table(sig, fwd, months, label):
    rows = []
    for name, s in sig.items():
        s = s[s != 0] if name in ("net_count", "net_usd") else s
        for h in HORIZONS:
            fr = fwd[h]
            ics = []
            for m in months:
                if m not in fr.index or m not in s.index.get_level_values(0):
                    continue
                sv = s.xs(m, level=0)
                rv = fr.loc[m]
                j = sv.index.intersection(rv.dropna().index)
                if len(j) >= 8:
                    ic = stats.spearmanr(sv.loc[j], rv.loc[j]).correlation
                    if not np.isnan(ic):
                        ics.append(ic)
            if len(ics) >= 10:
                ics = np.array(ics)
                rows.append({"date": label, "signal": name, "h_mois": h, "n_mois": len(ics),
                             "IC_moyen": round(ics.mean(), 4),
                             "t_iid": round(ics.mean() / (ics.std(ddof=1) / np.sqrt(len(ics))), 2),
                             "t_NW": round(nw_tstat(ics, h), 2),
                             "hit_pos_%": round(100 * (ics > 0).mean(), 0)})
    return pd.DataFrame(rows)


def breadth_spread(sig, fwd, months):
    """Traduction économique du signal breadth : rendement 6 mois des titres MULTI-acheteurs (≥2 membres
    distincts le même mois) − titres à acheteur UNIQUE (count=1), EW. (Les quintiles « purs » sont
    dégénérés car la plupart des titres ont count=1 ⇒ on oppose explicitement breadth haute vs basse.)"""
    s = sig["buy_count"]
    fr = fwd[6]
    spreads, years = [], []
    for m in months:
        if m not in fr.index or m not in s.index.get_level_values(0):
            continue
        sv = s.xs(m, level=0)
        rv = fr.loc[m].dropna()
        j = sv.index.intersection(rv.index)
        if len(j) < 25:
            continue
        sv, rv = sv.loc[j], rv.loc[j]
        hi, lo = rv[sv >= 2], rv[sv == 1]
        if len(hi) >= 3 and len(lo) >= 3:
            spreads.append(hi.mean() - lo.mean())
            years.append(m.year)
    sp = pd.Series(spreads)
    ann = sp.mean() * 2          # 6 mois → annualisé
    t = sp.mean() / (sp.std(ddof=1) / np.sqrt(len(sp)))
    by_year = pd.Series(spreads, index=years).groupby(level=0).mean()
    return ann, t, by_year


def main():
    df = data.load_transactions()
    panel = prices.load_panel(list(df["ticker"].dropna().unique()))
    fwd, months = monthly_forward_returns(panel)
    print(f"Panel : {panel.shape[1]} tickers en cache | {len(months)} mois | "
          f"transactions {len(df):,}".replace(",", " "))

    for date_col in ("filed", "traded"):
        sig = build_signals(df, date_col)
        tab = ic_table(sig, fwd, months, date_col)
        print(f"\n=== IC — entrée '{date_col}' ===")
        print(tab.to_string(index=False))

    sig = build_signals(df, "filed")
    ann, t, by_year = breadth_spread(sig, fwd, months)
    print(f"\n=== Spread breadth (≥2 acheteurs − 1 acheteur), 6 mois, entrée filed ===")
    print(f"  spread annualisé {ann*100:+.2f}%  t={t:.2f}")
    print(f"  par année : {by_year.round(3).to_dict()}")
    print("\nLecture : 'buy_count' = nb d'acheteurs distincts ; c'est le signal le plus net (IC positif). "
          "Les ventes ≈ 0 ; net_usd (montant) non significatif. Faible et instable → info réelle, "
          "à la limite de l'exploitable.")


if __name__ == "__main__":
    main()
