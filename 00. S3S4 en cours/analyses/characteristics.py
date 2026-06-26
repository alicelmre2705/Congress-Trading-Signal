"""ANALYSE — Quelles CARACTÉRISTIQUES de trade portent du signal ? (CAR vs SPY)

QUESTION : au-delà du « breadth » (cf. ic.py), certaines PROPRIÉTÉS d'un achat individuel
(taille de la fourchette $, chambre, délai de divulgation, nouveauté/prolixité du membre)
prédisent-elles un sur-rendement ? Et surtout : ce signal est-il une propriété GÉNÉRALISABLE
du type de trade, ou bien l'artefact d'une POIGNÉE de membres prolifiques ?

MÉTHODE : pour chaque achat tické, on calcule le CAR (cumulative abnormal return) du titre
contre SPY, entrée à `filed`+1 jour de bourse (date publique = INVESTISSABLE), horizons 6 et
12 mois (~126 / 252 jours de bourse). CAR = (prix_T/prix_0 − 1) − (SPY_T/SPY_0 − 1).
On segmente par caractéristique et on imprime le CAR moyen avec DEUX t-stats :
  - t NAÏF  : chaque trade = une observation indépendante (FAUX → gonfle artificiellement).
  - t CLUSTERISÉ PAR MEMBRE : on agrège d'abord en une moyenne par membre, puis t sur les
    moyennes-membres (un membre = une observation). C'est le test DÉCISIF : il neutralise le
    fait que quelques membres signent des milliers de trades corrélés.

CONCLUSION REPRODUITE : il y a bien un GRADIENT par taille (les grosses fourchettes >250k
sur-performent ~+4 % à 12 mois) et un effet « divulgation rapide » (≤10j ~+2,7 %), concentrés
dans la HOUSE (House>250k ~+5–6 %, Senate>250k négatif). La nouveauté ne porte rien (~0) et les
membres ultra-prolifiques sont légèrement négatifs. MAIS dès qu'on CLUSTERISE par membre, TOUS
les t-stats s'effondrent sous |t|=2 (House>250k 3.4→~0.9 ; >250k 2.5→~0.1 ; rapide 3.1→~1.5) :
le « signal » n'est pas une propriété du type de trade, c'est une poignée de membres (Mark Green,
Khanna, Perdue…). Rien de généralisable / exploitable.

Lancer : .venv/bin/python "00. S3S4 en cours/analyses/characteristics.py"
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))          # dossier S3S4 (data.py, prices.py)
import data, prices  # noqa: E402

HORIZONS = {"6m": 126, "12m": 252}                  # jours de bourse approx.


def compute_car(buys, panel, spy):
    """CAR vs SPY par achat, entrée filed+1 jour de bourse, horizons 6m/12m.

    Renvoie le DataFrame des achats enrichi des colonnes car_6m, car_12m (NaN si prix manquant).
    Vectorisé par ticker : on aligne chaque date d'entrée sur l'index de bourse, puis on lit le
    prix à l'offset h.
    """
    idx = panel.index
    spy = spy.reindex(idx).ffill()
    pos = pd.Series(np.arange(len(idx)), index=idx)   # date de bourse -> position entière

    out = buys.copy()
    for col in HORIZONS:
        out["car_" + col] = np.nan

    for tk, grp in out.groupby("ticker"):
        if tk not in panel.columns:
            continue
        px = panel[tk]
        # 1ʳᵉ date de bourse >= filed+1 (entrée investissable, post-divulgation)
        entry = (grp["filed"] + pd.Timedelta(days=1)).values
        e_pos = idx.searchsorted(entry, side="left")
        for i, p0 in zip(grp.index, e_pos):
            if p0 >= len(idx) - 1:
                continue
            d0 = idx[p0]
            base_px, base_spy = px.iloc[p0], spy.iloc[p0]
            if not np.isfinite(base_px) or base_px <= 0 or not np.isfinite(base_spy):
                continue
            for col, h in HORIZONS.items():
                p1 = p0 + h
                if p1 >= len(idx):
                    continue
                pt, st = px.iloc[p1], spy.iloc[p1]
                if not np.isfinite(pt) or not np.isfinite(st) or st <= 0:
                    continue
                stock_ret = pt / base_px - 1.0
                mkt_ret = st / base_spy - 1.0
                out.at[i, "car_" + col] = stock_ret - mkt_ret
    return out


def naive_t(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 5:
        return np.nan, np.nan, 0
    mu = x.mean()
    se = x.std(ddof=1) / np.sqrt(len(x))
    return mu, (mu / se if se > 0 else np.nan), len(x)


def clustered_t(df, car_col, member_col="bioguide"):
    """t CLUSTERISÉ PAR MEMBRE : moyenne par membre puis t sur les moyennes-membres.
    Neutralise la sur-représentation de quelques traders très actifs (= une obs par personne)."""
    g = df.dropna(subset=[car_col]).groupby(member_col)[car_col]
    mm = g.mean()                                    # un nombre par membre
    mm = mm[g.count() >= 1]
    if len(mm) < 5:
        return np.nan, np.nan, len(mm)
    mu = mm.mean()
    se = mm.std(ddof=1) / np.sqrt(len(mm))
    return mu, (mu / se if se > 0 else np.nan), len(mm)


def report_segment(df, label, car_col):
    mu_n, t_n, n = naive_t(df[car_col].values)
    mu_c, t_c, k = clustered_t(df, car_col)
    print(f"  {label:<34s} CAR {mu_n*100:+6.2f}%  | t_naïf {t_n:5.2f} (n={n:5d})"
          f"  || t_membre {t_c:5.2f} (k={k:3d} membres)")


def size_bucket(s):
    if s < 50_000:   return "1) <50k"
    if s < 100_000:  return "2) 50-100k"
    if s < 250_000:  return "3) 100-250k"
    if s < 1_000_000: return "4) 250k-1M"
    return "5) >1M"


def main():
    df = data.load_transactions()
    buys = data.buy_signals(df)                       # achats tickés
    tickers = list(buys["ticker"].dropna().unique())
    panel = prices.load_panel(tickers)
    spy = prices.get_spy()
    print(f"Achats tickés : {len(buys):,}".replace(",", " ")
          + f" | tickers {buys['ticker'].nunique()} (prix en cache : {panel.shape[1]})"
          + f" | membres {buys['bioguide'].nunique()}")

    b = compute_car(buys, panel, spy)
    cov = b["car_12m"].notna().mean()
    print(f"Couverture CAR 12m : {cov*100:.0f}% des achats (reste = prix manquant/trop récent)")
    print("\n>>> Entrée filed+1 ; CAR vs SPY ; t_naïf = 1 obs/trade (biaisé), "
          "t_membre = 1 obs/membre (DÉCISIF)\n")

    # 1) GRADIENT PAR TAILLE -------------------------------------------------
    b["bucket"] = b["size_usd"].map(size_bucket)
    print("=== 1) Taille de la fourchette $ (gradient attendu, >250k positif) ===")
    for h in ("6m", "12m"):
        print(f"  -- horizon {h} --")
        for bk in sorted(b["bucket"].unique()):
            report_segment(b[b["bucket"] == bk], bk, "car_" + h)

    # 2) TAILLE × CHAMBRE ----------------------------------------------------
    print("\n=== 2) >250k par CHAMBRE @12m (l'effet est dans la House) ===")
    big = b[b["size_usd"] >= 250_000]
    report_segment(big, ">250k TOUTES chambres", "car_12m")
    report_segment(big[big["chamber"] == "house"], ">250k HOUSE", "car_12m")
    report_segment(big[big["chamber"] == "senate"], ">250k SENATE", "car_12m")

    # 3) DÉLAI DE DIVULGATION (conviction) -----------------------------------
    b["delay_days"] = (b["filed"] - b["traded"]).dt.days
    fast = b[(b["delay_days"] >= 0) & (b["delay_days"] <= 10)]
    slow = b[b["delay_days"] > 10]
    print("\n=== 3) Délai de divulgation (≤10j = conviction/rapidité) @12m ===")
    report_segment(fast, "divulgation RAPIDE (<=10j)", "car_12m")
    report_segment(slow, "divulgation lente (>10j)", "car_12m")

    # 4) NOUVEAUTÉ & PROLIXITÉ ----------------------------------------------
    b = b.sort_values("traded")
    b["is_new"] = ~b.duplicated(subset=["bioguide", "ticker"], keep="first")
    cnt = b.groupby("bioguide")["ticker"].transform("size")
    b["prolific"] = cnt > 1000
    print("\n=== 4) Nouveauté (1er achat du ticker par le membre) & prolixité ===")
    report_segment(b[b["is_new"]], "NOUVEAU ticker pour le membre", "car_6m")
    report_segment(b[~b["is_new"]], "ré-achat (déjà détenu)", "car_6m")
    report_segment(b[b["prolific"]], "membres PROLIFIQUES (>1000 achats)", "car_6m")
    report_segment(b[~b["prolific"]], "membres normaux (<=1000)", "car_6m")

    # 5) TEST DÉCISIF : récapitulatif naïf vs clusterisé ---------------------
    print("\n=== 5) TEST DÉCISIF — récap des t-stats : naïf -> clusterisé par membre ===")
    cases = [
        ("House >250k @12m", big[big["chamber"] == "house"], "car_12m"),
        (">250k toutes ch. @12m", big, "car_12m"),
        ("divulgation rapide @12m", fast, "car_12m"),
    ]
    for name, sub, col in cases:
        _, t_n, n = naive_t(sub[col].values)
        _, t_c, k = clustered_t(sub, col)
        verdict = "EFFONDRE <2" if abs(t_c) < 2 else "tient"
        print(f"  {name:<26s} t_naïf {t_n:5.2f} (n={n:5d})  ->  t_membre {t_c:5.2f} "
              f"(k={k:3d})   [{verdict}]")

    # Qui porte le signal ? (les fameux 'noms')
    top = (big[big["chamber"] == "house"].dropna(subset=["car_12m"])
           .groupby("name")["car_12m"].agg(["mean", "size"]).query("size >= 5")
           .sort_values("mean", ascending=False).head(5))
    print("\n  Top membres House>250k (CAR 12m moyen, >=5 trades) :")
    for nm, row in top.iterrows():
        print(f"    {nm:<26s} {row['mean']*100:+6.2f}%  ({int(row['size'])} trades)")

    print("\nLecture / Conclusion : le gradient par taille, l'effet House>250k et l'effet "
          "« divulgation rapide » sont NETS en t naïf (>2.5), mais s'EFFONDRENT sous |t|=2 quand "
          "on clusterise par membre. Le signal n'est PAS une propriété généralisable du type de "
          "trade : il est porté par une poignée de membres (Mark Green, Khanna, Perdue…). "
          "Nouveauté ≈ 0 ; ultra-prolifiques légèrement négatifs. Non exploitable comme règle.")


if __name__ == "__main__":
    main()
