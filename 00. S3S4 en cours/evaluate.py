"""S3S4 / evaluate — honnêteté statistique : alpha factoriel, Deflated Sharpe, validation OOS.

- `factor_alpha` : régresse l'excès de rendement quotidien sur Fama-French-Carhart (Mkt-RF, SMB, HML,
  Mom) → alpha annualisé + t-stat (Newey-West si statsmodels présent, sinon OLS). Isole le beta tech.
- `psr` / `deflated_sharpe` : Probabilistic & Deflated Sharpe Ratio (López de Prado) — pénalise le
  nombre de variantes essayées (anti data-snooping).
"""
import numpy as np
import pandas as pd
from scipy import stats


def factor_alpha(daily: pd.Series, factors: pd.DataFrame) -> dict:
    """Alpha annualisé (rendement anormal) après contrôle des facteurs FF-Carhart + t-stat."""
    f = factors.reindex(daily.index).dropna()
    y = (daily.reindex(f.index) - f["RF"]).values
    cols = [c for c in ["Mkt-RF", "SMB", "HML", "Mom"] if c in f.columns]
    X = np.column_stack([np.ones(len(f))] + [f[c].values for c in cols])
    try:
        import statsmodels.api as sm
        res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
        a, t = res.params[0], res.tvalues[0]
        betas = dict(zip(cols, res.params[1:]))
    except Exception:
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        s2 = (resid @ resid) / (len(y) - X.shape[1])
        se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
        a, t = beta[0], beta[0] / se[0]
        betas = dict(zip(cols, beta[1:]))
    return {"alpha_annuel": a * 252, "alpha_t": t, "betas": {k: round(v, 3) for k, v in betas.items()},
            "beta_marche": round(betas.get("Mkt-RF", float("nan")), 3)}


def _sr_stats(daily: pd.Series):
    r = daily.dropna().values
    n = len(r)
    sr = r.mean() / (r.std(ddof=1) + 1e-12)            # Sharpe PAR OBSERVATION (quotidien)
    return sr, n, stats.skew(r), stats.kurtosis(r, fisher=False)


def psr(daily: pd.Series, sr_benchmark_daily=0.0) -> float:
    """Probabilistic Sharpe Ratio : P(SR vrai > benchmark), corrigé skew/kurtosis."""
    sr, n, sk, ku = _sr_stats(daily)
    num = (sr - sr_benchmark_daily) * np.sqrt(n - 1)
    den = np.sqrt(1 - sk * sr + (ku - 1) / 4.0 * sr ** 2)
    return float(stats.norm.cdf(num / (den + 1e-12)))


def expected_max_sr(sr_std_daily: float, n_trials: int) -> float:
    """SR0 = Sharpe maximal attendu sous H0 pour `n_trials` essais (López de Prado)."""
    if n_trials < 2 or sr_std_daily <= 0:
        return 0.0
    g = 0.5772156649  # Euler-Mascheroni
    z1 = stats.norm.ppf(1 - 1.0 / n_trials)
    z2 = stats.norm.ppf(1 - 1.0 / (n_trials * np.e))
    return sr_std_daily * ((1 - g) * z1 + g * z2)


def deflated_sharpe(daily: pd.Series, sr_std_daily: float, n_trials: int) -> float:
    """DSR : PSR contre le Sharpe max attendu compte tenu de `n_trials` variantes testées."""
    return psr(daily, expected_max_sr(sr_std_daily, n_trials))


def oos_split(daily: pd.Series, split="2021-01-01") -> dict:
    """Sharpe annualisé in-sample vs out-of-sample (un seul split temporel)."""
    a, b = daily[daily.index < split], daily[daily.index >= split]
    def shp(x):
        return float(x.mean() / (x.std() + 1e-12) * np.sqrt(252)) if len(x) > 20 else float("nan")
    return {"split": split, "sharpe_IS": round(shp(a), 2), "sharpe_OOS": round(shp(b), 2)}
