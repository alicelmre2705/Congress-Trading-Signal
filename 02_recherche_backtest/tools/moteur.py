"""Le moteur de M3 : score, plafond, exécution — extrait du notebook 16 (§3-§4, §10).

Les paramètres qui furent des RÉSULTATS de recherche (fenêtre de purge, plafond du nb 11 à
8,5 %…) ne reçoivent pas de valeur par défaut quand l'histoire en a connu plusieurs : les
passer explicitement, c'est garder visible ce que le nb 11 et le nb 16 ne mesurent pas pareil.
"""
from collections import deque

import numpy as np
import pandas as pd

from .donnees import W3, TOPN, CAP, FUSION


def cap_poids(w, cap=CAP):
    # remplissage par niveau : w_i = min(cap, λ·v_i), λ trouvé par redistribution itérative
    w = w.astype(float).copy()
    for _ in range(200):
        over = w > cap + 1e-12
        if not over.any():
            break
        exces = float((w[over] - cap).sum())
        w[over] = cap
        low = w < cap - 1e-12
        if not low.any() or w[low].sum() <= 0:
            break
        w[low] += exces * w[low] / w[low].sum()
    return w / w.sum()


def _instrument(g, univers="titres"):
    # ce que le portefeuille achète : le titre (classes fusionnées) ou son SPDR sectoriel
    if univers == "titres":
        return g.tk.map(lambda t: FUSION.get(t, t))
    if univers == "etf":
        return g.etf_proxy
    raise ValueError(f"univers inconnu : {univers}")


def poids_M3(D, i1, parti=None, topN=TOPN, cap=CAP, seuil=np.inf, mode="score", univers="titres"):
    """Les poids de M3 à la coupe i1 — parti=None ne filtre RIEN (le portefeuille unique).

    mode ∈ {score, dollars, elus, equal} ne change que la pondération ; l'univers reste
    défini par le score (B_i · m_i), achats seuls, fenêtre W₃ à la divulgation.
    """
    lo, hi = np.searchsorted(D.I_de, i1 - W3, "right"), np.searchsorted(D.I_de, i1, "right")
    g = D.df.iloc[D.ordre_d[lo:hi]]
    g = g[(g.op == "buy") & (g.taille_depot < seuil)]
    if parti is not None:
        g = g[g.party == parti]
    if not len(g):
        return {}
    g = g.assign(tkm=_instrument(g, univers))
    buy = g.groupby("tkm").A.sum()                                    # B_i : les dollars
    breadth = g.groupby("tkm").bioguide_id.nunique().reindex(buy.index)  # m_i : les élus distincts
    score = (buy * breadth).dropna()
    score = score[[tk for tk in score.index
                   if tk in D.PXV and np.isfinite(D.PXV[tk][i1 + 1]) and D.vivant(tk, i1)]]
    score = score.sort_values(ascending=False).head(topN)             # l'univers, toujours par le score
    if not len(score) or score.sum() <= 0:
        return {}
    w = {"score": score, "dollars": buy.reindex(score.index),
         "elus": breadth.reindex(score.index).astype(float),
         "equal": pd.Series(1.0, index=score.index)}[mode]
    if w.sum() <= 0:
        return {}
    return cap_poids(w / w.sum(), cap).to_dict()


def cibles(D, parti=None, **kw):
    """Un jeu de poids par coupe (la dernière coupe ne fait que clore la série)."""
    return {i: poids_M3(D, i, parti, **kw) for i in D.coupes[:-1]}


def cap_turnover(w_der, w_cible, tau_max):
    keys = set(w_der) | set(w_cible)
    TO = 0.5 * sum(abs(w_cible.get(k, 0.0) - w_der.get(k, 0.0)) for k in keys)
    if TO <= 1e-12:
        return dict(w_cible)
    lam = min(1.0, tau_max / TO)
    return {k: w_der.get(k, 0.0) + lam * (w_cible.get(k, 0.0) - w_der.get(k, 0.0)) for k in keys}


def run_livre(D, WP, tau_max=np.inf, cuts=None, cout_bps=0.0):
    """Moteur d'UN livre : parts figées, buy-and-hold, frein de rotation, frais.

    Rend (NAV, rotations réalisées). tau_max=∞ et cout_bps=0 ⇒ buy-and-hold pur.
    Copie conforme du notebook 16 (validée par test_ancres).
    """
    cal, PXV = D.cal, D.PXV
    cuts = D.coupes if cuts is None else cuts
    V = np.full(len(cal), np.nan)
    nbr, turns = {}, []
    e0 = cuts[0] + 1
    V[e0] = 100.0
    bornes = [(cuts[j] + 1, cuts[j + 1] + 1) for j in range(len(cuts) - 1)]
    for (e, e_next) in bornes:
        w_cible = {tk: wi for tk, wi in WP.get(e - 1, {}).items() if np.isfinite(PXV[tk][e])}
        val = sum(q * PXV[tk][e] for tk, q in nbr.items())
        w_der = {tk: q * PXV[tk][e] / val for tk, q in nbr.items()} if val > 0 else {}
        # 1er déploiement et sortie au cash : exemptés du frein (on ne vaporise jamais de NAV)
        w_real = dict(w_cible) if (not w_der or not w_cible) else cap_turnover(w_der, w_cible, tau_max)
        assert (not w_cible) or abs(sum(w_real.values()) - 1.0) < 1e-6, \
            "run_livre : poids capés ne somment pas à 1 (fuite de cash)"
        turns.append(0.5 * sum(abs(w_real.get(k, 0) - w_der.get(k, 0)) for k in set(w_real) | set(w_der)))
        if cout_bps:
            V[e] *= 1.0 - 2.0 * turns[-1] * cout_bps / 1e4
        nbr = {tk: V[e] * wi / PXV[tk][e] for tk, wi in w_real.items() if abs(wi) > 1e-12}
        for t in range(e + 1, min(e_next, len(cal) - 1) + 1):
            V[t] = sum(q * PXV[tk][t] for tk, q in nbr.items()) if nbr else V[t - 1]
    span = pd.Series(V, index=cal)
    span = span.loc[span.first_valid_index():span.last_valid_index()]
    return span, np.array(turns[1:])


def tranches_vendues(D, g):
    """FIFO par (élu, titre) : pour chaque vente, les (ancienneté, quantité) consommés + le non-apparié."""
    lots, out = deque(), {}
    for idx, i0, op, A in zip(g.index.values, g.i0.values, g.op.values, g.A.values):
        p = D.PXV[g.tk.iat[0]][i0]
        if not np.isfinite(p) or p <= 0:
            continue
        q = A / p
        if op == "buy":
            lots.append([i0, q])
        else:
            reste, pieces = q, []
            while reste > 1e-12 and lots:
                s0, q0 = lots[0]
                pris = min(reste, q0)
                reste -= pris
                lots[0][1] -= pris
                pieces.append((i0 - s0, pris))
                if lots[0][1] <= 1e-12:
                    lots.popleft()
            out[idx] = (pieces, reste)
    return out


def gamma_purge(D, seuil):
    """γ par vente : la part du lot détenue depuis ≤ `seuil` jours de bourse (FIFO plein historique).

    `seuil` est OBLIGATOIRE — le nb 11 mesure à 504 j (2 ans), le nb 16 à 756 j (prospectus) :
    ce n'est pas un détail d'implémentation, c'est un résultat de recherche.
    """
    ventes = {}
    for (_, _), g in D.df.groupby(["bioguide_id", "tk"], sort=False):
        ventes.update(tranches_vendues(D, g))
    gam = np.ones(len(D.df))
    for idx, (pieces, reste) in ventes.items():
        tot = sum(q for _, q in pieces) + reste
        if tot <= 0:
            continue
        gam[idx] = (sum(q for h, q in pieces if h <= seuil) + reste) / tot
    return gam


def poids_netting(D, gamma, i1, parti, topN=TOPN, cap=CAP):
    """M3 à l'identique, sauf que les ventes récentes réduisent la position (γ par vente).

    `gamma` vient de gamma_purge(D, seuil) — le seuil est un résultat de recherche (756 j au
    prospectus). Plancher 0 PAR ÉLU : jamais de position négative. (nb 16, §17.1)
    """
    lo, hi = np.searchsorted(D.I_de, i1 - W3, "right"), np.searchsorted(D.I_de, i1, "right")
    g = D.df.iloc[D.ordre_d[lo:hi]]
    g = g[g.party == parti]
    if not len(g):
        return {}
    tkm = g.tk.map(lambda t: FUSION.get(t, t)).values
    sg = g.A.values * np.where(g.op.values == "buy", 1.0, -gamma[g.index.values])
    per = pd.Series(sg).groupby([g.bioguide_id.values, tkm]).sum()
    per = per[per > 0]
    if not len(per):
        return {}
    neti, mi = per.groupby(level=1).sum(), per.groupby(level=1).size()
    score = (neti * mi).dropna()
    score = score[[t for t in score.index
                   if t in D.PXV and np.isfinite(D.PXV[t][i1 + 1]) and D.vivant(t, i1)]]
    score = score.sort_values(ascending=False).head(topN)
    if not len(score) or score.sum() <= 0:
        return {}
    return cap_poids(score / score.sum(), cap).to_dict()
