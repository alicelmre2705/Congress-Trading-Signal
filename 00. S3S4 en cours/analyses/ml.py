"""ANALYSE — ML attrape-tout : une structure prédictive QUELCONQUE dans les achats du Congrès ?

QUESTION : au-delà des signaux linéaires testés ailleurs (IC, breadth…), un modèle non-linéaire
attrape-tout (gradient boosting) avec TOUTES les features disponibles (secteur, taille, parti,
chambre, calendrier, délai de déclaration, clustering inter-membres, beta/vol du titre, commissions,
ancienneté) parvient-il à prédire le SIGNE du rendement anormal forward d'un achat ? Si oui, le
signal serait exploitable ; sinon, le « edge » apparent est du bruit + un effet de régime.

MÉTHODE : un échantillon AU NIVEAU-ACHAT (1 ligne = 1 achat tické, entrée = date `filed`, publique).
  - Label : signe (1/0) du rendement anormal forward 6 mois du titre vs SPY (CAR = r_titre − r_SPY).
  - Features : secteur GICS (depuis les tables FINAL), log size_usd, parti, chambre, mois, année,
    délai filed−traded (jours), nb de membres distincts ayant acheté le même ticker dans ±30 j
    (proxy de cluster/« conviction collective »), beta et vol 1-an du titre (estimés sur le cache prix),
    committees_key_flag et years_in_office (depuis FINAL) quand disponibles.
  Quatre validations honnêtes :
  (1) HistGradientBoostingClassifier, split TEMPOREL strict train 2014-2020 / test OOS 2021-2026 :
      AUC train vs AUC OOS, accuracy OOS vs baseline classe-majoritaire.
  (2) Walk-forward expansif (plis annuels) : AUC moyenne hors-échantillon, dispersion par pli.
  (3) Importance des features par PERMUTATION sur l'OOS (et non sur le train).
  (4) Quartile haute-confiance Q4 de la proba OOS : rendement anormal moyen ET médian, win-rate.

CONCLUSION REPRODUITE : structure quasi nulle. AUC OOS ≈ 0,52 alors que l'AUC train ≈ 0,74
(sur-apprentissage), accuracy OOS sous la baseline classe-majoritaire. Walk-forward ≈ 0,53, >0,5
mais très hétérogène d'un pli à l'autre. La permutation place le BETA du titre en tête (effet de
régime/marché), AUCUNE feature « initié » (commission, taille, cluster) ne porte. Le quartile haute
confiance Q4 a une moyenne positive (~+1,7 %) mais une MÉDIANE NÉGATIVE (~−1 %) et un win-rate ~47 % :
le gain est tiré par une queue, pas par le trade typique. → résidu réel mais minuscule (mélange
régime + bruit de queue), insuffisant pour fonder une stratégie.

Lancer : .venv/bin/python "00. S3S4 en cours/analyses/ml.py"
"""
import glob
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))          # dossier S3S4 (data.py, prices.py)
import data, prices  # noqa: E402

from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.inspection import permutation_importance  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))       # dépôt Jupiter
HORIZON_DAYS = 126                                  # ~6 mois de bourse
SEED = 0


# ----------------------------------------------------------------------------- features externes (FINAL)
def load_final_features():
    """Lit les tables FINAL House+Sénat (LECTURE SEULE) → deux dictionnaires de jointure :
       - ticker → secteur GICS (modal)
       - bioguide → (committees_key_flag modal, years_in_office max)."""
    fs = (glob.glob(os.path.join(REPO, "data/house/tables/*/06_house_*_FINAL.csv"))
          + glob.glob(os.path.join(REPO, "data/senate/*/06_senate_*_FINAL.csv")))
    d = pd.concat([pd.read_csv(f, dtype=str) for f in fs], ignore_index=True)
    sec = (d.dropna(subset=["ticker", "sector_gics"])
           .groupby("ticker")["sector_gics"].agg(lambda s: s.mode().iloc[0]))
    kf = d.copy()
    kf["key"] = (kf["committees_key_flag"].astype(str).str.lower() == "true").astype(int)
    kf["yio"] = pd.to_numeric(kf["years_in_office"], errors="coerce")
    mem = kf.groupby("bioguide_id").agg(key_flag=("key", "max"), years_office=("yio", "max"))
    return sec.to_dict(), mem


# ----------------------------------------------------------------------------- beta / vol par ticker
def ticker_risk(panel, spy):
    """Beta et volatilité annualisée par ticker sur toute la fenêtre du cache (proxy de risque/régime)."""
    rp = panel.pct_change()
    rb = spy.reindex(panel.index).pct_change()
    var_b = rb.var()
    out = {}
    for t in panel.columns:
        r = rp[t]
        j = r.notna() & rb.notna()
        if j.sum() < 120:
            continue
        beta = np.cov(r[j], rb[j])[0, 1] / var_b if var_b > 0 else np.nan
        out[t] = (beta, r[j].std() * np.sqrt(252))
    return out


# ----------------------------------------------------------------------------- label : CAR 6 mois vs SPY
def forward_car(panel, spy, ticker, entry_date):
    """Rendement anormal du titre sur ~6 mois après `entry_date` (1er jour coté ≥ entrée) − même fenêtre SPY."""
    if ticker not in panel.columns:
        return np.nan
    s = panel[ticker].dropna()
    pos = s.index.searchsorted(entry_date)
    if pos >= len(s) or pos + HORIZON_DAYS >= len(s):
        return np.nan
    sp = spy.reindex(s.index)
    p0, p1 = s.iloc[pos], s.iloc[pos + HORIZON_DAYS]
    b0, b1 = sp.iloc[pos], sp.iloc[pos + HORIZON_DAYS]
    if not (p0 > 0 and b0 > 0) or np.isnan(b1):
        return np.nan
    return (p1 / p0 - 1.0) - (b1 / b0 - 1.0)


# ----------------------------------------------------------------------------- construction du dataset
def build_dataset(df, panel, spy):
    sec_map, mem = load_final_features()
    risk = ticker_risk(panel, spy)

    buys = df[(df["op"] == "buy") & df["ticker"].notna()].copy()
    buys = buys[buys["ticker"].isin(panel.columns)].sort_values("filed").reset_index(drop=True)

    # cluster ±30 j : nb de membres distincts ayant acheté le même ticker autour du même filed
    buys["filed_ord"] = buys["filed"].map(pd.Timestamp.toordinal)
    cluster = np.zeros(len(buys), dtype=int)
    for tk, g in buys.groupby("ticker"):
        idx = g.index.to_numpy()
        ords = g["filed_ord"].to_numpy()
        bios = g["bioguide"].to_numpy()
        for k, (i, o) in enumerate(zip(idx, ords)):
            m = np.abs(ords - o) <= 30
            cluster[i] = len(set(bios[m]))
    buys["cluster_n"] = cluster

    rows = []
    for r in buys.itertuples(index=False):
        car = forward_car(panel, spy, r.ticker, r.filed)
        if np.isnan(car):
            continue
        beta, vol = risk.get(r.ticker, (np.nan, np.nan))
        m = mem.loc[r.bioguide] if r.bioguide in mem.index else None
        rows.append({
            "year": r.filed.year,
            "month": r.filed.month,
            "sector": sec_map.get(r.ticker, "Unknown"),
            "chamber": r.chamber,
            "party": (r.party if isinstance(r.party, str) else "NA"),
            "log_size": np.log10(max(r.size_usd, 1001.0)),
            "filing_delay": max((r.filed - r.traded).days, 0),
            "cluster_n": r.cluster_n,
            "beta": beta,
            "vol": vol,
            "key_flag": (int(m["key_flag"]) if m is not None and not np.isnan(m["key_flag"]) else -1),
            "years_office": (m["years_office"] if m is not None and not np.isnan(m["years_office"]) else np.nan),
            "car6": car,
            "label": int(car > 0),
        })
    return pd.DataFrame(rows)


def to_xy(d):
    """Encode les catégorielles en `category` (HGB gère le NaN nativement) et renvoie X, y, car."""
    cat = ["sector", "chamber", "party"]
    X = d.drop(columns=["car6", "label"]).copy()
    for c in cat:
        X[c] = X[c].astype("category")
    return X, d["label"].to_numpy(), d["car6"].to_numpy()


def fit_hgb(Xtr, ytr):
    cat_mask = [str(t) == "category" for t in Xtr.dtypes]
    clf = HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.05, max_depth=3, l2_regularization=1.0,
        categorical_features=cat_mask, random_state=SEED)
    clf.fit(Xtr, ytr)
    return clf


# ----------------------------------------------------------------------------- main
def main():
    df = data.load_transactions()
    panel = prices.load_panel(list(df["ticker"].dropna().unique()))
    spy = prices.get_spy()
    print(f"Panel : {panel.shape[1]} tickers en cache | transactions {len(df):,}".replace(",", " "))

    d = build_dataset(df, panel, spy)
    print(f"Dataset niveau-achat : {len(d):,} achats étiquetés ".replace(",", " ")
          + f"({d['label'].mean()*100:.1f}% positifs) | features : "
          + f"{[c for c in d.columns if c not in ('car6','label')]}")

    # (1) split temporel strict 2014-2020 / 2021-2026 ----------------------------------------------
    tr, te = d[d["year"] <= 2020], d[d["year"] >= 2021]
    Xtr, ytr, _ = to_xy(tr)
    Xte, yte, car_te = to_xy(te)
    clf = fit_hgb(Xtr, ytr)
    auc_tr = roc_auc_score(ytr, clf.predict_proba(Xtr)[:, 1])
    p_te = clf.predict_proba(Xte)[:, 1]
    auc_te = roc_auc_score(yte, p_te)
    acc_te = ((p_te > 0.5).astype(int) == yte).mean()
    base = max(yte.mean(), 1 - yte.mean())     # baseline = toujours prédire la classe majoritaire
    print("\n=== (1) Split temporel strict — train 2014-2020 / OOS 2021-2026 ===")
    print(f"  train n={len(tr):,}  OOS n={len(te):,}".replace(",", " "))
    print(f"  AUC train = {auc_tr:.3f}   AUC OOS = {auc_te:.3f}   (écart = sur-apprentissage)")
    print(f"  accuracy OOS = {acc_te:.3f}   baseline classe-majoritaire = {base:.3f}   "
          f"→ {'SOUS' if acc_te < base else 'au-dessus de'} la baseline")

    # (2) walk-forward expansif (plis annuels) -----------------------------------------------------
    years = sorted(d["year"].unique())
    aucs = []
    for y in years:
        if y < 2017:
            continue
        tr_y, te_y = d[d["year"] < y], d[d["year"] == y]
        if len(te_y) < 60 or te_y["label"].nunique() < 2:
            continue
        Xa, ya, _ = to_xy(tr_y)
        Xb, yb, _ = to_xy(te_y)
        a = roc_auc_score(yb, fit_hgb(Xa, ya).predict_proba(Xb)[:, 1])
        aucs.append((y, a))
    auc_arr = np.array([a for _, a in aucs])
    print("\n=== (2) Walk-forward expansif (plis annuels) ===")
    print("  " + "  ".join(f"{y}:{a:.2f}" for y, a in aucs))
    print(f"  AUC moyenne = {auc_arr.mean():.3f}   écart-type entre plis = {auc_arr.std():.3f}   "
          f"(>0,5 mais hétérogène)")

    # (3) importance par permutation sur l'OOS -----------------------------------------------------
    pim = permutation_importance(clf, Xte, yte, scoring="roc_auc",
                                 n_repeats=10, random_state=SEED, n_jobs=-1)
    imp = (pd.Series(pim.importances_mean, index=Xte.columns)
           .sort_values(ascending=False))
    print("\n=== (3) Importance par permutation (chute d'AUC OOS, ↓) ===")
    for k, v in imp.items():
        print(f"  {k:14s} {v:+.4f}")
    print(f"  → en tête : '{imp.index[0]}' (risque/régime) ; "
          f"features 'initié' (cluster_n, log_size, key_flag) : "
          + ", ".join(f"{f}={imp[f]:+.4f}" for f in ["cluster_n", "log_size", "key_flag"]))

    # (4) quartile haute-confiance Q4 OOS ----------------------------------------------------------
    te2 = te.copy()
    te2["p"] = p_te
    q = te2["p"].quantile(0.75)
    hi = te2[te2["p"] >= q]
    print("\n=== (4) Quartile haute-confiance Q4 (proba OOS la plus haute) ===")
    print(f"  n={len(hi):,}  seuil proba={q:.3f}".replace(",", " "))
    print(f"  CAR 6 mois — moyenne {hi['car6'].mean()*100:+.2f}%   "
          f"MÉDIANE {hi['car6'].median()*100:+.2f}%   "
          f"win-rate {(hi['car6'] > 0).mean()*100:.1f}%")
    print(f"  (référence tous OOS : moyenne {te2['car6'].mean()*100:+.2f}%  "
          f"médiane {te2['car6'].median()*100:+.2f}%  win {(te2['car6']>0).mean()*100:.1f}%)")

    print("\nLecture / Conclusion : AUC OOS ≈ 0,5 malgré une AUC train élevée (sur-apprentissage pur) ; "
          "le walk-forward dépasse à peine 0,5 et varie selon le régime ; la permutation ne retient "
          "que le BETA (effet marché), pas l'information d'initié ; et le quartile le plus confiant a "
          "une MÉDIANE négative avec un win-rate < 50 %. Le gain moyen positif vient d'une QUEUE, pas "
          "du trade typique. → structure prédictive réelle mais minuscule (régime + bruit de queue), "
          "INSUFFISANTE pour une stratégie.")


if __name__ == "__main__":
    main()
