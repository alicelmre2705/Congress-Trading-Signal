# Note de recherche — Stratégie « copy-trading du Congrès » (S3-4)

> **Destinataire : équipe QIS Ramify.** Cette note résume une stratégie **construite et backtestée selon la
> spécification Ramify**, avec ses chiffres honnêtes. Elle ne tranche pas « ça marche / ça ne marche pas » :
> elle livre la stratégie + les nombres + les limites pour que Ramify décide. La **source de vérité** de
> chaque chiffre est le code exécuté des notebooks ; cette note les cite, elle ne les remplace pas.
>
> | | |
> |---|---|
> | **`00_exploration.ipynb`** | trace/recalcule chaque chiffre des analyses préliminaires + **audit de complétude** (aucun chiffre orphelin ; 3 divergences assumées) |
> | **`01_backtest.ipynb`** | 9 variantes génériques « suivre le Congrès » net de coûts |
> | **`02_chasse_au_signal.ipynb`** | 6 angles de recherche de signal (IC, event-study, long-short, commission, ML…) |
> | **`03_strategie_ramify.ipynb`** | **LE livrable** : la stratégie spécifiée (sélection annuelle K, V1+V2, walk-forward, métriques, track records) |
> | `selection.py` · `data/prices/portfolio/evaluate/variants/leadership.py` | moteur réutilisable importé |

## 1. Méthodologie (ce qu'on a construit, fidèle à la spec)
- **Données** : caches Quiver **2014→2026** (House `_quiver_house_cache.csv`, Sénat `_quiver_senate_cache.csv`),
  113 675 transactions / 56 877 achats / 251 membres. *(Le pré-2020 papier OCR n'est pas inclus — coûteux en
  crédits ; les FINAL 2020-26 servent aux commissions/secteurs.)*
- **Entrée** = `disclosure_date` (`filed`) **+1 jour ouvré** (aucun look-ahead). **Sortie** = vente
  correspondante (même membre+ticker) sinon **+12 mois**.
- **Sélection annuelle rolling** : fin d'année Y, éligibles = membres ≥10 trades ; score = **Sharpe de leurs
  trades RÉTRÉCI vers la moyenne du groupe** (Mauboussin / James-Stein, anti-chance) **+ exploration UCB1** ;
  on prend **K** dont **≥ la moitié en commission clé** (Finance / Defense / Intelligence) ; on suit LEURS
  achats l'année **Y+1**. Walk-forward 2016→2026, rebalance annuel.
- **V1** = actions ; **V2** = on remplace chaque action par son **ETF SPDR sectoriel** (GICS→SPDR), logique
  identique. Coûts **20 bps one-way nets**. Benchmarks : **SPY**, **RSP** (équipondéré), **60/40** (SPY+AGG).
- **Anti-biais De Prado** : look-ahead réglé · survivorship borné · **Deflated Sharpe comptant les 8 configs
  de la grille K×version** · walk-forward · coûts inclus.

## 2. Résultats (K = 6, walk-forward net ; détails dans `03`)
| Stratégie | CAGR | Sharpe | max DD | alpha FF-Carhart | vs SPY (CAGR) |
|---|---|---|---|---|---|
| **V1 actions** (size, net) | **3,9 %** | 0,28 | −71 % | −2,9 %/an (t=−0,5, n.s.) | **−10,2 pts** |
| **V2 ETF sectoriel** | **8,8 %** | 0,58 | −33 % | **+0,15 %/an (t=0,05 ≈ 0)** | −5,3 pts |
| SPY (cap-weight) | 14,1 % | 0,86 | −34 % | — | 0 |
| RSP (equal-weight) | 11,7 % | 0,72 | −39 % | — | −2,4 pts |
| 60/40 (SPY+AGG) | 9,5 % | 0,91 | −22 % | — | −4,6 pts |

**Grille K ∈ {4,6,8,10}** : plus K est **grand** (moins on « sélectionne »), plus on **converge vers le
marché** — V1 passe de 5,2 % (K=4) à 15,0 % (K=10, alpha +0,85 %, Sharpe 0,78 < SPY 0,86). **Deflated
Sharpe** de la meilleure config (K=10 V1) = **0,97** : le flux n'est pas un artefact de la grille, **mais**
son Sharpe reste **sous SPY** et son alpha ≈ 0 → c'est du **beta**, pas de l'alpha.

**Track records & métriques niveau-trade** : pas de persistance — top-10 membres in-sample 2020-22
(**+22,8 %**) → OOS 2023-25 (**+3,8 %**, décroissance). Au niveau trade : **hit-rate 45 %**, profit factor
**0,96**, espérance **négative** = loterie à queue droite (l'« alpha » vient de quelques gros gagnants).

## 3. Lecture
1. **La sélection concentrée détruit de la valeur.** « Choisir les bons » par Sharpe passé (même rétréci +
   commissions) sous-performe ; ce n'est qu'en **diluant** (grand K, ou substitution sectorielle V2) qu'on
   **récupère le beta de marché**. La compétence sélectionnée ne persiste pas hors-échantillon.
2. **V2 ETF ≠ alpha, mais expose proprement.** La substitution sectorielle retire l'idiosyncratique — donc
   **aussi les paris perdants** : V2 fait nettement mieux que V1 (Sharpe 0,28 → 0,58, DD −71 % → −33 %,
   alpha ≈ 0) tout en **restant sous SPY**. C'est un **beta thématique dé-risqué**.
3. **Cadrage produit.** Aucun réglage ne bat le marché net. **Mais** une **V2 ETF « thématique Congrès »**
   est *livrable* — exactement le positionnement des ETF **NANC/KRUZ** (~1 Md$ d'encours) : on vend
   **transparence + récit + beta thématique**, pas une promesse d'alpha. La **donnée** (couche Semaines 1-2)
   garde toute sa valeur.

## 4. Limites (à dire franchement)
- **Survivorship** : 2 171/3 797 tickers en cache prix ; **1 626 délistés absents** (yfinance) → tous les
  rendements sont des **bornes hautes** (l'equal-weight « +27 % » de `00` §5 en est un mirage typique).
- **Trou Sénat / pré-2020** : Quiver démarre fin, le papier OCR pré-2020 est exclu → moins de régimes côté
  Sénat, échantillons par membre minces (médiane ~10-40 trades).
- **Commissions point-in-time approximées** : appartenance lue dans les FINAL (mandats récents), pas
  reconstituée année par année → le filtre « commission clé » est un proxy, documenté comme tel.
- **3 divergences vs les chiffres préliminaires** (auditées dans `00` §0) : le filtre commissions n'est
  **pas** contre-productif sur Quiver 2014+ ; le « +233 bps size-weight » **ne réplique pas** (périmètre
  FINAL 2020-26 + survivorship) ; la corrélation action-ETF est **0,7-0,9**, pas 0,5. On les montre, on ne
  les masque pas.
- **Capacité / réglementaire** : portefeuilles minces et concentrés (cap par membre nécessaire) ; risque
  d'interdiction du trading parlementaire 2025-26 qui rendrait le signal caduc.

## 5. Recommandation
- **Ne pas** positionner ceci comme un générateur d'alpha : sur ces données, l'edge net vs SPY est
  **≈ 0 / négatif**, sans persistance.
- **Évaluer la V2 ETF comme produit thématique** (beta « Congrès » transparent, dé-risqué vs V1), à la
  NANC/KRUZ — la décision est commerciale (récit/distribution), pas une question d'alpha.
- **Si poursuite recherche** : tester un univers **point-in-time avec délistés** (tuer le survivorship),
  reconstituer les **commissions année par année**, et explorer le seul signal résiduel identifié en
  `02` — la **breadth d'achat** (IC ≈ 0,02, réel mais sous le seuil d'exploitabilité net de coûts).
