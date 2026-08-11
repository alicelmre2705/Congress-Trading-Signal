"""LA PREUVE du paquet : rejouer M3 depuis la table clean et retrouver les ancres gelées.

Ancres de FICHE_M3 (annexe A « M3 sur les titres n'a pas bougé » et étape 12) :
    NAV NANC 661,57 · NAV GOP 573,57 (à 0,01 près — les valeurs assertées par le nb 16 lui-même)
    excès NANC +3,40 · GOP +1,24 · UNIQUE +2,51 (t 1,61 · 1,61 · 1,93 ; NAV unique 629)

Usage :  cd 02_recherche_backtest && ../.venv/bin/python -m tools.test_ancres
(exige les caches locaux non versionnés : cache/prices_v2/ et cache/ff_factors.csv)
"""
import numpy as np

from .donnees import charger
from . import moteur, mesure


def main():
    # Les ancres publiées sont adossées à la table V1 du 04/07 (archivée) — la table courante du
    # pipeline a depuis reçu des corrections (NOTE_DIFF_TABLE_CLEAN) qui les déplacent légèrement ;
    # la re-certification sur la table courante est le chantier « Temps 2 ».
    D = charger(table="v1")
    resultats = {}
    for parti, nom in [("Democrat", "NANC"), ("Republican", "GOP"), (None, "UNIQUE")]:
        nav, _ = moteur.run_livre(D, moteur.cibles(D, parti))
        resultats[nom] = mesure.bilan(D, nav, f"M3 · {nom}")
        b = resultats[nom]
        print(f"M3 · {nom:<7} excès {b['excès %/an']:+.2f} %/an (t {b['t']:.2f}) · "
              f"NAV {b['NAV']:.2f} · {b['ann. gagnantes']}")

    attendu = {"NANC": (661.57, 3.40, 1.61), "GOP": (573.57, 1.24, 1.61), "UNIQUE": (None, 2.51, 1.93)}
    for nom, (nav, exc, t) in attendu.items():
        b = resultats[nom]
        if nav is not None:
            assert abs(b["NAV"] - nav) < 0.01, f"{nom} : NAV {b['NAV']:.2f} ≠ {nav} — l'ancre a bougé"
        assert abs(round(b["excès %/an"], 2) - exc) < 0.005, f"{nom} : excès {b['excès %/an']:.2f} ≠ {exc}"
        assert abs(round(b["t"], 2) - t) < 0.005, f"{nom} : t {b['t']:.2f} ≠ {t}"
    assert round(resultats["UNIQUE"]["NAV"]) == 629, \
        f"UNIQUE : NAV {resultats['UNIQUE']['NAV']:.2f}, attendu ≈ 629"

    print("\n✅ ANCRES REPRODUITES — le paquet tools est bien le moteur du notebook 16 :")
    print("   NAV 661,57 / 573,57 · excès +3,40 / +1,24 / +2,51 · t 1,61 / 1,61 / 1,93")


if __name__ == "__main__":
    main()
