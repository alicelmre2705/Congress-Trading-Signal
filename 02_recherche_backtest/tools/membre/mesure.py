"""La boîte de mesure de la famille membre — extraite de copier_les_membres/tables_membres_tickers.

⚠️ Convention MEMBRE : α = régression du rendement BRUT sur le SPY brut (pas de taux sans
risque), annualisation GÉOMÉTRIQUE (1+α)^252−1 ; appraisal = α/σ_ε·√252, t = appraisal·√(n/252) ;
« excès » = écart de CAGR sur la fenêtre commune. La famille titre (tools.mesure) mesure un
Jensen en excès du RF, ×252 arithmétique : ne jamais comparer les deux.
"""
import numpy as np
import pandas as pd


def stats(r):
    nav = (1 + r).cumprod()
    T = len(r)
    cagr = nav.iloc[-1] ** (252 / T) - 1 if nav.iloc[-1] > 0 else np.nan
    return dict(cagr=cagr, vol=r.std() * np.sqrt(252),
                sharpe=r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else np.nan,
                maxdd=(nav / nav.cummax() - 1).min())


def info_ratio(M, r):
    # information ratio : écart moyen au SPY, rapporté à la régularité de cet écart
    x = (r - M.r_spy.reindex(r.index)).dropna()
    return x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan


def alpha_beta(M, r):
    """Régression r = alpha + beta*r_spy + eps -> beta, alpha annualisé, appraisal, t_appr."""
    d = pd.concat([r.rename("y"), M.r_spy.reindex(r.index).rename("x")], axis=1).dropna()
    if len(d) < 30 or d["x"].var() == 0:
        return dict(beta=np.nan, alpha_ann=np.nan, appraisal=np.nan, t_appr=np.nan)
    beta, alpha = np.polyfit(d["x"].values, d["y"].values, 1)
    eps = d["y"].values - (alpha + beta * d["x"].values)
    se = eps.std(ddof=2)
    appr = (alpha / se * np.sqrt(252)) if se > 0 else np.nan
    return dict(beta=beta, alpha_ann=(1 + alpha) ** 252 - 1, appraisal=appr,
                t_appr=appr * np.sqrt(len(d) / 252))


def exces_spy(M, r):
    """Écart de croissance annualisée (CAGR) contre le SPY, sur la même fenêtre."""
    nav = (1 + r).cumprod()
    cagr = nav.iloc[-1] ** (252 / len(r)) - 1
    rs = M.r_spy.reindex(r.index).fillna(0.0)
    navs = (1 + rs).cumprod()
    cagrs = navs.iloc[-1] ** (252 / len(rs)) - 1
    return cagr - cagrs


def sortino(r):
    # comme le Sharpe, mais seule la volatilité des jours de BAISSE pénalise
    d = r.dropna()
    dn = d[d < 0].std()
    return d.mean() / dn * np.sqrt(252) if dn > 0 else np.nan


def yearly_excess(M, r):
    b = M.r_spy.reindex(r.index).fillna(0.0)
    return pd.Series({y: ((1 + r[r.index.year == y]).prod() - 1)
                         - ((1 + b[b.index.year == y]).prod() - 1)
                      for y in sorted(set(r.index.year))})


def eval_yearly(M, r):
    e = yearly_excess(M, r)
    n = len(e)
    ir_an = e.mean() / e.std(ddof=1)
    return dict(exces_moyen=e.mean(), IR_annuel=ir_an, t=ir_an * np.sqrt(n),
                gagnantes=f"{int((e > 0).sum())}/{n}")


def eval_sem(M, r):
    b = M.r_spy.reindex(r.index).fillna(0.0)
    sem = r.index.year.values * 2 + (r.index.month.values > 6).astype(int)
    e = pd.Series({s: ((1 + r[sem == s]).prod() - 1) - ((1 + b[sem == s]).prod() - 1)
                   for s in sorted(set(sem))})
    n = len(e)
    ir = e.mean() / e.std(ddof=1)
    return dict(exces_an=2 * e.mean(), t=ir * np.sqrt(n),
                gagnantes=f"{int((e > 0).sum())}/{n}", n=n)


def score_ir(M, r):
    x = (r - M.r_spy.reindex(r.index)).dropna()
    return x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else -np.inf


def score_appr(M, r):
    a = alpha_beta(M, r)["appraisal"]
    return a if np.isfinite(a) else -np.inf


def classement_a_date(M, wf_ret, wf_traded, d, min_trades=10, min_days=126,
                      seuil_t=1.645, critere="ir", avec_nom=False):
    """Classement point-in-time strict (<= d) par IR ou appraisal, seuil t > seuil_t.

    Généralise classement_a_fin (d = 31/12/Y) et classement_a_date des notebooks.
    """
    rows = []
    for bid, r in wf_ret.items():
        rr = r.loc[:d]
        n_trades = int((wf_traded[bid] <= d).sum())
        n_days = len(rr)
        if n_days < 2 or rr.std() == 0 or n_trades < min_trades or n_days < min_days:
            continue
        if critere == "ir":
            x = (rr - M.r_spy.reindex(rr.index)).dropna()
            if len(x) < 2 or x.std() == 0:
                continue
            score = x.mean() / x.std() * np.sqrt(252)
            t = score * np.sqrt(n_days / 252)
        else:
            ab = alpha_beta(M, rr)
            score, t = ab["appraisal"], ab["t_appr"]
            if not np.isfinite(t):
                continue
        if t <= seuil_t:
            continue
        ligne = dict(bioguide_id=bid, score=score)
        if avec_nom:
            ligne.update(name=M.df.loc[M.df.bioguide_id == bid, "name"].iloc[0],
                         n_trades=n_trades, n_days=n_days, t=t)
        rows.append(ligne)
    cols = (["bioguide_id", "name", "n_trades", "n_days", "score", "t"] if avec_nom
            else ["bioguide_id", "score"])
    if not rows:
        return pd.DataFrame(columns=cols)
    out = pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
    return out[cols] if avec_nom else out


def classement_sharpe_a_date(wf_ret, d, min_days=126, min_sharpe=0.4):
    """Classement point-in-time par le SHARPE brut — aucun test t (Partie II des notebooks)."""
    rows = []
    for bid, r in wf_ret.items():
        rr = r.loc[:d]
        if len(rr) < min_days or rr.std() == 0:
            continue
        s = rr.mean() / rr.std() * np.sqrt(252)
        if s <= min_sharpe:
            continue
        rows.append(dict(bioguide_id=bid, score=s))
    return (pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
            if rows else pd.DataFrame(columns=["bioguide_id", "score"]))


# ── commissions → secteurs GICS (choix de recherche du §16, assumé et testé en sensibilité) ───

MAP16 = {
    "Committee on Agriculture": ["Consumer Staples", "Materials"],
    "Committee on Armed Services": ["Industrials"],
    "Committee on Financial Services": ["Financials", "Real Estate"],
    "Committee on Banking, Housing, and Urban Affairs": ["Financials", "Real Estate"],
    "Committee on Finance": ["Financials", "Health Care"],
    "Committee on Ways and Means": ["Financials", "Health Care"],
    "Committee on Energy and Commerce": ["Energy", "Utilities", "Health Care", "Communication Services"],
    "Committee on Energy and Natural Resources": ["Energy", "Utilities", "Materials"],
    "Committee on Environment and Public Works": ["Utilities", "Materials", "Industrials"],
    "Committee on Health, Education, Labor, and Pensions": ["Health Care"],
    "Committee on Commerce, Science, and Transportation": ["Industrials", "Information Technology", "Communication Services"],
    "Committee on Transportation and Infrastructure": ["Industrials"],
    "Committee on Science, Space, and Technology": ["Information Technology"],
    "Select Committee on Intelligence": ["Information Technology", "Communication Services", "Industrials"],
    "Committee on Homeland Security": ["Industrials", "Information Technology"],
    "Committee on the Judiciary": ["Information Technology", "Communication Services"],
    "Committee on Natural Resources": ["Energy", "Materials"],
    "Committee on Veterans' Affairs": ["Health Care"],
}


def secteurs_commissions(cm, table=MAP16):
    if not isinstance(cm, str):
        return set()
    out = set()
    for k, v in table.items():
        if k in cm:
            out.update(v)
    return out
