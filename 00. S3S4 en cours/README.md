# Semaines 3-4 — Stratégie & backtest (Congress Trading Signal)

**Recherche ISOLÉE.** On **lit** les données du dépôt, on **n'écrit que dans ce dossier** (aucun impact sur
le travail finalisé des Semaines 1-2 ni sur les golden). Tout tourne sur le kernel *S3S4 (.venv)* et le cache
de prix local. Les notebooks sont **déjà exécutés** (sorties sauvegardées → lisibles tels quels).

---

## 1. LE LIVRABLE — demandé par Ramify (brief `0.Notion_Ramify.pdf`)

La stratégie *spécifiée* par Ramify, construite section par section, en ses **deux versions** :

| Notebook | Ce qu'il livre |
|---|---|
| **`RAMIFY_V1_actions.ipynb`** | **Version 1 (actions).** Entrée `disclosure_date`+1 / sortie vente-ou-12 mois ; **sélection annuelle des K congressmen** (Sharpe rétréci de la *série de trades* + UCB + ≥ moitié en commission Finance/Defense/Intelligence) ; grille **K∈{4,6,8,10}** + Deflated Sharpe ; métriques Ramify (hit rate, return/trade, Sharpe, **alpha vs SPX** FF-Carhart, profit factor) ; **track records individuels** + persistance. |
| **`RAMIFY_V2_ETF.ipynb`** | **Version 2 (ETF sectoriels).** Même sélection, on substitue chaque action par son **ETF SPDR** (GICS) ; mesure de la **dilution V1→V2** ; **cadrage produit** (intégrable Ramify, type NANC/KRUZ). |

**`NOTE_RECHERCHE_QIS.md`** = la synthèse pour l'équipe QIS (méthodo, résultats, limites, recommandation,
**traçabilité de chaque chiffre**).

**Résultat en une ligne** : la stratégie spécifiée dégage un **alpha actions positif mais non significatif**
(V1), **dilué à ≈0/négatif** une fois traduit en ETF (V2) ; aucune version ne bat SPY en risque-ajusté →
**produit thématique livrable, pas un générateur d'alpha**.

---

## 2. RECHERCHE SUPPLÉMENTAIRE — notre valeur ajoutée (au-delà de la demande)

| Notebook | Rôle |
|---|---|
| **`SUPP_00_exploration.ipynb`** | Profil des données + **audit de complétude** : chaque chiffre des analyses préliminaires reproduit ou sourcé (3 divergences assumées). |
| **`SUPP_A_backtest_generique.ipynb`** | « Suivre tout le Congrès » — 9 variantes génériques net de coûts → pas d'edge net. |
| **`SUPP_B_chasse_au_signal.ipynb`** | Recherche objective de signal (6 angles) → seul survivant = la *breadth* d'achat (IC≈0,02, sous le seuil). |
| **`SUPP_C_approfondissement_V2.ipynb`** | **Le Sharpe de la V2 mène-t-il quelque part ?** Caractérisation (beta/corr/sous-périodes/blend) + V2 pilotée par la breadth + loi fondamentale Grinold-Kahn. |

---

## 3. Moteur réutilisable (importé par les notebooks — pas de duplication)

| Module | Rôle |
|---|---|
| `data.py` | journal des transactions Quiver (2014+), normalisé |
| `prices.py` | prix yfinance + facteurs Fama-French, **cache** (`cache/`, gitignoré) |
| `portfolio.py` | moteur event-driven (entrée `filed`+1), rendements **nets de coûts** |
| `evaluate.py` | alpha FF-Carhart, Deflated Sharpe, OOS, `nw_tstat`, `car_event`, `trade_returns`/`trade_stats`, `fundamental_law` |
| `selection.py` | **sélection annuelle** (Sharpe rétréci Mauboussin sur la *série de trades réalisés* + UCB + commissions), `with_realized`, `sector_breadth`, V2 ticker→ETF |
| `variants.py` | conviction-cluster, dé-concentration par membre |
| `leadership.py` | leadership de parti (point-in-time) + chairs de commission |

**Documentaire** : `STRATEGIE_ANALYSE.md` (littérature + produits NANC/KRUZ/Quiver + « pourquoi le hype », URLs) ·
`PROMPT_RECHERCHE_S34.md` (prompt autonome de (re)construction).
