"""LA PREUVE du paquet membre : rejouer le socle sur la table courante et retrouver l'entonnoir.

Ancres re-certifiées le 2026-08-11 (génération 2, table courante du pipeline 134 452 × 39) —
le tableau v1 → courante est consigné dans PISTES_TESTEES.md :
    𝒯^brut 134 417 (fenêtre 2013-2026) · exploitables 118 316 · tickers avec prix 3 286
    membres : 372 bruts · 359 couverts prix · 266 reconstruits · 223 éligibles

Usage :  cd 02_recherche_backtest && ../.venv/bin/python -m tools.membre.test_ancres_membre
(exige le cache local non versionné cache/prices_v2/)
"""
import pandas as pd

from . import donnees, moteur


def main():
    M = donnees.charger_membre()
    assert len(M.dfb) == 134_417, f"𝒯^brut = {len(M.dfb):,} ≠ 134 417 — l'entonnoir a bougé"
    assert len(M.df) == len(M.dfx) == 118_316, f"exploitables = {len(M.df):,} ≠ 118 316"
    assert len(M.need) == 3_286 and M.dfb.bioguide_id.nunique() == 372
    assert M.df.bioguide_id.nunique() == 359

    wf_ret, wf_traded = moteur.series_membres(M, verbose=False)
    assert len(wf_ret) == 266, f"membres reconstruits = {len(wf_ret)} ≠ 266"
    tab = pd.DataFrame([dict(n_trades=len(wf_traded[b]), n_days=len(r)) for b, r in wf_ret.items()])
    elig = int(((tab.n_trades >= 10) & (tab.n_days >= 126)).sum())
    assert elig == 223, f"éligibles = {elig} ≠ 223"

    tables = donnees.DOSSIER / "tables"
    membres = pd.read_csv(tables / "membres.csv")
    assert len(membres) == 372, f"tables/membres.csv : {len(membres)} lignes ≠ 372"
    assert int(membres["n_trades"].fillna(0).sum()) == 118_316, "tables/ désynchronisées du socle"

    print("✅ ANCRES MEMBRE REPRODUITES — le paquet tools.membre est bien le socle de la famille :")
    print("   𝒯^brut 134 417 · exploitables 118 316 · membres 372/359/266/223 · tables/ cohérentes")


if __name__ == "__main__":
    main()
