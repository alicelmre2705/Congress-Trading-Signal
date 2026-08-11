"""tools — le moteur de la lignée « titre », extrait du notebook 16, POUR LA SUITE.

Ce paquet n'est importé par AUCUN des six notebooks de recherche : ils restent autonomes
(doctrine du dépôt — voir le README du dossier, §6). Il existe pour la strate suivante :
un nouveau chantier démarre en important ceci au lieu de recopier le nb 16.

La preuve que ce code est bien celui du livrable : `python -m tools.test_ancres`
(lancé depuis `02_recherche_backtest/`) rejoue M3 depuis la table clean et asserte
les ancres gelées de FICHE_M3 — NAV 661,57 / 573,57, excès +3,40 / +1,24, unique +2,51.

    from tools.donnees import charger
    from tools import moteur, mesure

    D  = charger()                                   # table clean + prix + calendrier + facteurs
    WP = moteur.cibles(D, "Democrat")                # M3 : un jeu de poids par coupe
    nav, rot = moteur.run_livre(D, WP)
    print(mesure.bilan(D, nav, "mon run"))

Conventions héritées de la lignée titre (et DITES ici parce qu'elles ne sont pas universelles) :
α = Jensen en excès du taux sans risque, annualisé ×252 (arithmétique) ; excès = moyenne des
écarts d'années civiles au SPY ; la lignée « membre » (05b/07/09/12) mesure AUTRE CHOSE.
"""
from . import donnees, moteur, mesure, etf, poches  # noqa: F401
