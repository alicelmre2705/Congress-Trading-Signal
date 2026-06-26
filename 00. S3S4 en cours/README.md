# 00. S3S4 en cours — Recherche stratégie (Semaines 3-4)

**Recherche / premier jet — ISOLÉ.** On **lit** les données du dépôt, on **n'écrit que dans ce dossier**
(aucun impact sur le travail finalisé des Semaines 1-2 ni sur les golden).

## Le récit est dans 4 NOTEBOOKS (code + résultat + raisonnement, côte à côte)
- **`00_exploration.ipynb`** — *montrer la recherche : chaque chiffre, reproduit ou sourcé.* Recalcule sur
  Quiver 2014+ tous les nombres des analyses préliminaires (mix, latence, CAR, slices, persistance, dilution)
  + **audit de complétude** (aucun chiffre orphelin ; **3 divergences assumées** vs les calculs agents FINAL).
- **`03_strategie_ramify.ipynb`** — **LE livrable.** Construit la stratégie *spécifiée par Ramify* : sélection
  annuelle rolling de K congressmen (Sharpe rétréci + UCB + commissions clés), **walk-forward V1 actions & V2
  ETF** vs SPY/RSP/60-40, **grille K + Deflated Sharpe**, **track records individuels**, métriques niveau-trade,
  checklist De Prado, verdict + **cadrage produit**. → V1 sous-performe ; **V2 ≈ beta thématique dé-risqué**.
- **`01_backtest.ipynb`** — *« suivre le Congrès » bat-il le marché net de coûts ?* 9 variantes → **pas d'edge net.**
- **`02_chasse_au_signal.ipynb`** — *recherche objective de signal* (6 angles : IC · event-study · long-short ·
  commission · caractéristiques · ML). **→ Info faible mais réelle (*breadth* d'achat), sous le seuil d'exploitabilité.**

**Synthèse pour l'équipe QIS : `04_note_recherche.md`** (méthodo, résultats, limites, recommandation).

Les sorties sont **déjà exécutées et sauvegardées** dans les notebooks → lisibles tels quels (présentables),
et **relançables** (kernel *S3S4 (.venv)*, tout tourne sur le cache de prix).

## Moteur réutilisable (importé par les notebooks — pas de duplication)
| Module | Rôle |
|---|---|
| `data.py` | journal des transactions Quiver (2014+), normalisé |
| `prices.py` | prix yfinance + facteurs Fama-French, **cache** (`cache/`, gitignoré) |
| `portfolio.py` | moteur event-driven (entrée `filed`+1), rendements **nets de coûts** |
| `evaluate.py` | alpha FF-Carhart, Deflated Sharpe, OOS, `nw_tstat`, `car_event`, `trade_returns`/`trade_stats` |
| `variants.py` | conviction-cluster, dé-concentration par membre |
| `leadership.py` | leadership de parti (point-in-time) + chairs de commission |
| `selection.py` | **sélection annuelle rolling** (Sharpe rétréci Mauboussin + UCB + commissions clés), V2 ticker→ETF |

## Contexte & sources (documentaire)
- **`STRATEGIE_ANALYSE.md`** — littérature académique + produits réels (NANC/KRUZ, Quiver…) + « pourquoi
  le hype », avec URLs. C'est le complément *non empirique* des notebooks.
- **`PROMPT_RECHERCHE_S34.md`** — prompt autonome de (re)construction du book.
