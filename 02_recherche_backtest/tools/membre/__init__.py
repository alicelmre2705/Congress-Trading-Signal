"""tools.membre — le moteur de la famille « MEMBRE » (copier les élus), extrait des notebooks
copier_les_membres et tables_membres_tickers (génération 2, 2026-08-11).

⚠️ CONVENTIONS DE LA FAMILLE MEMBRE — ne JAMAIS mélanger avec tools.{moteur,mesure} (famille titre) :
  α = régression du rendement BRUT sur le SPY brut (pas de taux sans risque), annualisation
  GÉOMÉTRIQUE (1+α)^252−1 ; « excès » = écart de CAGR sur la fenêtre commune ; t de l'appraisal
  = appraisal·√(n/252). La famille titre mesure un Jensen en excès du RF, ×252 arithmétique :
  les chiffres ne sont pas comparables.

Usage :
    from tools.membre import donnees, moteur, mesure
    M = donnees.charger_membre()            # la table clean du pipeline (ou table="v1")
    wf_ret, wf_traded = moteur.series_membres(M)
    mesure.alpha_beta(M, wf_ret[bid])
"""
from . import donnees, moteur, mesure  # noqa: F401
