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
