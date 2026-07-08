# Pondérer le portefeuille top-$K$ autrement que $1/K$ — deux pistes (note maths)

> Prolonge le §6 du notebook `05b`. On garde **tout** le moteur en parts (§6.1) : la seule chose
> qu'on change, c'est le **vecteur de poids cibles** $w=(w_k)_{k\in\mathcal{S}_Y}$ posé à chaque
> coupe. Rien ici n'est encore codé — on pose les maths.

## 0. D'où viennent les poids (rappel)
À chaque coupe $t^R_Y$, on transforme les poids en nombres de parts :
$$\mathrm{nbr}^k_Y=\frac{w_k\,W(t^R_Y)}{\mathrm{NAV}^k(t^R_Y)}.$$
Les poids n'entrent **qu'ici**. Contraintes gardées partout : **long-only** $w_k\ge0$ et
**entièrement investi** $\sum_{k\in\mathcal{S}_Y}w_k=1$. Aujourd'hui $w_k=\tfrac1K$ : on met le
**même capital** sur chaque membre.

## 1. L'idée centrale : répartir le *capital* ≠ répartir le *risque*
Mettre $\tfrac1K$ du capital sur un membre **2× plus volatil**, c'est mettre **2× plus de risque**
sur lui. Le $\tfrac1K$ égalise les montants, pas les risques → le panier est en réalité piloté par
ses membres les plus agités. Les deux pistes ci-dessous corrigent ça : la piste 1 avec les
**volatilités** seules, la piste 2 en ajoutant les **corrélations**.

**Discipline point-in-time (obligatoire, cf. §6.3).** Tout ($\sigma_k$, $\Sigma$) s'estime sur les
rendements **passés** $s\le t^R_Y$, et s'applique à l'année **suivante** $Y+1$. Jamais de futur.

## 2. Piste 1 — égaliser le risque : l'inverse-volatilité
**Intuition.** On pèse chaque membre à l'**inverse** de sa volatilité : le calme reçoit plus, l'agité moins.

$$\boxed{\;w_k=\frac{1/\sigma_k}{\displaystyle\sum_{j\in\mathcal{S}_Y}1/\sigma_j}\;}\qquad
\sigma_k=\mathrm{std}\big(r_k(s)\big)_{s\le t^R_Y}\times\sqrt{252}.$$

**Exemple chiffré** (3 membres, $\sigma_A=12\%,\ \sigma_B=18\%,\ \sigma_C=36\%$).
$1/\sigma = 8{,}33\ ;\ 5{,}56\ ;\ 2{,}78$, somme $16{,}67$ →

| membre | $\sigma_k$ | $1/K$ | budget risque $w_k\sigma_k$ | **inverse-vol** $w_k$ | budget risque $w_k\sigma_k$ |
|---|---|---|---|---|---|
| A | 12 % | 33,3 % | 0,040 | **50,0 %** | **0,060** |
| B | 18 % | 33,3 % | 0,060 | **33,3 %** | **0,060** |
| C | 36 % | 33,3 % | **0,120** | **16,7 %** | **0,060** |

En $1/K$, C pèse **3× plus** de risque que A (0,120 vs 0,040). En inverse-vol, **tous à 0,060** :
le risque est réparti à parts égales.

**Pourquoi c'est exactement égal (si corrélations nulles).** Avec $\rho_{ij}=0$, la variance du
panier se sépare, $\sigma_p^2=\sum_k w_k^2\sigma_k^2$, et chaque membre y apporte $w_k^2\sigma_k^2$. Or
$$w_k\sigma_k=\frac{(1/\sigma_k)\,\sigma_k}{\sum_j 1/\sigma_j}=\frac{1}{\sum_j 1/\sigma_j}=\text{const}
\ \Rightarrow\ w_k^2\sigma_k^2=\text{const}\quad\forall k.$$
Chaque membre apporte **la même variance** — d'où « budget de risque égal ». Ne demande **que** les
$\sigma_k$ (la diagonale), jamais les corrélations.

## 3. Piste 2 — tenir compte des corrélations
**Intuition.** L'inverse-vol ignore que deux membres **corrélés** parient sur la même chose : leur
risque commun est compté deux fois. On introduit la matrice de covariance des $K$ membres,
estimée point-in-time ($s\le t^R_Y$) :
$$\Sigma_{ij}=\mathrm{Cov}(r_i,r_j),\qquad \rho_{ij}=\frac{\Sigma_{ij}}{\sigma_i\sigma_j},\qquad
\sigma_p^2=w^\top\Sigma\,w.$$

**Décomposer le risque (identité d'Euler).** $\sigma_p$ est homogène de degré 1 en $w$, donc le
risque total se répartit exactement entre membres :
$$\mathrm{RC}_k=\frac{w_k(\Sigma w)_k}{\sigma_p}\ \text{(contribution du membre $k$)},\qquad
\sum_{k\in\mathcal{S}_Y}\mathrm{RC}_k=\sigma_p.$$
*(Si $\rho_{ij}=0$, $\mathrm{RC}_k=w_k^2\sigma_k^2/\sigma_p$ : on retombe sur la piste 1.)*

**(a) Variance minimale (GMV) — « le panier le moins risqué ».**
$$\boxed{\;w^\star=\arg\min_{\,\mathbf{1}^\top w=1} w^\top\Sigma\,w
\;=\;\frac{\Sigma^{-1}\mathbf{1}}{\mathbf{1}^\top\Sigma^{-1}\mathbf{1}}\;}\quad(\text{si }\Sigma\succ0),$$
avec $w_k\ge0$ → programme quadratique (numérique). *Exemple* (2 membres, $\sigma_A=10\%,\ \sigma_B=20\%$) :
- corrélation $\rho=0$ → $w^\star\propto 1/\sigma_k^2 = (100,\,25)$ → $(80\%,\,20\%)$ *(l'inverse-**variance**, encore plus penché vers le calme A que l'inverse-vol)* ;
- corrélation $\rho=0{,}3$ → $w^\star\approx(89{,}5\%,\,10{,}5\%)$ : **plus B ressemble à A, moins il diversifie, plus le GMV l'abandonne** au profit de A.

GMV = **risque pur, aucune vue de rendement** ; concentre sur le peu-volatil / peu-corrélé ;
**très sensible** à l'erreur d'estimation de $\Sigma$ (l'inversion $\Sigma^{-1}$ amplifie le bruit).

**(b) Contributions au risque égales (ERC / *risk parity*) — « chacun le même risque ».**
$$\boxed{\;\text{trouver }w:\quad w_k(\Sigma w)_k=w_j(\Sigma w)_j\ \ \forall k,j\;},\qquad w_k\ge0,\ \sum_k w_k=1.$$
Pas de forme fermée → point fixe / numérique. C'est la généralisation propre de la piste 1 :
- si toutes les corrélations sont **égales** ($\rho_{ij}=\rho$) → **redonne l'inverse-vol** ;
- si en plus les vols sont égales ($\Sigma=\sigma^2 I$) → **redonne $1/K$**.

## 4. La hiérarchie — chaque cran relâche une hypothèse
$$\underbrace{1/K}_{\substack{\sigma\ \text{égales}\\ \rho=0}}\ \subset\
\underbrace{\text{inverse-vol}}_{\substack{\sigma\ \text{libres}\\ \rho=0}}\ \subset\
\underbrace{\text{ERC},\ \text{GMV}}_{\Sigma\ \text{complète, risque seul}}\ \subset\
\underbrace{\text{moyenne-variance (Markowitz)}}_{+\ \text{vue de rendement }\mu}$$

| méthode | ce qu'elle utilise | hypothèse qu'elle lâche |
|---|---|---|
| $1/K$ | rien | vols égales, $\rho=0$ |
| inverse-vol (piste 1) | les $\sigma_k$ | vols libres ; garde $\rho=0$ |
| ERC / GMV (piste 2) | tout $\Sigma$ | corrélations libres |
| Markowitz | $\Sigma$ **et** $\mu$ | + une vue de rendement |

ERC et GMV sont au **même étage d'information** ($\Sigma$, risque seul) mais visent des choses
différentes (risque **égal** vs risque **minimal**). Sur l'exemple à 3 membres, on penche de plus
en plus vers le calme A : $1/K\ (33\%) \to$ inverse-vol $(50\%) \to$ GMV$_{\rho=0}\ (64\%)$.

## 5. Garde-fou — pourquoi $1/K$ est si dur à battre
- Avec $K=4$, $\Sigma$ est $4\times4$ = **10 paramètres** (4 variances + 6 covariances) estimés sur
  des fenêtres **courtes** et *ragged* → forte **erreur d'estimation**.
- **DeMiguel–Garlappi–Uppal (2009, « Optimal versus naive diversification »)** : hors-échantillon,
  $1/N$ est difficile à battre — le gain d'optimisation est **mangé** par l'erreur d'estimation.
- ⇒ La **piste 1** (n'a besoin que des $\sigma_k$, robuste) est un premier pas plus sûr que la
  **piste 2** (a besoin de tout $\Sigma$, fragile — surtout GMV via $\Sigma^{-1}$).

## 6. Ce qu'il faudrait coder (étape future, pas ici)
Un seul point de branchement : `_poids` (cellule 38), qui renverrait $1/\sigma_k$ (piste 1) ou la
solution GMV/ERC de $\Sigma$, estimés point-in-time. Le moteur en parts consomme déjà n'importe
quel vecteur $w$ — donc `_parts_engine` reste inchangé. Cette note ne fait que **poser les maths**.
