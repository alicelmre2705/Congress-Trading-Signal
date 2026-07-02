# Stratégie V1 — Portefeuille par congressman (diagnostic de talent)

> Document de méthode. Objectif : poser **clairement**, avant tout code, *ce qu'on veut mesurer*,
> *comment on procède étape par étape*, et *toutes les formules mathématiques* avec leur intuition.
> Périmètre : **actions uniquement**, entrée à la **date de transaction (`traded`)**, classement des
> membres par **Sharpe simple**, pondérations **equal-weight ET size-weight comparées**, focus **top-4**.

---

## 0. La question à laquelle on répond

> « Si on avait détenu le portefeuille réel de tel congressman (ses achats jusqu'à ses ventes),
> aurait-il **battu le SPY**, une fois pris en compte le **risque (volatilité)**, et est-ce
> **statistiquement significatif** ? Puis : en classant les membres et en suivant les **4 meilleurs**,
> bat-on le marché ? »

**Nature de la V1 = diagnostic de talent, pas stratégie suivable.** Entrer à `traded` et classer sur
toute la période utilise de l'information du futur (on n'apprend le trade qu'à la déclaration `filed`
~28 j plus tard, et on ne connaît pas le top-4 à l'avance). La V1 dit donc **« y a-t-il du signal /
du flair ? »**. La version *implémentable* (entrée `filed` + sélection walk-forward, spec Ramify) est
la **Phase 2**. Ordre logique : d'abord vérifier qu'il y a du signal, ensuite voir s'il est exploitable.

---

## 1. Vocabulaire et notations

| Symbole | Sens |
|---|---|
| `P_{i,t}` | prix (clôture **ajustée** : dividendes + splits inclus) de l'action *i* le jour *t* |
| `r_{i,t}` | rendement quotidien de l'action *i* |
| `r^P_t` | rendement quotidien du portefeuille d'un membre |
| `r^B_t` | rendement quotidien du benchmark **SPY** |
| `H_t` | ensemble des positions détenues le jour *t* |
| `w_{i,t}` | poids de l'action *i* dans le portefeuille le jour *t* |
| `A_i` | montant $ déclaré de l'achat (`amount_midpoint`) |
| `V_t` | valeur (capital) cumulée du portefeuille, `V_0 = 1` |
| `252` | nombre de jours de bourse par an (base d'annualisation) |
| `r_f` | taux sans risque (pris = 0, comme dans les notebooks 03/04) |

---

## 2. Ce qui existe déjà (à réutiliser, pas à réécrire)

- **Données** : `data/clean/transactions_backtest_2020_2026.csv` — 72 368 lignes, 100 % avec ticker,
  94,5 % d'actions. Colonnes utiles : `transaction_date` (=`traded`), `disclosure_date` (=`filed`),
  `ticker`, `direction` (buy/sell), `amount_midpoint`, `bioguide_id`, `member_name`, `asset_type`.
  Variante longue si on veut 2014-2026 : `00. S3S4 en cours/table_congres_2014_2026.csv`.
- **Prix** : `00. S3S4 en cours/cache/prices/*.csv` — 2 172 tickers en clôture ajustée quotidienne
  (2013→2026), **+ `SPY.csv`**, `RSP.csv`, ETF sectoriels, `ff_factors.csv`. Rien à re-télécharger.
- **Moteur** (notebooks 03/04) : `build_positions`, `run_portfolio`, `ann_stats`, `sharpe`,
  `sortino`, `info_ratio`, `factor_alpha` (CAPM/FF avec Newey-West), `deflated_sharpe`,
  `expected_max_sr`, `member_sharpe`, `load_panel`, `get_bench`.

---

## 3. Vue d'ensemble — le pipeline en 6 étapes

```
1. Données transactions         (traded, ticker, sens, montant, membre)
        │
2. Positions par membre         (achat → vente = période de détention)
        │
3. Portefeuille quotidien/membre (poids × rendements ; equal & size)   ← prix en cache
        │
4. Stats par membre             (rendement, vol, Sharpe, alpha vs SPY, t)   ← SPY
        │
5. Classement par Sharpe        → top 4  (éligibles : ≥ 10 trades)
        │
6. Portefeuille top-4 vs SPY    (Sharpe, significativité, DSR)         ← SPY
```

---

## 4. Les étapes en détail (avec les maths)

### Étape 1 — Charger et filtrer
- Charger les transactions ; garder **actions seulement** (`asset_type == "Stock"`) ; conserver
  **achats et ventes** (on a besoin des ventes pour fermer les positions).

### Étape 2 — Construire les positions (c'est ici qu'on utilise `traded`)
Pour chaque membre *m* et chaque ticker *i*, apparier un achat à sa vente :
```
entrée  t_in  = date traded de l'achat
sortie  t_out = date traded de la vente du même membre sur i
                sinon  min(t_in + 252 jours de bourse, dernier jour dispo)
```
La position est détenue tous les jours `t_in < t ≤ t_out`. On entre à la **clôture** de `t_in`, donc
le 1er rendement compté est celui de `t_in + 1` (décalage d'un jour : on ne compte pas un rendement
qu'on n'a pas subi). → fonction `build_positions`, appelée sur `traded`.

### Étape 3 — Rendement quotidien du portefeuille du membre

**(a) Rendement d'une action** (clôture ajustée → rendement total, rien à ajouter) :
```
r_{i,t} = P_{i,t} / P_{i,t-1} − 1
```

**(b) Poids — les deux versions à comparer.** Soit `H_t` les positions détenues le jour *t* :
```
equal-weight :  w_{i,t} = 1 / |H_t|
size-weight  :  w_{i,t} = A_i / Σ_{j ∈ H_t} A_j        (A_i = amount_midpoint)
```
*Pourquoi comparer les deux : voir si le résultat vient d'une petite ligne chanceuse (EW) ou d'un vrai
positionnement en taille (size).*

**(c) Rendement du portefeuille** — on pondère avec les poids **de la veille** (`t-1`) :
```
r^P_t = Σ_i  w_{i, t-1} · r_{i,t}
```
*Pourquoi `t-1` : utiliser la répartition d'aujourd'hui pour toucher le rendement d'aujourd'hui serait
un look-ahead.* Les jours sans position : `r^P_t = 0` (cash). → fonction `run_portfolio`.

### Étape 4 — Statistiques par membre

**Capital cumulé :**
```
V_t = Π_{s ≤ t} (1 + r^P_s)          (V_0 = 1) ;  rendement total = V_T − 1
```

**CAGR (rendement annualisé composé)** — « le rendement annuel constant équivalent » :
```
CAGR = V_T ^ (252 / T) − 1           (T = nombre de jours de bourse)
```

**Volatilité annualisée (le risque)** — la variance croît avec le temps, l'écart-type en `√temps` :
```
σ_ann = écart-type(r^P_t) × √252
```

**Sharpe (rendement par unité de risque)** — *c'est le critère de classement retenu* :
```
Sharpe = moyenne(r^P_t) / écart-type(r^P_t) × √252        (r_f = 0)
```
Repère : **SPY ≈ 0,86** sur la période — la barre à battre.

**Max drawdown (pire perte encaissée)** — distingue un Sharpe honnête d'un rendement dopé au risque :
```
drawdown_t = V_t / max_{s ≤ t}(V_s) − 1
MaxDD      = min_t (drawdown_t)          (le plus négatif)
```

**Comparaison au SPY** — rendement actif `d_t = r^P_t − r^B_t` :
```
surperformance annualisée ≈ moyenne(d_t) × 252
tracking error          TE = écart-type(d_t) × √252
Information Ratio        IR = moyenne(d_t) / écart-type(d_t) × √252
```
L'**IR** répond proprement à « bat-il le SPY, risque compris ? » (surperf ÷ risque de la surperf).

**Alpha CAPM** — « bat-il le marché une fois retirée sa dose de marché ? » :
```
r^P_t − r_f = α + β · (r^B_t − r_f) + ε_t
```
- `β` = sensibilité au marché (β > 1 ⇒ le rendement vient du risque, pas du talent).
- `α` (annualisé = `α_jour × 252`) = **la vraie surperformance inexpliquée par le marché**.
→ fonctions `ann_stats`, `info_ratio`, `factor_alpha`.

### Étape 5 — Significativité (la partie centrale)

Deux questions derrière « est-ce significatif ? » :

**(a) L'alpha est-il distinguable de zéro (ou est-ce de la chance) ?**
```
t = α̂ / erreur-standard(α̂)          règle : |t| > 1,96 (≈ 2) ⇒ significatif à 5 %
```
**Piège** : nos rendements se **chevauchent** (une position dure des mois ; plusieurs membres
achètent le même titre) → autocorrélation → l'erreur-standard naïve est trop petite → fausse
significativité. Correction obligatoire : **Newey-West (HAC)**, qui gonfle l'erreur-standard.
(Dans les notebooks existants, un `t` tombe de **+10,6 à +1,41** une fois corrigé.)

**(b) On a pris le meilleur sur beaucoup de candidats — vrai ou juste le plus chanceux ?**
Dès qu'on **classe** et qu'on prend le **top-4**, on data-mine. Correction : **Deflated Sharpe Ratio** :
```
DSR = probabilité que le Sharpe observé dépasse le meilleur Sharpe
      obtenu par pur hasard en testant N candidats
seuil : DSR > 0,95 ⇒ pas un artefact de sélection
```
(Sur la recherche existante, le meilleur critère plafonne à **DSR = 0,94** — juste sous la barre.)
Intuition de fond (loi fondamentale) : `IR ≈ IC · √B` ; l'edge du Congrès étant minuscule (`IC ≈ 0,02`),
l'IR plafonne vers 0,2–0,3 quoi qu'on fasse. → fonctions `deflated_sharpe`, `expected_max_sr`, HAC dans `factor_alpha`.

### Étape 6 — Classement et portefeuille top-4
- Classer les membres **éligibles (≥ 10 trades)** par **Sharpe** ; prendre les 4 premiers.
- Les empiler en un seul portefeuille, équipondéré entre les 4 :
```
r^{top4}_t = (1/4) · Σ_{m ∈ top4} r^{P_m}_t
```
- Lui appliquer **toutes** les stats (§4) + significativité (§5) et comparer au SPY. C'est la réponse finale.
- **Tout le pipeline est refait deux fois : equal-weight puis size-weight, côte à côte.**

---

## 5. Honnêteté / pièges à afficher
- **Look-ahead assumé** (traded + classement plein-échantillon) ⇒ V1 = *diagnostic*, pas stratégie.
- **Survivorship bias** : 1 626 tickers délistés absents du cache ⇒ rendements = **bornes hautes**.
- **Autocorrélation** ⇒ `t` **Newey-West** obligatoire (le `t` naïf trompe).
- **Winsorisation** des rendements à **±50 %/jour** (glitches de prix).
- **Verdict attendu** (cohérent avec 03/04) : ne bat probablement pas le SPY en risque-ajusté ;
  la valeur est la **démonstration propre, isolée et entièrement comprise**.

---

## 6. Vérification (au moment où on codera)
- **Golden** : rendement moyen par ligne et séries par membre identiques aux notebooks 03/04 (écart < 1e-9).
- **Cohérence** : `V_T` reconstruit = produit des `(1 + r^P_t)`.
- **Contrôle SPY** : recomputer Sharpe SPY ≈ 0,86 sur la période.
- **EW vs size** : produire et commenter les deux tableaux de stats.

---

## 7. Suite (Phase 2, seulement si tu le décides)
Version **suivable** : entrée à `filed`, sélection **walk-forward** (top-K sur trades clôturés
≤ 31/12/N, appliqués en N+1), **coûts 20 bps** sur le turnover, puis **V2 = ETF sectoriels** (mapping GICS).
```
r^net_t = Σ w_{i,t-1} r_{i,t} − (bps/10^4) · Σ |w_{i,t} − w_{i,t-1}|     (bps = 20)
```

---

## 8. Décisions validées
- Livrable **maintenant** = ce document (méthode + maths), **pas de code** tant que non validé.
- Entrée `traded` · classement Sharpe simple · pondérations EW **et** size comparées · actions only · top-4.
- Données : `transactions_backtest_2020_2026.csv` (ou table 2014-2026) ; prix : cache existant + SPY.
