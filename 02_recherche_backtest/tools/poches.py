"""Le portefeuille final « deux poches » — extrait du §20 du notebook 16.

Une poche SPY + une poche signal, remélangées à chaque coupe (les poches DÉRIVENT entre deux
coupes — remélanger en continu fabriquerait du rendement, §20.2). Dose analytique
a_t = min(1, TE*/σ̂_t), σ̂ estimée sur H jours STRICTEMENT antérieurs à la coupe.
"""
import numpy as np
import pandas as pd

from . import mesure, moteur


def ajouter_spy(D):
    """SPY entre dans PXV (purement additif : jamais dans le flux de M3 — asserté)."""
    assert "SPY" not in set(D.df.tk), "SPY est un ticker du flux — l'ajouter changerait M3"
    D.PXV["SPY"] = D.spy.reindex(D.cal).ffill().to_numpy()


def serie_active(D, WS):
    """La poche active (le signal WS en buy-and-hold) et l'écart actif d = r_sig − r_SPY."""
    V_SIG = moteur.run_livre(D, WS)[0]
    r_sig = V_SIG.pct_change().dropna()
    r_ben = D.r_spy.reindex(r_sig.index).fillna(0.0)
    d = (r_sig - r_ben).rename("d")
    return V_SIG, d


def livre_deux_poches(D, a_of_i, WSIG, cuts=None):
    """(ii) EN POIDS — un vecteur (1−a)·SPY + a·w_signal par coupe (12 lignes)."""
    cuts = D.coupes if cuts is None else cuts
    WP = {}
    for i in cuts[:-1]:
        w, a = WSIG.get(i, {}), a_of_i(i)
        if not w or a is None:
            continue
        d_ = {tk: a * wi for tk, wi in w.items()}
        d_["SPY"] = d_.get("SPY", 0.0) + (1.0 - a)
        d_ = {k: v for k, v in d_.items() if v > 1e-15}
        assert abs(sum(d_.values()) - 1) < 1e-12, f"coupe {i} : Σw ≠ 1"
        WP[i] = d_
    return WP


def sigma_roll(D, d, H=756):
    """σ̂_t (%/an) : écart-type de d sur les H jours cotés ≤ t — ffill du passé vers le futur."""
    s = (d.rolling(H).std() * np.sqrt(252) * 100).rename("sigma_hat")
    return s.reindex(D.cal).ffill()


def doses(D, sig_at, te_cible, bande=0.0, cuts=None):
    """a_t = min(1, TE*/σ̂_t), avec bande morte optionnelle (séquentielle : dépend du détenu)."""
    cuts = [i for i in (D.coupes if cuts is None else cuts) if np.isfinite(sig_at.iloc[i])]
    out, a_det = {}, None
    for i in cuts[:-1]:
        s = sig_at.iloc[i]
        if not np.isfinite(s) or s <= 0:
            continue
        a = min(1.0, te_cible / s)
        if a_det is not None and abs(a - a_det) <= bande * a_det:
            a = a_det
        out[i], a_det = a, a
    return out


def calibration(D, d, sig_at, H=756, cuts=None):
    """TE réalisée sur (t, t+H] ÷ σ̂_t prédite en t — le seul contrôle honnête d'un budget."""
    cuts = [i for i in (D.coupes if cuts is None else cuts) if np.isfinite(sig_at.iloc[i])]
    ratios = []
    for i in cuts:
        apres = d[d.index > D.cal[i]].iloc[:H]
        if len(apres) < H:
            continue
        ratios.append(100 * np.sqrt(252) * apres.std() / sig_at.iloc[i])
    r = pd.Series(ratios)
    return {"médiane": float(r.median()), "part > 1": float((r > 1).mean()),
            "q95": float(r.quantile(0.95)), "n": len(r)}


def mesures(D, V, lab, WP=None, cuts=None, cout_bps=10.0):
    """Le jeu de mesures du §20 : excès géométrique ET arithmétique, TE, IR — et le net si WP."""
    b = mesure.bilan_ic(D, V, lab)
    rp = V.pct_change().dropna()
    e = rp - D.r_spy.reindex(rp.index).fillna(0.0)
    o = {"excès géom. %/an": b["excès %/an"], "t": b["t"], "IC bas": b["IC bas"],
         "IC haut": b["IC haut"], "excès arithm. %/an": 252 * 100 * e.mean(),
         "TE %/an": 100 * np.sqrt(252) * e.std(), "α₁ %/an": b["α %/an"], "β": b["β"],
         "NAV": b["NAV"], "n ans": b["n ans"]}
    o["IR"] = o["excès arithm. %/an"] / o["TE %/an"] if o["TE %/an"] > 1e-9 else np.nan
    if WP is not None:
        net = moteur.run_livre(D, WP, cuts=cuts, cout_bps=cout_bps)[0]
        o["excès NET %/an"] = mesure.bilan(D, net, lab + " (net)")["excès %/an"]
        _, turns = moteur.run_livre(D, WP, cuts=cuts)
        o["rotation %/an"] = float(np.mean(turns)) * 12 * 100 if len(turns) else np.nan
        o["lignes"] = len(WP[max(WP)])
    return o
