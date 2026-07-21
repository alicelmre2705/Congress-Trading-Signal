# Plan des slides — « Comprendre les portefeuilles des élus, en images »
### (V2 du plan — figure-first) · Extension de la Partie II du deck `SLIDES_DONNEES_S1S2_V2.tex`

---

## 0 · L'idée, corrigée

Ce deck n'est **pas** un récit qui court vers un verdict. C'est un **tour visuel pour comprendre la donnée** :
on reprend le **notebook 05B** et, **chaque fois qu'il y a un résultat, on le montre en image** ; on ajoute les
figures descriptives du **07** (comprendre les portefeuilles) et les fiches du **09** (la donnée sous tous les
angles). Le principe de chaque slide : **« voici à quoi ça ressemble »**, une figure par idée.

- **Colonne vertébrale = les figures.** Il y en a **59** dans les trois notebooks (05b : 27 · 07 : 20 · 09 : 12).
  On en retient **~40** (on enlève seulement le ticker et l'autopsie).
- **Exclus** (ta consigne) : l'**analyse par ticker** (09 §10-11) et l'**autopsie** (05b §13-17 : IC, placebo,
  Deflated Sharpe, sélection/allocation, commission, dimensions).
- **Le point-clé que tu as demandé** : « voici à quoi ressemble le portefeuille des **4 premiers** » →
  section E, avec la NAV du top-4 **et** les 4 fiches individuelles des membres qu'on copie.

**Le gabarit visuel** (déjà utilisé dans le 07, cellule 61 — `fiche_membre`) : **4 panneaux** = (A) NAV base 100
vs SPY · (B) timeline des trades (taille en $, achats vert / ventes rouge) · (C) poids empilés des 8 positions
principales · (D) excès annuel vs SPY. C'est la brique « à quoi ressemble un portefeuille ».

---

## 1 · Les règles du chef (rappel court)

Une idée par slide (titre = message) · plan annoncé · chronologie · **≤ 3 chiffres légendés** · zéro mini-détail ·
choix explicites · public qui découvre. Ici : **la figure porte l'idée**, le texte se limite à un titre-message
+ 1 phrase de légende + ≤ 2 chiffres.

---

## 2 · Le fil : six sections visuelles

| Section | Ce qu'on **voit** | Figures | Source |
|---|---|---:|---|
| **A · À quoi ressemble la population** | qui trade, combien, via qui, quelles tailles, quel délai | 5 | 07 §2 |
| **B · À quoi ressemble un portefeuille** | la valeur qui monte, les 266 d'un coup, la composition, le style (concentration/durée/secteurs) | 7 | 05b §1-2 · 07 §3 · 09 §4 |
| **C · Six membres, six portefeuilles** | la galerie des styles (fiches 4 panneaux) | 6 | 07 §5 |
| **D · Qui bat le marché ?** | éligibilité, les 2 mètres, les distributions de talent | 5 | 05b §3-4 · 07 §4 |
| **E · Copier les meilleurs (dont les 4 premiers)** | la sélection, **le portefeuille du top-4**, les réglages | 8 | 05b §5-12 |
| **F · La fiche complète d'un membre** *(option)* | un membre sous 6 angles = le livrable | 6 | 09 §2-9 |

Chaque section s'ouvre sur une **question** et se ferme sur une **image-réponse**. Cœur = A + B + C + E ;
D allège, F est une réserve « on sait tout dire d'une personne ».

---

## 3 · Le plan, slide par slide (figure-first)

> Format : **titre-message** · *ce que montre la figure* · **chiffres légendés** · `figure (notebook, cellule)` ·
> statut PNG.
> Statut : **PRÊTE** = déjà exportée en `docs/figs/` · **À GÉNÉRER** = replay scratchpad (façon `gen_figs_nb09.py`,
> sans ré-écrire les CSV).

---

### Section A — À quoi ressemble la population *(07 §2)*

*Intercalaire : « Qui sont ces gens, combien tradent-ils, et comment ? »*

**A1 — « La population dans le temps »**
- *4 sous-graphes* : transactions/an · membres actifs/an · achats vs ventes/an · part OCR (scans)/an.
- *Chiffres* : 118 029 trades exploitables · ~370 membres.
- `07, cell 22`. **À GÉNÉRER.**

**A2 — « Une poignée de membres fait l'essentiel »**
- *Courbe de Lorenz + top-10 membres* — l'inégalité de l'activité.
- *Chiffres* : **Gini 0,86** · les 2 plus actifs = **41 %** des trades.
- `07, cell 25`. **À GÉNÉRER.**

**A3 — « Et souvent, c'est le conjoint qui trade »**
- *Répartition par trade vs par membre* (chambre / parti / propriétaire).
- *Chiffres* : conjoint **37,9 %** > élu 25,4 %.
- `07, cell 27`. **À GÉNÉRER.**

**A4 — « Des montants déclarés en fourchettes »**
- *Distribution des fourchettes STOCK Act*.
- *Chiffre* : **75 %** des trades à la 1ʳᵉ tranche (milieu 8 000 $).
- `07, cell 30`. **À GÉNÉRER.** *(Choix : montant = milieu de fourchette.)*

**A5 — « Ils déclarent en moyenne 27 jours après »**
- *Délai de déclaration (histogramme) + part en retard (>45 j) par an*.
- *Chiffres* : médiane **27 j** · **11,7 %** en retard.
- `07, cell 32`. **À GÉNÉRER.** *(Choix : on date à la divulgation, jamais à la transaction.)*

*Réponse : marché ultra-concentré (Gini 0,86), souvent via le conjoint (38 %), déclaré ~27 j après.*

---

### Section B — À quoi ressemble un portefeuille *(05b §1-2 · 07 §3 · 09 §4)*

*Intercalaire : « On ne déclare que des transactions — à quoi ressemble le portefeuille qu'on en reconstruit ? »*

**B1 — « Un portefeuille se reconstruit trade par trade »**
- *La valeur V(t) d'un membre en $ ; pointillés = les achats.* On voit la valeur sauter à chaque apport.
- *Chiffre* : reconstruction **FIFO** ; ~135 trades (Pelosi).
- `05b, cell 11`. **PRÊTE** (`fig_05b_pelosi_valeur.png`). *(Choix : FIFO, short interdit.)*

**B2 — « Les 266 portefeuilles reconstruits, d'un coup »**
- *Spaghetti : chaque membre en base 100 (échelle log), SPY en noir.*
- *Chiffres* : **266** reconstruits · CAGR médian **12,8 %** · Sharpe médian **0,71**.
- `05b, cell 17`. **PRÊTE** (`fig_05b_spaghetti_nav.png`).

**B3 — « Ce qu'il y a dedans, et comment ça tourne »**
- *Valeur (log) + composition empilée des positions dans le temps* — le portefeuille « vu de l'intérieur ».
- *Chiffres* : HHI **0,33** → N_eff **3,0** · plus grosse ligne **43 %** en moyenne.
- `09, cell 47`. **À GÉNÉRER** (ou promouvoir depuis l'annexe `fig_09_portefeuille`).

**B4 — « Peu de lignes à la fois »**
- *Nombre effectif de positions (1/HHI) + activité vs diversité de tickers.*
- *Chiffre* : N_eff médian **4,5** positions.
- `07, cell 39`. **À GÉNÉRER.**

**B5 — « Ils gardent longtemps »**
- *Durées de détention fermées + courbe de survie Kaplan-Meier.*
- *Chiffre* : détention médiane **910 j** (KM).
- `07, cell 44`. **À GÉNÉRER.** *(Choix : KM, positions non revendues censurées.)*

**B6 — « Chacun a ses secteurs de prédilection »**
- *Heatmap membre × secteur GICS* (part du notional).
- *Chiffre* : secteur dominant le plus fréquent = informatique (**82** membres).
- `07, cell 48`. **À GÉNÉRER.**

**B7 — « Un turnover faible, un peu de saisonnalité »** *(optionnel)*
- *Turnover annualisé + saisonnalité mensuelle.*
- *Chiffre* : turnover médian **0,24×/an**.
- `07, cell 41`. **À GÉNÉRER.**

*Réponse : des portefeuilles concentrés (N_eff 4,5), tenus longtemps (910 j), penchés sur quelques secteurs.*

---

### Section C — Six membres, six portefeuilles *(07 §5)* — le cœur « à quoi ça ressemble »

*Intercalaire : « Concrètement, à quoi ressemblent des portefeuilles réels ? »*

Chaque slide = **une fiche 4 panneaux** (NAV vs SPY · timeline des trades · poids des 8 positions · excès annuel),
titre = nb trades | Sharpe | N_eff | % conjoint | lag médian.

**C1 — Nancy Pelosi** — l'hyper-médiatisée · `07, cell 63` · **135 trades, Sharpe 0,77, N_eff 3,0, conjoint 71 %**.
**C2 — Ro Khanna** — l'anti-Pelosi : des milliers de micro-trades diversifiés · `07, cell 65` · **~32 700 trades, 975 tickers**.
**C3 — Michael McCaul** — 2ᵉ plus actif, fortune familiale · `07, cell 67` · **~16 000 trades**.
**C4 — Josh Gottheimer** — le « day-trader », gros turnover · `07, cell 69` · **~3 000 trades**.
**C5 — Tommy Tuberville** — déclarations souvent tardives · `07, cell 71`.
**C6 — Richard Burr** — le cas COVID février 2020 (zoom des ventes avant le krach) · `07, cell 73` (+ `_explication_burr_covid_2020.png`).

Toutes **À GÉNÉRER** (fiches inline du 07). *(On peut aussi n'en garder que 4 si trop long — Pelosi, Khanna,
Gottheimer, Burr.)*

*Réponse : six styles radicalement différents — d'où l'idée de mesurer chacun, pas « le Congrès ».*

---

### Section D — Qui bat le marché ? *(05b §3-4 · 07 §4)*

*Intercalaire : « Peut-on repérer ceux qui ont vraiment un talent ? »*

**D1 — « Qui est jugeable : 223 sur 266 »**
- *Boîte d'éligibilité n_trades × n_jours* (coin haut-droit = éligible).
- *Chiffres* : **266 → 223** · seuil ≥ 10 trades **et** ≥ 126 j.
- `05b, cell 21`. **PRÊTE** (`fig_05b_eligibilite.png`).

**D2 — « Deux mètres : l'écart brut (IR) et l'alpha ajusté (appraisal) »**
- *Régression d'un membre : nuage r_membre vs r_SPY, droite α+β.*
- *Chiffres* : IR (suppose β=1) · appraisal = α / risque spécifique.
- `05b, cell 24`. **PRÊTE** (`fig_05b_regression_demo.png`). *(Choix : classer à l'appraisal.)*

**D3 — « La mesure trouve peu : 20 gagnants, ~11 par hasard »**
- *Distribution des t (IR) des 223 éligibles* ; barre du seuil 1,645.
- *Chiffres* : **20** significatifs · **~11** attendus par pur hasard.
- `05b, cell 27`. **PRÊTE** (`fig_05b_hist_t.png`).

**D4 — « IR gonflé ou vrai talent ? le rôle du β »**
- *Scatter IR vs appraisal, couleur = β* ; au-dessus de la diagonale = IR gonflé par le β.
- `05b, cell 32`. **À GÉNÉRER** (`fig_05b_scatter_ir_appr` existe côté 05b/figures).

**D5 — « Sur l'ensemble, un tiers bat le SPY »**
- *Distribution des Sharpe + excès de CAGR + nuage risque/rendement.*
- *Chiffre* : **34 %** des éligibles battent le SPY (≈ un tirage).
- `07, cell 52`. **À GÉNÉRER.**

*Réponse : une vingtaine ressortent, mais à peine plus que le hasard — d'où le test « copier les meilleurs ».*

---

### Section E — Copier les meilleurs : à quoi ressemble le portefeuille des 4 premiers *(05b §5-12)*

*Intercalaire : « Et si on copiait chaque année les mieux classés ? »*

**E1 — « On choisit qui copier, chaque année, sans regarder le futur »**
- *Nb de significatifs à chacune des 13 coupes annuelles (walk-forward), IR vs appraisal.*
- `05b, cell 36`. **PRÊTE** (`fig_05b_nsig_par_an.png`). *(Choix : walk-forward, point-in-time.)*

**E2 — « Voici à quoi ressemble le portefeuille des 4 premiers : sa NAV »**
- *NAV du copy-trading top-4, sélection IR vs appraisal vs SPY (base 100), rebalancement annuel.*
- *Chiffres* : top-4 IR **+3,1 %/an** d'excès · mais **β 1,20**, **α ≈ 0** (à énoncer sobrement, sans en faire le
  clou).
- `05b, cell 44`. **PRÊTE** (`fig_05b_nav_top4.png`).

**E3 — « Et voici les 4 portefeuilles qu'on copie » — NOUVELLE, le visuel que tu veux**
- *4 fiches 4 panneaux des membres en tête du classement (les « 4 premiers ») : à quoi ressemble chacun.*
- *Chiffres* : les 4 noms + Sharpe de chacun.
- **À GÉNÉRER** : appliquer le helper `fiche_membre` (07 cell 61) aux 4 membres sélectionnés (choisir l'année de
  référence — dernière coupe ou top-4 IR global ; à trancher).

**E4 — « Combien copier ? le choix de K »**
- *NAV pour K walk-forward (K de 4 à 20), IR vs appraisal vs SPY.*
- *Chiffre* : meilleur cas **+4,1 %/an, t 1,58** (K walk-forward, sélection IR).
- `05b, cell 51`. **PRÊTE** (`fig_05b_k_et_cadence.png`).

**E5 — « Et si on rééquilibre tous les 6 mois ? »** *(optionnel)*
- *NAV top-4 IR : annuel vs 6 mois vs SPY.*
- *Chiffre* : 6 mois **+0,4 %/an, t 0,14**.
- `05b, cell 55`. **À GÉNÉRER** (ou fondre dans E4).

**E6 — « Et si on change la répartition du capital ? »**
- *NAV top-4 IR : 1/K vs inverse-vol vs ERC vs GMV.*
- *Chiffre* : hiérarchie 1/K ⊂ inverse-vol ⊂ ERC/GMV — rien ne décroche.
- `05b, cell 63`. **PRÊTE** (`fig_05b_ponderations.png`). *(Choix : garde-fou 1/N difficile à battre.)*

**E7 — « Autre règle : classer au Sharpe brut »**
- *Sharpe des membres à ≥ 126 j ; éligibles au-dessus du seuil 0,4.*
- *Chiffre* : **224** éligibles (règle Sharpe).
- `05b, cell 80`. **PRÊTE** (`fig_05b_hist_sharpe.png`).

**E8 — « Même en balayant K, le t plafonne »**
- *Balayage K (2→20) sous sélection Sharpe : excès moyen et t.*
- *Chiffre* : **t max 1,22** (toutes grilles testées) — sous le seuil.
- `05b, cell 90`. **PRÊTE** (`fig_05b_balayage_k.png`).

*Réponse : le portefeuille des 4 premiers ressemble à un SPY un peu levier — de l'excès brut, mais porté par le β.*

---

### Section F — La fiche complète d'un membre *(09 §2-9)* — option « on sait tout dire d'une personne »

*Une réserve visuelle : un même membre (Pelosi) décliné sous 6 angles = la structure du livrable `membres.csv`.*
À montrer **soit** en déroulé (6 slides), **soit** en une planche contact.

- **F1 identité** `09, cell 31` · **F2 activité** `09, cell 39` · **F3 portefeuille** `09, cell 47` ·
  **F4 durées** `09, cell 55` · **F5 secteurs** `09, cell 63` · **F6 perf vs marché** `09, cell 71`.
- Bonus disponibles : track par trade `09, cell 80` · comportement `09, cell 88` · année par année `09, cell 111` ·
  3 distributions de contrôle `09, cell 121`.
- Figures `fig_09_*` en partie déjà exportées (`docs/figs/`) — le reste **À GÉNÉRER**.

---

## 4 · Ce qu'on met de côté (ta consigne)

| Écarté | Ce que c'est | Figures concernées |
|---|---|---|
| **Analyse par ticker** | flux Congrès sur un titre, NVDA vu du Congrès, excès à 21/63 j | 09 §10-11 (`cell 103`) + `tickers.csv` |
| **Autopsie** | IC, puissance/MDE, placebo, Deflated Sharpe, sélection/allocation, commission, dimensions | 05b §13-17 (`cells 95→144`) |
| **Ledoit-Wolf, ERC/GMV détaillés** | shrinkage de covariance | 05b §10 (`cell 75`) |
| **Extrêmes vs bruit, comportement↔perf** | « et le hasard ? » (saveur autopsie) | 07 §4.2-4.3 (`cells 54, 56`) |

---

## 5 · Les chiffres à retenir (légende obligatoire)

| Chiffre | Ce que c'est | Slide |
|---|---|---|
| **118 029** | trades exploitables (ticker coté + prix fiable) | A1 |
| **Gini 0,86** | concentration des trades (2 membres = 41 %) | A2 |
| **37,9 %** | trades passés par le conjoint | A3 |
| **27 j** | délai médian de déclaration | A5 |
| **266 / 223** | portefeuilles reconstruits / membres jugeables | B2, D1 |
| **N_eff 4,5 · 910 j** | positions effectives (médiane) / détention médiane (KM) | B4, B5 |
| **20 → ~11** | significatifs à l'IR / attendus par pur hasard | D3 |
| **34 %** | éligibles qui battent le SPY | D5 |
| **+3,1 %/an · β 1,20 · α≈0** | portefeuille top-4 (K=4 fixe, sélection IR) | E2 |
| **t 1,58 / t 1,22** | meilleur cas (K walk-forward IR) / max règle Sharpe | E4, E8 |

**Anti-confusion** : **+3,1 %/an** (top-4, en année) ≠ **+3,11 %/trade** (nb06) · **β 1,20** (top-4 K=4 fixe) ≠
config **t 1,58** (K walk-forward, β 1,17) · **266** ≠ **223** ≠ **224**.

---

## 6 · Prérequis avant d'écrire les slides

1. **Générer les figures « À GÉNÉRER »** en rejouant 05b/07/09 en scratchpad (un namespace, `plt.show`→savefig
   dpi 200 ; **sauter la cellule `to_csv`** ; asserts du notebook comme garde-fous) — les figures inline ne sont
   pas encore des PNG de slides.
2. **Trancher E3** : quels « 4 premiers » ? (top-4 IR global, ou top-4 de la dernière coupe walk-forward) — puis
   générer leurs 4 fiches avec `fiche_membre`.
3. **Décider la longueur** : cœur A+B+C+E ≈ **24 slides** ; +D (5) +F (6) → jusqu'à ~35. On peut réduire C à 4
   membres et rendre B7/E5/F optionnels.
4. **Positionnement** : ces slides étendent la Partie II du deck V2 ; renuméroter/insérer proprement et **grep
   les renvois** après.
5. Style : **la figure porte l'idée** — titre-message + 1 phrase + ≤ 2 chiffres, jamais de tableau dense.

---

*Fichier : `00_S1S2_donnees/docs/PLAN_SLIDES_BACKTEST.md` (V2, figure-first). Squelette à valider avant
d'écrire les slides.*
