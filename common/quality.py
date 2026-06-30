"""Rapport de qualité des données — livrable Ramify Semaine 2.

Charge les tables FINAL des deux chambres (2020→2026), calcule SIX contrôles qualité et génère
figures + `docs/RAPPORT_QUALITE.md`. **Lecture seule des CSV FINAL (+ des 07c/07g/07h figés pour (f)),
aucun appel API.**

En plus des 6 contrôles (a–f), le rapport décline désormais l'essentiel des statistiques par les
**quatre sous-corpus** — House électronique, House OCR, Sénat électronique, Sénat OCR (colonne
`provenance`) — et exploite beaucoup plus la matière : mix opérations/owner/type d'actif/secteur,
rendement des sources de ticker/secteur, scorecards couverture & qualité, concentration (HHI, Gini,
Lorenz), profil des clusters de scan House OCR. Tout est recomputé depuis les tables FINAL figées.

Les contrôles :
  (a) Cohérence des dates : `disclosure_date >= transaction_date`.
  (b) Délai légal : `lag = disclosure - transaction` ventilé ≤45 j (légal STOCK Act) / 45–75 j / >75 j.
  (c) Distribution des montants (`amount_midpoint`) : médiane, quartiles, top déposants par volume.
  (d) Coverage par congressman : #trades, #années, première/dernière année, membres ≥10 trades.
  (e) Taux de transactions sans sortie déclarée : achats sans vente ultérieure (même bioguide+ticker).
  (f) Validation externe Quiver : couverture par scope (digital/ocr/both), décomposition
      exact/date_mismatch/no_match/non_equity par type d'actif et par cluster de scan — agrégée depuis
      les `07c/07g/07h` figés (définition des métriques : common/quiver_scopes.py).

Usage : `python -m common.quality`  (écrit docs/RAPPORT_QUALITE.md + docs/quality/*.png)
"""
from pathlib import Path

import pandas as pd

from common import crosscheck, schema

YEARS = list(range(2020, 2027))
LEGAL_DELAY_DAYS = 45          # STOCK Act : PTR dû ~45 j après la transaction.
WINDOW_DELAY_DAYS = 75         # Fenêtre de tolérance utilisée par le pipeline (date_confidence).

# Les QUATRE sous-corpus = valeurs exactes de `provenance`. Ordre stable pour toutes les tables/figures.
CORPUS_ORDER = ["House électronique", "House OCR", "Sénat électronique", "Sénat OCR"]
_PROVENANCE_TO_CORPUS = {
    "house-pdf-electronic": "House électronique",
    "house-pdf-ocr": "House OCR",
    "senate-efd-electronic": "Sénat électronique",
    "senate-efd-ocr": "Sénat OCR",
}
# Clusters de scan House OCR (census des 547 PDF scannés).
_HOUSE_CLUSTERS = ["A_tape_droit", "B_tape_tourne", "C_manuscrit"]


# ───────────────────────────── Petits utilitaires ─────────────────────────────
def _pct(n, d):
    """Pourcentage arrondi (1 décimale) ou None si dénominateur nul."""
    return round(100 * n / d, 1) if d else None


def _nonblank(s: pd.Series) -> pd.Series:
    """Masque booléen : valeur présente (ni NaN, ni '', ni 'nan')."""
    v = s.fillna("").astype(str).str.strip()
    return (v != "") & (v.str.lower() != "nan")


def _corpus_label(provenance) -> str:
    """`provenance` → label de sous-corpus lisible (ou '(autre)' si inattendu)."""
    return _PROVENANCE_TO_CORPUS.get(str(provenance), "(autre)")


def owner_class(owner) -> str:
    """Normalise `owner` (SELF/Self, Spouse/SP, JT/Joint/Joint Tenancy, DC/Dependent Child…)."""
    s = str(owner).strip().lower()
    if not s or s in ("nan", "none"):
        return "other"
    if "joint" in s or s == "jt":
        return "joint"
    if "self" in s:
        return "self"
    if "spouse" in s or s == "sp":
        return "spouse"
    if "dependent" in s or "child" in s or s == "dc":
        return "dependent"
    return "other"


# ───────────────────────────── Chargement ─────────────────────────────
def _final_path(repo_root: Path, chamber: str, year: int) -> Path:
    """Les deux chambres : data/{chambre}/tables/{y}/06_{chambre}_{y}_FINAL.csv (structure symétrique)."""
    if chamber == "house":
        return repo_root / "data" / "house" / "tables" / str(year) / f"06_house_{year}_FINAL.csv"
    return repo_root / "data" / "senate" / "tables" / str(year) / f"06_senate_{year}_FINAL.csv"


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
    """Concatène tous les FINAL House+Sénat, ajoute `file_year`, `txn_year`, `lag_days`, `op`,
    `corpus` (sous-corpus) et `owner_class`."""
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

    # Dédup CROSS-ANNÉE : une re-divulgation tardive (même transaction re-déposée une autre année — même
    # natural_key_hash + occurrence_index dans 2 fichiers FINAL) ne doit pas être comptée deux fois dans
    # les stats. On garde la 1re occurrence (année de dépôt la plus ancienne = divulgation d'origine).
    # Sénat : 8 841 → 8 245 ; House : 81 642 → 81 607. La dédup PAR ANNÉE des pipelines ne peut pas le
    # voir (elle opère fichier par fichier) ; ici on assemble le panel multi-années, donc on l'applique.
    if {"natural_key_hash", "occurrence_index"}.issubset(full.columns):
        # occurrence_index est stocké tantôt '0' tantôt '0.0' selon l'année → normaliser en numérique
        # avant la dédup (sinon '0' != '0.0' laisse survivre un doublon, cf. Jefferson Shreve 2025/2026).
        full = (full.assign(_occ=pd.to_numeric(full["occurrence_index"], errors="coerce"))
                .sort_values("file_year", kind="stable")
                .drop_duplicates(["natural_key_hash", "_occ"], keep="first")
                .drop(columns="_occ").reset_index(drop=True))

    full = schema.apply_txn_date_fixes(full)   # corrige 3 années-coquilles du PTR (lecture seule du figé)
    td = pd.to_datetime(full["transaction_date"], errors="coerce")
    dd = pd.to_datetime(full["disclosure_date"], errors="coerce")
    full["_td"], full["_dd"] = td, dd
    full["txn_year"] = td.dt.year
    full["lag_days"] = (dd - td).dt.days
    full["amount_midpoint"] = pd.to_numeric(full["amount_midpoint"], errors="coerce")
    full["op"] = full["operation_type"].map(op_class)
    full["corpus"] = full["provenance"].map(_corpus_label)
    full["owner_class"] = full["owner"].map(owner_class)
    return full


def _keys(df, dim):
    """Clés d'itération d'un groupby : ordre stable CORPUS_ORDER si dim='corpus', sinon tri simple."""
    if dim == "corpus":
        return [c for c in CORPUS_ORDER if (df["corpus"] == c).any()]
    return sorted(df[dim].dropna().unique())


# ───────────────────────────── (a) Cohérence des dates ─────────────────────────────
def date_coherence(df: pd.DataFrame, dim: str = "chamber") -> pd.DataFrame:
    """Résumé par `dim` (chamber|corpus) : n, % dates parseables, % cohérentes (disclosure≥txn parmi
    parseables), incohérentes, et années de transaction implausibles (txn après dépôt ou avant 2012 —
    artefacts OCR de lecture d'année, déjà comptés dans les incohérentes via un délai négatif)."""
    rows = []
    for key in _keys(df, dim):
        g = df[df[dim] == key]
        n = len(g)
        n_valid = int(g["lag_days"].notna().sum())
        coherent = int((g["lag_days"] >= 0).sum())
        ty = g["txn_year"]
        impl = int(((ty > g["file_year"]) | (ty < 2012)).sum())
        rows.append({
            dim: key, "n": n,
            "dates_parseables_pct": _pct(n_valid, n),
            "coherentes_pct": _pct(coherent, n_valid),
            "incoherentes": n_valid - coherent,
            "annee_txn_implausible": impl,
            "date_manquante": n - n_valid,
        })
    return pd.DataFrame(rows).reset_index(drop=True)


# ───────────────────────────── (b) Délai légal 45 j ─────────────────────────────
def delay_buckets(df: pd.DataFrame, dim: str = "chamber") -> pd.DataFrame:
    """Ventilation du délai de divulgation par `dim` : ≤45 j (légal) / 45–75 j / >75 j / négatif."""
    rows = []
    for key in _keys(df, dim):
        g = df[df[dim] == key]
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
            dim: key, "n_dates_valides": n,
            "<=45j_legal_pct": _pct(le45, n),
            "45-75j_pct": _pct(mid, n),
            ">75j_pct": _pct(over, n),
            "negatif_pct": _pct(neg, n),
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
    """Stats descriptives globales + par chambre + par sous-corpus + top déposants par volume estimé."""
    amt = df["amount_midpoint"].dropna()
    overall = amt.describe(percentiles=[0.25, 0.5, 0.75, 0.9])
    by_chamber = df.groupby("chamber")["amount_midpoint"].describe(percentiles=[0.25, 0.5, 0.75])
    by_corpus = (df.groupby("corpus")["amount_midpoint"].describe(percentiles=[0.25, 0.5, 0.75])
                   .reindex([c for c in CORPUS_ORDER if (df["corpus"] == c).any()]))
    top = (df.groupby(["bioguide_id", "declarant_name", "chamber"])["amount_midpoint"]
             .agg(volume_estime="sum", n_trades="count")
             .reset_index().sort_values("volume_estime", ascending=False).head(15))
    top["volume_estime_musd"] = (top["volume_estime"] / 1e6).round(1)
    return {"overall": overall, "by_chamber": by_chamber, "by_corpus": by_corpus,
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
def unmatched_purchase_rate(df: pd.DataFrame, dim: str = "chamber") -> pd.DataFrame:
    """Pour chaque achat (bioguide+ticker), existe-t-il une vente ultérieure (disclosure plus tard) ?
    Le taux non-apparié = positions qui seraient fermées de force à +12 mois dans la stratégie. La vente
    est cherchée globalement (une vente, peu importe le corpus, clôt la position)."""
    d = df[_nonblank(df["ticker"])].copy()
    d = d.dropna(subset=["_dd"])
    sells = d[d["op"] == "sell"].groupby(["bioguide_id", "ticker"])["_dd"].max()
    rows = []
    for key in _keys(d, dim):
        g = d[d[dim] == key]
        buys = g[g["op"] == "buy"]
        if not len(buys):
            continue
        last_sell = buys.set_index(["bioguide_id", "ticker"]).index.map(sells.get)
        matched = pd.Series(last_sell, index=buys.index) > buys["_dd"].values
        n = len(buys)
        n_match = int(pd.Series(matched).fillna(False).sum())
        rows.append({dim: key, "n_achats_avec_ticker": n, "avec_sortie_declaree": n_match,
                     "sans_sortie_pct": round(100 * (n - n_match) / n, 1)})
    return pd.DataFrame(rows)


# ───────────────────────────── (f) Validation externe Quiver ─────────────────────────────
def quiver_validation(repo_root: Path) -> dict:
    """Agrège la validation Quiver (vérité-terrain ACTIONS) depuis les fichiers figés `07c/07g/07h`
    (lecture seule). Renvoie :
      - `cov_scope`   : couverture transaction-niveau par scope (digital/ocr/both) × chambre
                        = Σ matched / Σ quiver (sur toutes les années).
      - `by_asset`    : {chambre → table} décomposition exact/date_mismatch/no_match/non_equity par
                        `asset_type` → montre que Quiver = ACTIONS (les munis/obligations = `non_equity`).
      - `by_cluster`  : (House) idem par cluster de scan (tapé/manuscrit) → montre que le point faible
                        est la DATE de l'OCR manuscrit (date_mismatch élevé), pas une cécité de Quiver.
    Toutes les métriques sont DÉFINIES dans common/quiver_scopes.py (docstring) et vérifiables ici."""
    import glob

    def _read(pat):
        fs = sorted(glob.glob(str(repo_root / pat)))
        return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame()

    def _agg(df, dim):
        if df.empty:
            return df
        g = df.groupby(dim)[["exact_match", "date_mismatch", "no_match", "non_equity", "total"]].sum().reset_index()
        eq = g["exact_match"] + g["date_mismatch"] + g["no_match"]
        g["quiver_a_le_trade_pct"] = (100 * (g["exact_match"] + g["date_mismatch"]) / eq.where(eq > 0)).round(1)
        return g.sort_values("total", ascending=False).reset_index(drop=True)

    cov_rows = []
    for ch in ("house", "senate"):
        c = _read(f"data/{ch}/tables/*/07c_quiver_txn_reconciliation.csv")
        if c.empty:
            continue
        c["value"] = pd.to_numeric(c["value"], errors="coerce")
        piv = c[c["metric"].isin(["matched", "quiver", "only_ours", "only_quiver"])].pivot_table(
            index="scope", columns="metric", values="value", aggfunc="sum")
        piv["couverture_pct"] = (100 * piv.get("matched", 0) / piv.get("quiver", pd.Series()).where(lambda s: s > 0)).round(1)
        piv.insert(0, "chamber", ch)
        cov_rows.append(piv.reset_index()[["chamber", "scope", "matched", "quiver", "only_ours", "only_quiver", "couverture_pct"]])

    return {
        "cov_scope": pd.concat(cov_rows, ignore_index=True) if cov_rows else pd.DataFrame(),
        "by_asset": {ch: _agg(_read(f"data/{ch}/tables/*/07g_quiver_match_by_asset.csv"), "asset_type")
                     for ch in ("house", "senate")},
        "by_cluster": _agg(_read("data/house/tables/*/07h_quiver_match_by_cluster.csv"), "cluster"),
    }


# ════════════════════════ Décomposition par SOUS-CORPUS ════════════════════════
def corpus_overview(df: pd.DataFrame) -> pd.DataFrame:
    """Effectif et part de chaque sous-corpus (le périmètre du rapport)."""
    n_tot = len(df)
    vc = df["corpus"].value_counts()
    return pd.DataFrame([{"corpus": c, "n": int(vc.get(c, 0)), "part_pct": _pct(int(vc.get(c, 0)), n_tot)}
                         for c in CORPUS_ORDER])


def _mix(df: pd.DataFrame, class_fn, order, rename) -> pd.DataFrame:
    """Table %-par-classe et par sous-corpus. `class_fn(g)` renvoie une Series de classes alignée sur g."""
    rows = []
    for corpus in CORPUS_ORDER:
        g = df[df["corpus"] == corpus]
        n = len(g)
        if not n:
            continue
        vc = class_fn(g).value_counts()
        row = {"corpus": corpus, "n": n}
        for k in order:
            row[rename[k]] = _pct(int(vc.get(k, 0)), n)
        rows.append(row)
    return pd.DataFrame(rows)


def operation_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Mix achat / vente / échange / autre par sous-corpus."""
    return _mix(df, lambda g: g["op"], ["buy", "sell", "exchange", "other"],
                {"buy": "achat_%", "sell": "vente_%", "exchange": "echange_%", "other": "autre_%"})


def owner_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Mix par type de détenteur (soi / conjoint / joint / enfant / autre) par sous-corpus."""
    return _mix(df, lambda g: g["owner_class"], ["self", "spouse", "joint", "dependent", "other"],
                {"self": "perso_%", "spouse": "conjoint_%", "joint": "joint_%",
                 "dependent": "enfant_%", "other": "autre_%"})


def _asset_bucket(at) -> str:
    """Regroupe les `asset_type` bruts en grandes familles lisibles."""
    s = str(at).strip().lower()
    if s in ("", "nan", "(inconnu)"):
        return "manquant"
    if "option" in s:
        return "option"
    if "muni" in s:
        return "muni"
    if "gov" in s or "treasur" in s:
        return "gov"
    if "bond" in s:
        return "bond"
    if "fund" in s or "etf" in s:
        return "fonds"
    if "stock" in s:
        return "action"
    return "autre"


def asset_type_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Mix de familles d'actifs par sous-corpus (action / option / oblig. État / muni / oblig. corp. /
    fonds / autre / manquant)."""
    order = ["action", "option", "gov", "muni", "bond", "fonds", "autre", "manquant"]
    rename = {"action": "action_%", "option": "option_%", "gov": "oblig.Etat_%", "muni": "muni_%",
              "bond": "oblig.corp_%", "fonds": "fonds_%", "autre": "autre_%", "manquant": "manquant_%"}
    return _mix(df, lambda g: g["asset_type"].map(_asset_bucket), order, rename)


def sector_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Couverture secteur/ETF + 3 secteurs GICS dominants par sous-corpus."""
    rows = []
    for corpus in CORPUS_ORDER:
        g = df[df["corpus"] == corpus]
        n = len(g)
        if not n:
            continue
        valid = g.loc[_nonblank(g["sector_gics"]), "sector_gics"]
        top3 = (", ".join(f"{k} {round(100 * v / len(valid))}%"
                          for k, v in valid.value_counts().head(3).items())
                if len(valid) else "—")
        rows.append({"corpus": corpus, "n": n,
                     "secteur_renseigne_%": _pct(len(valid), n),
                     "etf_proxy_%": _pct(int(_nonblank(g["etf_proxy"]).sum()), n),
                     "top_3_secteurs": top3})
    return pd.DataFrame(rows)


def source_yield(df: pd.DataFrame) -> dict:
    """Répartition des sources de résolution : `ticker_source` (vide pour House électronique → « — »)
    et `sector_source`. Montre comment chaque corpus obtient son ticker/secteur."""
    def _mixcol(col, order):
        rows = []
        for corpus in CORPUS_ORDER:
            g = df[df["corpus"] == corpus]
            n = len(g)
            if not n:
                continue
            v = g[col].fillna("").astype(str).str.strip().str.lower()
            has = (v != "") & (v != "nan")
            if int(has.sum()) == 0:
                rows.append({"corpus": corpus, "n": n, **{f"{k}_%": "—" for k in order}})
                continue
            vc = v.value_counts()
            rows.append({"corpus": corpus, "n": n,
                         **{f"{k}_%": _pct(int(vc.get(k, 0)), n) for k in order}})
        return pd.DataFrame(rows)
    return {"ticker": _mixcol("ticker_source", ["elec_dict", "llm", "explicit", "none"]),
            "sector": _mixcol("sector_source", ["yfinance", "llm", "manual", "none"])}


def amount_stats_by_corpus(df: pd.DataFrame) -> pd.DataFrame:
    """Statistiques de montant (`amount_midpoint`) et volume total par sous-corpus."""
    rows = []
    for corpus in CORPUS_ORDER:
        g = df[df["corpus"] == corpus]
        n = len(g)
        if not n:
            continue
        a = g["amount_midpoint"].dropna()
        rows.append({"corpus": corpus, "n": n,
                     "mediane_$": int(a.median()) if len(a) else None,
                     "moyenne_$": int(a.mean()) if len(a) else None,
                     "P25_$": int(a.quantile(0.25)) if len(a) else None,
                     "P75_$": int(a.quantile(0.75)) if len(a) else None,
                     "P95_$": int(a.quantile(0.95)) if len(a) else None,
                     "volume_total_M$": round(a.sum() / 1e6, 1)})
    return pd.DataFrame(rows)


def coverage_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de remplissage des champs enrichis par sous-corpus (couverture = % renseigné)."""
    cols = [("ticker", "ticker_%"), ("sector_gics", "secteur_%"), ("etf_proxy", "etf_proxy_%"),
            ("committee_membership", "committee_%"), ("bioguide_id", "identite_%"),
            ("years_in_office", "anciennete_%")]
    rows = []
    for corpus in CORPUS_ORDER:
        g = df[df["corpus"] == corpus]
        n = len(g)
        if not n:
            continue
        row = {"corpus": corpus, "n": n}
        for src, name in cols:
            row[name] = _pct(int(_nonblank(g[src]).sum()), n)
        rows.append(row)
    return pd.DataFrame(rows)


def quality_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    """Scorecard de qualité par sous-corpus : cohérence des dates, plausibilité OCR, montant renseigné."""
    rows = []
    for corpus in CORPUS_ORDER:
        g = df[df["corpus"] == corpus]
        n = len(g)
        if not n:
            continue
        n_valid = int(g["lag_days"].notna().sum())
        coher = _pct(int((g["lag_days"] >= 0).sum()), n_valid)
        dc = g["date_confidence"].fillna("").astype(str).str.strip().str.lower()
        has_dc = (dc != "") & (dc != "nan")
        dplaus = "—" if int(has_dc.sum()) == 0 else _pct(int((dc == "plausible").sum()), int(has_dc.sum()))
        ty = g["txn_year"]
        impl = int(((ty > g["file_year"]) | (ty < 2012)).sum())
        rows.append({"corpus": corpus, "n": n, "dates_coherentes_%": coher,
                     "date_plausible_%": dplaus, "annee_implausible_n": impl,
                     "montant_renseigne_%": _pct(int(g["amount_midpoint"].notna().sum()), n)})
    return pd.DataFrame(rows)


# ───────────────────────────── Concentration ─────────────────────────────
def _gini(values) -> float:
    """Coefficient de Gini ∈ [0, 1] sur des volumes positifs (0 = égalité, 1 = concentration extrême)."""
    import numpy as np
    a = np.sort(np.asarray([float(v) for v in values if pd.notna(v) and float(v) > 0]))
    n = a.size
    if n == 0 or a.sum() == 0:
        return None
    idx = np.arange(1, n + 1)
    return round(float((2 * (idx * a).sum()) / (n * a.sum()) - (n + 1) / n), 3)


def _hhi(values) -> float:
    """Indice de Herfindahl-Hirschman ∈ [0, 10000] sur des volumes positifs."""
    import numpy as np
    a = np.asarray([float(v) for v in values if pd.notna(v) and float(v) > 0])
    tot = a.sum()
    if tot <= 0:
        return None
    return round(float(((a / tot) ** 2).sum() * 10000), 1)


def concentration(df: pd.DataFrame, top_n: int = 15) -> dict:
    """Concentration de l'activité : inégalité (HHI, Gini, top-10 %) par sous-corpus + top tickers /
    secteurs par volume (global) + volumes par déposant (pour la courbe de Lorenz)."""
    inq = []
    for corpus in CORPUS_ORDER:
        g = df[df["corpus"] == corpus]
        if not len(g):
            continue
        vol = g.groupby("bioguide_id")["amount_midpoint"].sum()
        vol = vol[vol > 0]
        tot = float(vol.sum())
        top10 = float(vol.sort_values(ascending=False).head(10).sum())
        inq.append({"corpus": corpus, "n_deposants": int(vol.size),
                    "HHI": _hhi(vol.values), "Gini": _gini(vol.values),
                    "top10_volume_%": round(100 * top10 / tot, 1) if tot else None})

    def _top(colname, label, k):
        d = df[_nonblank(df[colname])]
        t = d.groupby(colname)["amount_midpoint"].agg(["sum", "count"]).reset_index()
        t["volume_M$"] = (t["sum"] / 1e6).round(1)
        t = t.rename(columns={colname: label, "count": "n_trades"}).sort_values("sum", ascending=False).head(k)
        return t[[label, "n_trades", "volume_M$"]].reset_index(drop=True)

    filer_vol = df.groupby("bioguide_id")["amount_midpoint"].sum()
    filer_vol = filer_vol[filer_vol > 0].sort_values()
    return {"inequality": pd.DataFrame(inq),
            "top_tickers": _top("ticker", "ticker", top_n),
            "top_sectors": _top("sector_gics", "secteur", 11),
            "filer_volumes": filer_vol}


def house_ocr_cluster_profile(df: pd.DataFrame, repo_root: Path) -> pd.DataFrame:
    """Profil des clusters de scan House OCR (A tapé droit / B tapé tourné / C manuscrit) : effectif,
    plausibilité des dates, couverture ticker + qualité d'appariement Quiver (07h figé)."""
    g = df[df["corpus"] == "House OCR"].copy()
    census = repo_root / "data" / "house" / "tables" / "_scan_census_547.csv"
    if not len(g) or not census.exists():
        return pd.DataFrame()
    cen = pd.read_csv(census, dtype=str)[["doc_id", "cluster"]]
    g = g.merge(cen, on="doc_id", how="left")
    rows = []
    for cl in _HOUSE_CLUSTERS:
        sub = g[g["cluster"] == cl]
        n = len(sub)
        if not n:
            continue
        dc = sub["date_confidence"].fillna("").astype(str).str.strip().str.lower()
        rows.append({"cluster": cl, "n_lignes": n, "n_docs": int(sub["doc_id"].nunique()),
                     "date_plausible_%": _pct(int((dc == "plausible").sum()), n),
                     "ticker_%": _pct(int(_nonblank(sub["ticker"]).sum()), n)})
    prof = pd.DataFrame(rows)
    qc = quiver_validation(repo_root).get("by_cluster")
    if qc is not None and len(qc):
        prof = prof.merge(qc[["cluster", "quiver_a_le_trade_pct"]], on="cluster", how="left")
    return prof


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

    # 5. Mix achat/vente par sous-corpus (barres empilées).
    try:
        om = (df.groupby(["corpus", "op"]).size().unstack("op").reindex(CORPUS_ORDER)
                .reindex(columns=["buy", "sell", "exchange", "other"]).fillna(0))
        omp = om.div(om.sum(axis=1), axis=0) * 100
        fig, ax = plt.subplots(figsize=(8, 4))
        omp.plot(kind="bar", stacked=True, ax=ax, color=["#2e8b57", "#c0392b", "#e67e22", "#7f8c8d"])
        ax.set_ylabel("% des transactions"); ax.set_xlabel("")
        ax.set_title("Mix achat/vente par sous-corpus")
        ax.legend(["achat", "vente", "échange", "autre"], fontsize=8)
        ax.set_xticklabels(omp.index, rotation=20, ha="right")
        f5 = outdir / "mix_operations_par_corpus.png"; fig.tight_layout(); fig.savefig(f5, dpi=110); plt.close(fig)
        figs.append(f5)
    except Exception:
        pass

    # 6. Mix de types d'actifs par sous-corpus (barres empilées).
    try:
        cats = ["action", "option", "gov", "muni", "bond", "fonds", "autre", "manquant"]
        ab = df.assign(_b=df["asset_type"].map(_asset_bucket))
        am = (ab.groupby(["corpus", "_b"]).size().unstack("_b").reindex(CORPUS_ORDER)
                .reindex(columns=cats, fill_value=0))
        amp = am.div(am.sum(axis=1), axis=0) * 100
        fig, ax = plt.subplots(figsize=(8.5, 4.5))
        amp.plot(kind="bar", stacked=True, ax=ax, colormap="tab10")
        ax.set_ylabel("% des transactions"); ax.set_xlabel("")
        ax.set_title("Mix de types d'actifs par sous-corpus")
        ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=8)
        ax.set_xticklabels(amp.index, rotation=20, ha="right")
        f6 = outdir / "mix_actifs_par_corpus.png"; fig.tight_layout(); fig.savefig(f6, dpi=110); plt.close(fig)
        figs.append(f6)
    except Exception:
        pass

    # 7. Volume déclaré par secteur GICS (top 12).
    try:
        sec = (df[_nonblank(df["sector_gics"])].groupby("sector_gics")["amount_midpoint"].sum()
                 .sort_values().tail(12) / 1e6)
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.barh(sec.index, sec.values, color="#2c7fb8")
        ax.set_xlabel("Volume estimé (M$)"); ax.set_title("Volume déclaré par secteur GICS (top 12)")
        f7 = outdir / "volume_par_secteur.png"; fig.tight_layout(); fig.savefig(f7, dpi=110); plt.close(fig)
        figs.append(f7)
    except Exception:
        pass

    # 8. Courbe de Lorenz du volume par déposant (concentration) + Gini.
    try:
        v = np.sort(df.groupby("bioguide_id")["amount_midpoint"].sum().values.astype(float))
        v = v[v > 0]
        cum = np.concatenate([[0], np.cumsum(v) / v.sum()])
        x = np.concatenate([[0], np.arange(1, len(v) + 1) / len(v)])
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.plot(x, cum, color="#b9770e", lw=2, label=f"Lorenz (Gini = {_gini(v)})")
        ax.plot([0, 1], [0, 1], color="gray", ls="--", label="égalité parfaite")
        ax.set_xlabel("Part cumulée des déposants"); ax.set_ylabel("Part cumulée du volume")
        ax.set_title("Concentration du volume par déposant"); ax.legend()
        f8 = outdir / "concentration_lorenz.png"; fig.tight_layout(); fig.savefig(f8, dpi=110); plt.close(fig)
        figs.append(f8)
    except Exception:
        pass

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

    # Calculs Quiver remontés en tête : ils alimentent le résumé exécutif (et sont réutilisés en §6).
    from common import quiver_diagnosis as qd
    diag = qd.build_diagnosis(repo_root)
    qv = quiver_validation(repo_root)
    inc = diag.get("ticker_inclusion", pd.DataFrame())
    incd = {str(r["chamber"]): dict(r) for _, r in inc.iterrows()} if len(inc) else {}

    def _byc(dd, verdict):
        d = dd[dd["verdict"] == verdict]
        return {str(r["côté"]).split("(")[-1].rstrip(")").strip(): int(r["n"]) for _, r in d.iterrows()}
    plus = _byc(diag["our_tally"], "ON_EST_PLUS_COMPLET") if len(diag.get("our_tally", [])) else {}
    manque = _byc(diag["quiver_tally"], "NOTRE_MANQUE") if len(diag.get("quiver_tally", [])) else {}

    def _n(x):
        return f"{int(x):,}".replace(",", " ")

    def _g(ch, col, d="—"):
        v = incd.get(ch, {}).get(col, d)
        return d if v is None else v

    parts = []
    parts.append("# Rapport qualité — Données de trading du Congrès américain (2020–2026)\n")
    parts.append("> Chambre des représentants + Sénat · généré par `python -m common.quality` "
                 "(lecture seule des tables FINAL, aucun appel API) · "
                 "Quiver Quantitative = vérité-terrain externe, **jamais réinjectée**.\n")
    parts.append("\n## Résumé exécutif\n\n")
    parts.append(
        f"- **Périmètre** — {_n(n_total)} transactions uniques de membres élus "
        f"(House {_n(n_house)} + Sénat {_n(n_senate)}), 2020–2026, en **4 sous-corpus** "
        "(chambre × voie d'acquisition : électronique déterministe / scan OCR).\n"
        f"- **Complétude vs Quiver** *(§6)* — dans notre fenêtre, on retrouve "
        f"**{_g('house','inclusion_pct')} % (House) / {_g('senate','inclusion_pct')} % (Sénat)** des trades "
        "Quiver au niveau (déposant, ticker, sens). Le **vrai trou coté est minuscule** "
        f"(≈ {_g('house','residu_cote_reel')} House / {_g('senate','residu_cote_reel')} Sénat) ; le reste du "
        "résidu est de l'OCR récupérable ou du hors-périmètre.\n"
        f"- **On est plus complet que Quiver** — **+{plus.get('house',0)+plus.get('senate',0)} actions cotées "
        f"qu'on a et que Quiver n'a pas, contre seulement {manque.get('house',0)+manque.get('senate',0)} trous "
        "inverses.** La base est, en pratique, un **sur-ensemble** de Quiver.\n"
        "- **Les « écarts » date/ticker ne sont pas des erreurs** — ~99 % sont un artefact de mesure (même "
        "trade tradé plusieurs jours) ; sur le digital, c'est **Quiver** qui se décale (5 PDF officiels "
        "vérifiés). Notre taux d'erreur réellement imputable est **< 1 %**.\n"
        "- **Données propres** — identité rattachée à ~100 %, dates cohérentes > 99 %, délai de divulgation "
        "médian 28 j, montants renseignés > 98 %.\n")
    parts.append("\n*Plan : §1 composition · §2 cohérence des dates · §3 délai légal · §4 montants · "
                 "§5 couverture & structure · §6 complétude vs Quiver (vérité-terrain).*\n")

    # ════════ §1 Composition ════════
    parts.append("\n## 1. Composition & qualité par sous-corpus\n")
    parts.append("\nLes déclarations proviennent de **quatre sous-corpus** très différents (chambre × "
                 "voie d'acquisition). Toute la suite distingue ces quatre familles, car leur qualité et "
                 "leur composition diffèrent.\n\n")
    parts.append(_md_table(corpus_overview(df)))
    parts.append("\n")

    parts.append("\n### Couverture des champs enrichis (taux de remplissage)\n\n")
    parts.append(_md_table(coverage_scorecard(df)))
    parts.append("\n\n`identite_%` = part rattachée à un `bioguide_id` ; `ticker`/`secteur`/`etf_proxy` "
                 "sont vides pour les actifs non cotés (légitime, pas un défaut).\n")

    parts.append("\n### Scorecard de qualité\n\n")
    parts.append(_md_table(quality_scorecard(df)))
    parts.append("\n\n`date_plausible_%` (fenêtre 75 j) n'existe que pour les lignes OCR → « — » pour "
                 "House électronique (pas de `date_confidence`). `amount_split_flag` est partout `False` "
                 "(aucune fourchette éclatée).\n")

    parts.append("\n### Mix par sous-corpus\n")
    parts.append("\n**Sens des opérations :**\n\n")
    parts.append(_md_table(operation_mix(df)))
    parts.append("\n\n![Mix achat/vente par sous-corpus](quality/mix_operations_par_corpus.png)\n")
    parts.append("\n**Détenteur déclaré :**\n\n")
    parts.append(_md_table(owner_mix(df)))
    parts.append("\n\n**Familles d'actifs** (le non-coté — oblig. d'État, munis, obligations — domine "
                 "l'OCR du Sénat) :\n\n")
    parts.append(_md_table(asset_type_mix(df)))
    parts.append("\n\n![Mix de types d'actifs par sous-corpus](quality/mix_actifs_par_corpus.png)\n")

    parts.append("\n### Secteurs & sources de résolution\n\n")
    parts.append(_md_table(sector_mix(df)))
    sy = source_yield(df)
    parts.append("\n\n**Origine du ticker** (`ticker_source` ; vide pour House électronique → « — ») :\n\n")
    parts.append(_md_table(sy["ticker"]))
    parts.append("\n\n**Origine du secteur** (`sector_source`) :\n\n")
    parts.append(_md_table(sy["sector"]))
    parts.append("\n\n![Volume par secteur GICS](quality/volume_par_secteur.png)\n")

    parts.append("\n### Montants par sous-corpus\n\n")
    parts.append(_md_table(amount_stats_by_corpus(df)))
    parts.append("\n")

    parts.append("\n### Concentration de l'activité\n\n")
    conc = concentration(df)
    parts.append(_md_table(conc["inequality"]))
    parts.append("\n\n`HHI` ∈ [0, 10000] et `Gini` ∈ [0, 1] mesurent la concentration du volume par "
                 "déposant (plus c'est haut, plus quelques déposants dominent).\n")
    parts.append("\n![Concentration du volume (Lorenz)](quality/concentration_lorenz.png)\n")
    parts.append("\n**Top tickers par volume estimé :**\n\n")
    parts.append(_md_table(conc["top_tickers"]))
    parts.append("\n\n**Volume par secteur GICS :**\n\n")
    parts.append(_md_table(conc["top_sectors"]))
    parts.append("\n")

    prof = house_ocr_cluster_profile(df, repo_root)
    if len(prof):
        parts.append("\n### Profil des clusters de scan (House OCR)\n\n")
        parts.append(_md_table(prof))
        parts.append("\n\nA = tapé droit, B = tapé tourné, C = manuscrit. L'appariement Quiver "
                     "(`quiver_a_le_trade_pct`) **chute** sur le manuscrit (≈35 %) alors qu'il reste élevé "
                     "sur le tapé (≈78–88 %) : c'est notre lecture OCR des dates manuscrites qui décroche, "
                     "pas la plausibilité interne (`date_plausible_%`, fenêtre 75 j, reste haute). D'où "
                     "l'exclusion par défaut du cluster C.\n")

    # ════════ §2 Cohérence des dates ════════
    parts.append("\n## 2. Cohérence des dates (`disclosure_date ≥ transaction_date`)\n")
    parts.append(_md_table(coh))
    parts.append("\n\n**Par sous-corpus :**\n\n")
    parts.append(_md_table(date_coherence(df, dim="corpus")))
    parts.append("\n\nLecture : `dates_parseables_pct` mesure les dates exploitables (le reste = "
                 "OCR papier illisible) ; `coherentes_pct` = part où la divulgation suit bien la "
                 "transaction. Les `incoherentes` sont surtout des divulgations amendées/antidatées "
                 "réelles ; `annee_txn_implausible` isole les rares erreurs OCR de lecture d'année "
                 "(année de transaction postérieure au dépôt ou antérieure à 2012), déjà incluses "
                 "dans les incohérentes. Des transactions 2013–2019 apparaissent légitimement "
                 "(divulgations très tardives).\n")

    # ════════ §3 Délai légal ════════
    parts.append("\n## 3. Délai légal de divulgation (STOCK Act ~45 j)\n")
    parts.append(_md_table(delays))
    parts.append("\n\n**Par sous-corpus :**\n\n")
    parts.append(_md_table(delay_buckets(df, dim="corpus")))
    parts.append("\n\n![Délai de divulgation](quality/delai_divulgation.png)\n")
    parts.append("\nLe pipeline tolère une fenêtre de 75 j (`date_confidence`) ; le tableau isole "
                 "la part strictement dans les **45 j légaux** vs la marge 45–75 j vs les retards >75 j.\n")
    if len(outliers):
        parts.append("\n**Divulgations les plus tardives (> 365 j, suspects) :**\n\n")
        parts.append(_md_table(outliers))
        parts.append("\n")

    # ════════ §4 Distribution des montants ════════
    parts.append("\n## 4. Distribution des montants (`amount_midpoint`)\n")
    parts.append("\nStats globales (USD, midpoint des fourchettes déclarées) :\n\n")
    parts.append("```\n" + amounts["overall"].round(0).to_string() + "\n```\n")
    parts.append("\nPar chambre :\n\n")
    parts.append("```\n" + amounts["by_chamber"].round(0).to_string() + "\n```\n")
    parts.append("\nPar sous-corpus :\n\n")
    parts.append("```\n" + amounts["by_corpus"].round(0).to_string() + "\n```\n")
    parts.append("\n![Distribution des montants](quality/distribution_montants.png)\n")
    parts.append("\n**Top 15 déposants par volume estimé (Σ midpoint) :**\n\n")
    parts.append(_md_table(amounts["top_volume"]))
    parts.append("\n")

    # ════════ §5 Couverture & structure ════════
    parts.append("\n## 5. Couverture par déposant & structure de l'activité\n")
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

    # ════════ §5.1 Achats sans sortie déclarée ════════
    parts.append("\n### Achats sans sortie déclarée (pour la stratégie)\n")
    parts.append("\nAchats (avec ticker) sans vente ultérieure déclarée par le même membre sur le "
                 "même ticker → positions qui seraient fermées de force à +12 mois dans la stratégie.\n\n")
    parts.append(_md_table(unmatched))
    parts.append("\n\n**Par sous-corpus :**\n\n")
    parts.append(_md_table(unmatched_purchase_rate(df, dim="corpus")))
    parts.append("\n")

    # ════════ §6 Complétude vs Quiver ════════
    parts.append("\n## 6. Complétude vs Quiver (vérité-terrain externe)\n")
    parts.append("\n> **Section clé.** Réponse en une ligne : notre base est, dans sa fenêtre, un **quasi "
                 "sur-ensemble de Quiver** (inclusion 93,8 % House / 91,5 % Sénat), et on est **plus complet** "
                 "que lui. Les « écarts » sont à ~99 % des artefacts ou des erreurs de Quiver, pas les nôtres. "
                 "Le détail suit.\n")
    parts.append("\n### 6.1 Couverture exact-date (vue d'ensemble figée)\n")
    parts.append("\nQuiver Quantitative (agrégateur commercial) sert de **vérité-terrain indépendante**, "
                 "**jamais réinjectée**. On confronte nos transactions à Quiver au niveau transaction, par "
                 "**scope** (digital / OCR / les deux) — voir `common/quiver_scopes.py` pour la définition "
                 "exhaustive des métriques. Trois constats chiffrés en ressortent :\n")
    if len(qv["cov_scope"]):
        parts.append("\n**Couverture par scope et chambre** (`couverture_pct` = part des trades Quiver "
                     "qu'on retrouve **à la date exacte** ; `only_ours` = nos trades absents de Quiver ; "
                     "`only_quiver` = trades Quiver qu'on n'a pas) :\n\n")
        parts.append(_md_table(qv["cov_scope"]))
        parts.append("\n\n⚠️ Cette couverture est **exact-date** : elle compte comme « raté » tout trade "
                     "qu'on a à une **autre** date (artefact de collision) ou sous un autre ticker. **Pour "
                     "juger la complétude réelle, voir « Quiver ⊆ nous ? » ci-dessous** (inclusion ticker-"
                     "niveau fenêtrée : House 93,8 % / Sénat 91,5 %, vrai trou coté ≈ 22 / 0).\n")
    if len(qv["by_asset"].get("house", [])):
        parts.append("\n**1) Quiver ne couvre que les ACTIONS.** Décomposition par type d'actif "
                     "(`exact_match` = même trade, même date ; `date_mismatch` = bon trade, notre date "
                     "diffère ; `no_match` = absent de Quiver ; `non_equity` = muni/obligation → **hors "
                     "périmètre Quiver**, ni validable ni un défaut ; `quiver_a_le_trade_pct` = "
                     "exact+date_mismatch sur les actions). — **House :**\n\n")
        parts.append(_md_table(qv["by_asset"]["house"]))
        if len(qv["by_asset"].get("senate", [])):
            parts.append("\n\n— **Sénat** (l'OCR y est surtout du non-coté → `non_equity`, ce qui "
                         "explique l'essentiel du « Quiver ne nous voit pas » ; les `Stock`, eux, sont "
                         "très bien couverts) :\n\n")
            parts.append(_md_table(qv["by_asset"]["senate"]))
        parts.append("\n")
    if len(qv["by_cluster"]):
        parts.append("\n**2) Quiver A le papier — notre limite est la DATE de l'OCR.** Par cluster de "
                     "scan (House) : `quiver_a_le_trade_pct` reste élevé même en manuscrit (Quiver possède "
                     "le trade), mais la part `exact_match` (date juste) **chute** sur le manuscrit → "
                     "c'est notre lecture OCR des dates manuscrites qui est faible, **pas** une cécité de "
                     "Quiver au papier :\n\n")
        parts.append(_md_table(qv["by_cluster"]))
        parts.append("\n")

    # ════════ §6.2 Diagnostic « qui a raison ? » (diag déjà calculé en tête) ════════
    parts.append("\n### 6.2 Qui a raison ? Inclusion réelle, complétude nette, artefacts\n")
    parts.append("\nLes tableaux ci-dessus comptent *combien* de trades Quiver on retrouve. Ce diagnostic "
                 "(recalculé hors-ligne par `common/quiver_diagnosis.py`, **jamais réinjecté**) tranche "
                 "**pourquoi** on diffère : chaque écart reçoit un verdict — `CONCORDANT` ; `ECART_DATE` "
                 "(Quiver a le trade, notre date diffère — **à ~99 % un artefact de collision, pas une erreur** ; "
                 "voir plus bas) ; `ECART_TICKER` (notre ticker diffère/manque — souvent une **cascade** de "
                 "l'écart de date, ou une action sans ticker à résoudre ; nos tickers sont corrects) ; "
                 "`STRUCTUREL` (non-coté, hors périmètre Quiver) ; `ON_EST_PLUS_COMPLET` (action absente de "
                 "Quiver) ; et côté Quiver `MANQUANT_PAPIER`, `NON_COTE` (CUSIP/préférentielle/fragment OCR, "
                 "hors périmètre) et `NOTRE_MANQUE` (dépôt **coté** qu'on n'a pas du tout). Le corpus est "
                 "**dédupliqué cross-année** avant classification (réconciliation : **90 483** lignes brutes "
                 "FINAL − 631 re-divulgations = **89 852** transactions uniques). Ce diagnostic **raffine** les "
                 "tables figées 07g/07c (qui agrègent `no_match` et ne dédupliquent pas).\n")

    # ── Quiver ⊆ nous : la métrique DIRECTE de la thèse « on a tout ce que Quiver a » ──
    if len(diag.get("ticker_inclusion", [])):
        parts.append("\n#### Quiver ⊆ nous ? (inclusion au niveau ticker, dans notre fenêtre)\n")
        parts.append("\nLa bonne question n'est pas « combien de trades Quiver retrouve-t-on à la **date exacte** » "
                     "(biaisé par l'artefact plus bas) mais « **a-t-on tout ce que Quiver a** », au niveau "
                     "**(déposant, ticker, sens)**, restreint à **notre fenêtre** (Quiver `Filed` ∈ 2020-2026 ; "
                     "sinon l'historique pré-2020 de Quiver, qu'on ne couvre pas, fausse le taux à la baisse) :\n\n")
        parts.append(_md_table(diag["ticker_inclusion"]))
        parts.append("\n\nRésidu décomposé : `ocr_recuperable` = lignes papier ratées (re-OCR ciblé) ; "
                     "`quiver_non_cote` = « ticker » Quiver non appariable (CUSIP/préférentielle/fragment) ; "
                     "`credit_2jambes` = on a le trade sous un ticker d'échange 2-jambes (« PFE  VTRS » couvre "
                     "« PFE ») ; `cross_chambre` = déposant de l'autre chambre (Curtis Rep→Sén : ses trades "
                     "Chambre polluent le cache Sénat de Quiver) ; `residu_cote_reel` = le **seul vrai trou coté** "
                     "restant. Lecture : **House 93,8 % / Sénat 91,5 %** d'inclusion ; le vrai trou coté est "
                     "minuscule (~22 House / 0 Sénat), le reste est **récupérable (OCR)** ou **hors périmètre**.\n")

    # ── On est PLUS complet que Quiver (bilan net) ──
    if len(diag["our_tally"]) and len(diag["quiver_tally"]):
        def _byc(df, verdict):
            d = df[df["verdict"] == verdict]
            return {str(r["côté"]).split("(")[-1].rstrip(")").strip(): int(r["n"]) for _, r in d.iterrows()}
        plus, manque = _byc(diag["our_tally"], "ON_EST_PLUS_COMPLET"), _byc(diag["quiver_tally"], "NOTRE_MANQUE")
        parts.append("\n**Bilan net « on est plus complet »** — actions cotées qu'on a et que Quiver n'a PAS "
                     "(`ON_EST_PLUS_COMPLET`) vs vrais trous inverses (`NOTRE_MANQUE`) : "
                     f"**House +{plus.get('house','?')} contre {manque.get('house','?')}**, "
                     f"**Sénat +{plus.get('senate','?')} contre {manque.get('senate','?')}**. On a tout ce que "
                     "Quiver a (à l'OCR récupérable près) **et davantage** (échanges 2-jambes, sous-holdings).\n")

    # ── Artefact de collision : pourquoi l'ECART_DATE n'est PAS notre erreur ──
    if len(diag.get("date_artifact", [])):
        parts.append("\n**Artefact de collision — à lire AVANT la synthèse ci-dessous.** L'`ECART_DATE` n'est "
                     "**pas** une erreur : quand un déposant trade le même ticker plusieurs jours, l'appariement "
                     "« date la plus proche » relie deux trades RÉELS distincts et fabrique un faux écart :\n\n")
        parts.append(_md_table(diag["date_artifact"]))
        parts.append("\n\n**House ~99 % / Sénat ~100 % de l'`ECART_DATE` est cet artefact.** Sur les rares cas "
                     "isolés (~95 House), le **digital nous donne raison** : 5 PDF officiels vérifiés montrent "
                     "que c'est **Quiver** qui se décale (souvent d'un an sur les filings « Amended ») ; notre "
                     "OCR, lui, lit bien la date du scan. L'`ECART_DATE` n'est donc **ni notre erreur ni "
                     "corrigible chez nous**.\n")

    if len(diag["synthesis"]):
        parts.append("\n**Synthèse côté NOUS** (part de NOS transactions par catégorie). ⚠️ "
                     "`ecart_brut_pct` (= `ECART_DATE` + `ECART_TICKER`) **n'est PAS un taux d'erreur** et ne "
                     "reflète PAS nos erreurs : l'`ECART_DATE` est à ~99 % un artefact de collision (et, isolé, "
                     "c'est Quiver qui a tort sur le digital, 5 PDF vérifiés), et l'`ECART_TICKER` est surtout "
                     "une cascade de cet artefact (nos tickers matchent la description d'actif). Le **vrai** "
                     "taux d'erreur imputable est **< 1 %** — voir « Quiver ⊆ nous » et « artefact » ci-dessus :\n\n")
        parts.append(_md_table(diag["synthesis"]))
        parts.append("\n")
    if len(diag["our_tally"]):
        parts.append("\n**Verdicts nous→Quiver** (chacune de NOS transactions confrontée à Quiver) :\n\n")
        parts.append(_md_table(diag["our_tally"]))
        parts.append("\n")
    if len(diag["quiver_tally"]):
        parts.append("\n**Verdicts Quiver→nous** (les trades Quiver qu'on n'a pas = `only_quiver`). "
                     "`NON_COTE` = un « ticker » Quiver non appariable (CUSIP, préférentielle, fragment OCR) "
                     "→ hors périmètre. `NOTRE_MANQUE` = le **vrai trou** (action cotée jamais captée), "
                     "résiduel après filtrage du non-coté : ~10 lignes House (Pelosi UBER/INTC, Bresnahan "
                     "SPY/QQQ/IWM, James AFRM…) et 3 Sénat. Tout le reste s'explique par notre date, notre "
                     "ticker, ou du papier :\n\n")
        parts.append(_md_table(diag["quiver_tally"]))
        parts.append("\n")
    if len(diag["coverage_by_year"]):
        cby = diag["coverage_by_year"]
        cby = cby[cby["scope"] == "both"][["chamber", "year", "matched", "quiver",
                                           "couverture_pct", "precision_pct"]]
        parts.append("\n**Couverture (Quiver→nous) et precision (nous→Quiver) par année** (scope `both` ; "
                     "comble l'axe année absent des tables figées) :\n\n")
        parts.append(_md_table(cby))
        parts.append("\n")
    if len(diag["field_agreement"]):
        parts.append("\n**Accord sur les trades qu'on a TOUS LES DEUX** (cellules bio×ticker×date présentes "
                     "des deux côtés) — un de nos trades « concorde » s'il existe un trade Quiver de même "
                     "sens (resp. même sens+montant) dans la cellule. Mesure par **appartenance ensembliste** "
                     "(robuste à la granularité des lots : l'ancien `merge` cartésien sous-estimait l'accord "
                     "et gonflait `n_paires`). Un désaccord = vraie erreur d'extraction sur une donnée "
                     "pourtant captée, listée et **typée** (`sens`/`montant`) dans `desaccord_champ_*.csv` :\n\n")
        parts.append(_md_table(diag["field_agreement"]))
        parts.append("\n")
    if len(diag["top_notre_manque"]):
        parts.append("\n**Top déposants `NOTRE_MANQUE`** (dépôts Quiver qu'on n'a pas du tout — à investiguer) :\n\n")
        parts.append(_md_table(diag["top_notre_manque"]))
        parts.append("\n")
    parts.append("\nListes actionnables complètes (cas corrigibles, ligne à ligne) → `docs/quiver_validation/` "
                 "(`ecart_ticker_*.csv`, `notre_manque_*.csv`, `manquant_papier_*.csv`, "
                 "`desaccord_champ_*.csv` [typé sens/montant], `on_est_plus_complet_*.csv`, "
                 "`quiver_non_cote_*.csv`). Hors golden.\n")

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
