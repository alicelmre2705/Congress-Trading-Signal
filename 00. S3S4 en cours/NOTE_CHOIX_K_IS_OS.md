# Le §11 expliqué : choisir K avec un découpage IS/OS qui grandit avec le temps

## 1. Le problème que le §11 règle

Au §8, à chaque fin d'année, on choisit le $K$ (combien de membres copier) qui a le **meilleur
score sur tout le passé**. Le piège : le passé sert **à la fois** à choisir le K et à mesurer s'il
est bon. C'est comme noter 17 élèves sur un examen dont ils ont déjà vu les réponses — le premier
de la classe n'est pas forcément le plus fort, c'est peut-être juste celui qui a le mieux récité.

Concrètement : le §8 trouvait que laisser K se choisir montait le $t$ à $1{,}58$. Mais ce chiffre
est-il un vrai gain, ou l'écho de l'échantillon qui a servi au choix ? **Pour le savoir, il faut
tester le choix sur des données qu'il n'a jamais vues.** C'est tout l'objet du §11.

## 2. L'idée : couper le passé en deux, et refaire ça chaque année

À chaque date de décision (fin d'année $Y$), on coupe le passé disponible en deux morceaux :

- **IS (in-sample)** = les **premiers 75 %** → c'est là qu'on **choisit** : $K_{IS} = $ le K au
  meilleur score sur l'IS ;
- **OS (out-of-sample)** = les **derniers 25 %** (au moins 63 jours de bourse) → ça ne sert
  **jamais** à choisir. Ça sert uniquement à **juger** : le K élu sur l'IS, quel rang fait-il sur
  cette suite qu'il n'a pas vue ?

Puis on joue $K_{IS}$ pendant l'année $Y{+}1$ — le vrai test final, comme partout dans le notebook.
Le découpage grandit tout seul avec l'historique — exactement ce que tu décrivais (quelques mois au
début, plusieurs années à la fin) :

![](figures/fig_isos_frise.png)

| coupe | IS (choisit K) | OS (juge le choix) | on joue |
|---|---|---|---|
| fin-2016 | 189 jours (jan → sept 2016) | 63 jours (oct → déc 2016) | 2017 |
| fin-2019 | 3 ans (2016 → 2018) | 1 an (2019) | 2020 |
| fin-2023 | 6 ans (2016 → déc 2021) | 2 ans (2022-2023) | 2024 |
| fin-2025 | 7,5 ans (2016 → juin 2023) | 2,5 ans (juil 2023 → déc 2025) | 2026 |

Rien d'autre ne change : les 17 stratégies-K ($K = 4 \dots 20$) sont celles du §8, déjà
walk-forward côté membres ; le score est celui de la sélection (IR quotidien pour la sélection IR,
appraisal pour la sélection appraisal) ; l'année jouée est mesurée comme partout.

## 3. Une coupe déroulée en entier (fin-2023, sélection IR)

1. **Le passé disponible** : les rendements des 17 stratégies-K du 04/01/2016 au 29/12/2023
   (2 012 jours).
2. **Le split** : IS = du 04/01/2016 au 29/12/2021 (1 509 jours) ; OS = du 30/12/2021 au
   29/12/2023 (503 jours).
3. **On choisit sur l'IS** : on calcule le score IR de chacune des 17 stratégies-K sur l'IS
   seulement → le meilleur est $K_{IS} = 18$.
4. **On juge sur l'OS** : on calcule le score des 17 K sur l'OS → $K = 18$ n'y est que
   **7ᵉ sur 16** valeurs distinctes ; le gagnant de l'OS aurait été $K = 12$. Le choix de l'IS
   n'était donc ni bon ni catastrophique — mi-tableau.
5. **On joue quand même** $K = 18$ en 2024 (c'est la règle : l'OS ne choisit jamais, il observe)
   → excès réalisé $+4{,}4\,\%$.

Et on recommence à chaque coupe, de fin-2016 à fin-2025 (fin-2015 : aucun historique → $K = 4$
par défaut, comme au §8).

## 4. Comment lire la table du §11 (colonne par colonne)

| colonne | ce que c'est |
|---|---|
| **fin IS / OS / n_OS** | les bornes réelles du découpage à cette coupe (communes aux 2 critères) |
| **K_IS** | le K élu sur l'IS — celui qu'on joue l'année suivante |
| **rang OS « d/D »** | le rang du K élu parmi les **D scores distincts** de l'OS ; 1/D = le choix IS était aussi le meilleur OS ; D/D = le pire |
| **K_OS** | le K qui aurait gagné l'OS (a posteriori — jamais utilisé) |
| **excès** | l'excès vs SPY réellement fait l'année jouée avec K_IS |
| **ρ** | corrélation de rang entre les scores IS et OS des 17 K : $+1$ = même classement des K dans l'IS et l'OS (le passé prédit), $0$ = aucun lien, $-1$ = classement inversé |

**Pourquoi « d/D » et des « — » ?** Quand il y a moins de membres significatifs que $K$
($n_{sig} < K$), le top-K prend tout le monde → les stratégies $K = n_{sig}, \dots, 20$ sont
**identiques**, donc leurs scores sont exactement ex-aequo. Aux coupes ≤ 2019, presque tous les K
coïncident : il n'y a rien à classer, on affiche « 1/1 » ou « — » plutôt que de faire semblant.
Le diagnostic ne devient réel qu'à partir de ~2021.

## 5. Comment lire la figure (le scatter)

Un point = **un K à une coupe** : en horizontal son score sur l'IS, en vertical son score sur l'OS
(un gros point = plusieurs K ex-aequo empilés ; la couleur = la coupe).

- **Si choisir K sur le passé marchait**, les points suivraient la diagonale : bon score IS ⇒ bon
  score OS.
- **Ce qu'on voit** : des colonnes verticales — à score IS presque identique, le score OS va de
  $-1$ à $+2$. Le passé d'un K ne dit à peu près rien de sa suite.

## 6. Les résultats

**a) Le K élu sur l'IS est rarement confirmé par l'OS.** Ses rangs OS (sélection IR) : 4/5, 12/16,
10/16, 7/16, 2/10, 10/14 — mi-tableau ou pire, jamais premier. Côté appraisal : jusqu'à **17/17**
(dernier) à la coupe fin-2021. Et le gagnant de l'OS change presque à chaque coupe (4, 11, 18, 12,
13, 4) : même l'OS ne désigne pas un K stable.

**b) ρ n'a pas de signe stable** (IR : $-0{,}55$ à $+0{,}63$ ; appraisal : $-0{,}76$ à $+0{,}74$) :
le classement des K sur l'IS ne prédit pas leur classement sur l'OS.

**c) Le prix de la validation** — la table comparative :

| stratégie | excès/an | t | β | t_appr |
|---|---|---|---|---|
| K=4 fixe (sél IR) | +3,1 % | 0,94 | 1,20 | −0,13 |
| K walk-forward §8 (choisi sur TOUT le passé) | +4,1 % | **1,58** | 1,17 | +0,45 |
| K IS/OS §11 (choisi sur l'IS seul) | +3,6 % | **1,29** | 1,19 | +0,16 |
| K=4 fixe (sél appraisal) | −2,5 % | −1,24 | 1,01 | −0,75 |
| K walk-forward §8 (sél appraisal) | −1,0 % | −0,54 | 0,97 | −0,29 |
| K IS/OS §11 (sél appraisal) | −1,1 % | −0,64 | 0,99 | −0,38 |

Dès que le choix de K n'a plus le droit de « réviser sur l'examen » (75 % du passé au lieu de
100 %), le $t$ retombe de $1{,}58$ à $1{,}29$ : **une partie du gain du §8 était l'écho de
l'échantillon**. Et toujours rien ne franchit le seuil ($\approx 1{,}81$ à $n = 11$ ans).

## 7. Ce qu'on peut conclure — et ce qu'on ne peut pas

**On peut dire** :
- le meilleur K du passé n'est pas le meilleur K du futur (rangs OS mi-tableau, ρ instable,
  gagnant OS qui change chaque année) → **« combien copier » n'est pas apprenable** sur ces
  données ;
- le $t = 1{,}58$ du §8 se lit comme une **borne haute** — validé proprement, il retombe à 1,29 ;
- le verdict global du notebook (pas d'alpha, β ≈ 1,2, rien au-dessus du seuil) en sort
  **renforcé**.

**On ne peut pas dire** :
- que ρ faible « prouve » le sur-apprentissage au sens statistique : les 17 stratégies-K sont
  emboîtées (la strat-$K{+}1$ = la strat-$K$ + un membre) donc quasi colinéaires, les OS des
  premières coupes sont courts et bruités, et les coupes successives partagent le même historique
  → pas de p-value légitime, c'est un **faisceau d'indices** ;
- que le K-IS/OS est un « concurrent » du §8 : il choisit avec 25 % d'information récente en
  moins — son $t$ plus bas mesure d'abord le prix de la validation, pas une stratégie de plus.
