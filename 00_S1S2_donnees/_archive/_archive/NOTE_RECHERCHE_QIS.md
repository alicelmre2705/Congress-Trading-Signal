# Note de recherche — Congress Trading Signal, Semaines 3-4 (pour l'équipe QIS Ramify)

> **Destinataire : équipe QIS Ramify.** La stratégie *spécifiée par le brief* (`0.Notion_Ramify.pdf`),
> construite et backtestée, avec ses chiffres honnêtes — pour que Ramify décide. **Source de vérité = le code
> exécuté des notebooks** ; cette note les *cite* (avec le pointeur de section), elle ne les remplace pas.
> Le §7 « Traçabilité » garantit qu'aucun chiffre n'est orphelin.

| Notebook | Contenu |
|---|---|
| **`RAMIFY_V1_actions.ipynb`** | **Livrable V1 (actions)** — la stratégie spécifiée, section par section du brief |
| **`RAMIFY_V2_ETF.ipynb`** | **Livrable V2 (ETF sectoriels)** — même stratégie, instrument = ETF ; dilution V1→V2 |
| `SUPP_00 / A / B / C` | recherche supplémentaire (exploration, backtest générique, chasse au signal, approfondissement V2) |

## 1. Méthodologie (fidèle au brief)
- **Données** : caches Quiver **2014→2026** (House + Sénat), 56 877 achats / 251 membres. *(Pré-2020 papier
  OCR exclu — coûteux ; les FINAL 2020-26 servent aux commissions/secteurs.)*
- **Entrée** = `disclosure_date` **+1 jour ouvré** (sans look-ahead). **Sortie** = vente correspondante
  (même membre+ticker) sinon **+12 mois**. *(`RAMIFY_V1` §2.)*
- **Sélection annuelle** : fin d'année Y, parmi les **éligibles** (≥10 trades **clôturés** → aucun
  look-ahead), score = **Sharpe de la *série de trades réalisés* RÉTRÉCI vers la moyenne du groupe**
  (Mauboussin) **+ exploration UCB1** (Sutton & Barto), avec **≥ la moitié des K en commission clé**
  (Finance/Defense/Intelligence). Suivi des achats l'année Y+1 ; positions des sortants laissées courir.
  *(`RAMIFY_V1` §3.)*
- **V1** = actions ; **V2** = substitution ETF SPDR sectoriel (GICS). Coûts **20 bps one-way nets**.
  Benchmarks : **SPY**, **RSP**, **60/40**. Anti-biais De Prado : look-ahead réglé, survivorship borné,
  **Deflated Sharpe** comptant la grille K, walk-forward.

## 2. Résultats — V1 actions (walk-forward net)
| K | n_pos | CAGR | Sharpe | alpha FF-Carhart (t) | vs SPY (CAGR) |
|---|---|---|---|---|---|
| 4 | 735 | 10,2 % | 0,56 | +1,7 % (0,33) | −3,9 pts |
| **6** | 1 391 | 9,4 % | 0,52 | +0,7 % (0,14) | −4,7 pts |
| 8 | 1 652 | 13,3 % | **0,71** | **+4,0 % (0,88)** | −0,8 pt |
| 10 | 2 139 | 12,6 % | 0,68 | +3,7 % (0,83) | −1,6 pt |

*(SPY : CAGR 14,1 % / Sharpe 0,86 ; RSP 11,7 %/0,72 ; 60/40 9,5 %/0,91. `RAMIFY_V1` §4-5.)*
**Lecture** : la sélection fidèle (Sharpe sur la série de trades réalisés) dégage un **alpha actions positif
mais NON significatif** (meilleur K=8 : +4,0 %/an, *t*=0,88) ; **aucun K ne bat le Sharpe de SPY**. Deflated
Sharpe = 0,99 (le flux n'est pas un artefact de la grille, mais Sharpe < SPY → c'est du **beta**, pas de
l'alpha). Niveau trade (`RAMIFY_V1` §6) : hit-rate **47,6 %**, profit factor **1,47**, médiane **négative** =
queue droite. **Pas de persistance** (`RAMIFY_V1` §7) : top-10 in-sample 2020-22 **+22,8 %** → OOS 2023-25 **+3,8 %**.

## 3. Résultats — V2 ETF (dilution)
- V2 (K=6) : CAGR **6,0 %**, Sharpe **0,45**, maxDD **−38 %**, alpha FF-Carhart **−3,8 %/an (t=−1,5)**.
- **Dilution V1→V2** systématique à chaque K (**−4,5 % à −5,8 %/an** d'alpha) : la substitution sectorielle
  **efface le gain idiosyncratique** (l'edge est firm-specific). *(`RAMIFY_V2` §3-4.)*
- V2 = **beta sectoriel dé-risqué** (vol/DD réduits), sous SPY — pas de l'alpha.

## 4. Approfondissement V2 (le Sharpe mène-t-il quelque part ? `SUPP_C`)
- **Caractérisation** : V2 β=0,76, corr 0,81 ; Sharpe sous SPY sur les **deux** sous-périodes (0,55→0,30) ;
  ni levier ni blend ne dépassent SPY (blend optimal à α=0 = SPY seul). → le 0,45-0,58 **ne peut pas battre
  le marché**.
- **Leçon de construction** : la *sélection de membres* DÉTRUIT de la valeur — une V2 « tout le Congrès »
  pondérée par la **breadth** d'achat monte à **Sharpe ~0,75** (vs 0,45 en sélection), proche de SPY — mais
  reste un **beta sous le marché** (alpha FF −1,5 %, *t*≈−2). ⇒ pour un produit, câbler en **breadth /
  tout-le-Congrès**, pas en sélection.
- **Plafond théorique (Grinold-Kahn)** : avec IC≈0,02, l'IR atteignable plafonne **~0,2-0,3** quelle que soit
  la construction → l'edge est **structurellement petit**.

## 5. Limites (franches)
- **Survivorship** : 2 171/3 797 tickers en cache prix ; **1 626 délistés absents** → rendements = **bornes
  hautes**. *(`RAMIFY_V1` §1.)*
- **Trou Sénat / pré-2020** : Quiver démarre tard, papier OCR exclu → échantillons minces par membre.
- **Commissions point-in-time approximées** (snapshot FINAL, pas reconstituées année par année).
- Le brief demandait le **framework Ramify** ; on a livré un **moteur Python local** (décision actée).

## 6. Recommandation
1. **Ne pas** positionner ceci en générateur d'alpha : l'alpha V1 est **non significatif** et **disparaît en
   V2** ; aucune version ne bat SPY en risque-ajusté.
2. **Évaluer la V2 comme produit thématique** (beta « Congrès » transparent, dé-risqué), à la NANC/KRUZ —
   décision **commerciale**. Si construit : **pondérer tout-le-Congrès / breadth**, pas la sélection.
3. **Si poursuite recherche** : univers **point-in-time avec délistés** (tuer le survivorship), commissions
   **année par année**, et exploiter au mieux le seul signal résiduel (**breadth**, IC≈0,02) — sachant que la
   loi fondamentale en borne le potentiel.

## 7. Traçabilité — chaque chiffre → sa cellule (zéro orphelin)
| Chiffre | Source (notebook · section) |
|---|---|
| 56 877 achats / 251 membres / couverture 2171/3797 | `RAMIFY_V1` §1 |
| Entrée+1 / sortie vente-ou-12 mois (exemples) | `RAMIFY_V1` §2 |
| Scoreboard + sélection annuelle par année | `RAMIFY_V1` §3 |
| V1 vs SPY/RSP/60-40 + alpha FF-Carhart | `RAMIFY_V1` §4 |
| Grille K{4,6,8,10} + Deflated Sharpe | `RAMIFY_V1` §5 |
| Hit rate / profit factor / espérance | `RAMIFY_V1` §6 |
| Track records + persistance IS→OOS | `RAMIFY_V1` §7 |
| Dilution V1→V2 (par K) + alpha V2 | `RAMIFY_V2` §3-4 |
| Beta/corr/sous-périodes/blend V2 | `SUPP_C` §1 |
| V2 breadth-tilt (Sharpe 0,75) | `SUPP_C` §2 |
| Loi fondamentale IR=IC√breadth | `SUPP_C` §3 |
| Breadth IC≈0,02 | `SUPP_B` (chasse au signal) |
| 3 divergences vs agents FINAL | `SUPP_00` §0 (audit) |
| Littérature (Ziobrowski/Karadas/STOCK Act), produits (NANC/KRUZ/Quiver) | `STRATEGIE_ANALYSE.md` (URLs) |
| Couche données 90 487 txns / golden | pipeline Semaines 1-2 (hors S3-4) |
