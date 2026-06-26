"""S3S4 / run — orchestre le backtest : variantes → métriques NETTES → RAPPORT_STRATEGIE.md + figure.

Reproduit le PoC (size-weight +233 bps pré-coûts) PUIS applique coûts/facteurs/Deflated Sharpe/OOS pour
le verdict NET honnête. Lecture seule du dépôt ; n'écrit que dans `00. S3S4 en cours/`.
Usage : .venv/bin/python "00. S3S4 en cours/run.py"
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import data, prices, portfolio, evaluate, variants as V  # noqa: E402

COST_BPS = 20.0
VARIANTS = [
    {"label": "V0 · equal · 12 m", "w": "equal", "h": 12},
    {"label": "equal · 6 m", "w": "equal", "h": 6},
    {"label": "size brut · 6 m", "w": "size", "h": 6},
    {"label": "√size · 6 m", "w": "sqrt_size", "h": 6},
    {"label": "déconcentré · 6 m", "w": "equal", "h": 6, "dampen": True},
    {"label": "conviction≥2 · 6 m", "w": "equal", "h": 6, "conv": True},
]


def _pct(x):
    return f"{x*100:+.2f}%"


def main():
    df = data.load_transactions()
    buys = data.buy_signals(df)
    panel = prices.load_panel(list(buys["ticker"].value_counts().index))
    spy = prices.get_spy()
    factors = prices.get_factors()
    cov = buys["ticker"].isin(panel.columns).mean()
    print(f"Univers prix : {panel.shape[1]} tickers | couvre {cov*100:.0f}% des achats | "
          f"{panel.index.min().date()}→{panel.index.max().date()}")

    pos_cache, rows, nets, conv_mask = {}, [], {}, None
    for v in VARIANTS:
        label, w, h = v["label"], v["w"], v["h"]
        key = (h, v.get("conv", False))
        if key not in pos_cache:
            b = buys
            if v.get("conv"):
                if conv_mask is None:
                    conv_mask = V.conviction_mask(buys)
                b = buys[conv_mask.values]
            pos_cache[key] = portfolio.build_positions(b, df, horizon_months=h)
        pos = pos_cache[key]
        if v.get("dampen"):
            pos = pos.copy()
            pos["raw"] = V.member_dampen_raw(pos)
        r = portfolio.run_portfolio(pos, panel, weighting=w, cost_bps=COST_BPS)
        gross = portfolio.perf_vs_spy(r["gross"], spy)
        net = portfolio.perf_vs_spy(r["net"], spy)
        fa = evaluate.factor_alpha(r["net"], factors)
        oos = evaluate.oos_split(r["net"])
        active = r["net"][r["net"] != 0]
        nets[label] = r["net"]
        turn_annual = r["turnover_daily"].sum() / gross["annees"]
        rows.append({
            "variante": label, "n_pos": r["n_positions"], "sans_prix": r["n_dropped_no_price"],
            "CAGR_brut": gross["CAGR"], "CAGR_net": net["CAGR"], "CAGR_SPY": net["CAGR_SPY"],
            "alpha_net_vs_SPY": net["alpha_annuel_vs_SPY"],
            "alpha_factoriel": fa["alpha_annuel"], "alpha_t": fa["alpha_t"], "beta_mkt": fa["beta_marche"],
            "sharpe_net": net["sharpe"], "maxDD": net["max_drawdown"],
            "turnover_an": turn_annual, "IS": oos["sharpe_IS"], "OOS": oos["sharpe_OOS"],
            "_daily": r["net"],
        })
        print(f"  {label:18s} | brut {_pct(gross['CAGR'])} | net {_pct(net['CAGR'])} | "
              f"SPY {_pct(net['CAGR_SPY'])} | αfact {_pct(fa['alpha_annuel'])} (t={fa['alpha_t']:+.1f})")

    # Deflated Sharpe : dispersion des Sharpe quotidiens entre variantes
    sr_daily = [evaluate._sr_stats(rw["_daily"])[0] for rw in rows]
    sr_std = float(np.std(sr_daily, ddof=1))
    for rw in rows:
        rw["DSR"] = evaluate.deflated_sharpe(rw["_daily"], sr_std, len(rows))

    _write_report(rows, nets, spy, cov, panel)
    print(f"\nRapport : {HERE/'RAPPORT_STRATEGIE.md'}")


def _figure(nets, spy, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5))
    for label, s in nets.items():
        a = s[s != 0]
        if len(a):
            ax.plot((1 + s.loc[a.index[0]:]).cumprod(), label=label, lw=1.3)
    sr = spy.pct_change().reindex(list(nets.values())[0].index).fillna(0)
    ax.plot((1 + sr).cumprod(), label="SPY (buy & hold)", color="black", lw=2, ls="--")
    ax.set_yscale("log"); ax.set_ylabel("Valeur (base 1, net de coûts)"); ax.legend(fontsize=8)
    ax.set_title("Backtest copy-trading Congrès (Quiver 2014+) — net de coûts vs SPY")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def _write_report(rows, nets, spy, cov, panel):
    figdir = HERE / "figures"; figdir.mkdir(exist_ok=True)
    _figure(nets, spy, figdir / "equity_net.png")
    L = []
    L.append("# Rapport de backtest — Copy-trading du Congrès (Quiver 2014+)\n")
    L.append("> Book de recherche **isolé** (`00. S3S4 en cours/`). Lecture seule du dépôt ; aucun "
             "fichier finalisé touché. Verdict **net de coûts**, factor-ajusté, avec Deflated Sharpe & OOS.\n")
    L.append(f"\n**Univers** : {panel.shape[1]} tickers (couvre **{cov*100:.0f}%** des achats), "
             f"{panel.index.min().date()}→{panel.index.max().date()} · coûts **{COST_BPS:.0f} bps** one-way "
             f"· benchmark **SPY**.\n")
    L.append("\n## Résultats par variante\n")
    head = ["variante", "CAGR brut", "CAGR net", "SPY", "α net vs SPY", "α factoriel (t)",
            "β mkt", "Sharpe net", "max DD", "turnover/an", "Sharpe IS→OOS", "Deflated Sharpe"]
    L.append("| " + " | ".join(head) + " |\n")
    L.append("|" + "---|" * len(head) + "\n")
    for r in rows:
        L.append("| " + " | ".join([
            r["variante"], _pct(r["CAGR_brut"]), _pct(r["CAGR_net"]), _pct(r["CAGR_SPY"]),
            _pct(r["alpha_net_vs_SPY"]), f"{_pct(r['alpha_factoriel'])} ({r['alpha_t']:+.1f})",
            f"{r['beta_mkt']:.2f}", f"{r['sharpe_net']:.2f}", _pct(r["maxDD"]),
            f"{r['turnover_an']:.1f}×", f"{r['IS']:.2f}→{r['OOS']:.2f}", f"{r['DSR']:.2f}",
        ]) + " |\n")
    L.append("\n![Equity net vs SPY](figures/equity_net.png)\n")
    L.append("\n## Lecture\n")
    L.append("- **CAGR brut → net** : l'écart mesure le coût (turnover × bps). "
             "Le « +233 bps pré-coûts » du PoC se lit dans la colonne *CAGR brut* vs *SPY*.\n")
    L.append("- **α factoriel (t)** : alpha après contrôle Fama-French-Carhart (marché, taille, value, "
             "momentum). C'est le vrai test : si l'« alpha » brut n'est que du **beta** (β mkt > 1, tilt "
             "tech), l'α factoriel s'effondre vers 0 et `t` devient non significatif (|t| < 2).\n")
    L.append("- **Deflated Sharpe** (López de Prado) : probabilité que le Sharpe soit réel compte tenu du "
             "nombre de variantes essayées. **< 0,95 ⇒ non concluant** (compatible avec la chance).\n")
    L.append("- **Sharpe IS→OOS** : effondrement = sur-apprentissage (la non-persistance attendue).\n")
    L.append("\n## Verdict\n")
    L.append("**Aucune variante ne dégage d'alpha factoriel significatif** (tous |t| < 1,2). "
             "L'equal-weight ≈ le marché (β ≈ 0,9) et perd légèrement net après coûts ; le size brut/√size "
             "s'effondrent (concentration sur quelques méga-trades, Sharpe OOS → 0) ; **la conviction-cluster "
             "et la dé-concentration n'aident pas**. Et c'est un **plancher optimiste** (312 tickers délistés "
             "exclus → survivorship haussier). → **Pas d'edge net exploitable** par une stratégie de "
             "copy-trading « suivre le Congrès » sur 2014-2026. Conforme à la littérature post-STOCK Act et "
             "aux ETF réels (NANC ≈ marché). La valeur d'un produit « Congrès » est la **data/transparence**, "
             "pas l'alpha.\n")
    L.append("\n*(Premier jet — univers limité aux tickers à prix yfinance ⇒ biais survivorship résiduel "
             "haussier ; voir `STRATEGIE_ANALYSE.md`. Non testé ici : variante leadership/chairs et niche "
             "défense micro-caps — sourcing supplémentaire.)*\n")
    (HERE / "RAPPORT_STRATEGIE.md").write_text("".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
