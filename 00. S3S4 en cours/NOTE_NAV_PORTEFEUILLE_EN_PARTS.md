# NAV du portefeuille en parts — méthode du chef de recherche

Formalisation des notes manuscrites du chef (2 feuilles, 7 juillet 2026), expliquée étape par
étape. L'idée centrale tient en une phrase :

> **On ne calcule pas le rendement du portefeuille en moyennant des rendements de membres.
> On construit d'abord la *valeur* du portefeuille (sa NAV), jour après jour, comme on tiendrait
> un vrai compte en banque — et le rendement n'est que le ratio de deux valeurs successives.**

---

## 0. L'image à avoir en tête : chaque élu est un fonds

- Le portefeuille personnel d'un élu $k$, reconstruit dans le notebook, a une performance pure
  $\mathrm{NAV}^k(t)$ (son rendement time-weighted composé). On peut la voir comme **le prix d'une
  part d'un fonds** : « le fonds Comstock », « le fonds Fetterman »… Ce prix existe sur tout
  l'historique du membre, il monte et descend tous les jours.
- Notre stratégie de copie, c'est un compte de départ (100 euros) avec lequel on **achète des parts
  de ces fonds** — exactement comme on achèterait des parts de plusieurs ETF.
- La question « quel est le rendement de la stratégie ? » devient alors triviale : c'est le
  rendement de ce compte. Toute la subtilité est de tenir le compte correctement, et pour ça il
  faut suivre **une seule quantité : le nombre de parts détenues**, noté $\mathrm{nbr}^k(t)$.

Pourquoi les *parts* et pas les *poids* ? Parce que quand on ne touche à rien, ce sont les parts
qui sont constantes — les poids, eux, bougent tout seuls avec les prix. Piloter le calcul par les
poids, c'est se tromper d'objet : on verra en §5 que ça revient à trader tous les jours sans le
dire.

## 1. Les dates : deux calendriers

- **Tous les jours de bourse** : $[\,t_0,\ \dots,\ t_n\,]$ — le calendrier où vivent les prix.
- **Les dates de rebalancement** : $[\,t_0^R,\ \dots,\ t_m^R\,]$ — le petit sous-ensemble de jours
  où l'on a le droit d'agir (chez nous : chaque 31/12 ; au §9 du notebook : 30/06 et 31/12).
  Le calendrier englobe la période gérée : $t_0 \le t_0^R$ et $t_n \ge t_m^R$.

Entre deux dates de rebalancement, **on ne touche à rien** : pas d'achat, pas de vente, pas
d'ajustement. C'est la définition même de « copier et tenir ».

À chaque date $t_j^R$, la sélection (le top-$K$ du moment) fournit des **poids cibles**
$w_j^k \ge 0$ avec $\sum_k w_j^k = 1$ ; un membre hors sélection a simplement $w_j^k = 0$.

## 2. Le jour de départ : on investit 100 euros

Au premier rebalancement $t_0^R$, on a $\mathrm{NAV}_0 = 100$ (euros). On veut mettre la fraction
$w_0^k$ de cette somme dans le fonds du membre $k$, donc on y consacre $w_0^k \times \mathrm{NAV}_0$
euros. Combien de parts cela fait-il ? Comme pour n'importe quel achat :

$$
\text{nombre de parts} = \frac{\text{montant investi}}{\text{prix de la part}}
\qquad\Longrightarrow\qquad
\mathrm{nbr}^k(t_0^R) = \frac{w_0^k \times \mathrm{NAV}_0}{\mathrm{NAV}^k(t_0^R)}
$$

**Vérification (sanité)** : la valeur totale achetée vaut bien 100,

$$
\sum_k \mathrm{nbr}^k(t_0^R)\times\mathrm{NAV}^k(t_0^R)
= \sum_k w_0^k \times \mathrm{NAV}_0
= \mathrm{NAV}_0 .
$$

*Exemple (celui de la NOTE_MATHS : membre $A$ = « Apple », membre $B$ = « Coca », 50/50).* Les
deux fonds cotent 100 au départ. On investit 50 euros dans chacun :
$\mathrm{nbr}^A = 50/100 = 0{,}5$ part et $\mathrm{nbr}^B = 0{,}5$ part.

## 3. Entre deux rebalancements : les parts sont constantes, la valeur bouge

Puisqu'on ne touche à rien :

$$
\forall\, t \in [\,t_j^R,\ t_{j+1}^R\,[\ :\qquad \mathrm{nbr}^k(t) = \mathrm{nbr}^k(t_j^R)
$$

et la valeur du compte, chaque jour, est ce qu'on possède au prix du jour :

$$
\mathrm{NAV}(t) \;=\; \sum_k \mathrm{nbr}^k(t)\times\mathrm{NAV}^k(t)
$$

C'est tout. Il n'y a rien d'autre à décider : les parts sont figées, les prix
$\mathrm{NAV}^k(t)$ font vivre la valeur.

**Conséquence importante — les poids dérivent.** Le poids *effectif* du membre $k$ au jour $t$
est la fraction de la valeur totale logée chez lui :

$$
w^k(t) \;=\; \frac{\mathrm{nbr}^k(t)\,\mathrm{NAV}^k(t)}{\mathrm{NAV}(t)} .
$$

Dès le lendemain du rebalancement, $w^k(t) \ne w_j^k$ : si le fonds $A$ monte plus vite que $B$,
sa poche grossit mécaniquement. Personne n'a rien tradé — c'est la performance qui déforme les
poids. Vouloir garder les poids constants exigerait de vendre du gagnant et racheter du perdant
**tous les jours**.

*Exemple, jour 1 : $A$ fait +100 %, $B$ 0 %.* Les prix des parts passent à
$\mathrm{NAV}^A = 200$, $\mathrm{NAV}^B = 100$. La valeur du compte :
$\mathrm{NAV} = 0{,}5\times 200 + 0{,}5\times 100 = 150$, soit **+50 %** — logique, la moitié du
compte a doublé. Les poids effectifs sont maintenant $100/150 = 2/3$ pour $A$ et $1/3$ pour $B$.

## 4. Au rebalancement suivant : compter, puis redéployer

À la date $t_{j+1}^R$, en **fin de journée**, deux opérations dans cet ordre :

**(a) On compte ce qu'on possède**, avec les *anciennes* parts (celles détenues depuis le
rebalancement précédent, donc celles « de la veille ») valorisées aux prix du jour :

$$
\mathrm{NAV}^{\mathrm{avl}}(t_{j+1}^R) \;=\; \sum_k \mathrm{nbr}^k(t_{j+1}^R - 1)\times\mathrm{NAV}^k(t_{j+1}^R)
$$

(« avl » = *available*, la richesse disponible). C'est le solde du compte ce soir-là — ni plus,
ni moins.

**(b) On redéploie tout** selon les nouveaux poids cibles $w_{j+1}^k$ (la nouvelle sélection),
avec la même règle « montant / prix de la part » qu'au départ :

$$
\mathrm{nbr}^k(t_{j+1}^R) \;=\; \frac{w_{j+1}^k \times \mathrm{NAV}^{\mathrm{avl}}(t_{j+1}^R)}{\mathrm{NAV}^k(t_{j+1}^R)}
$$

Un membre qui sort de la sélection ($w_{j+1}^k = 0$) voit ses parts vendues ; le produit finance
les entrants et les renforcements. Un entrant est acheté au niveau de prix $\mathrm{NAV}^k$ atteint
ce jour-là.

**Vérification (autofinancement)** : le rebalancement réalloue mais ne crée ni ne détruit de
l'argent. La valeur juste après vaut

$$
\sum_k \mathrm{nbr}^k(t_{j+1}^R)\times\mathrm{NAV}^k(t_{j+1}^R)
= \sum_k w_{j+1}^k \times \mathrm{NAV}^{\mathrm{avl}}(t_{j+1}^R)
= \mathrm{NAV}^{\mathrm{avl}}(t_{j+1}^R),
$$

c'est-à-dire exactement la valeur juste avant. **La NAV du portefeuille est donc continue à
travers le rebalancement** — aucun saut artificiel, aucune remise à zéro.

*Exemple, suite : au soir du jour 2, on rebalance vers 50/50.* (Jour 2 : $B$ fait +20 %, $A$ 0 % ;
prix des parts $\mathrm{NAV}^A = 200$, $\mathrm{NAV}^B = 120$.)
Solde disponible : $0{,}5\times 200 + 0{,}5\times 120 = 160$. Cibles : 80 euros par fonds.
Nouvelles parts : $\mathrm{nbr}^A = 80/200 = 0{,}4$ (on **vend** $0{,}1$ part du gagnant) et
$\mathrm{nbr}^B = 80/120 \approx 0{,}667$ (on **achète** $0{,}167$ part du retardataire).
Contrôle : $0{,}4\times 200 + 0{,}667\times 120 = 80 + 80 = 160$. ✓

## 5. Le rendement : un simple ratio de la NAV

Le compte a maintenant une valeur $\mathrm{NAV}(t)$ définie **chaque jour de bourse, sur une seule
série continue** (base 100 à $t_0^R$). Le rendement quotidien en découle — et de nulle part
ailleurs :

$$
r(t) \;=\; \frac{\mathrm{NAV}(t)}{\mathrm{NAV}(t-1)} \;-\; 1
$$

Et c'est pareil à toute échelle : le rendement sur n'importe quelle fenêtre de détention $D_H$
(une semaine, un semestre, une année, une période de rebalancement complète) se lit sur la même
courbe :

$$
r_{D_H}(t) \;=\; \frac{\mathrm{NAV}(t)}{\mathrm{NAV}(t-D_H)} \;-\; 1 .
$$

C'est le sens du schéma de la feuille 2 : une seule courbe $\mathrm{NAV}(t)$, et *tous* les
rendements (quotidiens pour les stats, par période pour l'évaluation) sont des ratios de points de
cette courbe. Pas de séries recollées, pas de base remise à 1 chaque année.

**Pourquoi la moyenne à poids figés est fausse — la démonstration en 3 lignes.** Développons le
rendement quotidien à partir de la définition (parts constantes ce jour-là) :

$$
1 + r(t)
= \frac{\sum_k \mathrm{nbr}^k\,\mathrm{NAV}^k(t)}{\mathrm{NAV}(t-1)}
= \sum_k \underbrace{\frac{\mathrm{nbr}^k\,\mathrm{NAV}^k(t-1)}{\mathrm{NAV}(t-1)}}_{=\;w^k(t-1)}
  \times \frac{\mathrm{NAV}^k(t)}{\mathrm{NAV}^k(t-1)}
$$

d'où, puisque $\sum_k w^k(t-1) = 1$ :

$$
r(t) \;=\; \sum_k w^k(t-1)\; r_k(t) .
$$

Le rendement du portefeuille est bien une moyenne pondérée des rendements des membres — mais
pondérée par les **poids effectifs de la veille** $w^k(t-1)$, ceux qui dérivent. Écrire
$r_{\text{strat}}(t) = \sum_k w_j^k\, r_k(t)$ avec les poids **cibles constants** n'est correct que
le premier jour ; ensuite, c'est supposer qu'on remet le portefeuille à $w_j^k$ chaque soir — un
rebalancement quotidien caché, qui vend systématiquement les gagnants et recharge les perdants
sans payer le moindre trade.

*Exemple, jour 2 (avant le rebalancement du soir) : $A$ 0 %, $B$ +20 %.* Poids de la veille :
$2/3$ et $1/3$. Vrai rendement : $r = \tfrac{2}{3}\times 0 + \tfrac{1}{3}\times 20\,\% = 6{,}67\,\%$
— cohérent avec la NAV : $160/150 - 1 = 6{,}67\,\%$. ✓ La moyenne à poids figés donnerait
$\tfrac{1}{2}\times 20\,\% = 10\,\%$ : **faux**. (C'est l'exemple Apple/Coca de la NOTE_MATHS,
retrouvé ici depuis les parts.)

Récapitulatif de l'exemple complet :

| jour | événement | $\mathrm{NAV}^A$ | $\mathrm{NAV}^B$ | parts $A$ / $B$ | $\mathrm{NAV}(t)$ | $r(t)$ |
|---|---|---|---|---|---|---|
| $t_0^R$ | achat 50/50 | 100 | 100 | 0,5 / 0,5 | 100 | — |
| jour 1 | $A$ +100 % | 200 | 100 | 0,5 / 0,5 | 150 | +50 % |
| jour 2 | $B$ +20 % | 200 | 120 | 0,5 / 0,5 | 160 | +6,67 % |
| $t_1^R$ soir | rebalancement 50/50 | 200 | 120 | 0,4 / 0,667 | 160 | (continuité) |

## 6. Les feuilles telles quelles : deux membres AL et AY

Ce qui précède, écrit par le chef pour deux membres ($AL$, $AY$) et $\mathrm{NAV}_0 = 100$ :

$$
\mathrm{nbr}^{AL}(t_0^R) = \frac{w_0^{AL}\times\mathrm{NAV}_0}{\mathrm{NAV}^{AL}(t_0^R)},
\qquad
\mathrm{nbr}^{AY}(t_0^R) = \frac{w_0^{AY}\times\mathrm{NAV}_0}{\mathrm{NAV}^{AY}(t_0^R)}
$$

$$
\forall\, t \in [\,t_0^R,\ t_1^R\,[\ :\quad
\mathrm{nbr}^{AL}(t)=\mathrm{nbr}^{AL}(t_0^R),\quad
\mathrm{nbr}^{AY}(t)=\mathrm{nbr}^{AY}(t_0^R)
$$

$$
\mathrm{NAV}(t) = \mathrm{nbr}^{AL}(t)\times\mathrm{NAV}^{AL}(t)
                + \mathrm{nbr}^{AY}(t)\times\mathrm{NAV}^{AY}(t)
$$

À $t_1^R$, à la fin de la journée :

$$
\mathrm{NAV}^{\mathrm{avl}}(t_1^R)
   = \mathrm{nbr}^{AL}(t_1^R-1)\times\mathrm{NAV}^{AL}(t_1^R)
   + \mathrm{nbr}^{AY}(t_1^R-1)\times\mathrm{NAV}^{AY}(t_1^R)
$$

$$
\mathrm{nbr}^{AL}(t_1^R) = \frac{w_1^{AL}\times\mathrm{NAV}^{\mathrm{avl}}(t_1^R)}{\mathrm{NAV}^{AL}(t_1^R)},
\qquad \mathrm{nbr}^{AY}(t_1^R) = \dots\ \text{(idem)}
$$

puis pour tout $t \in [\,t_1^R,\ t_2^R\,[$ : parts constantes, même formule de $\mathrm{NAV}(t)$,
et $r(t) = \mathrm{NAV}(t)/\mathrm{NAV}(t-1) - 1$.

## 7. Correspondance avec le notebook 05b

- **Ce que la méthode confirme.** La combinaison *figée* ($\sum_k w_k r_k$ à poids constants) est
  exactement le rebalancement quotidien caché démontré en §5 — le bug déjà corrigé au §6 du
  notebook ($t$ 1,14 → 0,94). La méthode du chef et la combinaison « dérive » disent la même chose
  sur ce point.
- **L'équivalence, au sein d'une période de tenue.** En divisant $\mathrm{NAV}(t)$ par sa valeur au
  rebalancement (et en substituant la définition des parts) :

$$
\frac{\mathrm{NAV}(t)}{\mathrm{NAV}(t_j^R)}
= \sum_k w_j^k \times \frac{\mathrm{NAV}^k(t)}{\mathrm{NAV}^k(t_j^R)}
$$

  c'est-à-dire : le facteur de croissance du portefeuille = moyenne pondérée (aux poids cibles du
  départ) des facteurs de croissance des membres **depuis le rebalancement**. C'est exactement le
  $N(t) = \sum_k w_k\,\mathrm{NAV}_k(t)$ du notebook, où les $\mathrm{NAV}_k$ sont rebasées à 1 en
  début de période. Sur une période donnée, `r_dr_eq` et la méthode en parts produisent donc les
  mêmes rendements quotidiens.
- **Ce qui change vraiment** par rapport à `run_strategy` :
  1. **Une seule NAV continue de bout en bout** (base 100 à $t_0^R$), au lieu de blocs annuels
     rebasés à 1 puis concaténés en rendements ; le raccord entre années n'est plus une couture de
     code (`ry.iloc[0] = navc.iloc[0] - 1`) mais une conséquence démontrée de l'autofinancement (§4).
  2. **Les parts $\mathrm{nbr}^k$ sont la variable d'état** ; valeur, poids effectifs et rendements
     en découlent — le rebalancement (vendre les sortants, financer les entrants) devient explicite
     et vérifiable (continuité de la NAV à chaque $t^R$).
  3. Les $\mathrm{NAV}^k$ des membres sont calculées **une fois sur tout leur historique** et on y
     « achète » au niveau atteint $\mathrm{NAV}^k(t_j^R)$ — pas de re-cumul par bloc.
  4. Toute évaluation (excès annuel, semestriel, fenêtre $D_H$ quelconque) se lit sur la même série
     $\mathrm{NAV}(t)$ — une définition unique du rendement à toutes les échelles.
