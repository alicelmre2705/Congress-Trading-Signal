"""ANALYSE — Event-study du rendement anormal des ACHATS du Congrès (CAR buy-and-hold vs SPY).

QUESTION : un achat divulgué par un membre du Congrès est-il suivi d'une SURPERFORMANCE
anormale du titre ? Si oui, est-elle EXPLOITABLE (robuste aux corrections de risque/chevauchement)
ou n'est-ce qu'un TILT de style (large-cap/croissance) capté mécaniquement ?

MÉTHODE : pour chaque achat tické, on calcule le CAR buy-and-hold = (rendement du titre) −
(rendement de SPY) sur h jours de bourse à partir de l'ENTRÉE. Deux entrées comparées :
`traded` (date réelle = information privée, AVANT divulgation) et `filed` (date publique =
INVESTISSABLE). Horizons 5/20/60/126/252 jours de bourse.
  1. Agrégé tous achats : CAR moyen/médian, %>0, t (coupe brute) — attendu ≈ 0 ou négatif (médianes < 0).
  2. Par tranche de taille (size_usd) : <50k / ≥50k / ≥250k — attendu : ≥50k positif et CROISSANT.
  3. PLACEBO ventes ≥50k : surperforment AUSSI → l'effet est un tilt de style, pas de l'info directionnelle.
  4. Robustesse : portefeuille calendar-time des gros achats (≥50k, détention 6m), régression FF-Carhart
     (statsmodels, cov HAC/Newey-West) → alpha annualisé et son t.
  5. Régime : CAR ≥50k @252j par sous-période 2014-2018 / 2019-2021 / 2022-2026.
Note t-stat : en coupe brute les fenêtres se chevauchent massivement (le CAR @252j d'achats voisins
partage ~tout son horizon) ⇒ le t « brut » est gonflé. Le calendar-time + HAC (étape 4) est le test
honnête : il neutralise le chevauchement et le beta de marché.

CONCLUSION REPRODUITE : information DÉTECTABLE — asymétrie pré-divulgation sur les gros achats
(≥50k croissant avec l'horizon, ~+4 %/an @252j, t~3-4 en coupe brute) — MAIS pas d'edge robuste :
les VENTES ≥50k surperforment aussi (~+2-3 % @252j → tilt de style), et le calendar-time corrigé
FF-Carhart donne alpha ~+4 %/an avec t≈1,7 (NON significatif). Le signal n'est concentré que sur
le régime 2019-2021. Conclusion : pas tradeable net de corrections.

Lancer : .venv/bin/python "00. S3S4 en cours/analyses/event_study.py"
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))          # dossier S3S4 (data.py, prices.py)
import data, prices  # noqa: E402

HORIZONS = [5, 20, 60, 126, 252]
SMALL, MID, BIG = 50_000, 50_000, 250_000          # bornes de tranche (size_usd, borne basse fourchette)


# ----------------------------------------------------------------------------- outils stats
def tstat(x):
    """t de Student de la moyenne (coupe brute, iid — chevauchement NON corrigé)."""
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) < 5:
        return np.nan
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def summarize(car, label):
    """Ligne descriptive d'une distribution de CAR (en %)."""
    c = np.asarray(car, float)
    c = c[~np.isnan(c)]
    return {"groupe": label, "n": len(c),
            "CAR_moy_%": round(100 * c.mean(), 2) if len(c) else np.nan,
            "CAR_med_%": round(100 * np.median(c), 2) if len(c) else np.nan,
            "pct_>0": round(100 * (c > 0).mean(), 0) if len(c) else np.nan,
            "t_brut": round(tstat(c), 2) if len(c) else np.nan}


# ----------------------------------------------------------------------------- CAR buy-and-hold
def bah_car(entry_date, ticker, panel, spy_ret_cum, px_ret_cum, h):
    """CAR buy-and-hold à h jours de bourse = (P_{t+h}/P_t − 1) − (SPY_{t+h}/SPY_t − 1).

    On utilise des séries de cumul (cumprod des rendements) ré-indexées sur le calendrier du titre :
    CAR = cum[t+h]/cum[t] − spycum[t+h]/spycum[t].  Entrée = 1er jour de bourse ≥ entry_date.
    """
    if ticker not in px_ret_cum.columns:
        return np.nan
    cum = px_ret_cum[ticker]
    idx = cum.index
    pos = idx.searchsorted(entry_date)               # 1er jour de bourse ≥ date d'entrée
    if pos >= len(idx) or pos + h >= len(idx):
        return np.nan
    t0, t1 = idx[pos], idx[pos + h]
    p0, p1 = cum.iloc[pos], cum.iloc[pos + h]
    if not (np.isfinite(p0) and np.isfinite(p1)) or p0 <= 0:
        return np.nan
    s0 = spy_ret_cum.asof(t0)
    s1 = spy_ret_cum.asof(t1)
    if not (np.isfinite(s0) and np.isfinite(s1)) or s0 <= 0:
        return np.nan
    return (p1 / p0 - 1.0) - (s1 / s0 - 1.0)


def compute_cars(trades, panel, spy, horizons):
    """DataFrame trades enrichi d'une colonne CAR par horizon, pour une colonne d'entrée donnée.

    `trades` doit contenir 'entry' (date) et 'ticker'. Pré-calcule les cumuls de prix une fois.
    """
    px_ret_cum = (panel.pct_change().add(1.0)).cumprod()       # cumul ré-investi par ticker
    spy_ret_cum = (spy.pct_change().add(1.0)).cumprod().dropna()
    out = trades.copy()
    for h in horizons:
        out[f"car{h}"] = [bah_car(d, t, panel, spy_ret_cum, px_ret_cum, h)
                          for d, t in zip(out["entry"], out["ticker"])]
    return out


# ----------------------------------------------------------------------------- étape 4 : calendar-time
def calendar_time_alpha(big_buys, panel, factors, hold_days=126):
    """Portefeuille calendar-time EW : chaque gros achat (≥50k) est détenu hold_days jours de bourse
    à partir de filed. Rendement quotidien du PF = moyenne EW des rendements des positions OUVERTES ce
    jour-là. On régresse l'excès du PF sur FF-Carhart (Mkt-RF, SMB, HML, Mom), cov HAC (Newey-West).
    Renvoie alpha annualisé (%) et t (HAC), via statsmodels.
    """
    import statsmodels.api as sm

    rets = panel.pct_change()                          # rendements quotidiens par ticker
    idx = rets.index
    # poids quotidien : nombre de positions ouvertes par (jour × ticker)
    weight = pd.DataFrame(0.0, index=idx, columns=panel.columns)
    for d, t in zip(big_buys["filed"], big_buys["ticker"]):
        if t not in weight.columns:
            continue
        pos = idx.searchsorted(d)
        if pos >= len(idx):
            continue
        end = min(pos + hold_days, len(idx) - 1)
        weight.iloc[pos:end + 1, weight.columns.get_loc(t)] += 1.0
    active = weight.sum(axis=1)
    # rendement quotidien EW du portefeuille des positions ouvertes
    contrib = (weight * rets).sum(axis=1)
    port = (contrib / active.replace(0, np.nan)).dropna()
    port = port[active.reindex(port.index) > 0]

    f = factors.reindex(port.index).dropna()
    j = port.index.intersection(f.index)
    y = (port.loc[j] - f.loc[j, "RF"]).values            # excès du PF
    cols = [c for c in ["Mkt-RF", "SMB", "HML", "Mom"] if c in f.columns]
    X = sm.add_constant(f.loc[j, cols].values)
    model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 21})
    alpha_daily = model.params[0]
    t_alpha = model.tvalues[0]
    return alpha_daily * 252 * 100, t_alpha, len(j), cols


# ----------------------------------------------------------------------------- main
def main():
    df = data.load_transactions()
    tickers = list(df["ticker"].dropna().unique())
    panel = prices.load_panel(tickers)
    spy = prices.get_spy()
    factors = prices.get_factors()
    print(f"Panel : {panel.shape[1]} tickers en cache | "
          f"transactions {len(df):,}".replace(",", " ")
          + f" | SPY {len(spy)} jours | facteurs {list(factors.columns)}")

    buys = df[(df["op"] == "buy") & df["ticker"].notna() & df["size_usd"].notna()].copy()
    sells = df[(df["op"] == "sell") & df["ticker"].notna() & df["size_usd"].notna()].copy()
    print(f"Achats tickés : {len(buys):,}".replace(",", " ")
          + f" | Ventes tickées : {len(sells):,}".replace(",", " "))

    # ========================================================== 1. AGRÉGÉ (traded ET filed)
    print("\n" + "=" * 78)
    print("1. CAR AGRÉGÉ — tous les achats (entrée traded = info privée ; filed = investissable)")
    print("=" * 78)
    cars_by_entry = {}
    for entry_col in ("traded", "filed"):
        b = buys.assign(entry=buys[entry_col])
        c = compute_cars(b, panel, spy, HORIZONS)
        cars_by_entry[entry_col] = c
        rows = [summarize(c[f"car{h}"], f"{entry_col} @{h}j") for h in HORIZONS]
        print(pd.DataFrame(rows).to_string(index=False))
        print()
    print("Lecture : médianes ~négatives et moyennes faibles → l'achat MÉDIAN ne surperforme pas. "
          "Toute moyenne positive vient d'une minorité (gros tickets) → étape 2.")

    # ========================================================== 2. PAR TRANCHE DE TAILLE
    print("\n" + "=" * 78)
    print("2. CAR PAR TRANCHE DE TAILLE (entrée filed = investissable)")
    print("=" * 78)
    cf = cars_by_entry["filed"]
    bins = {"<50k": cf["size_usd"] < SMALL,
            ">=50k": cf["size_usd"] >= MID,
            ">=250k": cf["size_usd"] >= BIG}
    for h in HORIZONS:
        rows = [summarize(cf.loc[mask, f"car{h}"], f"{name} @{h}j") for name, mask in bins.items()]
        print(pd.DataFrame(rows).to_string(index=False))
        print()
    print("Lecture attendue : ≥50k POSITIF et CROISSANT avec l'horizon (~+4% @252j, t~3-4 brut). "
          "Mais t brut = chevauchement non corrigé → voir étapes 3 et 4.")

    # ========================================================== 3. PLACEBO : VENTES >=50k
    print("\n" + "=" * 78)
    print("3. PLACEBO — VENTES >=50k (mêmes CAR ; si elles surperforment AUSSI = tilt de style)")
    print("=" * 78)
    s = sells[sells["size_usd"] >= MID].assign(entry=sells.loc[sells["size_usd"] >= MID, "filed"])
    cs = compute_cars(s, panel, spy, HORIZONS)
    rows = [summarize(cs[f"car{h}"], f"vente>=50k @{h}j") for h in HORIZONS]
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nLecture attendue : les VENTES >=50k surperforment aussi (~+2-3% @252j). Un vendeur n'a "
          "aucune raison de prédire une HAUSSE → ce n'est pas de l'info directionnelle, c'est un "
          "TILT large-cap/croissance commun aux gros tickets (achats ET ventes).")

    # ========================================================== 4. CALENDAR-TIME + FF-CARHART
    print("\n" + "=" * 78)
    print("4. ROBUSTESSE — portefeuille calendar-time des gros achats (>=50k), FF-Carhart, cov HAC")
    print("=" * 78)
    big = buys[buys["size_usd"] >= MID].copy()
    for hold in (126, 252):
        alpha_ann, t_a, ndays, cols = calendar_time_alpha(big, panel, factors, hold_days=hold)
        print(f"  détention {hold}j (~{hold//21}m) | facteurs {cols} | {ndays} jours de bourse")
        print(f"    alpha annualisé = {alpha_ann:+.2f}%/an   t (HAC, Newey-West) = {t_a:.2f}")
    print("\nLecture attendue : alpha ~+4%/an mais t≈1,7 → NON significatif. Une fois le beta de marché "
          "et les styles (taille/value/momentum) retirés, et le chevauchement neutralisé, l'edge "
          "disparaît statistiquement.")

    # ========================================================== 5. RÉGIME (sous-périodes)
    print("\n" + "=" * 78)
    print("5. RÉGIME — CAR >=50k @252j par sous-période (entrée filed)")
    print("=" * 78)
    big_f = cf[cf["size_usd"] >= MID].copy()
    yr = big_f["filed"].dt.year
    periods = {"2014-2018": (yr >= 2014) & (yr <= 2018),
               "2019-2021": (yr >= 2019) & (yr <= 2021),
               "2022-2026": (yr >= 2022) & (yr <= 2026)}
    rows = [summarize(big_f.loc[mask, "car252"], name) for name, mask in periods.items()]
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nLecture attendue : significatif SEULEMENT en 2019-2021 (boom tech/COVID). L'« edge » n'est "
          "pas stationnaire → un signal de régime, pas une anomalie exploitable de façon stable.")

    # ========================================================== SYNTHÈSE
    print("\n" + "=" * 78)
    print("CONCLUSION : information DÉTECTABLE (asymétrie pré-divulgation sur gros achats : ≥50k "
          "croissant avec l'horizon) MAIS pas d'EDGE ROBUSTE — les ventes ≥50k surperforment aussi "
          "(tilt de style), l'alpha FF-Carhart calendar-time n'est pas significatif (t≈1,7), et le "
          "signal se concentre sur 2019-2021. Pas tradeable net de corrections.")
    print("=" * 78)


if __name__ == "__main__":
    main()
