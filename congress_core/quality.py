"""Rapport de qualité des données — livrable Ramify Semaine 2.

Charge les tables FINAL des deux chambres (2020→2026), calcule les CINQ contrôles qualité demandés
par Ramify, et génère figures + `docs/RAPPORT_QUALITE.md`. **Lecture seule des CSV FINAL, aucun
appel API.**

Les cinq contrôles :
  (a) Cohérence des dates : `disclosure_date >= transaction_date`.
  (b) Délai légal : `lag = disclosure - transaction` ventilé ≤45 j (légal STOCK Act) / 45–75 j / >75 j.
  (c) Distribution des montants (`amount_midpoint`) : médiane, quartiles, top déposants par volume.
  (d) Coverage par congressman : #trades, #années, première/dernière année, membres ≥10 trades.
  (e) Taux de transactions sans sortie déclarée : achats sans vente ultérieure (même bioguide+ticker).

Usage : `python -m congress_core.quality`  (écrit docs/RAPPORT_QUALITE.md + docs/quality/*.png)
"""
from pathlib import Path

import pandas as pd

from congress_core import crosscheck

YEARS = list(range(2020, 2027))
LEGAL_DELAY_DAYS = 45          # STOCK Act : PTR dû ~45 j après la transaction.
WINDOW_DELAY_DAYS = 75         # Fenêtre de tolérance utilisée par le pipeline (date_confidence).


# ───────────────────────────── Chargement ─────────────────────────────
def _final_path(repo_root: Path, chamber: str, year: int) -> Path:
    """House : data/house/tables/{y}/… ; Sénat : data/senate/{y}/… (arborescences différentes)."""
    if chamber == "house":
        return repo_root / "data" / "house" / "tables" / str(year) / f"06_house_{year}_FINAL.csv"
    return repo_root / "data" / "senate" / str(year) / f"06_senate_{year}_FINAL.csv"


def op_class(op) -> str:
    """Normalise les variantes d'`operation_type` (Sale / Sale (Full) / Sale (Partial) / Partial Sale
    / Purchase / Exchange) en classe canonique."""
    s = str(op).lower()
    if "purchase" in s:
        return "buy"
    if "sale" in s:
        return "sell"
    if "exchange" in s:
        return "exchange"
    return "other"


def load_final(repo_root: Path) -> pd.DataFrame:
    """Concatène tous les FINAL House+Sénat, ajoute `file_year`, `txn_year`, `lag_days`, `op`."""
    frames = []
    for chamber in ("house", "senate"):
        for year in YEARS:
            p = _final_path(repo_root, chamber, year)
            if not p.exists():
                continue
            df = pd.read_csv(p, dtype=str)
            df["file_year"] = year
            frames.append(df)
    if not frames:
        raise FileNotFoundError(f"Aucune table FINAL trouvée sous {repo_root}/data")
    full = pd.concat(frames, ignore_index=True)

    td = pd.to_datetime(full["transaction_date"], errors="coerce")
    dd = pd.to_datetime(full["disclosure_date"], errors="coerce")
    full["_td"], full["_dd"] = td, dd
    full["txn_year"] = td.dt.year
    full["lag_days"] = (dd - td).dt.days
    full["amount_midpoint"] = pd.to_numeric(full["amount_midpoint"], errors="coerce")
    full["op"] = full["operation_type"].map(op_class)
    return full


# ───────────────────────────── (a) Cohérence des dates ─────────────────────────────
def date_coherence(df: pd.DataFrame) -> pd.DataFrame:
    """Résumé par chambre : n, % dates parseables, % cohérentes (disclosure≥txn parmi parseables),
    incohérentes, et années de transaction implausibles (txn après dépôt ou avant 2012 — artefacts
    OCR de lecture d'année, déjà comptés dans les incohérentes via un délai négatif)."""
    rows = []
    for chamber, g in df.groupby("chamber"):
        n = len(g)
        valid = g["lag_days"].notna()
        n_valid = int(valid.sum())
        coherent = int((g["lag_days"] >= 0).sum())
        ty = g["txn_year"]
        impl = int(((ty > g["file_year"]) | (ty < 2012)).sum())
        rows.append({
            "chamber": chamber, "n": n,
            "dates_parseables_pct": round(100 * n_valid / n, 1),
            "coherentes_pct": round(100 * coherent / n_valid, 1) if n_valid else None,
            "incoherentes": n_valid - coherent,
            "annee_txn_implausible": impl,
            "date_manquante": n - n_valid,
        })
    return pd.DataFrame(rows).reset_index(drop=True)


# ───────────────────────────── (b) Délai légal 45 j ─────────────────────────────
def delay_buckets(df: pd.DataFrame) -> pd.DataFrame:
    """Ventilation du délai de divulgation par chambre : ≤45 j (légal) / 45–75 j / >75 j / négatif."""
    rows = []
    for chamber, g in df.groupby("chamber"):
        lag = g["lag_days"]
        valid = lag.notna()
        n = int(valid.sum())
        if not n:
            continue
        neg = int((lag < 0).sum())
        le45 = int(((lag >= 0) & (lag <= LEGAL_DELAY_DAYS)).sum())
        mid = int(((lag > LEGAL_DELAY_DAYS) & (lag <= WINDOW_DELAY_DAYS)).sum())
        over = int((lag > WINDOW_DELAY_DAYS).sum())
        rows.append({
            "chamber": chamber, "n_dates_valides": n,
            "<=45j_legal_pct": round(100 * le45 / n, 1),
            "45-75j_pct": round(100 * mid / n, 1),
            ">75j_pct": round(100 * over / n, 1),
            "negatif_pct": round(100 * neg / n, 1),
            "delai_median_j": int(lag[valid & (lag >= 0)].median()) if n else None,
        })
    return pd.DataFrame(rows)


def delay_outliers(df: pd.DataFrame, threshold: int = 365, top: int = 15) -> pd.DataFrame:
    """Plus grands délais (divulgations très tardives) — suspects au sens Ramify."""
    g = df[df["lag_days"] > threshold].copy()
    g = g.sort_values("lag_days", ascending=False).head(top)
    return g[["declarant_name", "chamber", "transaction_date", "disclosure_date",
              "lag_days", "ticker", "operation_type"]].reset_index(drop=True)


# ───────────────────────────── (c) Distribution des montants ─────────────────────────────
def amount_distribution(df: pd.DataFrame) -> dict:
    """Stats descriptives globales + par chambre + top déposants par volume estimé (Σ midpoint)."""
    amt = df["amount_midpoint"].dropna()
    overall = amt.describe(percentiles=[0.25, 0.5, 0.75, 0.9])
    by_chamber = df.groupby("chamber")["amount_midpoint"].describe(percentiles=[0.25, 0.5, 0.75])
    top = (df.groupby(["bioguide_id", "declarant_name", "chamber"])["amount_midpoint"]
             .agg(volume_estime="sum", n_trades="count")
             .reset_index().sort_values("volume_estime", ascending=False).head(15))
    top["volume_estime_musd"] = (top["volume_estime"] / 1e6).round(1)
    return {"overall": overall, "by_chamber": by_chamber,
            "top_volume": top[["declarant_name", "chamber", "n_trades", "volume_estime_musd"]]}


# ───────────────────────────── (d) Coverage par congressman ─────────────────────────────
def coverage_per_member(df: pd.DataFrame) -> pd.DataFrame:
    """Réutilise crosscheck.per_filer_status (digital/OCR par bioguide) et l'augmente de
    #années actives, première/dernière année de transaction."""
    parts = []
    for chamber, g in df.groupby("chamber"):
        parts.append(crosscheck.per_filer_status(g, None, chamber))
    base = pd.concat(parts, ignore_index=True)

    yrs = (df.dropna(subset=["txn_year"]).groupby("bioguide_id")["txn_year"]
             .agg(n_annees="nunique", premiere_annee="min", derniere_annee="max").reset_index())
    out = base.merge(yrs, on="bioguide_id", how="left")
    for c in ("n_annees", "premiere_annee", "derniere_annee"):
        out[c] = out[c].astype("Int64")
    return out.sort_values("our_total", ascending=False).reset_index(drop=True)


def eligible_members(coverage: pd.DataFrame, min_trades: int = 10) -> dict:
    """Compte des membres « éligibles » au backtest (≥ min_trades) — critère Ramify K-sélection."""
    elig = coverage[coverage["our_total"] >= min_trades]
    return {"min_trades": min_trades, "n_eligibles": int(len(elig)),
            "n_total_membres": int(len(coverage)),
            "n_eligibles_3plus_annees": int((elig["n_annees"] >= 3).sum())}


# ───────────────────────────── (e) Achats sans sortie déclarée ─────────────────────────────
def unmatched_purchase_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Pour chaque achat (bioguide+ticker), existe-t-il une vente ultérieure (disclosure plus tard) ?
    Le taux non-apparié = positions qui seraient fermées de force à +12 mois dans la stratégie."""
    d = df[df["ticker"].notna() & (df["ticker"].astype(str).str.strip() != "")].copy()
    d = d.dropna(subset=["_dd"])
    sells = d[d["op"] == "sell"].groupby(["bioguide_id", "ticker"])["_dd"].max()
    rows = []
    for chamber, g in d.groupby("chamber"):
        buys = g[g["op"] == "buy"]
        if not len(buys):
            continue
        last_sell = buys.set_index(["bioguide_id", "ticker"]).index.map(sells.get)
        matched = pd.Series(last_sell, index=buys.index) > buys["_dd"].values
        n = len(buys)
        n_match = int(pd.Series(matched).fillna(False).sum())
        rows.append({"chamber": chamber, "n_achats_avec_ticker": n,
                     "avec_sortie_declaree": n_match,
                     "sans_sortie_pct": round(100 * (n - n_match) / n, 1)})
    return pd.DataFrame(rows)


# ───────────────────────────── Figures ─────────────────────────────
def _figures(df, coverage, outdir: Path) -> list:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    outdir.mkdir(parents=True, exist_ok=True)
    figs = []

    # 1. Délai de divulgation (histogramme borné) + lignes 45 j / 75 j.
    fig, ax = plt.subplots(figsize=(8, 4))
    lag = df["lag_days"].dropna()
    lag = lag[(lag >= 0) & (lag <= 200)]
    ax.hist(lag, bins=60, color="#3b6ea5")
    ax.axvline(LEGAL_DELAY_DAYS, color="#c0392b", ls="--", label="45 j (légal)")
    ax.axvline(WINDOW_DELAY_DAYS, color="#e67e22", ls="--", label="75 j (fenêtre)")
    ax.set_xlabel("Délai de divulgation (jours)"); ax.set_ylabel("Transactions")
    ax.set_title("Délai transaction → divulgation"); ax.legend()
    f1 = outdir / "delai_divulgation.png"; fig.tight_layout(); fig.savefig(f1, dpi=110); plt.close(fig)
    figs.append(f1)

    # 2. Distribution des montants (échelle log10 du midpoint).
    fig, ax = plt.subplots(figsize=(8, 4))
    amt = df["amount_midpoint"].dropna()
    amt = amt[amt > 0]
    ax.hist(np.log10(amt), bins=40, color="#2e8b57")
    ax.set_xlabel("log10(montant médian estimé, $)"); ax.set_ylabel("Transactions")
    ax.set_title("Distribution des montants déclarés (midpoint des fourchettes)")
    f2 = outdir / "distribution_montants.png"; fig.tight_layout(); fig.savefig(f2, dpi=110); plt.close(fig)
    figs.append(f2)

    # 3. Transactions par an et par chambre.
    fig, ax = plt.subplots(figsize=(8, 4))
    piv = (df.dropna(subset=["txn_year"]).assign(txn_year=df["txn_year"].astype("Int64"))
             .groupby(["txn_year", "chamber"]).size().unstack("chamber").reindex(YEARS))
    piv.plot(kind="bar", ax=ax, color={"house": "#3b6ea5", "senate": "#8e44ad"})
    ax.set_xlabel("Année de transaction"); ax.set_ylabel("Transactions")
    ax.set_title("Volume de transactions par an et par chambre")
    f3 = outdir / "transactions_par_an.png"; fig.tight_layout(); fig.savefig(f3, dpi=110); plt.close(fig)
    figs.append(f3)

    # 4. Top 12 déposants par nombre de transactions.
    fig, ax = plt.subplots(figsize=(8, 5))
    top = coverage.head(12).iloc[::-1]
    ax.barh(top["name"], top["our_total"], color="#b9770e")
    ax.set_xlabel("Transactions"); ax.set_title("Top 12 déposants (volume de transactions)")
    f4 = outdir / "top_deposants.png"; fig.tight_layout(); fig.savefig(f4, dpi=110); plt.close(fig)
    figs.append(f4)

    return figs


# ───────────────────────────── Rapport Markdown ─────────────────────────────
def _md_table(df: pd.DataFrame) -> str:
    """Formate un DataFrame en table Markdown (sans dépendance `tabulate`)."""
    cols = [str(c) for c in df.columns]
    head = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    lines = [head, sep]
    for _, row in df.iterrows():
        cells = []
        for v in row.tolist():
            if v is None or (isinstance(v, float) and pd.isna(v)) or (v is pd.NA):
                cells.append("")
            else:
                cells.append(str(v).replace("|", "\\|"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_report(repo_root: Path) -> Path:
    df = load_final(repo_root)
    coverage = coverage_per_member(df)
    docs = repo_root / "docs"
    figdir = docs / "quality"
    figs = _figures(df, coverage, figdir)

    coh = date_coherence(df)
    delays = delay_buckets(df)
    outliers = delay_outliers(df)
    amounts = amount_distribution(df)
    elig = eligible_members(coverage)
    unmatched = unmatched_purchase_rate(df)

    n_total = len(df)
    n_house = int((df["chamber"] == "house").sum())
    n_senate = int((df["chamber"] == "senate").sum())

    parts = []
    parts.append("# Rapport de qualité des données — Congress Trading\n")
    parts.append("> Livrable Ramify, Semaine 2. Généré par `python -m congress_core.quality` "
                 "(lecture seule des tables FINAL, aucun appel API).\n")
    parts.append(f"**Périmètre :** {n_total:,} transactions FINAL (House {n_house:,} + "
                 f"Sénat {n_senate:,}), années 2020–2026.\n".replace(",", " "))

    parts.append("\n## (a) Cohérence des dates (`disclosure_date ≥ transaction_date`)\n")
    parts.append(_md_table(coh))
    parts.append("\n\nLecture : `dates_parseables_pct` mesure les dates exploitables (le reste = "
                 "OCR papier illisible) ; `coherentes_pct` = part où la divulgation suit bien la "
                 "transaction. Les `incoherentes` sont surtout des divulgations amendées/antidatées "
                 "réelles ; `annee_txn_implausible` isole les rares erreurs OCR de lecture d'année "
                 "(année de transaction postérieure au dépôt ou antérieure à 2012), déjà incluses "
                 "dans les incohérentes. Des transactions 2013–2019 apparaissent légitimement "
                 "(divulgations très tardives).\n")

    parts.append("\n## (b) Délai légal de divulgation (STOCK Act ~45 j)\n")
    parts.append(_md_table(delays))
    parts.append("\n\n![Délai de divulgation](quality/delai_divulgation.png)\n")
    parts.append("\nLe pipeline tolère une fenêtre de 75 j (`date_confidence`) ; le tableau isole "
                 "la part strictement dans les **45 j légaux** vs la marge 45–75 j vs les retards >75 j.\n")
    if len(outliers):
        parts.append("\n**Divulgations les plus tardives (> 365 j, suspects) :**\n\n")
        parts.append(_md_table(outliers))
        parts.append("\n")

    parts.append("\n## (c) Distribution des montants (`amount_midpoint`)\n")
    parts.append("\nStats globales (USD, midpoint des fourchettes déclarées) :\n\n")
    parts.append("```\n" + amounts["overall"].round(0).to_string() + "\n```\n")
    parts.append("\nPar chambre :\n\n")
    parts.append("```\n" + amounts["by_chamber"].round(0).to_string() + "\n```\n")
    parts.append("\n![Distribution des montants](quality/distribution_montants.png)\n")
    parts.append("\n**Top 15 déposants par volume estimé (Σ midpoint) :**\n\n")
    parts.append(_md_table(amounts["top_volume"]))
    parts.append("\n")

    parts.append("\n## (d) Coverage par congressman\n")
    parts.append(f"\n{len(coverage)} déposants distincts. **{elig['n_eligibles']}** ont "
                 f"≥ {elig['min_trades']} transactions (éligibles au backtest), dont "
                 f"**{elig['n_eligibles_3plus_annees']}** actifs sur ≥ 3 années.\n")
    parts.append("\n![Top déposants](quality/top_deposants.png)\n")
    parts.append("\n![Transactions par an](quality/transactions_par_an.png)\n")
    parts.append("\n**Top 20 déposants (transactions, OCR%, années actives) :**\n\n")
    cov_show = coverage.head(20)[["name", "our_total", "our_ocr", "ocr_share_pct",
                                  "n_annees", "premiere_annee", "derniere_annee"]]
    parts.append(_md_table(cov_show))
    parts.append("\n")

    parts.append("\n## (e) Taux de transactions sans sortie déclarée\n")
    parts.append("\nAchats (avec ticker) sans vente ultérieure déclarée par le même membre sur le "
                 "même ticker → positions qui seraient fermées de force à +12 mois dans la stratégie.\n\n")
    parts.append(_md_table(unmatched))
    parts.append("\n")

    report = docs / "RAPPORT_QUALITE.md"
    report.write_text("".join(parts) + "\n", encoding="utf-8")
    return report


def main():
    repo_root = Path(__file__).resolve().parent.parent
    report = build_report(repo_root)
    print(f"Rapport écrit : {report}")
    print(f"Figures : {report.parent / 'quality'}")


if __name__ == "__main__":
    main()
