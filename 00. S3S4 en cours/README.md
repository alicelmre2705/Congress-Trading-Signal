# 00. S3S4 en cours — Book de recherche stratégie (Semaines 3-4)

**Recherche / premier jet — ISOLÉ.** Ce dossier backteste des stratégies de copy-trading du Congrès.
Il **lit** les données du dépôt (caches Quiver, `congress_core`) mais **n'écrit que dans ce dossier** —
aucun impact sur le travail finalisé des Semaines 1-2 ni sur les golden.

## Contenu
- `STRATEGIE_ANALYSE.md` — note d'analyse (chiffres tracés à leur source).
- `PROMPT_RECHERCHE_S34.md` — prompt autonome de construction du book.
- `data.py` — journal des transactions depuis les caches Quiver (2014+).
- `prices.py` — prix yfinance + facteurs Fama-French, cache disque (`cache/`, gitignoré).
- `portfolio.py` — moteur event-driven, série de rendements **nette de coûts**.
- `evaluate.py` — alpha factoriel (FF-Carhart), Deflated Sharpe, OOS.
- `variants.py` — filtres/pondérations (conviction-cluster, dé-concentration par membre).
- `run.py` — orchestre les variantes → `RAPPORT_STRATEGIE.md` + `figures/`.

## Lancer
```
.venv/bin/python "00. S3S4 en cours/run.py"
```
(Le 1er run télécharge ~1500 tickers dans `cache/` ; ensuite c'est instantané.)

## Analyses du signal (code reproductible)
`analyses/` contient **un script documenté par angle** cherchant activement de l'information
(IC, event-study, long-short, commission, caractéristiques de trade, ML) — voir `analyses/README.md`.
Chacun se relance en < 2 min sur le cache. C'est le code derrière chaque conclusion (pas de boîte noire).

## Verdict (2014-2026, net de coûts, factor-ajusté)
**Pas d'edge net exploitable.** Le backtest (9 variantes) ne dégage aucun alpha significatif
(`RAPPORT_STRATEGIE.md`). La chasse au signal (`analyses/`) trouve une **information faible mais réelle**
(la *breadth* d'achat, IC≈0,02) — mais **sous le seuil d'exploitabilité** net de coûts. Synthèse complète
dans `STRATEGIE_ANALYSE.md` §6.
