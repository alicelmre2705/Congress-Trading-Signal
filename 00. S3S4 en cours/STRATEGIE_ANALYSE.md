# Analyse Stratégie & Backtest — NOTE DE RECHERCHE (non finalisée)

> **Note de recherche isolée — Semaines 3-4.** Pure documentation : **aucune donnée ni aucun code
> finalisé (Semaines 1-2) n'a été modifié pour produire ce document.** Elle vit dans le dossier **`S3S4/`**
> (séparé de `docs/`, qui est la documentation finalisée des Semaines 1-2). But : consigner ce qu'on a
> appris (chiffres + méthode + sources) **avant** de construire le moindre backtest, pour que **chaque
> résultat soit vérifiable**. Date : 2026-06-26.

---

## 0. PROVENANCE de chaque chiffre (comment vérifier)

Chaque résultat est taggé par son origine :

- **[CALC-moi]** — calcul lancé directement en **lecture seule** pendant la session (commandes visibles
  dans l'historique du chat). Confiance haute, reproductible.
- **[CALC-agent]** — calcul produit par un agent de recherche (même méthode, mêmes données) ; corroboré
  et reproductible, mais **non re-vérifié ligne à ligne**.
- **[SOURCE]** — littérature / presse / produit, avec URL.

**Méthode commune des [CALC-*] sur nos données = event-study.** Pour chaque achat divulgué, entrée à la
`disclosure_date` (**sans look-ahead**), prix récupéré via `yfinance`, rendement à 1/3/6/12 mois **moins**
celui du SPX (= rendement « anormal », CAR), puis agrégation (moyenne, médiane, % positifs, t-stat).
Univers testés : top-40 liquide [CALC-moi] puis ~200-250 tickers [CALC-agent].

**⚠ Limites de CES sondages** (ce sont des calculs jetables, à confirmer par un vrai backtest) :
- rien n'est sauvegardé (calculs ad hoc) ;
- **survivorship** — `yfinance` ignore les tickers délistés → biais haussier ;
- **fenêtres chevauchantes** — t-stats optimistes (~÷2 après correction) ;
- **SPX brut, non ajusté des facteurs** — le beta tech gonfle l'« alpha » apparent ;
- **pas de coûts** sauf mention explicite.

Ils sont **directionnellement solides et convergents** avec la littérature, mais doivent être **confirmés
net de coûts** par le book de recherche isolé (voir §5).

---

## 1. Résultats sur NOS données (event-study, lecture seule)

| Mesure | Valeur | Source |
|---|---|---|
| Mix achats / ventes | 51 % / 48 % (équilibré) | [CALC-moi] |
| Latence de divulgation médiane | ~28 j (p90 ~47 j) | [CALC-moi] |
| Horizon de détention réel | médiane **91 j** (achat→1ʳᵉ vente) / 123 j (règle Quiver) | [CALC-moi] / [CALC-agent] |
| Couverture ticker propre | 99 % des lignes tickées (3 304 distincts) | [CALC-moi] |
| **Achats — CAR 12 mois** | **+2,76 %** (top-40, t=4,66) ; **+1,54 %** (large, t≈2,5 ajusté) | [CALC-moi] / [CALC-agent] |
| Médiane / % gagnants / skew | **−2,8 % / 45,3 % / +4,6** ; top décile ≈ **500 %** de l'alpha | [CALC-agent] |
| Ventes | non prédictives (les titres vendus montent ensuite) | [CALC-moi] |
| **Train/test (sélection membres)** | top-10 2020-22 **+82 %** → 2023-25 **−4,5 %** (renversement) | [CALC-agent] |
| Persistance individuelle | Carper +5,8→−12,8 · Cisneros +5,2→−10,0 · Hern +3,2→−4,8 (%) | [CALC-agent] |
| Filtre « commissions clés » | **+1,08 %** vs **+2,09 %** (hors commissions) | [CALC-agent] |
| Slices | Sénat +6,15 % · GOP +2,75 % · gros montants +2,16 % vs +0,72 % | [CALC-agent] |
| **Portefeuille size-weighted** | **17,55 % CAGR vs SPY 15,22 % = +233 bps PRÉ-coûts** ; equal-weight 13,29 % | [CALC-agent] |
| … net (20 bps, ~6 rotations/an) | **12,67 % = −255 bps vs SPY** ; survivorship +1-3 % CAGR | [CALC-agent] |
| Conviction-cluster | 98 % des achats sont multi-membres | [CALC-agent] |
| Concentration déposants | Khanna ≈ **40 %** des achats (top-5 ≈ 58 %) | [CALC-moi] / [CALC-agent] |

**Lecture.** Un edge moyen existe mais **médiane négative + < 46 % de gagnants** = loterie à queue droite ;
la **sélection par performance passée se renverse** hors échantillon ; le **filtre commissions est
contre-productif** ; **seule la pondération par taille/conviction** montre un signal — mais **négatif net
après coûts**.

---

## 2. Littérature [SOURCE]

- **Pré-STOCK Act** : Ziobrowski 2004 (+12,3 %/an Sénat), 2011 (+6 %/an House) — **contesté** par
  Eggers & Hainmueller 2013 (**−2 à −3 %/an** sur portefeuilles réels). Karadas 2019 : +35 % pour
  républicains puissants (horizon 1 semaine), disparaît après 2012.
  → <https://andy.egge.rs/papers/Eggmueller_CapitolLosses.pdf>
- **STOCK Act 2012** : Carhart alpha du Congrès **9,5 %/an → 0,9 %/an**.
- **Récent** : **Chen & Sacerdote, NBER w35041 (2026)** — « underperform or at best match » ; les trades
  **suivent** le sentiment retail des réseaux sociaux, pas en anticipation. → <https://www.nber.org/papers/w35041>
  **Wei & Zhou, NBER w34524 (2024)** — **+47 %/an pour les LEADERS** (chairs/leadership), via influence
  politique + accès corporatif. → <https://www.nber.org/papers/w34524>
- **Molk & Partnoy 2023** : les trades **négatifs** (shorts/puts) ont +1-2 % en 10-15 j — **hors de notre
  périmètre** (pas de données options/short). → <https://corpgov.law.harvard.edu/2024/07/29/negative-trading-in-congress/>

---

## 3. Produits réels & « pourquoi le hype » [SOURCE]

- **ETF NANC** (Démocrates) +26,8 % / +18,5 % ≈ marché (tilt tech) ; **KRUZ** (Républicains) sous-performe.
- **Quiver « Congress Buys » 37 % CAGR** / **GovGreed 72 % win rate** = **backtests SANS coûts, slippage
  ni look-ahead**. → <https://www.quiverquant.com/strategies/s/Congress%20Buys/>
- **Autopilot** ~750 M$ d'encours (dont le portefeuille Pelosi) = mono-leader + survivorship. **Pelosi
  2019-2022 = +9,1 %/an vs S&P +12,4 % (a SOUS-performé).** → <https://www.pelositracker.com/>
- **GitHub** : les dépôts sont des **scrapers de données** (ex. neelsomani/senator-filings 412★) ;
  **aucun backtest open-source** combinant méthodo divulguée + coûts + OOS + perf positive.
- **Le hype** ≈ 70-80 % narratif/outrage + meme culture + monétisation (Unusual Whales a grossi en hypant
  puis a pivoté vers la vente de données). Ce n'est pas la performance qui le porte.

---

## 4. Verdict honnête

1. **Edge agrégé NET ≈ 0** post-STOCK Act (nos données et la littérature convergent).
2. **Seul signal pré-coûts** = pondération **taille/conviction** (+233 bps brut) → **effacé** par
   turnover + coûts + survivorship + beta tech.
3. **Pas de persistance** de la sélection par performance passée ; **filtre commissions contre-productif**.
4. **V2 ETF sectoriel dilue 70-80 %** de l'edge (idiosyncratique ; corr NVDA-XLK ≈ 0,5).
5. **Le hype vend de la data et du récit, pas un alpha net** ; les ETF réels (NANC/KRUZ) le confirment.

---

## 5. Suite — book de recherche ISOLÉ (dans CE dossier `S3S4/`)

Pour confirmer/chiffrer tout cela **net de coûts** sans rien compromettre du travail finalisé, on
construira le book de recherche **ici même, dans `S3S4/`** (voir `S3S4/PROMPT_RECHERCHE_S34.md`) :
- **net de coûts**, **point-in-time** (anti-survivorship), **factor-ajusté** (Fama-French-Carhart),
  **Deflated Sharpe** + validation **OOS** ;
- sur l'**historique Quiver 2014+ déjà en cache local** : `data/house/tables/_quiver_house_cache.csv`
  (100 333 lignes) + `data/senate/reference/_quiver_senate_cache.csv` (13 342 lignes), `filed` 2014→2026,
  colonne `Trade_Size_USD` (taille réelle → pondération conviction) ;
- variante prioritaire = **taille/conviction** (pas l'equal-weight) ; **V2 ETF** mesurée comme dilution.

> Le book **lira** les données finalisées (`data/`, `congress_core/`) mais **n'écrira que dans `S3S4/`** —
> aucun impact sur les Semaines 1-2 ni sur les golden.

---

## 6. Round 3 — chasse OBJECTIVE au signal (code reproductible dans `analyses/`)

> Reproche légitime : les rounds 1-2 *confirmaient* un a priori (« edge ≈ 0 »). Round 3 reprend la base
> **comme un quant qui la découvre**, avec le mandat de **trouver du signal s'il existe** — 6 angles
> indépendants, chacun **un script documenté et vérifiable** dans `analyses/` (voir `analyses/README.md`).

**Résultat réconcilié — plus nuancé que « rien » :**

1. **Il existe une information faible mais RÉELLE** (`analyses/ic.py`) : le **nombre d'acheteurs distincts**
   (breadth) prédit le rendement cross-sectionnel — IC ≈ **0,02**, t_NW **1,95** (6 m, investissable) à
   **2,86** (12 m). Trois faits solides : seuls les **achats** informent ; c'est le **comptage** (pas le
   montant $) ; ce **n'est pas du beta** (corrélation de rang).
2. **Mais ce n'est pas un edge tradeable**, et les 5 autres angles le confirment tous :
   - `event_study.py` : gros trades ~+4 %/252j **mais les ventes aussi** (tilt de style) ; alpha
     FF-Carhart **non significatif** (t≈1,7) ; concentré 2019-2021.
   - `long_short.py` : market-neutral **nul** (t<1,3) → le beta ne « cache » aucun alpha.
   - `committee.py` : l'alignement commission↔secteur s'**inverse** au contrôle secteur×année (beta
     défense) ; **86 %** vient de 2 traders.
   - `characteristics.py` : taille/chambre/vitesse de déclaration **s'effondrent** au clustering par membre
     → une poignée d'individus, pas un type de trade.
   - `ml.py` : AUC **OOS ≈ 0,52** (sur-apprentissage), aucune feature « initié », médiane Q4 négative.

**Verdict final (objectif, pas a priori) :** information réelle (breadth) **sous le seuil
d'exploitabilité** — IC minuscule × instabilité de régime × survivorship × coûts × concentration sur
quelques membres. C'est pourquoi un produit *data* (Quiver) a de la valeur (info à faire remonter) sans
qu'une stratégie suivable batte le marché **net de coûts**. Tout le code est dans `analyses/` (relançable).
