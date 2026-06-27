"""Validation Quiver multi-scopes — réconciliation transaction-niveau sur digital / OCR / les deux.

Quiver = vérité-terrain EXTERNE (jamais réinjectée). On mesure la concordance séparément par piste,
parce que Quiver ne couvre pas les deux pistes de la même façon selon la chambre :

  • `digital` : nos PTR électroniques  vs Quiver → couverture « propre » (dates exactes).
  • `ocr`     : nos scans / papier      vs Quiver → mesure la qualité de l'OCR LÀ où Quiver a la donnée.
  • `both`    : la table FINALE (dig+OCR) vs Quiver → la validation d'ensemble (ce que le rapport cite).

──────────────────────────────────────────────────────────────────────────────────────────────────
DIFFÉRENCE House / Sénat (que le scope `ocr` révèle automatiquement) :
  • HOUSE : Quiver A le papier (ex. Rohit Khanna ≈ 29 000 lignes Quiver) → l'OCR EST validé en externe
            (~75 % de match transaction-niveau ; l'écart = surtout des dates OCR mal lues). L'OCR House
            est énorme (~49 000 lignes).
  • SÉNAT : Quiver est AVEUGLE au papier (ex. Blumenthal, Feinstein = 0 ligne Quiver) → le scope `ocr`
            ressort VIDE (coverage_pct = None) → ici seulement « OCR = source unique » est vrai
            (validation interne uniquement : date_confidence, stabilité run-à-run). OCR Sénat ~1 700 lignes.

──────────────────────────────────────────────────────────────────────────────────────────────────
MÉTRIQUES produites par `reconcile` (renvoyées POUR CHAQUE scope) :
  txn_reco (comptes) :
      common_members        nb de déposants présents chez nous ET chez Quiver
      quiver_amendment_dups nb de doublons d'amendements retirés côté Quiver (dédup)
      ours_tickerizable     nb de nos transactions avec un ticker normalisable (clé valide)
      quiver                nb de transactions Quiver (pour les déposants communs) = dénominateur
      matched               nb de clés (bioguide×ticker×date×sens) présentes des DEUX côtés
      only_quiver           transactions Quiver non retrouvées chez nous (manques ou dates décalées)
      only_ours             nos transactions absentes de Quiver (papier Quiver-aveugle, ou bruit)
      coverage_pct          matched / quiver  (couverture = part de Quiver qu'on retrouve)
  field_agreement (% d'accord sur les transactions appariées, + n_pairs) :
      sense                 achat/vente/échange
      date_traded           date de transaction (Traded) — chute si dates OCR bruitées
      date_filed            date de dépôt (Filed) — robustesse alternative
      amount_bucket         fourchette de montant (borne basse)
  ticker_per_{member,senator} : par déposant — tickers communs / nous-seul / Quiver-seul
  only_quiver_txn             : la LISTE des trades Quiver qu'on n'a pas (bioguide, ticker, date, sens)
"""
import pandas as pd


def reconcile_scopes(reconcile_fn, scopes, qwin):
    """Applique `reconcile_fn(df, qwin)` à chaque scope (dict nom→DataFrame ∈ digital/ocr/both).

    Renvoie `(txn_reco, field_agreement, rec_both)` :
      - `txn_reco` / `field_agreement` = les tables de `reconcile`, empilées avec une colonne `scope`
        en tête (digital / ocr / both) → un seul fichier par famille, lisible des trois côtés.
      - `rec_both` = le dict complet du scope `both` (FINAL), pour écrire le détail par déposant
        (`ticker_per_member` / `ticker_per_sen`) et `only_quiver_txn` sur la table d'ensemble.
    `coverage_pct = None` sur un scope (ex. OCR Sénat) signifie « Quiver n'a aucune donnée » — informatif.
    """
    txn, field, rec_both = [], [], None
    for name, df in scopes.items():
        r = reconcile_fn(df, qwin)
        t = r["txn_reco"].copy(); t.insert(0, "scope", name); txn.append(t)
        f = r["field_agreement"].copy(); f.insert(0, "scope", name); field.append(f)
        if name == "both":
            rec_both = r
    return pd.concat(txn, ignore_index=True), pd.concat(field, ignore_index=True), rec_both


# ── Décomposition fine « qui a quoi » vs Quiver (07g / 07h) ───────────────────────────────────────
# CLASSES de chaque transaction à NOUS, confrontée à Quiver (la vérité-terrain actions) :
#   exact_match    : Quiver a le même trade, MÊME DATE de transaction → concordance parfaite.
#   date_mismatch  : Quiver a le trade (même bioguide×ticker×sens) mais notre DATE diffère
#                    → on a capté le bon trade, mais notre lecture (souvent OCR) a mal lu la date.
#   no_match       : aucune correspondance Quiver (ni avec ni sans date) → soit Quiver ne l'a pas,
#                    soit notre ticker est faux. C'est le « only_ours » réel des actions.
#   non_equity     : pas de ticker (muni, obligation, fonds privé…) → HORS périmètre Quiver
#                    (Quiver ne suit que les actions cotées) → ni validable ni un défaut.
# Ce que ça RÉVÈLE (chiffré, par run) :
#   • Quiver N'EST PAS aveugle au papier : exact+date_mismatch = la part que Quiver POSSÈDE.
#   • Le point faible = la DATE de notre OCR (surtout MANUSCRIT) → date_mismatch élevé.
#   • Le non_equity (gros au Sénat : munis) explique l'essentiel du « Quiver ne nous voit pas ».
def match_breakdown(our_df, qwin, norm_ticker, norm_sense, cluster_map=None):
    """Classe chaque transaction de `our_df` (exact_match / date_mismatch / no_match / non_equity) vs
    `qwin` (fenêtre Quiver), puis agrège par `asset_type` (les 2 chambres) et, si `cluster_map` est
    fourni (dict doc_id→cluster, House), par `cluster`. Renvoie (by_asset_df, by_cluster_df|None) ;
    chaque table : une ligne par valeur, colonnes des 4 classes + total + `quiver_has_pct`
    (= part des ACTIONS que Quiver possède = (exact+date_mismatch)/(exact+date_mismatch+no_match))."""
    d = our_df.copy()
    d["_tk"] = d["ticker"].map(norm_ticker)
    d["_sense"] = d["operation_type"].map(norm_sense)
    d["_d"] = pd.to_datetime(d["transaction_date"], errors="coerce").dt.date
    q = qwin.copy()
    q["_tk"] = q["Ticker"].map(norm_ticker); q["_sense"] = q["Transaction"].map(norm_sense)
    q["_d"] = pd.to_datetime(q["Traded"], errors="coerce").dt.date
    QK = set(zip(q["BioGuideID"], q["_tk"], q["_d"], q["_sense"]))
    QK3 = set(zip(q["BioGuideID"], q["_tk"], q["_sense"]))

    def _cls(r):
        if r["_tk"] == "":
            return "non_equity"
        if (r["bioguide_id"], r["_tk"], r["_d"], r["_sense"]) in QK:
            return "exact_match"
        if (r["bioguide_id"], r["_tk"], r["_sense"]) in QK3:
            return "date_mismatch"
        return "no_match"

    d["match_class"] = d.apply(_cls, axis=1)

    def _agg(df, dim):
        g = df.groupby([dim, "match_class"]).size().unstack(fill_value=0)
        for c in ("exact_match", "date_mismatch", "no_match", "non_equity"):
            if c not in g.columns:
                g[c] = 0
        g["total"] = g[["exact_match", "date_mismatch", "no_match", "non_equity"]].sum(axis=1)
        eq = g["exact_match"] + g["date_mismatch"] + g["no_match"]
        g["quiver_has_pct"] = (100 * (g["exact_match"] + g["date_mismatch"]) / eq.where(eq > 0)).round(1)
        return g.reset_index()[[dim, "exact_match", "date_mismatch", "no_match", "non_equity", "total", "quiver_has_pct"]]

    by_asset = _agg(d.assign(asset_type=d["asset_type"].fillna("(inconnu)")), "asset_type")
    by_cluster = None
    if cluster_map is not None and "doc_id" in d.columns:
        d["cluster"] = d["doc_id"].map(cluster_map)
        sub = d.dropna(subset=["cluster"])
        if len(sub):
            by_cluster = _agg(sub, "cluster")
    return by_asset, by_cluster
