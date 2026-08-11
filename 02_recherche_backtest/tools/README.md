# tools/ — le moteur de la lignée « titre », pour la suite

**À quoi ça sert.** Démarrer une nouvelle strate de recherche (une « strate 8 ») sans recopier le
notebook 16 : chargement de la table clean, prix, calendrier conforme, moteur M3 (score, plafond
par remplissage de niveau, parts figées, frein, coût), purge FIFO, boîte de mesure (bilan, IC,
quatre facteurs, α/β glissants) et compteur de multiplicité `ESSAIS`.

**Qui l'utilise.** Les deux notebooks **vivants** de `3_livrable_M3/` :
`M3_preuve_complete.ipynb` (le nb 16, génération 2 du 11/08 — socle importé d'ici, toutes ses
validations conservées, ré-exécuté en entier : mêmes ancres) et `M3_table_pipeline.ipynb` (la
table courante). Les notebooks aux **sorties figées** (lignée membre, les trois volets du 11)
n'importent pas ce paquet et ne le feront pas : ils sont autonomes par doctrine (voir
`../README.md` §6 — deux lignées, deux alphas, des oracles qui valent parce qu'ils
réimplémentent). Dans ce README, « notebook 16 » = `M3_preuve_complete.ipynb` (renommé le 11/08).

**La preuve.** `test_ancres` rejoue M3 depuis la table clean et asserte les ancres gelées de
`FICHE_M3`. Exécuté le 2026-08-11 :

```
$ cd 02_recherche_backtest && ../.venv/bin/python -m tools.test_ancres
flux 113,369 opérations · 350 membres · 2,755 titres · calendrier 3,645 j · 149 coupes dès 2014-02-28
M3 · NANC    excès +3.40 %/an (t 1.61) · NAV 661.57 · 9/13
M3 · GOP     excès +1.24 %/an (t 1.61) · NAV 573.57 · 9/13
M3 · UNIQUE  excès +2.51 %/an (t 1.93) · NAV 629.09 · 8/13
✅ ANCRES REPRODUITES — le paquet tools est bien le moteur du notebook 16
```

(≈ 9 s ; exige les caches locaux non versionnés `cache/prices_v2/` et `cache/ff_factors.csv` —
ils se reconstruisent via yfinance et la Kenneth French Data Library.)

**Démarrage type :**

```python
from tools.donnees import charger
from tools import moteur, mesure

D  = charger()
WP = moteur.cibles(D, "Democrat")            # ou None : le portefeuille unique
nav, rotations = moteur.run_livre(D, WP, cout_bps=10.0)
print(mesure.bilan(D, nav, "mon essai"))     # ← s'ajoute au compteur ESSAIS : tout essai se publie
```

**Deux conventions à connaître avant d'écrire un chiffre** : l'α de `mesure` est un Jensen en
excès du taux sans risque, annualisé ×252 (la convention de la lignée titre — la lignée membre
mesure autre chose) ; et `gamma_purge(D, seuil)` exige son seuil **explicitement** (504 j au
nb 11, 756 j au nb 16 : c'est un résultat de recherche, pas un défaut de fonction).
