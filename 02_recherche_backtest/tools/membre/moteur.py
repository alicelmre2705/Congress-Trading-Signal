"""Le moteur de la famille membre : parts, NAV, pondérations — extrait de copier_les_membres.

Reconstruction des portefeuilles en PARTS (pas de short : les ventes non couvertes sont
tronquées), rendement time-weighted winsorisé ±50 %/j, moteur de combinaison en parts
(autofinancement), pondérations 1/K · inverse-vol · GMV · ERC, covariance Ledoit-Wolf
multi-cibles (vendorée), FIFO de détention (jours CALENDAIRES — celui de la famille titre,
tools.moteur.tranches_vendues, compte en jours de bourse).
"""
from collections import deque

import numpy as np
import pandas as pd
from scipy.optimize import minimize

NUMBER_WORKING_DAYS = 252
RISK_WINDOW_MIN = 60      # < 60 jours COMMUNS -> Sigma peu fiable -> repli inverse-vol


def eff_price(M, tk, d):
    # prix du 1er jour de bourse >= d (on transige au marché)
    s = M.prices[tk]
    pos = s.index.searchsorted(d)
    if pos >= len(s):
        return None, None
    p = s.iloc[pos]
    if not np.isfinite(p) or p <= 0:
        return None, None
    return s.index[pos], p


def member_shares(M, g):
    # g = trades d'un membre  ->  N (parts détenues par jour, colonnes = tickers)
    cols = {}
    for tk, gt in g.groupby("ticker"):
        h, events = 0.0, {}
        for _, row in gt.sort_values("traded").iterrows():
            dd, p = eff_price(M, tk, row["traded"])
            if dd is None:
                continue
            qty = row["size_usd"] / p
            h = h + qty if row["op"] == "buy" else h - min(qty, h)   # pas de short
            events[dd] = h
        if events:
            cols[tk] = pd.Series(events).sort_index().reindex(M.cal).ffill().fillna(0.0)
    return pd.DataFrame(cols) if cols else None


def daily_return(M, N):
    P = pd.DataFrame({tk: M.prices[tk] for tk in N.columns})
    Nsh = N.shift(1)                                     # parts de la veille
    num = (Nsh * P).sum(axis=1)                          # Σ n_i(t-1) P_i(t)
    den = (Nsh * P.shift(1)).sum(axis=1)                 # Σ n_i(t-1) P_i(t-1)
    r = pd.Series(np.where(den > 0, num / den - 1.0, 0.0), index=N.index)
    r = r.clip(-0.5, 0.5)                                # winsorisation ±50 %/jour
    active = N.sum(axis=1) > 0
    if not active.any():
        return pd.Series(dtype=float)
    return r.loc[active.idxmax(): active[::-1].idxmax()]


def series_membres(M, verbose=True):
    """Une série de rendement par membre (écarte les séries < 2 j ou de variance nulle)."""
    wf_ret, wf_traded = {}, {}
    for bid, g in M.df.groupby("bioguide_id"):
        N = member_shares(M, g)
        if N is None:
            continue
        r = daily_return(M, N)
        if len(r) < 2 or r.std() == 0:
            continue
        wf_ret[bid] = r
        wf_traded[bid] = pd.to_datetime(np.sort(g["traded"].values))
    if verbose:
        print(len(wf_ret), "membres avec une série de rendement")
    return wf_ret, wf_traded


def navk(M, wf_ret):
    """Le prix de part de chaque membre-fonds, calculé UNE FOIS sur tout le calendrier."""
    return pd.DataFrame({bid: (1 + r.reindex(M.cal).fillna(0.0)).cumprod()
                         for bid, r in wf_ret.items()})


def parts_engine(M, NAVK, blocs, W0=100.0):
    """blocs = [(jours tenus, bids, poids initiaux)] chronologiques -> dict r / nav / journal."""
    W, rets, navs, journal = W0, [], [], []
    for idx, bids, w in blocs:
        tR = M.cal[M.cal.get_loc(idx[0]) - 1]              # coupe = veille du 1er jour tenu
        nbr = pd.Series(w * W / NAVK.loc[tR, bids].values, index=bids)
        nav = NAVK.loc[idx, bids].mul(nbr, axis=1).sum(axis=1)
        r = nav / nav.shift(1) - 1
        r.iloc[0] = nav.iloc[0] / W - 1                    # 1er jour : contre la richesse redéployée
        journal.append(dict(rebal=tR, nbr=nbr, W_avant=W, W_apres=float(nav.iloc[-1])))
        W = float(nav.iloc[-1])                            # autofinancement -> coupe suivante
        rets.append(r)
        navs.append(nav)
    return dict(r=pd.concat(rets).sort_index(), nav=pd.concat(navs).sort_index(), journal=journal)


def poids(sel, mode):
    """sel = [(score, bid)] ; mode = "equal" ou pondération ∝ score."""
    if mode == "equal":
        return np.ones(len(sel)) / len(sel)
    sc = np.array([s for s, _ in sel])
    return sc / sc.sum() if sc.sum() > 0 else np.ones(len(sel)) / len(sel)


# ── pondérations point-in-time (§9-§10 de copier_les_membres) ─────────────────────────────────

def fenetre_pit(wf_ret, bids, tR):
    """Rendements passés (s <= tR) des membres, alignés sur leurs dates COMMUNES."""
    return pd.concat({b: wf_ret[b].loc[:tR] for b in bids}, axis=1, sort=False).dropna(how="any")[bids]


def sigmas_pit(wf_ret, bids, tR):
    return np.array([wf_ret[b].loc[:tR].std(ddof=1) * np.sqrt(252) for b in bids])


def cov_pit(wf_ret, bids, tR):
    return np.cov(fenetre_pit(wf_ret, bids, tR).values, rowvar=False) * 252


def gmv_from_cov(Sig):
    """min w'Σw s.c. 1'w=1, w>=0 (SLSQP long-only)."""
    n = len(Sig)
    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1.0, "jac": lambda w: np.ones(n)},)
    res = minimize(lambda w: w @ Sig @ w, np.ones(n) / n, jac=lambda w: 2 * Sig @ w,
                   method="SLSQP", bounds=[(0.0, 1.0)] * n, constraints=cons,
                   options={"ftol": 1e-12, "maxiter": 500})
    w = np.clip(res.x, 0, None)
    return w / w.sum()


def erc_from_cov(Sig, w0):
    """Contributions au risque égales : min de la dispersion des RC_k = w_k(Σw)_k."""
    n = len(Sig)

    def obj(w):
        rc = w * (Sig @ w)
        return np.sum((rc[:, None] - rc[None, :]) ** 2)

    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1.0},)
    res = minimize(obj, w0, method="SLSQP", bounds=[(1e-12, 1.0)] * n, constraints=cons,
                   options={"ftol": 1e-14, "maxiter": 1000})
    w = np.clip(res.x, 0, None)
    return w / w.sum()


def w_equal(wf_ret, bids, tR):
    return np.ones(len(bids)) / len(bids)


def w_invvol(wf_ret, bids, tR):
    inv = 1.0 / sigmas_pit(wf_ret, bids, tR)
    return inv / inv.sum()


def w_gmv(wf_ret, bids, tR):
    return gmv_from_cov(cov_pit(wf_ret, bids, tR))


def w_erc(wf_ret, bids, tR):
    return erc_from_cov(cov_pit(wf_ret, bids, tR), w_invvol(wf_ret, bids, tR))


# ── Ledoit-Wolf multi-cibles (vendoré — §10) ──────────────────────────────────────────────────

class CovarianceMatrixRecipes:
    """Cibles : diagonal (LW 2004), single_factor (LW 2001), constant_correlation (LW 2003)."""

    def __init__(self, data):
        self.data = data
        self.Sample_covariance = data.cov().values        # ddof=1, cov brute du §9
        self.p = len(data.columns)
        self.n = len(data)

    @staticmethod
    def _is_positive_semidefinite(Mx):
        try:
            np.linalg.cholesky(Mx + 1e-16 * np.eye(len(Mx)))
            return True
        except np.linalg.LinAlgError:
            return False

    @staticmethod
    def cov_to_corr(cov):
        inv = np.diag(1 / np.sqrt(np.diag(cov)))
        return inv @ cov @ inv

    def shrunk_covariance_matrix(self, method, target):
        F, a = self._params(method, target)
        return (a * F + (1 - a) * self.Sample_covariance) * NUMBER_WORKING_DAYS, a

    def _params(self, method, target):
        if method == "sample_covariance":
            return np.eye(self.p), 0.0
        if method == "ledoit_wolf":
            if target == "diagonal":
                return self._lw_diagonal()
            if target == "single_factor":
                return self._lw_single_factor()
            if target == "constant_correlation":
                return self._lw_constant_correlation()
        raise ValueError(f"(method, target) inattendu : {(method, target)}")

    def _lw_diagonal(self):                                          # cible mu*I (LW 2004)
        if self.p == 1:
            return np.eye(1), 0.0
        R = np.nan_to_num(self.data.values)
        Rc = R - R.mean(axis=0)
        S = self.Sample_covariance * (self.n - 1) / self.n
        s2 = np.sum(S ** 2) / self.p
        mu = S.trace() / self.p
        delta = s2 - mu ** 2
        beta_ = (1 / (self.n ** 2 * self.p)) * np.sum(np.sum(Rc ** 2, axis=1) ** 2) - (1 / self.n) * s2
        beta = max(0, min(beta_, delta))
        return mu * np.eye(self.p), (0.0 if delta == 0 else beta / delta)

    def _lw_single_factor(self):                                    # cible 1-facteur (LW 2001)
        R = np.nan_to_num(self.data.values)
        Rc = R - R.mean(axis=0)
        mkt = R.mean(axis=1).reshape(self.n, 1)
        sample = np.cov(np.append(Rc, mkt, axis=1), rowvar=False) * (self.n - 1) / self.n
        betas = sample[0:self.p, self.p].reshape(self.p, 1)
        var_m = sample[self.p, self.p]
        S = sample[:self.p, :self.p]
        F = np.dot(betas, betas.T) / var_m
        F[np.eye(self.p) == 1] = np.diag(S)
        c = np.linalg.norm(S - F, "fro") ** 2
        Rc2 = Rc ** 2
        p_mat = (1 / self.n) * np.dot(Rc2.T, Rc2) - S ** 2
        p = np.sum(p_mat)
        mask = np.eye(self.p) == 0.0
        r_diag = p_mat[~mask].sum()
        z = Rc * np.tile(mkt - mkt.mean(axis=0), (self.p,))
        r1 = np.sum(((1 / self.n) * np.dot(Rc2.T, z) * np.tile(betas, (self.p,)).T / var_m)[mask])
        r2 = np.sum(((1 / self.n) * np.dot(z.T, z) * np.dot(betas, betas.T) / var_m ** 2)[mask])
        r3 = np.sum((S * F)[mask])
        r = (r1 + r1 - r2 - r3) + r_diag
        return F, max(0.0, min(1.0, ((p - r) / c) / self.n))

    def _lw_constant_correlation(self):                             # cible corr constante (LW 2003)
        R = np.nan_to_num(self.data.values)
        Rc = R - R.mean(axis=0)
        S = self.Sample_covariance * (self.n - 1) / self.n
        mask = np.eye(self.p) == 0.0
        corr = self.cov_to_corr(S)
        vd = np.diag(np.sqrt(np.diag(S)))
        vdi = np.diag(1 / np.sqrt(np.diag(S)))
        rbar = corr[mask].sum() / (self.p * (self.p - 1))
        Ct = np.eye(self.p)
        Ct[mask] = rbar
        F = vd @ Ct @ vd
        Rc2 = Rc ** 2
        pi_mat = (1 / self.n) * np.dot(Rc2.T, Rc2) - S ** 2
        pi_hat = np.sum(pi_mat)
        diag_part = np.sum(pi_mat[~mask])
        m1 = np.dot((Rc ** 3).T, Rc) / self.n - np.diag(np.diag(S)).dot(S)
        off = np.sum((rbar * np.dot(vdi, m1).dot(vd))[mask])
        gamma = np.linalg.norm(S - F, "fro") ** 2
        return F, max(0.0, min(1.0, ((pi_hat - (diag_part + off)) / gamma) / self.n))


TARGETS_LW = {"sample": ("sample_covariance", "diagonal"), "LW-diag": ("ledoit_wolf", "diagonal"),
              "LW-1fac": ("ledoit_wolf", "single_factor"), "LW-cc": ("ledoit_wolf", "constant_correlation")}


def cov_pit_shrunk(wf_ret, bids, tR, target):
    """Sigma annualisée K×K sur la fenêtre commune. (None, nan) si < RISK_WINDOW_MIN jours communs."""
    R = fenetre_pit(wf_ret, bids, tR)
    if len(R) < RISK_WINDOW_MIN or R.shape[1] < 2:
        return None, np.nan
    m, s = TARGETS_LW[target]
    return CovarianceMatrixRecipes(R).shrunk_covariance_matrix(m, s)


# ── FIFO de détention (jours calendaires — copier_les_membres/tables_membres_tickers) ─────────

def fifo_holding(M, g, last_day=None):
    """Apparie chaque vente aux achats les plus anciens (FIFO) -> épisodes de détention.

    Rend (closed, opened) : listes de (durée en jours CALENDAIRES, parts) ; les épisodes encore
    ouverts sont censurés à `last_day` (défaut : dernier jour du calendrier).
    """
    last_day = M.cal.max() if last_day is None else last_day
    closed, opened = [], []
    for tk, gt in g.groupby("ticker"):
        lots = deque()
        for _, row in gt.sort_values("traded").iterrows():
            dd, p = eff_price(M, tk, row["traded"])
            if dd is None:
                continue
            q = row["size_usd"] / p
            if row["op"] == "buy":
                lots.append([dd, q])
            else:
                held = sum(l[1] for l in lots)
                take_tot = min(q, held)
                while take_tot > 1e-12 and lots:
                    tau_b, parts = lots[0]
                    take = min(parts, take_tot)
                    closed.append(((dd - tau_b).days, take))
                    take_tot -= take
                    if parts - take <= 1e-12:
                        lots.popleft()
                    else:
                        lots[0][1] = parts - take
        for tau_b, parts in lots:
            if parts > 1e-9:
                opened.append(((last_day - tau_b).days, parts))
    return closed, opened
