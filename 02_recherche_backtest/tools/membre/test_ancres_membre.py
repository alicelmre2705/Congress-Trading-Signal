"""LA PREUVE du paquet membre : rejouer le socle sur la table courante et retrouver l'entonnoir.

Ancres re-certifiées le 2026-08-12 — la table clean du pipeline est désormais PROPRE au sens
plein (entonnoir A→F : fenêtre 2013-2026 et couverture prix remontées dans le pipeline) :
    clean = exploitable : 118 316 trades · 3 286 tickers couverts · 0 jeté au chargement · 359 membres
    𝒯^brut (fenêtré avant prix, lu dans la table BRUTE, verdicts ∅+F) : 134 417 · 372 · 4 607
    membres : 266 reconstruits · 223 éligibles
(le déplacement des filtres ne change AUCUN périmètre — tableaux dans PISTES_TESTEES.md)

Usage :  cd 02_recherche_backtest && ../.venv/bin/python -m tools.membre.test_ancres_membre
(exige le cache local non versionné cache/prices_v2/)
"""
import pandas as pd

from . import donnees, moteur


def main():
    M = donnees.charger_membre()
    assert len(M.dfb) == 134_417 and M.dfb.bioguide_id.nunique() == 372 \
        and M.dfb.ticker.nunique() == 4_607, "𝒯^brut (table brute, fenêtré) a bougé"
    assert len(M.df) == len(M.dfx) == 118_316, \
        f"exploitables = {len(M.df):,} ≠ 118 316 — l'entonnoir du pipeline a bougé"
    assert M.n_jetes == 0, f"{M.n_jetes:,} trades jetés au chargement — la clean n'est plus couverte-prix"
    assert len(M.need) == 3_286 and not M.corrompus, "couverture prix dégradée"
    assert M.df.bioguide_id.nunique() == 359

    wf_ret, wf_traded = moteur.series_membres(M, verbose=False)
    assert len(wf_ret) == 266, f"membres reconstruits = {len(wf_ret)} ≠ 266"
    tab = pd.DataFrame([dict(n_trades=len(wf_traded[b]), n_days=len(r)) for b, r in wf_ret.items()])
    elig = int(((tab.n_trades >= 10) & (tab.n_days >= 126)).sum())
    assert elig == 223, f"éligibles = {elig} ≠ 223"

    tables = donnees.DOSSIER / "tables"
    membres = pd.read_csv(tables / "membres.csv")
    assert int(membres["n_trades"].fillna(0).sum()) == 118_316, "tables/ désynchronisées du socle"

    print("✅ ANCRES MEMBRE REPRODUITES — la table clean EST le périmètre exploitable :")
    print("   118 316 trades · 3 286 tickers · 0 jeté · membres 359/266/223 · tables/ cohérentes")


if __name__ == "__main__":
    main()
