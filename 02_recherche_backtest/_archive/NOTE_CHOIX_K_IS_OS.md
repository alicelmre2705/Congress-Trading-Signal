# Choisir K : le test IS/OS en une page

**La question.** Le §8 choisit chaque année le $K$ (combien de membres copier) qui a le mieux
marché sur **tout** le passé. Problème : le même passé sert à **choisir** et à **juger** — le $K$
élu a peut-être juste bien récité son examen. Le §11 teste ça.

**Le test** — chaque ligne du schéma = une décision :

![](figures/fig_isos_frise.png)

- **bleu (IS, 75 % du passé)** : on y choisit $K$ — le meilleur score parmi $K = 4 \dots 20$ ;
- **orange (OS, les 25 % récents)** : jamais utilisé pour choisir. On regarde seulement quel
  **rang** le $K$ élu y fait — bon choix s'il reste en tête, hasard s'il retombe dans le paquet ;
- **vert** : on joue le $K$ élu l'année suivante (le vrai test, comme partout dans le notebook).

Le découpage grandit tout seul : 9 mois / 3 mois à la première coupe, ~6 ans / 2 ans en 2023.

**Le tableau du §11 = le journal de ces décisions** (une ligne par année jouée). La ligne « 2024 »
disséquée, case par case :

![](figures/fig_isos_ligne_tab11.png)

Pour lire tout le tableau d'un coup d'œil : descendre la colonne **rang OS** — si choisir $K$ sur
le passé marchait, elle serait pleine de 1/16 ; en vrai le $K$ élu retombe dans le paquet presque
à chaque fois.

**Pourquoi les rangs sont « sur 16 » (ou 10, ou 1) et pas « sur 17 » ?** Comme une course où 17
dossards sont portés par moins de 17 coureurs : quand il n'y a que 7 membres significatifs, top-10,
top-15 et top-20 copient les 7 mêmes personnes — même portefeuille, même score. On ne classe que
les stratégies **réellement différentes** :

![](figures/fig_isos_rang_dD.png)

**Et la colonne ρ ?** On classe les 17 $K$ sur le bleu, puis on les reclasse sur l'orange ; ρ dit
si c'est le même classement ($+1$ = identique, $0$ = aucun lien, $-1$ = inversé) :

![](figures/fig_isos_rho.png)

**Et les gros ronds du scatter du §11 ?** Les $K$ identiques ont exactement le même score IS et le
même score OS → leurs ronds tomberaient pile l'un sur l'autre. On les fusionne en un seul rond
dont la **taille = le nombre de $K$ empilés** :

![](figures/fig_isos_gros_ronds.png)

**Ce qu'on trouve — 3 faits.**

1. Le $K$ élu sur le bleu finit **mi-tableau ou pire** sur l'orange : rangs 4/5, 12/16, 10/16,
   7/16, 2/10, 10/14 (sélection IR) — jamais premier ; côté appraisal, jusqu'à **dernier (17/17)**.
2. Le $K$ gagnant de l'orange **change presque chaque année** (4, 11, 18, 12, 13, 4) : il n'existe
   pas de « bon K » stable à découvrir.
3. Le $t$ de la stratégie : **1,58** quand $K$ est choisi sur tout le passé (§8) → **1,29** quand
   il n'a droit qu'au bleu. L'écart, c'est ce que le §8 devait au fait de réviser sur l'examen.
   (Et toujours rien ne franchit le seuil $\approx 1{,}81$.)

**Conclusion.** Le meilleur $K$ du passé ne dit rien du meilleur $K$ du futur : « combien copier »
n'est **pas apprenable** sur ces données — le verdict « pas d'alpha » en sort renforcé.

*(Détails — bornes exactes des découpages, rangs par année, corrélations IS/OS, cas ex-aequo des
premières coupes : table `tab11` et figure du §11 du notebook.)*
