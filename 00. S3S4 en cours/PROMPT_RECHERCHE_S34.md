# PROMPT — Book de recherche stratégie (Semaines 3-4)

> **Prompt autonome.** À exécuter dans une **session fraîche** depuis le dépôt
> `/Users/lemairealice/Downloads/Jupiter`. Il construit un **book de recherche backtest** des stratégies
> de copy-trading du Congrès sur l'historique **Quiver 2014+**, **entièrement dans le dossier `S3S4/`**
> (où se trouve déjà ce prompt et l'analyse `S3S4/STRATEGIE_ANALYSE.md`), **sans jamais modifier le travail
> finalisé des Semaines 1-2**. Tout ce qui suit est auto-suffisant : un exécutant sans mémoire de la
> conversation d'origine doit pouvoir le réaliser.

## Règles d'or (NON négociables)
1. **ISOLATION** — tu écris **UNIQUEMENT dans `S3S4/`**. Tu peux **LIRE** le reste du dépôt
   (`data/`, `congress_core/`…) mais **ne modifie/supprime JAMAIS** un fichier hors `S3S4/` — surtout pas
   les golden (`tests/regression/*golden*`), les tables `*_FINAL.csv`, `congress_core/`, ni `docs/`. Aucune
   migration de données finalisées.
2. **Recherche / premier jet** — code exploratoire assumé, mais propre et reproductible ; pas de golden global.
3. **Honnêteté** — le but est de **mesurer un edge NET**, pas de « prouver » une stratégie. Rapporte les
   résultats même (surtout) s'ils sont ≈ 0 / négatifs.
4. **Environnement** — `.venv/bin/python` (Python 3.12). Ajoute au besoin `pandas_datareader` (facteurs
   Fama-French) et `statsmodels` ; `matplotlib` est déjà installé. Ne commite rien sans demande explicite.

## Contexte — résultats DÉJÀ établis (pour orienter, NE PAS refaire)
Détails et provenance dans **`S3S4/STRATEGIE_ANALYSE.md`**. En résumé (event-study sur les données du
dépôt + littérature + produits + GitHub/presse) :
- **Edge agrégé net ≈ 0** post-STOCK Act (NBER w35041, Chen & Sacerdote 2026 : les trades du Congrès
  « suivent » le sentiment retail, pas en anticipation). Achats : CAR 12 m **+1,5 % moyen mais médiane
  NÉGATIVE**, < 46 % gagnants, alpha = décile supérieur (loterie à queue droite).
- **Pondération par TAILLE/conviction = seul signal pré-coûts** : mini-backtest portefeuille
  **size-weighted ≈ +233 bps vs SPY pré-coûts**, mais **≈ −255 bps NET** (turnover ~6 rotations/an à
  20 bps) ; l'equal-weight sous-performe. → la variante **size/conviction est LE candidat** à tester.
- **Pas de persistance OOS** : top-K membres 2020-22 → renversement 2023-25 (la sélection par perf passée
  ne tient pas). **Filtre « commissions clés » contre-productif** (+1,08 % vs +2,09 % hors commissions).
- **V2 ETF sectoriel dilue 70-80 %** de l'edge (idiosyncratique). **Stars (Pelosi/Wyden) = beta tech**
  (Mag 7), pas alpha. **Hype = data/récit**, pas alpha net (ETF NANC ≈ marché, KRUZ sous-perf ; backtests
  Quiver/GovGreed excluent coûts/survivorship/look-ahead).

**Mission** : confirmer/chiffrer tout cela **PROPREMENT sur l'historique long (2014+), NET de coûts**, et
dire honnêtement si une construction survit.

## Donnée : historique Quiver 2014+ (DÉJÀ en cache local, aucune clé API)
Les caches Quiver embarqués couvrent **2012/2014 → 2026** (~10-12 ans). Jeu **principal** du backtest :
- `data/house/tables/_quiver_house_cache.csv` (**100 333 lignes**, `filed` 2014→2026) +
  `data/senate/reference/_quiver_senate_cache.csv` (**13 342 lignes**, `filed` 2014→2026).
- Colonnes : `BioGuideID`, `Ticker`, `Transaction` (Purchase/Sale), `traded`, **`filed` (= divulgation →
  ENTRÉE sans look-ahead)**, **`Trade_Size_USD` (taille réelle $ → pondération conviction)**, `Party`.
- **Validé** : concorde avec l'extraction finalisée (audit Quiver Semaines 1-2). Charge-les en **lecture
  seule** (tu peux en dupliquer une copie dans `S3S4/data/` si pratique, sans toucher l'original).
- Source **secondaire** (optionnelle) : tables FINAL 2020-2026 (`data/house/tables/*/06_house_*_FINAL.csv`,
  `data/senate/*/06_senate_*_FINAL.csv`) — ajoutent les trades papier OCR absents de Quiver.

## Principe directeur : traiter en *first-class* les 4 tueurs d'edge
1. **Coûts & turnover** — modèle bid-ask + impact + commission, paramétrable (retail ~20 bps / instit
   ~5-10 bps) ; drag annualisé rapporté (turnover ≈ 6 rotations/an → ~5 %/an à 20 bps).
2. **Survivorship** — **univers point-in-time** : inclure les tickers délistés (sortie à la dernière
   cotation / radiation), ou a minima auditer et borner la part de positions sur délistés (le PoC excluait
   ATVI/WBA/SQ → +1-3 % CAGR fictifs).
3. **Look-ahead** — entrée stricte à `filed` (date de divulgation) **+ T+1 ouvré** ; aucune donnée future.
4. **Ajustement factoriel** — alpha vs SPY brut **ET** vs **Fama-French-Carhart + secteur** (isoler le
   beta tech qui explique 80-90 % des « stars »).

## Architecture (tout dans `S3S4/`)
- `S3S4/data.py` — charge les **caches Quiver 2014+** (House+Sénat), construit le journal de signaux :
  (`BioGuideID`, `Ticker`, `filed`, `traded`, `Transaction`, `Trade_Size_USD`, `Party`). Peut LIRE
  `congress_core` si utile ; option de greffer le FINAL OCR-only.
- `S3S4/prices.py` — yfinance + **facteurs Ken French** (CSV/pandas_datareader), **cache prix dans
  `S3S4/cache/`** ; splits (auto_adjust) ; gestion/borne des délistés (anti-survivorship).
- `S3S4/portfolio.py` — moteur **event-driven** : ouvre à `filed`+1 ouvré, ferme à la vente correspondante
  ou à l'horizon H ; pondérations **equal / size (`Trade_Size_USD`) / conviction-cluster** ; **cap par
  membre** ; série de rendements **nette de coûts**.
- `S3S4/evaluate.py` — CAGR, **alpha + t corrigé** (calendar-time), Sharpe **et Deflated Sharpe**, max DD,
  turnover, hit rate, capacité ; **régression factorielle** ; **train/test + purged CV + PBO**.
- `S3S4/variants.py` — V0 baseline Ramify / **V1 size-weight (prioritaire)** / conviction-cluster (≥ N
  membres en 30 j) / grille d'horizons 1-6 m / **V2 substitution ETF** (dilution).
- `S3S4/report.py` → **`S3S4/RAPPORT_STRATEGIE.md`** + figures (equity curve **net** vs SPY, waterfall
  **brut→net**, alpha par variante, factor loadings).
- `S3S4/tests/` — **no-look-ahead**, reproduction du PoC (size-weight ≈ +233 bps pré-coûts ; event-study
  12 m ≈ +1,5 %), cache prix idempotent. **Tests LOCAUX** — n'impactent pas `tests/regression`.
- `S3S4/README.md` — but, données (Quiver 2014+), nature exploratoire, règle d'isolation.

## Séquencement
1. `data` + `prices` (+ cache) — fondations ; vérifier la couverture prix & la part de délistés.
2. `portfolio` + coûts/turnover — **reproduire +233 bps pré-coûts**, puis appliquer les coûts → net.
3. `evaluate` (factoriel + Deflated Sharpe + OOS) — le cœur « honnête ».
4. `variants` (size/conviction d'abord, puis V2 dilution).
5. `report` + tests.

## Décisions actées (issues de l'analyse)
- **Pondération taille/conviction prioritaire** (l'equal-weight sous-performe même pré-coûts).
- **Exit ~4-6 mois** (médiane réelle ~123 j), grille testée ; **pas 12 par défaut**.
- **Cap par membre** (Khanna ≈ 40 % des achats).
- **Benchmark factor-ajusté + Deflated Sharpe partout** ; **univers point-in-time obligatoire**.
- **V1 actions d'abord** ; **V2 ETF** = mesure de la dilution (attendue ~70-80 %).
- **Fenêtre historique 2014/2016 → 2026** (données Quiver locales) : plus de régimes → OOS crédible
  (in-sample début de période, test sur les années récentes).
- **Isolation stricte** : tout dans `S3S4/`, lecture seule du finalisé, aucun golden impacté.

## Dépendances à ajouter
`pandas_datareader` (ou CSV Ken French) pour les facteurs ; `yfinance` déjà présent ; documenter le biais
survivorship si aucune source de délistés n'est ajoutée.

## Verdict attendu & honnêteté
Attendu : edge brut faible (size/conviction), **net ≈ 0 / négatif** après coûts + facteurs ; V2 dilue.
Conclusion vendable à Ramify : la valeur d'un produit « Congrès » = **data/signal/transparence**, pas
l'alpha pur. Si une variante survit *net* (peu probable, possible sur un sous-ensemble), l'isoler et la
stress-tester (Deflated Sharpe, OOS, capacité).

## Vérification
- Tests no-look-ahead + reproduction du PoC + cache prix idempotent.
- L'equity curve **nette** reproduit le passage +233 bps pré-coûts → ~SPY/négatif net.
- Deflated Sharpe & OOS rapportés **pour chaque variante** (le renversement train/test doit apparaître).
