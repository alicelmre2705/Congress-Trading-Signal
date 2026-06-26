# 00. S3S4 en cours — Recherche stratégie (Semaines 3-4)

**Recherche / premier jet — ISOLÉ.** On **lit** les données du dépôt, on **n'écrit que dans ce dossier**
(aucun impact sur le travail finalisé des Semaines 1-2 ni sur les golden).

## Le récit est dans 2 NOTEBOOKS (code + résultat + raisonnement, côte à côte)
- **`01_backtest.ipynb`** — *« suivre le Congrès » bat-il le marché net de coûts ?* Données Quiver 2014+ →
  positions → **9 variantes** → tableau + courbe de capital + verdict. **→ Pas d'edge net exploitable.**
- **`02_chasse_au_signal.ipynb`** — *chasse OBJECTIVE au signal* (6 angles : IC · event-study · long-short ·
  commission · caractéristiques · ML), chacun **hypothèse → code → résultat → on garde / on lâche + pourquoi**.
  **→ Information faible mais réelle (la *breadth* d'achat), sous le seuil d'exploitabilité.**

Les sorties sont **déjà exécutées et sauvegardées** dans les notebooks → lisibles tels quels (présentables),
et **relançables** (kernel *S3S4 (.venv)*, tout tourne sur le cache de prix).

## Moteur réutilisable (importé par les notebooks — pas de duplication)
| Module | Rôle |
|---|---|
| `data.py` | journal des transactions Quiver (2014+), normalisé |
| `prices.py` | prix yfinance + facteurs Fama-French, **cache** (`cache/`, gitignoré) |
| `portfolio.py` | moteur event-driven (entrée `filed`+1), rendements **nets de coûts** |
| `evaluate.py` | alpha factoriel FF-Carhart, Deflated Sharpe, OOS, `nw_tstat`, `car_event` |
| `variants.py` | conviction-cluster, dé-concentration par membre |
| `leadership.py` | leadership de parti (point-in-time) + chairs de commission |

## Contexte & sources (documentaire)
- **`STRATEGIE_ANALYSE.md`** — littérature académique + produits réels (NANC/KRUZ, Quiver…) + « pourquoi
  le hype », avec URLs. C'est le complément *non empirique* des notebooks.
- **`PROMPT_RECHERCHE_S34.md`** — prompt autonome de (re)construction du book.
