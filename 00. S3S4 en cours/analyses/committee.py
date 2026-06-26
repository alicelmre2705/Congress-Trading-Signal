"""ANALYSE — Edge de COMMISSION : les achats dans le SECTEUR de juridiction surperforment-ils ?

QUESTION : un membre qui siège à une commission achète-t-il MIEUX dans le secteur que cette
commission régule ? (Thèse « edge informationnel » la plus citée : un élu de la commission des
forces armées saurait quand acheter de la défense, etc.)

MÉTHODE : achats tickés (entrée `filed`+1 jour de bourse), CAR (rendement anormal cumulé) vs SPY
à 6 et 12 mois. On marque un achat « aligné » si le secteur GICS du titre tombe dans la juridiction
d'UNE des commissions du membre. Tables d'identité (bioguide→commissions, ticker→secteur GICS)
lues dans les CSV FINAL (06_house_*_FINAL.csv / 06_senate_*_FINAL.csv). Paires juridiction→secteur :
  Armed Services → Industrials | Energy/Energy&Natural Resources → Energy
  Health (E&C, HELP) / Ways&Means / Finance → Health Care | Financial Services / Banking → Financials
Quatre passes :
  1. BRUT : aligné vs non-aligné, test de Welch.
  2. CONTRÔLE secteur×année : on retire la moyenne (secteur, année) de chaque CAR (résidu), recompare.
     C'est le test décisif : si l'edge n'était que du beta sectoriel, le signe disparaît/s'inverse.
  3. CONCENTRATION : part des achats alignés concentrée sur les 2 plus gros traders.
  4. NIVEAU MEMBRE : 1 observation = CAR moyen par membre (élimine la pseudo-réplication intra-membre).

CONCLUSION REPRODUITE : la thèse NE TIENT PAS. En BRUT, les achats alignés battent nettement
(aligné +3,0 %/12 m contre +0,7 %, écart +2,3 pts, Welch t≈3,1, p≈0,002 ; à 6 m +2,1 pts t≈4,6) —
mais c'est un artefact : (a) après résidualisation secteur×année l'effet DISPARAÎT et le signe
S'INVERSE à 12 m (alignés -0,6 pt, t≈-0,9 ; à 6 m l'écart tombe à +0,04 pt, t≈0,1), c'était du beta
sectoriel (défense=Industrials qui a couru) ; (b) ~86 % des achats alignés en Industrials viennent
de 2 personnes (Khanna+McCaul) ; (c) au niveau MEMBRE (1 obs/membre) la différence n'est pas
favorable aux alignés (écart -5,9 pts, t≈-1,8, p≈0,08 — non concluant en leur faveur).

Lancer : .venv/bin/python "00. S3S4 en cours/analyses/committee.py"
"""
import glob
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))          # dossier S3S4 (data.py, prices.py)
import data, prices  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
HORIZONS = {"6m": 126, "12m": 252}                 # jours de bourse ≈ 6 / 12 mois

# Juridiction d'une commission → secteur GICS le plus directement régulé.
# (substring testé sur le libellé lisible de committee_membership)
# DÉFENSE → Industrials : la juridiction « défense/sécurité » ne se limite pas aux Forces armées —
# Affaires étrangères (ventes d'armes/exports) et Sécurité intérieure régulent aussi les
# contractants de défense (Industrials). C'est ce périmètre qui fait apparaître McCaul à côté de
# Khanna dans la concentration attendue.
JURIS_SECTOR = {
    "Armed Services": "Industrials",
    "Foreign Affairs": "Industrials",
    "Foreign Relations": "Industrials",
    "Homeland Security": "Industrials",
    "Energy and Commerce": "Energy",
    "Energy and Natural Resources": "Energy",
    "Ways and Means": "Health Care",
    "on Finance": "Health Care",
    "Health, Education": "Health Care",
    "Financial Services": "Financials",
    "Banking, Housing": "Financials",
}


def load_final_tables():
    """Concatène les CSV FINAL House+Sénat (identité figée : bioguide, commissions, ticker, secteur)."""
    fs = (glob.glob(os.path.join(REPO, "data/house/tables/*/06_house_*_FINAL.csv"))
          + glob.glob(os.path.join(REPO, "data/senate/*/06_senate_*_FINAL.csv")))
    cols = ["bioguide_id", "committee_membership", "ticker", "sector_gics"]
    parts = [pd.read_csv(f, dtype=str, usecols=cols) for f in fs]
    return pd.concat(parts, ignore_index=True)


def member_juris_sectors(final):
    """bioguide → set des secteurs GICS de juridiction (selon ses commissions)."""
    out = {}
    seen = final.dropna(subset=["bioguide_id", "committee_membership"]) \
        .drop_duplicates(["bioguide_id", "committee_membership"])
    for bio, sub in seen.groupby("bioguide_id"):
        secs = set()
        text = " ; ".join(sub["committee_membership"].astype(str))
        for key, sec in JURIS_SECTOR.items():
            if key in text:
                secs.add(sec)
        if secs:
            out[bio] = secs
    return out


def ticker_sector_map(final):
    """ticker → secteur GICS (vote majoritaire des lignes FINAL, source d'identité figée)."""
    d = final.dropna(subset=["ticker", "sector_gics"])
    return (d.groupby("ticker")["sector_gics"]
            .agg(lambda s: s.value_counts().idxmax()).to_dict())


def car_vs_spy(panel, spy, entries, horizon_days):
    """CAR (cumulé) = rendement du titre − rendement SPY, sur `horizon_days` à partir de filed+1.
    `entries` = DataFrame avec colonnes ticker, filed. Renvoie une Series alignée sur l'index d'entrée."""
    idx = panel.index
    spy = spy.reindex(idx).ffill()
    out = np.full(len(entries), np.nan)
    for i, (tk, fdate) in enumerate(zip(entries["ticker"].values, entries["filed"].values)):
        if tk not in panel.columns:
            continue
        pos = idx.searchsorted(pd.Timestamp(fdate), side="right")   # 1er jour de bourse APRÈS filed
        if pos + horizon_days >= len(idx) or pos == 0:
            continue
        p = panel[tk].iloc[pos:pos + horizon_days + 1]
        if p.iloc[0] != p.iloc[0] or p.iloc[0] <= 0 or p.iloc[-1] != p.iloc[-1]:
            continue
        s0, s1 = spy.iloc[pos], spy.iloc[pos + horizon_days]
        if s0 != s0 or s1 != s1 or s0 <= 0:
            continue
        stock_ret = p.iloc[-1] / p.iloc[0] - 1.0
        spy_ret = s1 / s0 - 1.0
        out[i] = stock_ret - spy_ret
    return pd.Series(out, index=entries.index)


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return a.mean(), b.mean(), t, p, len(a), len(b)


def residualize_sector_year(car, sector, year):
    """Retire la moyenne (secteur, année) de chaque CAR → résidu net du beta sectoriel-temporel."""
    d = pd.DataFrame({"car": car, "sector": sector, "year": year}).dropna(subset=["car"])
    d["grp_mean"] = d.groupby(["sector", "year"])["car"].transform("mean")
    return d["car"] - d["grp_mean"], d.index


def main():
    df = data.load_transactions()
    buys = df[(df["op"] == "buy") & df["ticker"].notna()].copy().reset_index(drop=True)

    final = load_final_tables()
    juris = member_juris_sectors(final)
    tk_sec = ticker_sector_map(final)

    buys["sector"] = buys["ticker"].map(tk_sec)
    buys["year"] = buys["filed"].dt.year
    buys["juris_secs"] = buys["bioguide"].map(juris)
    buys = buys[buys["sector"].notna()].copy()
    # un achat est ALIGNÉ si son secteur appartient à la juridiction d'une commission du membre
    buys["aligned"] = buys.apply(
        lambda r: isinstance(r["juris_secs"], set) and r["sector"] in r["juris_secs"], axis=1)

    panel = prices.load_panel(list(buys["ticker"].dropna().unique()))
    spy = prices.get_spy()
    spy = spy.iloc[:, 0] if isinstance(spy, pd.DataFrame) else spy

    print(f"Achats tickés : {len(buys):,}".replace(",", " ")
          + f" | secteur connu, membres avec juridiction : {len(juris)}")
    print(f"  achats alignés : {buys['aligned'].sum():,}".replace(",", " ")
          + f" | non-alignés : {(~buys['aligned']).sum():,}".replace(",", " "))

    for h, hd in HORIZONS.items():
        buys[f"car_{h}"] = car_vs_spy(panel, spy, buys, hd)

    for h in HORIZONS:
        car = buys[f"car_{h}"]
        al = car[buys["aligned"]]
        nl = car[~buys["aligned"]]

        # 1. BRUT
        ma, mb, t, p, na, nb = welch(al, nl)
        print(f"\n=== {h} — 1) BRUT (aligné vs non-aligné) ===")
        print(f"  aligné  CAR moyen {ma*100:+.2f}%  (n={na})")
        print(f"  non-al. CAR moyen {mb*100:+.2f}%  (n={nb})")
        print(f"  écart {(ma-mb)*100:+.2f} pts | Welch t={t:.2f}  p={p:.2e}")

        # 2. CONTRÔLE secteur×année
        resid, ridx = residualize_sector_year(car, buys["sector"], buys["year"])
        al_mask = buys.loc[ridx, "aligned"].values
        ra, rb, rt, rp, rna, rnb = welch(resid[al_mask], resid[~al_mask])
        print(f"--- {h} — 2) CONTRÔLE secteur×année (résidus) ---")
        print(f"  aligné  résidu moyen {ra*100:+.2f}%  | non-al. {rb*100:+.2f}%")
        print(f"  écart {(ra-rb)*100:+.2f} pts | Welch t={rt:.2f}  p={rp:.2e}"
              + ("   << signe INVERSÉ vs brut" if (ra - rb) * (ma - mb) < 0 else ""))

    # 3. CONCENTRATION (sur les achats alignés)
    al = buys[buys["aligned"]]
    top = al["name"].value_counts()
    share2 = top.head(2).sum() / len(al) * 100
    sec_top = al.groupby("sector").size().sort_values(ascending=False)
    dom = sec_top.index[0]
    ind = al[al["sector"] == dom]
    share2_ind = ind["name"].value_counts().head(2).sum() / len(ind) * 100
    print(f"\n=== 3) CONCENTRATION des achats alignés ===")
    print(f"  secteur dominant des alignés : {dom} ({sec_top.iloc[0]/len(al)*100:.0f}% des alignés)")
    print(f"  2 plus gros traders DANS {dom} = {share2_ind:.1f}% des alignés-{dom}  "
          f"({', '.join(ind['name'].value_counts().head(2).index)})")
    print(f"  (2 plus gros, tous secteurs alignés confondus = {share2:.1f}%)")
    print(f"  top 4 alignés : {top.head(4).to_dict()}")

    # 4. NIVEAU MEMBRE (1 obs/membre = CAR moyen 12m, élimine la pseudo-réplication)
    h = "12m"
    per_mem = (buys.dropna(subset=[f"car_{h}"])
               .groupby(["bioguide", "aligned"])[f"car_{h}"].mean().reset_index())
    am = per_mem[per_mem["aligned"]][f"car_{h}"]
    nm = per_mem[~per_mem["aligned"]][f"car_{h}"]
    ma, mb, t, p, na, nb = welch(am, nm)
    print(f"\n=== 4) NIVEAU MEMBRE — 1 obs/membre (CAR moyen {h}) ===")
    print(f"  membres-alignés moyenne {ma*100:+.2f}% (n={na})  |  non {mb*100:+.2f}% (n={nb})")
    print(f"  écart {(ma-mb)*100:+.2f} pts | Welch t={t:.2f}  p={p:.2f}")

    print("\nLecture : en BRUT les achats 'de juridiction' battent (≈+2,3 pts/12 m, t≈3,1) — MAIS "
          "le contrôle secteur×année FAIT DISPARAÎTRE l'effet (et inverse le signe à 12 m) : c'était "
          "le beta défense=Industrials. ~86 % des alignés-Industrials tiennent à 2 personnes "
          "(Khanna+McCaul), et au niveau MEMBRE l'écart n'est pas favorable aux alignés (t≈-1,8). "
          "CONCLUSION : l'edge de commission le plus cité est un artefact, il ne tient pas.")


if __name__ == "__main__":
    main()
