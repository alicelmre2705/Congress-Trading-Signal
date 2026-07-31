# Livraison backtest — données de trading du Congrès (Chambre)

**Pour un backtesteur qui reçoit cette donnée.** Transactions boursières déclarées par les élus de la
Chambre des représentants, extraites, nettoyées, vérifiées, et prêtes à backtester. House 2013-2026.

---

## 1 · Par où commencer

**Le fichier d'entrée = `flux_backtest.csv`** (129 538 transactions, dédupliquées, avec cours).
Chaque ligne : un membre achète/vend un ticker, à une date, pour un montant.

- **Deux dates par ligne**, au choix selon le réalisme voulu :
  - `traded` = **date de l'opération** → borne haute (le trade est connu instantanément — irréaliste).
  - `disclosure_date` = **date de publication** → réaliste (le public l'apprend ~27 j après pour le fil
    de l'eau, ~1 an après pour les rapports annuels). `delai_divulgation_j` donne l'écart.
- **Montant** : `size_usd` = milieu de la fourchette déclarée (jamais un montant exact — la loi n'exige
  qu'une tranche).
- Pour initialiser un portefeuille au patrimoine réel du membre : `portefeuilles_entree.csv` +
  les positions `../cache/tables/11_holdings_complets.csv`.

> ⚠ **Ne pas** backtester sur `04_transactions_v1.csv` (brut) : il contient **58 214 doublons**
> (même trade re-déclaré dans plusieurs documents). `flux_backtest.csv` est la version propre.

---

## 2 · Ce qu'il y a dans ce dossier

| fichier | quoi | où |
|---|---|---|
| `flux_backtest.csv` | **l'entrée** — 129 538 transactions propres, 2 dates | *ici* (à générer, voir §5) |
| `portefeuilles_entree.csv` | 284 portefeuilles de départ | *ici* |
| `registre_membres.csv` | 900 membres, trajectoires | *ici* |
| `tickers_couverts.csv` | 6 552 tickers avec cours (le tradeable) | *ici* |
| `DICTIONNAIRE.md` | **chaque colonne de chaque fichier** (type, sens, clé) | *ici* |
| `SYNTHESE_EXTRACTION_HOUSE.pdf` | la **certification qualité** (propre / complet / backtestable) | *ici* |
| transactions brutes (166 149, tous types) | `04_transactions_v1.csv` | `../cache/tables/` |
| positions Schedule A (420 916, C/H/O/A/T) | `11_holdings_complets.csv` | `../cache/tables/` |
| séries de cours (`TICKER.csv`) | | `../../02_recherche_backtest/cache/prices_v2/` |

*(Les deux grosses tables et les séries de cours ne sont pas dupliquées ici — elles sont déjà dans le
dépôt, documentées dans `DICTIONNAIRE.md`.)*

---

## 3 · Comment c'est construit (en un coup d'œil)

De 900 membres et 6 types de dépôts → un flux de 129 538 transactions chez 408 membres, en 9 étapes :
le membre **dépose** (photo d'entrée H/C, déclaration rapide P, rapport annuel O, sortie T) → deux
sections (**Schedule A** = positions, **Schedule B** = transactions) → on **rassemble / trie / valorise**
(seul ce qui a un cours entre) → on **reconstruit** en portefeuilles de parts → on **vérifie**.
**Le récit complet est dans `../SYNTHESE_EXTRACTION_HOUSE.pdf` (4 p.) et `../FICHE_DONNEES_HOUSE.pdf` (5 p.).**

---

## 4 · Limites connues (à respecter dans un backtest)

- **Horloge** : reconstruit à la date d'opération = borne haute. Pour du réaliste, rejouer sur
  `disclosure_date` (données prêtes, 2 dates dans le flux).
- **Départ** : 166 des 408 membres ont un portefeuille d'entrée connu ; **242 partent de zéro**.
- **Prix** : **12,1 %** des lignes déclarées n'ont aucun cours (1 234 tickers) — **confirmé réel** (re-test).
- **Échantillon** : **11 années** civiles → écart minimal détectable **4,6 %/an** (un edge plus petit est invisible).
- **Montants** : fourchettes, jamais au dollar près.

*(Détail chiffré + feux 🟢🟡🔴 dans `SYNTHESE_EXTRACTION_HOUSE.pdf`.)*

---

## 5 · Reproduire / regénérer

Tout se régénère en ré-exécutant `../Portefeuilles_House_Complet.ipynb`.
Pour produire `flux_backtest.csv` : lancer la cellule **`add2dates2026`** (elle écrit
`flux_house_2dates.csv` et s'auto-vérifie : taille = 129 538, délais 27/374/393 j). Déposer le CSV ici.

---

## 6 · Pourquoi c'est fiable

- les 5 tables de départ sont **gelées** (empreinte sha256 conforme au manifeste) ;
- la population est re-croisée au référentiel officiel des mandats : **98,9 %** de concordance ;
- **chaque cascade** est vérifiée par un `assert` (la somme doit boucler, sinon le notebook s'arrête) ;
- la classe d'un actif est décidée **avant** tout prix (pas de fonds déguisé en action) ;
- la reconstruction est **jugée** par des positions déclarées qui n'ont jamais servi à la construire :
  rappel médian **9 → 57 %** ;
- **aucun chiffre écrit en dur** — tout se régénère.
