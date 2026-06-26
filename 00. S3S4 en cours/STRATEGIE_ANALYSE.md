# Contexte, littérature & produits — complément documentaire (non empirique)

> Les **analyses empiriques reproductibles** (event-study, IC, long-short, commission, caractéristiques,
> ML, backtest 9 variantes) sont dans les notebooks **`01_backtest.ipynb`** et **`02_chasse_au_signal.ipynb`**
> (code + résultats + verdicts inline). Ce document rassemble ce qui est **documentaire** : la littérature,
> les produits réels, et l'explication du « hype » — avec les sources. Il sert à situer nos résultats.

## 1. Littérature académique (alpha réaliste)
- **Pré-STOCK Act** : Ziobrowski 2004 (+12,3 %/an Sénat), 2011 (+6 %/an House) — **contesté** par
  Eggers & Hainmueller 2013 (**−2 à −3 %/an** sur portefeuilles réels, critique du look-ahead).
  Karadas 2019 : +35 %/an pour républicains puissants (horizon 1 semaine), **disparaît après 2012**.
  → <https://andy.egge.rs/papers/Eggmueller_CapitolLosses.pdf>
- **STOCK Act 2012** : Carhart alpha du Congrès **9,5 %/an → 0,9 %/an**.
- **Récent** : **Chen & Sacerdote, NBER w35041 (2026)** — « underperform or at best match » ; les trades
  **suivent** le sentiment retail (réseaux sociaux), pas en anticipation. → <https://www.nber.org/papers/w35041>.
  **Wei & Zhou, NBER w34524 (2024)** — **+47 %/an pour les LEADERS** (chairs/leadership), concentré sur
  < 5-10 % des membres. → <https://www.nber.org/papers/w34524>
- **Molk & Partnoy 2023** : les trades **négatifs** (shorts/puts) ont +1-2 % en 10-15 j — **hors de notre
  périmètre** (pas de données options/short). → <https://corpgov.law.harvard.edu/2024/07/29/negative-trading-in-congress/>

## 2. Produits réels & « pourquoi le hype »
- **ETF NANC** (Démocrates) +26,8 % / +18,5 % ≈ marché (tilt tech) ; **KRUZ** (Républicains) sous-performe.
- **Quiver « Congress Buys » 37 % CAGR** / **GovGreed 72 % win rate** = **backtests SANS coûts, slippage ni
  look-ahead**. → <https://www.quiverquant.com/strategies/s/Congress%20Buys/>
- **Autopilot** ~750 M$ d'encours (dont Pelosi) = mono-leader + survivorship. **Pelosi 2019-2022 = +9,1 %/an
  vs S&P +12,4 % (a SOUS-performé).** → <https://www.pelositracker.com/>
- **GitHub** : les dépôts sont des **scrapers de données** (ex. neelsomani/senator-filings 412★) ;
  **aucun backtest open-source** combinant méthodo divulguée + coûts + OOS + perf positive.
- **Le hype** ≈ 70-80 % narratif/outrage + meme culture + monétisation (Unusual Whales a grossi en hypant
  puis a pivoté vers la vente de données). Ce n'est pas la performance qui le porte.

## 3. Verdict réconcilié (ce que NOS notebooks établissent)
1. **Backtest** (`01`) : aucune des 9 variantes ne dégage d'alpha factoriel significatif, net de coûts.
2. **Chasse au signal** (`02`) : il existe une **information faible mais réelle** — le **nombre d'acheteurs
   distincts** (breadth), IC ≈ 0,02, ni beta ni bruit — **mais sous le seuil d'exploitabilité** (instable
   selon les régimes, survivorship, coûts, concentration sur quelques membres). Chaque autre « thèse
   d'edge » (taille, commission, leadership, conviction, ML) se dissout au contrôle.
3. **Conséquence** : un produit **data** (type Quiver) a de la valeur — il y a une info à faire remonter —
   **sans** qu'une stratégie suivable batte le marché net de coûts. La V2 ETF diluerait encore.

## 4. Limites communes (à dire au chef de recherche)
**Survivorship** (univers prix = tickers encore cotés → CAR long-horizon = bornes hautes) ·
**fenêtres chevauchantes** (t « naïfs » gonflés → versions Newey-West / clustering par membre rapportées) ·
**multiple testing** (des dizaines de coupes → ~1 « significatif » par hasard) ·
`size_usd` = borne basse de la fourchette STOCK Act (montant réel inconnu) ·
entrée `filed` = ce qu'un suiveur peut réellement faire (l'edge éventuel à `traded` n'est pas exploitable).
