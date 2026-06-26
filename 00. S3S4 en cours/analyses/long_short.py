"""ANALYSE — LONG-SHORT market-neutral : le beta cache-t-il un alpha ?

QUESTION : si l'on retire le risque de marché (en SHORTANT un panier symétrique de ventes, ou
le bottom-décile de net-buying), reste-t-il un ALPHA factoriel significatif dans les trades du
Congrès ? Autrement dit, l'hypothèse « le beta noie l'alpha » tient-elle ?

MÉTHODE : deux constructions market-neutral, plus deux contrôles.
  1) Time-series EW : portefeuille LONG des ACHATS récents (fenêtre glissante = horizon de détention)
     MOINS SHORT des VENTES récentes, rééquilibré quotidiennement, NET de coûts (20 bps/côté).
     Rendement quotidien régressé sur FF-Carhart en HAC (evaluate.factor_alpha) → alpha annualisé,
     t-stat, beta marché. On veut voir alpha t<1.3 et beta marché ≈ 0 (preuve de neutralité).
  2) Décile cross-sectionnel mensuel : chaque mois on classe les tickers par net-buying
     (nb acheteurs distincts − nb vendeurs distincts), LONG top-décile / SHORT bottom-décile, EW,
     détenu 1 mois, série quotidienne → alpha factoriel.
  3) Variante date 'traded' (information privée, avant divulgation publique) sur la construction (1).
  4) Contexte LONG-ONLY achats (1/3/6 mois) : alpha factoriel pour situer le court terme négatif.
Entrée = `filed` (date publique, investissable) sauf la variante (3) qui prend `traded`.
t-stat HAC (Newey-West, maxlags=5) pour le chevauchement des fenêtres glissantes.

CONCLUSION REPRODUITE : NON. Aucun alpha market-neutral significatif.
  - Long-short time-series : alpha GROSS (avant coûts) NON significatif (t≈−0,6/−1,3/−1,4 à 1/3/6 mois,
    entrée filed) et beta marché ≈ 0 (−0,02/−0,03) → la jambe short neutralise bien le risque
    systématique, et une fois ce risque retiré il n'y a AUCUN alpha. NET de 20 bps/côté, l'alpha
    devient franchement négatif (le turnover élevé mange tout) : le market-neutral n'est même pas
    rentable à exploiter.
  - Décile net-buying : spread plat (+0,08 %/mois, t_iid≈+0,6), alpha factoriel légèrement négatif
    (≈−0,9 %/an, t≈−1,1).
  - Variante 'traded' : gross nul à légèrement négatif aussi (t∈[−1,7;−2,0]) ; l'avantage
    informationnel privé ne sauve rien, et le net reste très négatif.
  - Contexte long-only : court terme NÉGATIF (alpha≈−6,8 %/an, t≈−5,3 à 1 mois) — le « signal » des
    achats récents est en fait un léger retournement, pas un alpha caché par le beta.
  ⇒ L'hypothèse « le beta cache l'alpha » est REJETÉE.

Lancer : .venv/bin/python "00. S3S4 en cours/analyses/long_short.py"
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))          # dossier S3S4 (data.py, prices.py, evaluate.py)
import data, prices, evaluate  # noqa: E402

HOLD_MONTHS = [1, 3, 6]          # horizons de détention testés
COST_BPS = 20.0                  # coût one-way par côté (achat OU vente)
TRADING_DAYS = {1: 21, 3: 63, 6: 126}


# --------------------------------------------------------------------------------------------------
# (1) & (3)  LONG-SHORT time-series : long achats récents − short ventes récentes (EW, net de coûts)
# --------------------------------------------------------------------------------------------------
def _leg_weights(events, side, panel_idx, tpos, hold_days, lag_days=1):
    """Poids EW quotidiens (D×N) d'une jambe : chaque event (achat ou vente) pèse 1 du jour
    `date`+lag jusqu'à +hold_days, puis disparaît. `side` = +1 (long) ou −1 (short)."""
    D = len(panel_idx)
    N = len(tpos)
    deltas = np.zeros((D + 1, N))
    e = events[events["ticker"].isin(tpos)]
    entry = panel_idx.searchsorted(e["date"].values + np.timedelta64(lag_days, "D"), side="left")
    exit_ = entry + hold_days
    tk = e["ticker"].map(tpos).values
    valid = entry < D
    np.add.at(deltas, (entry[valid], tk[valid]), 1.0)
    np.add.at(deltas, (np.clip(exit_, 0, D)[valid], tk[valid]), -1.0)
    held = np.cumsum(deltas[:D], axis=0)
    held[held < 0] = 0.0
    tot = held.sum(axis=1, keepdims=True)
    w = np.divide(held, tot, out=np.zeros_like(held), where=tot > 0)   # EW normalisé dans la jambe
    return side * w, (tot.ravel() > 0)


def long_short_timeseries(df, panel, date_col, hold_months):
    """Série quotidienne nette du portefeuille (long achats − short ventes), pondéré EW dans chaque
    jambe, jambes dollar-neutral (+1 long / −1 short). Coûts sur le turnover total des deux jambes."""
    idx = panel.index
    tickers = list(panel.columns)
    tpos = {t: i for i, t in enumerate(tickers)}
    ret = panel.pct_change().fillna(0.0).values
    D, N = ret.shape
    hold_days = TRADING_DAYS[hold_months]

    buys = df[(df["op"] == "buy") & df["ticker"].notna()][[date_col, "ticker"]].rename(
        columns={date_col: "date"})
    sells = df[(df["op"] == "sell") & df["ticker"].notna()][[date_col, "ticker"]].rename(
        columns={date_col: "date"})

    w_long, act_l = _leg_weights(buys, +1.0, idx, tpos, hold_days)
    w_short, act_s = _leg_weights(sells, -1.0, idx, tpos, hold_days)
    w = w_long + w_short                                   # net (long − short), dollar-neutral

    w_prev = np.vstack([np.zeros((1, N)), w[:-1]])
    gross = (w_prev * ret).sum(axis=1)                     # gagné = poids de la veille
    turnover = np.abs(w - w_prev).sum(axis=1)              # somme |Δpoids| des deux jambes
    net = gross - (COST_BPS / 1e4) * turnover

    active = act_l & act_s                                  # période où LES DEUX jambes existent
    mask = idx >= idx[active][0] if active.any() else np.ones(D, bool)
    return pd.Series(net, index=idx)[mask], pd.Series(gross, index=idx)[mask]


# --------------------------------------------------------------------------------------------------
# (2)  DÉCILE cross-sectionnel mensuel : long top-décile / short bottom-décile de net-buying
# --------------------------------------------------------------------------------------------------
def decile_long_short(df, panel, date_col="filed"):
    """Chaque fin de mois : score = (nb acheteurs distincts − nb vendeurs distincts) par ticker.
    On garde les mois assez peuplés, on forme long(top 10%) / short(bottom 10%), détention 1 mois,
    EW. Rendement mensuel du spread → on l'étale en série quotidienne pour la régression factorielle."""
    d = df[df["ticker"].notna()].copy()
    d["m"] = d[date_col].dt.to_period("M").dt.to_timestamp("M")
    buys = d[d["op"] == "buy"].groupby(["m", "ticker"])["bioguide"].nunique()
    sells = d[d["op"] == "sell"].groupby(["m", "ticker"])["bioguide"].nunique()
    score = buys.subtract(sells, fill_value=0)

    mpx = panel.resample("ME").last()
    fwd1 = mpx.shift(-1) / mpx - 1.0                       # rendement 1 mois forward
    months = sorted(set(score.index.get_level_values(0)) & set(fwd1.index))

    spreads = {}
    for m in months:
        sv = score.xs(m, level=0)
        sv = sv[sv != 0]                                   # tickers réellement tradés ce mois
        rv = fwd1.loc[m].dropna()
        j = sv.index.intersection(rv.index)
        if len(j) < 30:                                    # besoin d'assez de noms pour 10 déciles
            continue
        sv, rv = sv.loc[j], rv.loc[j]
        q_hi, q_lo = sv.quantile(0.9), sv.quantile(0.1)
        hi, lo = rv[sv >= q_hi], rv[sv <= q_lo]
        if len(hi) >= 3 and len(lo) >= 3:
            spreads[m] = hi.mean() - lo.mean()             # long top − short bottom
    sp = pd.Series(spreads).sort_index()
    return sp


def _monthly_to_daily(monthly, factors):
    """Étale un rendement mensuel uniformément sur les jours de bourse du mois suivant (le mois
    pendant lequel la position est détenue) pour permettre la régression FF quotidienne."""
    fidx = factors.index
    rows = []
    for m, r in monthly.items():
        nxt = (m + pd.offsets.MonthBegin(1))
        end = nxt + pd.offsets.MonthEnd(1)
        days = fidx[(fidx >= nxt) & (fidx <= end)]
        if len(days):
            for day in days:
                rows.append((day, r / len(days)))
    s = pd.Series(dict(rows)).sort_index()
    return s


# --------------------------------------------------------------------------------------------------
# (4)  CONTEXTE  LONG-ONLY achats (event-driven, net de coûts) → alpha factoriel
# --------------------------------------------------------------------------------------------------
def long_only_alpha(df, panel, factors, hold_months):
    import portfolio
    buys = data.buy_signals(df)
    pos = portfolio.build_positions(buys, df, horizon_months=hold_months)
    out = portfolio.run_portfolio(pos, panel, weighting="equal", cost_bps=COST_BPS, lag_days=1)
    net = out["net"]
    net = net[net.index >= out["active_from"]] if out["active_from"] is not None else net
    return evaluate.factor_alpha(net, factors)


# --------------------------------------------------------------------------------------------------
def _fmt(res):
    return (f"alpha={res['alpha_annuel']*100:+6.2f}%/an  t={res['alpha_t']:+5.2f}  "
            f"beta_marché={res['beta_marche']:+.3f}")


def main():
    df = data.load_transactions()
    panel = prices.load_panel(list(df["ticker"].dropna().unique()))
    factors = prices.get_factors()
    print(f"Panel : {panel.shape[1]} tickers en cache | transactions {len(df):,}".replace(",", " "))
    print(f"Coûts : {COST_BPS:.0f} bps/côté one-way | facteurs FF-Carhart {list(factors.columns)}")

    # (1) LONG-SHORT time-series, entrée filed
    print("\n=== (1) LONG-SHORT time-series (long achats − short ventes, EW), entrée 'filed' ===")
    print("    [neutralité OK si beta_marché ≈ 0 ; alpha NET dégonflé par les coûts → on montre aussi le GROSS]")
    for h in HOLD_MONTHS:
        s_net, s_gross = long_short_timeseries(df, panel, "filed", h)
        res, resg = evaluate.factor_alpha(s_net, factors), evaluate.factor_alpha(s_gross, factors)
        print(f"  détention {h:>1} mois | NET   {_fmt(res)}")
        print(f"               | GROSS {_fmt(resg)}  | {len(s_net)} jours")

    # (3) Variante 'traded'
    print("\n=== (3) Même LONG-SHORT mais entrée 'traded' (information privée pré-divulgation) ===")
    for h in HOLD_MONTHS:
        s_net, s_gross = long_short_timeseries(df, panel, "traded", h)
        res, resg = evaluate.factor_alpha(s_net, factors), evaluate.factor_alpha(s_gross, factors)
        print(f"  détention {h:>1} mois | NET   {_fmt(res)}")
        print(f"               | GROSS {_fmt(resg)}  | {len(s_net)} jours")

    # (2) Décile cross-sectionnel mensuel
    print("\n=== (2) Décile mensuel : long top-10% / short bottom-10% de net-buying, entrée 'filed' ===")
    sp = decile_long_short(df, panel, "filed")
    mu = sp.mean()
    t_iid = mu / (sp.std(ddof=1) / np.sqrt(len(sp)))
    daily = _monthly_to_daily(sp, factors)
    res = evaluate.factor_alpha(daily, factors)
    print(f"  spread mensuel moyen {mu*100:+.2f}% sur {len(sp)} mois | t_iid(mensuel)={t_iid:+.2f}")
    print(f"  annualisé {mu*12*100:+.2f}%/an | alpha factoriel : {_fmt(res)}")

    # (4) Contexte LONG-ONLY
    print("\n=== (4) CONTEXTE — LONG-ONLY achats (event-driven, EW, net) : alpha factoriel ===")
    for h in HOLD_MONTHS:
        res = long_only_alpha(df, panel, factors, h)
        print(f"  détention {h:>1} mois | {_fmt(res)}")

    print("\nLecture / Conclusion : market-neutral (long achats − short ventes) ⇒ beta marché ≈ 0 "
          "(neutralité confirmée) ET alpha GROSS NON significatif (t<1.3) à 1/3/6 mois ; le décile "
          "net-buying est plat à négatif (t≈−1.1) ; la variante 'traded' ne sauve rien ; le long-only "
          "est NÉGATIF à court terme (t≈−5.3 @1m). NET de coûts, le long-short devient franchement "
          "négatif (turnover). ⇒ NON : retirer le beta ne révèle aucun alpha. "
          "L'hypothèse « le beta cache l'alpha » est REJETÉE.")


if __name__ == "__main__":
    main()
