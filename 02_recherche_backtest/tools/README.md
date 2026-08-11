# tools/ — les moteurs des deux familles de recherche

Deux sous-ensembles aux **conventions incompatibles**, jamais mélangés :
la racine du paquet (`donnees`, `moteur`, `mesure`, `etf`, `poches`) porte la famille **titre**
(M3) ; le sous-paquet [`membre/`](membre/__init__.py) porte la famille **membre** (copier les
élus) — α brut annualisé en géométrique côté membre, Jensen en excès du taux sans risque ×252
côté titre. Chaque famille a sa preuve : `python -m tools.test_ancres` (titre, table v1) et
`python -m tools.membre.test_ancres_membre` (membre, table courante). Les notebooks vivants qui
les importent : `3_livrable_M3/` (titre) ; `tables_membres_tickers` et
`1_copier_les_membres/copier_les_membres` (membre, génération 2 du 11/08 — le socle importé
consomme les colonnes du pipeline, plus aucun re-nettoyage local ; seuls les prix restent
nettoyés côté recherche, le pipeline ne les possède pas).

## La famille titre — pour la suite

**À quoi ça sert.** Démarrer une nouvelle étape de recherche sans recopier `M3_preuve_complete` :
chargement de la table clean, prix, calendrier conforme, moteur M3 (score, plafond
par remplissage de niveau, parts figées, frein, coût), purge FIFO, boîte de mesure (bilan, IC,
quatre facteurs, α/β glissants) et compteur de multiplicité `ESSAIS`.

**Qui l'utilise.** Les deux notebooks **vivants** de `3_livrable_M3/` :
`M3_preuve_complete.ipynb` (génération 2 du 11/08 — socle importé d'ici, toutes ses
validations conservées, ré-exécuté en entier : mêmes chiffres témoins) et
`M3_table_pipeline.ipynb` (la table courante). Les notebooks aux **sorties figées** (la famille
membre, les trois volets de `2_noter_les_titres/`) n'importent pas ce paquet et ne le feront
pas : ils sont autonomes par doctrine (voir `../PISTES_TESTEES.md`, « la doctrine » — deux
familles, deux alphas, des recalculs de contrôle qui valent parce qu'ils réimplémentent).

**La preuve.** `test_ancres` rejoue M3 depuis la table clean et vérifie les *ancres* — les
chiffres témoins gelés de `FICHE_M3`. Exécuté le 2026-08-11 :

```
$ cd 02_recherche_backtest && ../.venv/bin/python -m tools.test_ancres
flux 113,369 opérations · 350 membres · 2,755 titres · calendrier 3,645 j · 149 coupes dès 2014-02-28
M3 · NANC    excès +3.40 %/an (t 1.61) · NAV 661.57 · 9/13
M3 · GOP     excès +1.24 %/an (t 1.61) · NAV 573.57 · 9/13
M3 · UNIQUE  excès +2.51 %/an (t 1.93) · NAV 629.09 · 8/13
✅ ANCRES REPRODUITES — le paquet tools est bien le moteur de M3_preuve_complete
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
excès du taux sans risque, annualisé ×252 (la convention de la famille titre — la famille membre
mesure autre chose) ; et `gamma_purge(D, seuil)` exige son seuil **explicitement** (504 j dans
`noter_les_titres`, 756 dans `M3_preuve_complete` : c'est un résultat de recherche, pas un
défaut de fonction).
