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
  (e) Devenir des achats à +12 mois (règle du backtest) : revendu ≤12 mois / fermé de force à +12 mois /
      trop récent pour juger (censuré), apparié sur la date de divulgation (même bioguide+ticker).
  (f) Validation externe Quiver : couverture par scope (digital/ocr/both), décomposition
      exact/date_mismatch/no_match/non_equity par type d'actif et par cluster de scan — agrégée depuis
      les `07c/07g/07h` figés (définition des métriques : common/quiver_scopes.py).

Usage : `python -m common.quality`  (écrit docs/RAPPORT_QUALITE.md + docs/quality/*.png)
"""
import bisect
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
    # ticker_source : House digital ne le stocke pas (le ticker est lu DIRECTEMENT dans le PDF, entre
    # parenthèses). On le dérive pour uniformiser les 4 sous-corpus (frozen intact) : « explicit » si le
    # ticker est présent (donc lu dans la déclaration), « none » sinon. N'affecte que les lignes non taguées.
    if "ticker_source" in full.columns:
        _ts = full["ticker_source"].fillna("").astype(str).str.strip().str.lower()
        _blank = (_ts == "") | (_ts == "nan")
        _has_tk = _nonblank(full["ticker"])
        full.loc[_blank & _has_tk, "ticker_source"] = "explicit"
        full.loc[_blank & ~_has_tk, "ticker_source"] = "none"
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


# ───────────────────────── (e) Devenir des achats à +12 mois (règle de la stratégie) ─────────────────────────
FORCED_CLOSE_HORIZON_DAYS = 365   # la stratégie ferme une position au plus tard 12 mois après l'achat


def purchase_exit_breakdown(df: pd.DataFrame, dim: str = "chamber",
                            horizon_days: int = FORCED_CLOSE_HORIZON_DAYS) -> pd.DataFrame:
    """Suit CHAQUE achat (avec ticker) dans le temps selon la règle réelle du backtest : est-il revendu
    par le même membre sur le même ticker DANS l'horizon de `horizon_days` (12 mois) ? L'appariement se
    fait sur la date de DIVULGATION (`_dd`) — ce que la stratégie peut observer — la première vente
    strictement postérieure à l'achat faisant foi. Trois issues, calées sur la stratégie :
      revendu_12m   : une vente est divulguée dans les 12 mois → sortie volontaire avant le plafond.
      ferme_force   : aucune vente sous 12 mois ET l'achat a ≥12 mois de recul → la stratégie clôt à +12 mois.
      trop_recents  : aucune vente sous 12 mois MAIS <12 mois de recul (divulgué après window_end−12 mois)
                      → indéterminé (troncature de fenêtre), EXCLU des dénominateurs.
    Les deux taux (`*_pct`) portent sur les OBSERVABLES = n_achats − trop_recents.
    NB : une seule métrique honnête remplace l'ancien « sans sortie » qui, sans horizon ni gestion de la
    troncature, sous-comptait les fermetures forcées et gonflait le taux avec des achats non observables."""
    d = df[_nonblank(df["ticker"])].dropna(subset=["_dd"]).copy()
    window_end = d["_dd"].max()
    H = pd.Timedelta(days=horizon_days)
    # dates de vente triées par (membre, ticker) → recherche de la 1re vente postérieure par bisection
    sell_map = {k: sorted(g) for k, g in
                d[d["op"] == "sell"].dropna(subset=["_dd"]).groupby(["bioguide_id", "ticker"])["_dd"]}

    def _first_sell_after(bio, tk, buy_dd):
        arr = sell_map.get((bio, tk))
        if not arr:
            return None
        i = bisect.bisect_right(arr, buy_dd)
        return arr[i] if i < len(arr) else None

    rows = []
    for key in _keys(d, dim):
        buys = d[(d[dim] == key) & (d["op"] == "buy")]
        if not len(buys):
            continue
        n_sold = n_forced = n_recent = 0
        for bio, tk, buy_dd in zip(buys["bioguide_id"], buys["ticker"], buys["_dd"]):
            fs = _first_sell_after(bio, tk, buy_dd)
            if fs is not None and fs <= buy_dd + H:
                n_sold += 1                       # revendu dans les 12 mois
            elif buy_dd + H <= window_end:
                n_forced += 1                     # assez de recul, pas de vente → fermé de force
            else:
                n_recent += 1                     # <12 mois d'observation → censuré
        n = len(buys)
        obs = n - n_recent
        rows.append({dim: key, "n_achats": n, "trop_recents": n_recent, "n_observables": obs,
                     "revendu_12m": n_sold,
                     "revendu_12m_pct": round(100 * n_sold / obs, 1) if obs else None,
                     "ferme_force": n_forced,
                     "ferme_force_pct": round(100 * n_forced / obs, 1) if obs else None})
    return pd.DataFrame(rows)


# ───────────────────────────── (f) Validation externe Quiver ─────────────────────────────
def quiver_validation(repo_root: Path) -> dict:
    """Agrège la validation Quiver (vérité-terrain ACTIONS) depuis les fichiers figés `07c/07g/07h`
    (lecture seule). NB : seuls 07c/07g/07h sont lus ; les autres figés (`07/07b/07d/07e/07f/06d`) sont
    des sorties HISTORIQUES du pipeline, conservées pour la lignée/régression (golden), non utilisées ici.
    Renvoie :
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
        # date_plausible = transaction dans la fenêtre légale [0, 75 j] avant la divulgation. Recalculé ici
        # depuis lag_days pour TOUS les sous-corpus (reproduit le flag `date_confidence` stocké côté OCR /
        # Sénat, et le comble pour House digital, qui ne stocke pas ce flag → uniformité + régénérable).
        lag = g["lag_days"]
        dplaus = _pct(int(((lag >= 0) & (lag <= WINDOW_DELAY_DAYS)).sum()), n)
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

    # 9. Composition par TRANCHE de montant déclaré, par sous-corpus (barres 100 % empilées) — montre
    #    visuellement que la plus petite tranche (≤ 15 k$, midpoint 8 000 $) domine → d'où P25 = médiane.
    try:
        edges = [0, 15000, 50000, 250000, 1e6, float("inf")]
        labs = ["≤ 15 k$", "15–50 k$", "50–250 k$", "250 k–1 M$", "> 1 M$"]
        amt = df.dropna(subset=["amount_midpoint"]).copy()
        amt["_bkt"] = pd.cut(amt["amount_midpoint"], bins=edges, labels=labs, include_lowest=True)
        piv = (amt.groupby(["corpus", "_bkt"]).size().unstack("_bkt")
                 .reindex(CORPUS_ORDER).reindex(columns=labs).fillna(0))
        pivp = piv.div(piv.sum(axis=1), axis=0) * 100
        fig, ax = plt.subplots(figsize=(8.5, 3.2))
        left = np.zeros(len(pivp)); colors = plt.cm.YlOrRd(np.linspace(0.30, 0.92, len(labs)))
        for j, lab in enumerate(labs):
            vals = pivp[lab].values
            ax.barh(pivp.index, vals, left=left, color=colors[j], label=lab, edgecolor="white", linewidth=0.5)
            for yi, (l, w) in enumerate(zip(left, vals)):
                if w >= 6:
                    ax.text(l + w / 2, yi, f"{w:.0f}%", va="center", ha="center", fontsize=7,
                            color="white" if j >= 2 else "#333")
            left += vals
        ax.set_xlabel("% des transactions"); ax.set_xlim(0, 100); ax.invert_yaxis()
        ax.set_title("Composition par tranche de montant déclaré — la plus petite tranche domine")
        ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=8, title="tranche ($)")
        f9 = outdir / "mix_montants_par_corpus.png"; fig.tight_layout(); fig.savefig(f9, dpi=110); plt.close(fig)
        figs.append(f9)
    except Exception:
        pass

    return figs


# ───────────────────────────── Rapport Markdown ─────────────────────────────
# Map UNIQUE nom-machine → en-tête FR clair, appliquée au rendu de TOUTES les tables (les DataFrames
# sources gardent leurs noms machine pour les annexes/golden). Une colonne absente passe inchangée.
_COLS = {
    "chamber": "chambre", "corpus": "sous-corpus", "part_pct": "part %",
    "ticker_%": "ticker %", "secteur_%": "secteur %", "etf_proxy_%": "ETF %",
    "committee_%": "commission %", "identite_%": "identité %", "anciennete_%": "ancienneté %",
    "dates_coherentes_%": "dates cohérentes %", "date_plausible_%": "date plausible %",
    "annee_implausible_n": "année aberrante (n)", "montant_renseigne_%": "montant renseigné %",
    "achat_%": "achat %", "vente_%": "vente %", "echange_%": "échange %", "autre_%": "autre %",
    "perso_%": "perso %", "conjoint_%": "conjoint %", "joint_%": "joint %", "enfant_%": "enfant %",
    "action_%": "action %", "option_%": "option %", "oblig.Etat_%": "oblig. État %", "muni_%": "muni %",
    "oblig.corp_%": "oblig. corp. %", "fonds_%": "fonds %", "manquant_%": "manquant %",
    "secteur_renseigne_%": "secteur renseigné %", "top_3_secteurs": "top 3 secteurs",
    "elec_dict_%": "dico élec %", "llm_%": "LLM %", "explicit_%": "explicite %", "none_%": "aucune %",
    "yfinance_%": "yfinance %", "manual_%": "manuel %",
    "mediane_$": "médiane $", "moyenne_$": "moyenne $", "volume_total_M$": "volume total M$",
    "n_deposants": "n déposants", "top10_volume_%": "top10 volume %", "n_trades": "n trades",
    "volume_M$": "volume M$", "secteur": "secteur", "n_lignes": "n lignes", "n_docs": "n docs",
    "quiver_a_le_trade_pct": "Quiver a le trade %",
    "dates_parseables_pct": "dates exploitables %", "coherentes_pct": "cohérentes %",
    "incoherentes": "incohérentes", "annee_txn_implausible": "année aberrante", "date_manquante": "date manquante",
    "n_dates_valides": "n dates valides", "<=45j_legal_pct": "≤45j légal %", "45-75j_pct": "45–75j %",
    ">75j_pct": ">75j %", "negatif_pct": "négatif %", "delai_median_j": "délai médian (j)",
    "declarant_name": "déposant", "transaction_date": "date txn", "disclosure_date": "date divulg.",
    "lag_days": "délai (j)", "operation_type": "opération", "volume_estime_musd": "volume estimé M$",
    "name": "nom", "our_total": "total", "our_ocr": "dont OCR", "ocr_share_pct": "OCR %",
    "n_annees": "n années", "premiere_annee": "1re année", "derniere_annee": "dern. année",
    "n_achats": "achats (avec ticker)", "trop_recents": "trop récents", "n_observables": "observables",
    "revendu_12m": "revendu ≤12m", "revendu_12m_pct": "revendu ≤12m %",
    "ferme_force": "fermé de force", "ferme_force_pct": "fermé de force +12m %",
    "scope": "scope", "matched": "appariés", "quiver": "Quiver", "only_ours": "nous seul",
    "only_quiver": "Quiver seul", "couverture_pct": "couverture %", "precision_pct": "precision %",
    "asset_type": "type d'actif", "exact_match": "exact (date)", "date_mismatch": "date ≠",
    "no_match": "absent", "non_equity": "non-coté", "total": "total", "cluster": "cluster",
    "quiver_dans_fenetre": "trades Quiver (fenêtre)", "inclus": "qu'on a", "inclusion_pct": "inclusion %",
    "residu": "résidu", "ocr_recuperable": "dont OCR récup.", "quiver_non_cote": "dont non-coté",
    "credit_2jambes": "dont 2-jambes", "cross_chambre": "dont autre chambre", "residu_cote_reel": "vrai trou coté",
    "apparie_exact": "apparié exact", "apparie_proche": "apparié proche (≤7j)", "candidat_ecart": "candidat écart",
    "dont_meme_depot": "dont même dépôt", "nous_seul": "nous-seul", "quiver_seul": "quiver-seul",
    "candidat_pct": "candidat %",
    "lignes_brutes": "lignes brutes", "re_divulgations_dedup": "re-divulgations (dédup)",
    "transactions_uniques": "transactions uniques",
    "declarant": "déposant", "sens": "sens",
    "provenance": "provenance", "notre_date": "notre date", "quiver_date": "date Quiver",
    "delta_jours": "delta (j)", "doc_id": "doc_id",
    "on_a_en_plus": "actions qu'on a en +", "vrais_trous": "vrais trous", "solde_net": "solde net",
    "nos_txns": "nos txns", "concordant_pct": "concordant %", "ecart_brut_pct": "écart brut %",
    "structurel_pct": "structurel %", "on_est_plus_complet_pct": "on est + complet %",
    "côté": "côté", "verdict": "verdict", "pct": "%", "a_corriger": "à corriger",
    "year": "année", "n_paires_appariées": "n paires", "accord_sens_pct": "accord sens %",
    "accord_montant_bas_pct": "accord montant %", "bioguide": "bioguide", "n_notre_manque": "n trous",
    "n_eligibles": "n éligibles", "state_district": "État/district",
}


def _md_table(df: pd.DataFrame) -> str:
    """Formate un DataFrame en table Markdown (sans dépendance `tabulate`). Applique `_COLS` aux en-têtes
    (rendu uniquement : le DataFrame source garde ses noms machine)."""
    df = df.rename(columns=_COLS)
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


def _leg(txt: str) -> str:
    """Légende courte (une ligne italique) sous une table : dit à quoi correspondent les colonnes/valeurs."""
    return f"\n*{txt}*\n"


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
    exit_bd = purchase_exit_breakdown(df)

    n_total = len(df)
    n_house = int((df["chamber"] == "house").sum())
    n_senate = int((df["chamber"] == "senate").sum())

    # Calculs Quiver remontés en tête : ils alimentent le résumé exécutif (et sont réutilisés en §6).
    from common import quiver_diagnosis as qd
    diag = qd.build_diagnosis(repo_root)
    inc = diag.get("ticker_inclusion", pd.DataFrame())
    drec = diag.get("date_reconciliation", pd.DataFrame())
    recon = diag.get("reconciliation", pd.DataFrame())

    def _byc(dd, verdict):
        d = dd[dd["verdict"] == verdict]
        return {str(r["côté"]).split("(")[-1].rstrip(")").strip(): int(r["n"]) for _, r in d.iterrows()}
    plus = _byc(diag["our_tally"], "ON_EST_PLUS_COMPLET") if len(diag.get("our_tally", [])) else {}
    manque = _byc(diag["quiver_tally"], "NOTRE_MANQUE") if len(diag.get("quiver_tally", [])) else {}

    def _n(x):
        return f"{int(x):,}".replace(",", " ")

    def _cell(table, ch, col, d="—"):
        """Valeur régénérable d'une table (par `chamber`). Toute la prose chiffrée passe par ici."""
        if not len(table):
            return d
        row = table[table["chamber"] == ch]
        if not len(row):
            return d
        v = row.iloc[0].get(col, d)
        return d if (v is None or (isinstance(v, float) and pd.isna(v))) else v

    # Chiffres « données propres » du résumé — tous recalculés (jamais hardcodés).
    yr = f"{min(qd.YEARS)}–{max(qd.YEARS)}"
    _lag = df["lag_days"]
    id_pct = round(100 * _nonblank(df["bioguide_id"]).mean(), 1)
    coh_pct = round(100 * int((_lag >= 0).sum()) / int(_lag.notna().sum()), 1) if _lag.notna().any() else "—"
    med_lag = int(_lag[_lag >= 0].median()) if (_lag >= 0).any() else "—"
    amt_pct = round(100 * df["amount_midpoint"].notna().mean(), 1)

    parts = []
    parts.append("# Rapport qualité — Données de trading du Congrès américain\n")
    parts.append(f"> Chambre des représentants + Sénat · {yr} · généré par `python -m common.quality` "
                 "(lecture seule des tables FINAL, aucun appel API) · "
                 "Quiver Quantitative = vérité-terrain externe, **jamais réinjectée**.\n")
    parts.append("\n## Résumé exécutif\n\n")
    parts.append(
        f"- **Périmètre** — {_n(n_total)} transactions uniques de membres élus "
        f"(House {_n(n_house)} + Sénat {_n(n_senate)}), {yr}, en **4 sous-corpus** "
        "(chambre × voie d'acquisition : électronique déterministe / scan OCR).\n"
        f"- **Complétude vs Quiver** *(§6)* — dans notre fenêtre, on retrouve "
        f"**{_cell(inc,'house','inclusion_pct')} % (House) / {_cell(inc,'senate','inclusion_pct')} % (Sénat)** "
        "des trades Quiver au niveau (déposant, ticker, sens). Le **vrai trou coté est minuscule** "
        f"({_cell(inc,'house','residu_cote_reel')} House / {_cell(inc,'senate','residu_cote_reel')} Sénat) ; le "
        "reste du résidu est de l'OCR récupérable ou du hors-périmètre.\n"
        f"- **On est plus complet que Quiver** — **+{plus.get('house',0)+plus.get('senate',0)} actions cotées "
        f"qu'on a et que Quiver n'a pas, contre {manque.get('house',0)+manque.get('senate',0)} trous "
        "inverses.** La base est, en pratique, un **sur-ensemble** de Quiver.\n"
        f"- **Les « écarts » de date ne sont pas des erreurs** — la réconciliation 1-à-1 (§6.3) montre que "
        f"l'essentiel est du « nous-seul » (Quiver n'a pas le trade) ; seuls {_cell(drec,'house','dont_meme_depot')} "
        "candidats House (même dépôt) méritent l'œil, et le vrai contrôle des dates reste l'audit PDF (§2).\n"
        f"- **Données propres** — identité rattachée à {id_pct} %, dates cohérentes {coh_pct} %, délai de "
        f"divulgation médian {med_lag} j, montants renseignés {amt_pct} %.\n")
    parts.append("\n*Plan : §1 composition · §2 cohérence des dates · §3 délai légal · §4 montants · "
                 "§5 couverture & structure · §6 complétude vs Quiver (vérité-terrain).*\n")

    # ════════ §1 Composition ════════
    parts.append("\n## 1. Composition & qualité par sous-corpus\n")
    parts.append("\nLes déclarations proviennent de **quatre sous-corpus** très différents (chambre × "
                 "voie d'acquisition). Toute la suite distingue ces quatre familles, car leur qualité et "
                 "leur composition diffèrent.\n\n")
    parts.append(_md_table(corpus_overview(df)))
    parts.append(_leg("sous-corpus = chambre × voie (électronique déterministe / scan OCR) · n = transactions "
                      "uniques · part % du total"))

    parts.append("\n### Couverture des champs enrichis (taux de remplissage)\n\n")
    parts.append(_md_table(coverage_scorecard(df)))
    parts.append(_leg("% de lignes où le champ est renseigné · identité = rattachée à un `bioguide_id` · "
                      "ticker/secteur/ETF vides = actif non coté (normal, pas un défaut)"))

    parts.append("\n### Scorecard de qualité\n\n")
    parts.append(_md_table(quality_scorecard(df)))
    parts.append(_leg("dates cohérentes = divulgation ≥ transaction · date plausible = transaction ∈ [0, 75 j] "
                      "avant divulgation · année aberrante = année impossible (postérieure au dépôt, ou < 2012) · "
                      "montant renseigné = `amount_midpoint` non vide"))

    parts.append("\n### Mix par sous-corpus\n")
    parts.append("\n**Sens des opérations :**\n\n")
    parts.append(_md_table(operation_mix(df)))
    parts.append(_leg("achat = `operation_type` contient « Purchase » · vente = contient « Sale » "
                      "(**inclut Sale (Partial) et (Full)**) · échange = « Exchange » · autre = reste"))
    parts.append("\n![Mix achat/vente par sous-corpus](quality/mix_operations_par_corpus.png)\n")
    parts.append("\n**Détenteur déclaré :**\n\n")
    parts.append(_md_table(owner_mix(df)))
    parts.append(_leg("titulaire du compte : perso = Self · conjoint = Spouse/SP · joint = Joint/JT · "
                      "enfant = Dependent/Child/DC · autre = reste ou non déclaré"))
    parts.append("\n**Familles d'actifs** (le non-coté — oblig. d'État, munis, obligations — domine "
                 "l'OCR du Sénat) :\n\n")
    parts.append(_md_table(asset_type_mix(df)))
    parts.append(_leg("familles d'`asset_type` : action = Stock · option · oblig. État = Gov/Treasury · "
                      "muni = Municipal · oblig. corp. = Bond · fonds = Fund/ETF · manquant = vide"))
    parts.append("\n![Mix de types d'actifs par sous-corpus](quality/mix_actifs_par_corpus.png)\n")

    parts.append("\n### Secteurs & sources de résolution\n\n")
    parts.append(_md_table(sector_mix(df)))
    parts.append(_leg("secteur renseigné % / ETF % = taux de remplissage (vide = non coté) · top 3 = secteurs "
                      "GICS dominants"))
    sy = source_yield(df)
    parts.append("\n**Origine du ticker** (`ticker_source` — comment le ticker a été obtenu) :\n\n")
    parts.append(_md_table(sy["ticker"]))
    parts.append(_leg("comment le ticker est obtenu : dico élec = repris de l'électronique · LLM = résolu par "
                      "LLM · explicite = déjà présent dans la source · aucune = non résolu"))
    parts.append("\n**Origine du secteur** (`sector_source`) :\n\n")
    parts.append(_md_table(sy["sector"]))
    parts.append(_leg("comment le secteur GICS est obtenu : yfinance = base factuelle · LLM · manuel = "
                      "correction d'audit · aucune"))
    parts.append("\n\n![Volume par secteur GICS](quality/volume_par_secteur.png)\n")

    parts.append("\n### Montants par sous-corpus\n\n")
    parts.append(_md_table(amount_stats_by_corpus(df)))
    parts.append(_leg("$ = midpoint des fourchettes déclarées · P25/P75/P95 = percentiles · volume total = Σ midpoint"))
    parts.append("\n\n![Composition par tranche de montant](quality/mix_montants_par_corpus.png)\n")
    parts.append(_leg("la plus petite tranche (≤ 15 k$, midpoint 8 000 $) domine → dès qu'elle dépasse 50 %, "
                      "le P25 ET la médiane y tombent ensemble (cas House/Sénat élec). Sénat OCR < 50 % → "
                      "médiane 32 500 ≠ P25 8 000."))

    parts.append("\n### Concentration de l'activité\n\n")
    conc = concentration(df)
    parts.append(_md_table(conc["inequality"]))
    parts.append("\n\n`HHI` ∈ [0, 10000] et `Gini` ∈ [0, 1] mesurent la concentration du volume par "
                 "déposant (plus c'est haut, plus quelques déposants dominent).\n")
    parts.append("\n![Concentration du volume (Lorenz)](quality/concentration_lorenz.png)\n")
    parts.append("\n**Top tickers par volume estimé :**\n\n")
    parts.append(_md_table(conc["top_tickers"]))
    parts.append(_leg("volume M$ = Σ midpoint des trades du ticker · n trades = nombre de transactions"))
    parts.append("\n**Volume par secteur GICS :**\n\n")
    parts.append(_md_table(conc["top_sectors"]))
    parts.append("\n")

    # (Le profil des clusters de scan House OCR est en §6.6 : la colonne « Quiver a le trade % »
    #  est de la vérité-terrain externe → sa place est dans la section Quiver, pas ici.)

    # ════════ §2 Cohérence des dates ════════
    parts.append("\n## 2. Cohérence des dates (`disclosure_date ≥ transaction_date`)\n")
    parts.append(_md_table(coh))
    parts.append("\n\n**Par sous-corpus :**\n\n")
    parts.append(_md_table(date_coherence(df, dim="corpus")))
    parts.append(_leg("dates exploitables = dates parseables (le reste = OCR illisible) · cohérentes = "
                      "divulgation ≥ transaction · incohérentes = divulgation AVANT transaction (amendement/"
                      "antidaté) · année aberrante = année impossible (postérieure au dépôt, ou < 2012) · date "
                      "manquante = illisible. Des transactions 2013–2019 sont légitimes (divulgations tardives)."))
    _n_ocr_fix = len(schema.KNOWN_TXN_DATE_FIXES_BY_DOC)
    parts.append(f"\n**Audit des anomalies (échantillon de 12 PDF re-lus à la source).** ~½ sont FIDÈLES : "
                 f"coquilles du **déposant lui-même** (un PTR imprime littéralement `01/35/22`), cellules vides "
                 f"ou parts de société sans date de transaction — on les transcrit sans les inventer. ~⅓ = "
                 f"**notre OCR** (mois/jour mal lu), corrigé à la lecture **quand le formulaire est lisible** "
                 f"({_n_ocr_fix} dates vérifiées, clé doc+date, figé inchangé). ~⅙ = **provenance** (hallucination "
                 f"OCR ou pièce jointe absente du PDF). **On ne fabrique aucune date** : les illisibles restent "
                 f"flaggées.\n")

    # ════════ §3 Délai légal ════════
    parts.append("\n## 3. Délai légal de divulgation (STOCK Act ~45 j)\n")
    parts.append(_md_table(delays))
    parts.append("\n\n**Par sous-corpus :**\n\n")
    parts.append(_md_table(delay_buckets(df, dim="corpus")))
    parts.append(_leg("n dates valides = transactions dont le délai est CALCULABLE (les deux dates, transaction "
                      "ET divulgation, présentes et lisibles ; « valide » = mesurable, pas « juste ») · délai = "
                      "divulgation − transaction (jours) · ≤45 j = délai légal STOCK Act · 45–75 j = marge tolérée · "
                      ">75 j = retard · négatif = anomalie (divulgation avant transaction), comptée quand même dans "
                      "n dates valides · délai médian en jours"))
    parts.append("\n![Délai de divulgation](quality/delai_divulgation.png)\n")
    if len(outliers):
        parts.append("\n**Divulgations les plus tardives (> 365 j, suspects) :**\n\n")
        parts.append(_md_table(outliers))
        parts.append(_leg("délai (j) = divulgation − transaction · divulgations > 1 an après la transaction "
                          "(souvent des amendements ou de vieux comptes régularisés)"))

    # ════════ §4 Distribution des montants ════════
    parts.append("\n## 4. Distribution des montants (`amount_midpoint`)\n")
    parts.append("\nStats globales (USD, midpoint des fourchettes déclarées) :\n\n")
    parts.append("```\n" + amounts["overall"].round(0).to_string() + "\n```\n")
    parts.append("\nPar chambre :\n\n")
    parts.append("```\n" + amounts["by_chamber"].round(0).to_string() + "\n```\n")
    parts.append("\nPar sous-corpus :\n\n")
    parts.append("```\n" + amounts["by_corpus"].round(0).to_string() + "\n```\n")
    parts.append(_leg("count = nb · mean = moyenne · std = écart-type · 25/50/75 % = quartiles · USD (midpoint "
                      "des fourchettes déclarées)"))
    parts.append("\n![Distribution des montants](quality/distribution_montants.png)\n")
    parts.append("\n**Top 15 déposants par volume estimé (Σ midpoint) :**\n\n")
    parts.append(_md_table(amounts["top_volume"]))
    parts.append(_leg("volume estimé M$ = Σ midpoint des transactions du déposant · n trades = nombre de transactions"))

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
    parts.append(_leg("total = nb transactions · dont OCR / OCR % = part scannée · n années = années actives · "
                      "1re/dern. année = première/dernière année de transaction"))

    # ════════ §5.1 Devenir des achats à +12 mois (règle de la stratégie) ════════
    _cut = (df["_dd"].max() - pd.Timedelta(days=FORCED_CLOSE_HORIZON_DAYS)).date()
    parts.append("\n### Devenir des achats à +12 mois (revente vs fermeture forcée, pour la stratégie)\n")
    parts.append(f"\nPour chaque achat (avec ticker), on suit la position : est-elle **revendue par le même "
                 f"membre sur le même ticker dans les 12 mois** (l'horizon de fermeture forcée de la "
                 f"stratégie) ? L'appariement se fait sur la **date de divulgation** — ce que la stratégie "
                 f"peut observer. Les achats divulgués il y a **moins de 12 mois** (après {_cut}) n'ont pas "
                 f"assez de recul pour juger : marqués *trop récents* et exclus des taux.\n\n")
    parts.append(_md_table(exit_bd))
    parts.append("\n\n**Par sous-corpus :**\n\n")
    parts.append(_md_table(purchase_exit_breakdown(df, dim="corpus")))
    parts.append(_leg("achats (avec ticker) · trop récents = <12 mois de recul depuis la divulgation "
                      "(indéterminé, hors dénominateur) · observables = achats − trop récents · "
                      "revendu ≤12m = une vente du même ticker divulguée dans les 12 mois · "
                      "fermé de force +12m = aucune vente sous 12 mois → la stratégie clôt la position · "
                      "les deux % portent sur les observables"))

    # ════════ §6 Complétude vs Quiver (tables-first, tout régénérable) ════════
    parts.append("\n## 6. Complétude vs Quiver (vérité-terrain externe)\n")
    parts.append("\n> **Section clé.** Quiver est un fournisseur commercial des mêmes données = notre **juge "
                 "externe**. But : montrer qu'on a **au moins tout ce que Quiver a** (Quiver ⊆ nous), qu'on est "
                 "même **plus complet**, et que nos différences ne sont **pas des erreurs**. On procède comme un "
                 "**entonnoir, de strictesse croissante** : Niveau 1 → 2 → 3. Chiffres recalculés par "
                 "`common/quiver_diagnosis.py`, **jamais réinjectés**.\n")

    # 6.1 Méthode (clé + les 3 niveaux annoncés + périmètre dédupliqué)
    parts.append("\n### 6.1 Méthode\n")
    parts.append("\nChaque transaction est confrontée à Quiver par une clé normalisée, en **trois niveaux de plus "
                 "en plus stricts** : **N1** a-t-on le trade ? *(sans la date, §6.2)* → **N2** le même trade à la "
                 "même date ? *(§6.3)* → **N3** qui corrige quoi ? *(§6.5)*.\n\n")
    _meth = pd.DataFrame([
        {"élément": "univers comparé", "définition": f"tous les trades Quiver `Filed` ∈ {yr} (notre fenêtre de scrape)"},
        {"élément": "clé d'appariement", "définition": "(`bioguide`, ticker normalisé, sens) — **+ date** au Niveau 2, **sans date** au Niveau 1"},
        {"élément": "normalisation ticker", "définition": "MAJ + trim ; rejette {vide, NAN, NONE, --} ; retire ` PUT`/` CALL` ; `.`/`-` → `_`"},
        {"élément": "normalisation sens", "définition": "1re lettre p/s/e → Purchase / Sale / Exchange"},
    ])
    parts.append(_md_table(_meth))
    if len(recon):
        parts.append("\n**Périmètre** — le FINAL est dédupliqué cross-année avant comparaison (une re-divulgation "
                     "tardive ne compte qu'une fois) :\n\n")
        parts.append(_md_table(recon))
    parts.append("\n\n*Réf. : `house/quiver.py` (`norm_ticker`, `norm_sense`), `common/quiver_diagnosis.py`.*\n")

    # 6.2 Niveau 1 — inclusion date-AGNOSTIQUE (a-t-on le trade, sans la date ni le nombre)
    if len(inc):
        parts.append("\n### 6.2 Niveau 1 — A-t-on le trade ? (sans la date)\n")
        parts.append("\nOn compare des **combinaisons** `(membre, action, sens)`, en **ignorant volontairement la "
                     "date ET le nombre** : `(Khanna, AAPL, Achat)` compte pour **un**, qu'il l'ait acheté 1 fois "
                     "ou 50. La question est donc grossière **exprès** : *« a-t-on raté une combinaison ENTIÈRE que "
                     "Quiver connaît ? »* — le comptage trade par trade, c'est le Niveau 2 (§6.3).\n\n")
        parts.append(f"On retrouve **{_cell(inc,'house','inclusion_pct')} % (House)** et "
                     f"**{_cell(inc,'senate','inclusion_pct')} % (Sénat)** des combinaisons Quiver. Le **vrai trou** "
                     f"est minuscule ({_cell(inc,'house','residu_cote_reel')} House / "
                     f"{_cell(inc,'senate','residu_cote_reel')} Sénat) ; le reste est récupérable ou hors "
                     "périmètre :\n\n")
        parts.append(_md_table(inc))
        parts.append("\n\n*Résidu :* **OCR récup.** = lignes papier ratées · **non-coté** = « ticker » Quiver non "
                     "appariable (CUSIP, préférentielle, fragment) · **2-jambes** = trade sous un ticker d'échange "
                     "(« PFE  VTRS » couvre « PFE ») · **autre chambre** = déposant Rep→Sén polluant le cache Sénat "
                     "· **vrai trou coté** = le seul manque réel.\n")
        if len(diag.get("net_completeness", [])):
            parts.append("\n**Bilan net** — combinaisons cotées qu'on a et que Quiver n'a PAS vs trous inverses → "
                         "on est un **sur-ensemble** de Quiver :\n\n")
            parts.append(_md_table(diag["net_completeness"]))

    # 6.3 Niveau 2 — réconciliation date-ANCRÉE (avec l'exemple concret d'appariement 1-à-1)
    if len(drec):
        parts.append("\n### 6.3 Niveau 2 — Le même trade, à la même date ?\n")
        parts.append("\nOn descend au trade près. Comme un membre peut trader le même titre **plusieurs fois**, on "
                     "ne demande PAS « ma date est-elle dans l'ensemble Quiver ? » : on **apparie 1-à-1** nos trades "
                     "à ceux de Quiver, à l'intérieur de chaque `(membre, ticker, sens)`. Exemple :\n\n")
        parts.append("```\nKhanna, AAPL, Achat — dates :\n"
                     "  NOUS   : 08-jan-2020 · 13-fév-2020 · 01-juin-2020 · 10-mars-2023\n"
                     "  QUIVER : 08-jan-2020 · 12-fév-2020 ·                10-mars-2023\n\n"
                     "Étape 1 — on retire les dates IDENTIQUES (une par une) :\n"
                     "  08-jan ↔ 08-jan   et   10-mars-2023 ↔ 10-mars-2023   → 2 « apparié exact »\n"
                     "  (le trade 2023 s'apparie à SON 2023, jamais à un 2020)\n\n"
                     "Étape 2 — on apparie les RESTES au plus proche (plafond 90 j) :\n"
                     "  13-fév (nous) ↔ 12-fév (Quiver) = 1 j   → « apparié proche » (≤ 7 j, bruit de date)\n"
                     "  01-juin (nous) : aucun reste Quiver à < 90 j   → « NOUS-SEUL » (trade en plus)\n"
                     "```\n")
        parts.append("\nDeux garde-fous répondent à « comment gérer qu'un membre ait plusieurs trades » : "
                     "l'appariement **1-à-1 respecte les quantités** (si on a 50 trades et Quiver 40, **≥ 10 "
                     "restent forcément en « nous-seul »**) ; le **plafond de 90 j** + l'**ancrage au dépôt** "
                     "empêchent mécaniquement de confondre un trade 2020 et un trade 2023. Chaque trade tombe alors "
                     "dans **une** catégorie :\n\n")
        parts.append(_md_table(drec))
        parts.append(_leg("apparié exact = même date · apparié proche = même trade à ≤ 7 j (bruit/convention de "
                          "date) · candidat écart = paire à 7–90 j à inspecter (§6.4) · dont même dépôt = dans le "
                          "MÊME PTR (seul signal fort) · nous-seul = Quiver n'a PAS le trade (on est plus complet) "
                          "· quiver-seul = on a raté."))
        parts.append(f"\n**Pourquoi les chiffres semblent contredire le §6.2 : c'est le niveau de strictesse.** "
                     f"Au Niveau 1 (sans date), le vrai trou est {_cell(inc,'house','residu_cote_reel')}/"
                     f"{_cell(inc,'senate','residu_cote_reel')} ; au Niveau 2 (trade + date), on compte "
                     f"{_cell(drec,'house','nous_seul')} trades « nous-seul » — normal, on trade plus souvent que "
                     "Quiver ne capte au trade près. **Les deux disent la même chose : on est plus complet.**\n")

    # 6.4 Les candidats d'écart de date « même dépôt » — drill-down du §6.3 (table générée + doc_id)
    cnd = diag.get("date_candidates", pd.DataFrame())
    parts.append("\n### 6.4 Les candidats d'écart de date (même dépôt)\n")
    if len(cnd):
        parts.append(f"\nLes **seuls** candidats honnêtes d'erreur de date = les paires **dans un même dépôt** "
                     f"({_cell(drec,'house','dont_meme_depot')} House / {_cell(drec,'senate','dont_meme_depot')} "
                     "Sénat). Prudence : un petit delta peut être une **convention de date Quiver**, pas notre "
                     "erreur. **Le vrai contrôle des dates reste l'audit PDF (§2)**, pas Quiver. `doc_id` = pièce "
                     "consultable :\n\n")
        parts.append(_md_table(cnd.head(12)))
        parts.append(f"\n\n*(Top 12 par delta croissant ; les {len(cnd)} candidats sont dans "
                     "`quiver_validation/candidats_ecart_date_meme_depot.csv`.)*\n")
    else:
        parts.append("\nAucun candidat « même dépôt » — les écarts résiduels sont du « nous-seul » ou du bruit de "
                     "convention de date.\n")

    # 6.5 Niveau 3 — que reste-t-il à corriger ? (champs restants + to-do actionnable)
    parts.append("\n### 6.5 Niveau 3 — Que reste-t-il à corriger ?\n")
    parts.append("\nOn a vérifié l'**existence** (§6.2) et la **date** (§6.3). Restent deux choses : les **autres "
                 "champs** des trades qu'on partage avec Quiver (sens, montant), et la **liste de ce qui est "
                 "vraiment à corriger**.\n")
    if len(diag["field_agreement"]):
        parts.append("\n**Autres champs — sens & montant.** Pour les trades qu'on a **tous les deux** (mêmes "
                     "membre + ticker + date), est-on d'accord sur le sens (achat/vente) et le montant ?\n\n")
        parts.append(_md_table(diag["field_agreement"]))
        parts.append(_leg("on apparie les cellules (membre, ticker, date) présentes des DEUX côtés ; un désaccord "
                          "= vraie erreur d'extraction, listée dans `desaccord_champ_*.csv`."))
    # to-do : compteurs tirés des tallies déjà calculés (via _byc)
    _et = _byc(diag["our_tally"], "ECART_TICKER") if len(diag.get("our_tally", [])) else {}
    _mp = _byc(diag["quiver_tally"], "MANQUANT_PAPIER") if len(diag.get("quiver_tally", [])) else {}
    _todo = pd.DataFrame([
        {"à corriger": "vrais trous cotés (`NOTRE_MANQUE`)", "House": manque.get("house", 0),
         "Sénat": manque.get("senate", 0), "nature": "**DUR** — trade coté absent de chez nous (le résidu final filtré)",
         "annexe": "`notre_manque_*`"},
        {"à corriger": "lignes OCR papier (`MANQUANT_PAPIER`)", "House": _mp.get("house", 0),
         "Sénat": _mp.get("senate", 0), "nature": "borne haute — trades Quiver de déposants qu'on OCR, absents de nos clés exactes",
         "annexe": "`manquant_papier_*`"},
        {"à corriger": "tickers à revoir (`ECART_TICKER`)", "House": _et.get("house", 0),
         "Sénat": _et.get("senate", 0), "nature": "borne haute — autre ticker ce jour-là (gonflée par la multiplicité, PAS un taux d'erreur)",
         "annexe": "`ecart_ticker_*`"},
    ])
    parts.append("\n**La to-do (à corriger).** Un seul chiffre est **dur** — les vrais trous `NOTRE_MANQUE` (le "
                 "résidu après tous les filtres) ; les deux autres sont des **bornes hautes** ensemblistes = des "
                 "listes à revoir cas par cas dans `docs/quiver_validation/`, pas des taux d'erreur :\n\n")
    parts.append(_md_table(_todo))
    if len(diag["top_notre_manque"]):
        parts.append("\n**Qui ?** — les déposants derrière les vrais trous (`NOTRE_MANQUE`), à investiguer :\n\n")
        parts.append(_md_table(diag["top_notre_manque"]))
        parts.append("\n")

    # 6.6 Annexe (compacte) : note tables figées + profil des clusters de scan House OCR
    parts.append("\n### 6.6 Annexe\n")
    parts.append("\nLes tables **figées** `07c/07g/07h` reproduisent la même comparaison en *exact-date* (elles "
                 "**sous-comptent**, cf. §6.3) ; conservées pour la lignée/régression, non re-rendues ici. Les "
                 "autres figées (`07/07b/07d/07e/07f/06d`) sont des sorties historiques du pipeline.\n")
    prof = house_ocr_cluster_profile(df, repo_root)
    if len(prof):
        parts.append("\n**Profil des clusters de scan (House OCR)** — pourquoi le manuscrit est exclu (A = tapé "
                     "droit, B = tapé tourné, C = manuscrit) :\n\n")
        parts.append(_md_table(prof))
        parts.append(_leg("`date plausible %` / `ticker %` = qualité INTERNE (sans Quiver) · `Quiver a le trade %` "
                          "= part de nos trades cotés que Quiver possède AUSSI (appariée sur membre+ticker+sens, "
                          "date ou non). Sur le manuscrit (C), la qualité interne reste haute mais `Quiver a le "
                          "trade %` s'effondre (ticker/identité mal lus, ou Quiver mince sur le papier) → faute de "
                          "pouvoir le confirmer contre la vérité-terrain, on l'exclut par défaut (conservateur)."))
    parts.append("\nListes actionnables complètes (ligne à ligne) → `docs/quiver_validation/` "
                 "(`ecart_ticker_*`, `notre_manque_*`, `manquant_papier_*`, `desaccord_champ_*` [typé], "
                 "`on_est_plus_complet_*`, `quiver_non_cote_*`, `candidats_ecart_date_meme_depot`). "
                 "Hors golden.\n")

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
