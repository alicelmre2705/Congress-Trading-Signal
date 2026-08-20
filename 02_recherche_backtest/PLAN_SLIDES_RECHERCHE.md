# Plan du deck — `02_recherche_backtest/SLIDES_RECHERCHE.tex`

> **✅ Écrit et compilé** — `SLIDES_RECHERCHE.pdf`, **111 pages**, 91 frames, 64 figures,
> zéro débordement. `tectonic -X compile SLIDES_RECHERCHE.tex` depuis `02_recherche_backtest/`.
>
> **L'objet du deck** : à la fin, on a compris le dossier `02_recherche_backtest/` de `main` —
> ce qu'il contient, dans quel ordre ça s'est fait, et ce que ça vaut.
> **Le deck épouse la structure du dossier.**

| partie | l'objet du dossier | pages |
|---|---|---|
| 0 | ouverture — la question, les deux dates, comment lire | 1--8 |
| 1 | `tables_membres_tickers` + `tables/` + `tools/` — **le socle** | 9--14 |
| 2 | `1_copier_les_membres/` — **la strate membre** | 15--40 |
| 3 | `2_noter_les_titres/` — **le virage** | 41--70 |
| 4 | `3_livrable_M3/` — **le livrable** | 71--94 |
| 5 | `PISTES_TESTEES.md` + les limites | 95--105 |
| — | annexes (le seul endroit à tableau dense) | 106--111 |

**Le dispositif qui tient l'ensemble** : la *carte du dossier* (`\cartefig{k}`), redessinée à
l'ouverture de chaque partie avec le curseur « vous êtes ici » — le même principe que `\pipefig{k}`
dans `SLIDES_DONNEES`.

**Style** : thème Madrid, barre `helec` `#3B6EA5` — **resserré**. Deux couleurs de chrome au lieu de
huit, `\tuile` en cartouche à filet, `\carte` en hauteur naturelle, `\bandlecture` neutre et
`\reserve` ambre à la place de `\repband` vert et `\choixbox` rouge, `\fil{partie}{source}` en
tête de chaque slide.

**Les règles du chef** (`_archive/docs/PLAN_SLIDES_BACKTEST.md`) sont respectées : une idée par
slide, titre = message, chronologie, **≤ 3 chiffres légendés**, la figure porte l'idée, **jamais de
tableau dense dans le corps** — les balayages complets sont en annexe.

**La slide 2.20** (« C'était mesurable d'avance ») est faite **sans figure**, en citant
`PISTES_TESTEES.md`, strate 2 : les §13--§17 de `copier_les_membres.ipynb` ne sont pas dans le
notebook courant.
---

## Partie 0 · Ouverture — 6 slides

| réf | titre-message | figure |
|---|---|---|
| 0.1 | Treize ans de déclarations, une question : peut-on en tirer une stratégie ? | `figs/flux.png` |
| 0.2 | **La carte du dossier — deux familles, trois étapes, ~90 pistes** | schéma TikZ à créer |
| 0.3 | Onze mots à connaître avant de commencer | `\badge` ×11 |
| **0.4** | **τ et δ : le STOCK Act crée deux dates, une seule est investissable** | TikZ 2 nœuds + `figs_pop/P4b_delai.png` ★ |
| 0.5 | Ce que la littérature disait déjà — le null, et trois poches conditionnelles | tableau à 6 lignes |
| 0.6 | Comment se lit un résultat ici — et les deux seuils, 2,18 et 1,96 | — |

> **0.2 est la slide-pivot du deck.** C'est la carte du dossier, redessinée à chaque intercalaire
> avec le curseur « vous êtes ici » — exactement le dispositif `\pipefig{k}` de `SLIDES_DONNEES`,
> qui est ce qui empêche de partir dans tous les sens.
> **0.5** condense `2_noter_les_titres/ETAT_DE_L_ART_STRATEGIES.md` (69 fiches) en une slide.

---

## Partie 1 · Le socle — 6 slides
### `tables_membres_tickers.ipynb` · `tables/` · `tools/`

| réf | titre-message | figure |
|---|---|---|
| 1.1 | D'où viennent les lignes — l'entonnoir, de la table clean aux deux périmètres | `figs_deck/fig_09_entonnoir.png` |
| 1.2 | On ne déclare que des transactions : le portefeuille se reconstruit (FIFO) | `figs_deck/B1_vt_membre.png` |
| 1.3 | Le rendement en parts — un apport n'est jamais une performance | `figs_deck/B2_spaghetti.png` |
| 1.4 | Quatre tables propres : membres, titres, membre × année, dictionnaire | `figs_deck/fig_09_identite.png` |
| 1.5 | Un membre sous six angles — ce que la table sait dire d'une personne | `figs_deck/fig_09_portefeuille.png` |
| 1.6 | `tools/` — deux moteurs, jamais mélangés, chacun avec sa preuve rejouable | — |

> **1.6** dit la doctrine : deux familles, deux alphas (géométrique côté membre, Jensen ×252 côté
> titre), et pourquoi les notebooks figés n'importent aucun module.
> `python -m tools.test_ancres` · `python -m tools.membre.test_ancres_membre`.

---

## Partie 2 · Copier les membres — 18 slides
### `1_copier_les_membres/` — la question : copier les meilleurs élus bat-il le marché ?

**A · la population**

| réf | titre-message | figure |
|---|---|---|
| 2.1 | Une centaine d'élus actifs par an — et deux personnes font 41 % des lignes | `figs_pop/P1_population_temps.png` + `figs_pop/P2_top_membres.png` |
| 2.2 | Les deux plus gros déposants ne passent pas leurs ordres | tableau 3 colonnes |
| 2.3 | Le conjoint passe 38 % des ordres ; 75 % des montants sont dans la première fourchette | `figs_pop/P3_proprietaires.png` ★ + `figs_pop/P4a_fourchettes.png` ★ |
| 2.4 | 19 % des achats tombent dans un secteur régulé par leurs comités | `figs_pop/P4c_conflit.png` |
| 2.5 | Chacun a ses secteurs de prédilection | `figs_pop/P6_secteurs.png` ★ |
| 2.6 | Des positions lentes — tenue médiane ~1 an, 44 % jamais revendues | `figs_pop/P5b_duree.png` |

**B · la mesure**

| réf | titre-message | figure |
|---|---|---|
| 2.7 | La question naïve donne un « oui » trompeur — 34 % battent le SPY, Sharpe 0,72 contre 0,83 | `figs_pop/P7a_distributions.png` |
| 2.8 | La porte d'entrée : 223 des 266 portefeuilles sont jugeables | `figs_deck/fig_05b_eligibilite.png` |
| 2.9 | Deux mètres : l'IR (suppose β = 1) et l'appraisal (retire le β) | `figs_deck/fig_05b_regression_demo.png` |
| **2.10** | **20 gagnants à l'IR, 12 après le β — ≈ 11 attendus par pur hasard** | `figs_deck/fig_05b_hist_t.png` |
| 2.11 | Les deux mètres ne classent pas pareil — la couleur, c'est le β | `figs_deck/fig_05b_ir_vs_appraisal.png` |

**C · les cinq réglages**

| réf | titre-message | figure |
|---|---|---|
| 2.12 | L'échelle : QUI · COMBIEN · QUAND · COMMENT · LA RÈGLE — un seul réglage change à la fois | TikZ `rung` (existe) |
| 2.13 | Test 1 · copier le top-4 — +3,1 %/an, mais β 1,20 et α ≈ 0 | `figs_deck/fig_05b_nav_top4.png` |
| 2.14 | Tests 2 & 3 · combien copier, à quelle cadence — t 1,58, seuil 1,81 | `figs_deck/fig_05b_k_et_cadence.png` |
| 2.15 | Test 4 · répartir par le risque — max t_appraisal +0,48 | `figs_deck/fig_05b_ponderations.png` |
| 2.16 | Test 5 · classer au Sharpe brut — le t plafonne à 1,21 | `figs_deck/fig_05b_balayage_k.png` |

**D · les portraits, et la clôture**

| réf | titre-message | figure |
|---|---|---|
| 2.17 | Whitehouse, le seul candidat robuste — 718 trades, +6 %/an | `figs_pop/G_W000802_portrait.png` |
| 2.18 | Fetterman et Ruiz, premiers du classement — sur 10 trades | `figs_pop/G_F000479_portrait.png` + `figs_pop/G_R000599_portrait.png` |
| 2.19 | McClain +41 %/an par son β 1,76 ; Khanna 32 700 trades, profit factor 0,88 | `figs_pop/G_M001136_portrait.png` + `figs_pop/G_K000389_portrait.png` |
| 2.20 ▲ | **C'était mesurable d'avance** — IC 0,048 · MDE 8 %/an · 160 essais, DSR 0,11 | à produire (§13-§14) |
| 2.21 | La strate est close : on mesure des personnes, pas le Congrès | — |

*(21 réfs, ~18 slides après regroupement de 2.3 et 2.17-2.19.)*

---

## Partie 3 · Noter les titres — 21 slides
### `2_noter_les_titres/` — le virage : on note les titres, plus les élus

**A · le socle**

| réf | titre-message | figure |
|---|---|---|
| 3.1 | Le virage : on arrête de mesurer des personnes | intercalaire |
| 3.2 | Le périmètre titre — 134 464 → 113 369 opérations | `figs/univers.png` |
| **3.3** | **Une vente prend toujours le plus vieux lot — l'âge étiquette la part, il ne choisit pas le lot** | `figs_arch/scenarios_fifo.png` ★ |
| 3.4 | La purge γ — 89,5 % de la masse vendue alimente le signal | `figs/gamma.png` + `figs/durees.png` |
| 3.5 | Le signal ticker : une voix par membre, quel que soit le montant | `figs/selection.png` ★ |
| 3.6 | Ce que la pondération change : membres actifs, plus grosse ligne, titres par membre | `figs/poids.png` |
| 3.7 | On choisit W sur la concentration, jamais sur le rendement — W = 42 j | 4 colonnes compactes |

**B · les six tests fondateurs**

| réf | titre-message | figure |
|---|---|---|
| 3.8 | T1 · la base à τ — +1,71 %/an (t 1,03) : un plafond théorique | `figs/nav.png` + `figs/exces.png` |
| 3.9 | Le β reste collé à 1 (0,93–1,11) | `figs/beta_glissant.png` |
| 3.10 | T2, T3, T4 · le cap, puis le short — les titres net-vendus **montent** | `figs/extensions.png` |
| **3.11** | **T5 · à la divulgation, +0,35 %/an (t 0,18)** — le résultat qui commande tout | `figs/divulgation.png` |
| 3.12 | Les quatre coins : τ / δ × sans cap / cap 25 % | `figs/coins.png` |
| 3.13 | T6 · les comités — +7,67 à τ, mais −3,65 à δ | `figs/comites.png` |
| **3.14** | **Le placebo : 20 comités tirés au hasard, et le +7,7 % réel dedans** | `figs/comites_placebo.png` ★ |
| 3.15 | Le filtre retient très inégalement les secteurs — 63 % Industrie, 0 % Immobilier | `figs/comites_secteurs.png` |
| 3.16 | Toutes les pistes, à la divulgation, sur un même axe | `figs/pistes.png` |

**C · les quatre méthodes**

| réf | titre-message | figure |
|---|---|---|
| 3.17 | M1 → M4 : une seule chose change à la fois | tableau 4 lignes |
| **3.18** | **Ce que chacune donne — M3 retenue** | `figs/meth17_nav.png` + `figs/meth17_cascade.png` |

**D · les produits réels**

| réf | titre-message | figure |
|---|---|---|
| 3.19 | NANC / GOP : ce que disent les 17 pièces officielles, et les trois régimes du fonds | planche de vignettes |
| **3.20** | **On retrouve leurs grands noms, pas leurs tailles** | `figs/nanc_gop_diag.png` ★ |
| 3.21 | Les trois répliques retenues — A, B, C ; ρ 0,73–0,75 | `figs/nanc_gop_v3.png` |
| **3.22** | **Leurs positions valent jusqu'à 25× le flux déclaré** | tableau 13 dates |
| 3.23 | Quiver — 22,6 %/an répliqué contre 36,2 % annoncés | `figs/quiver.png` |
| 3.24 | On matche tout ce qui est divulgué ; l'écart vit dans leur boîte noire | réserve |

*(24 réfs, ~21 slides : 3.7 et 3.12 basculent en annexe.)*

---

## Partie 4 · Le livrable M3 — 20 slides
### `3_livrable_M3/` — que vaut M3, et comment la tenir en portefeuille ?

**A · la spécification**

| réf | titre-message | figure |
|---|---|---|
| 4.1 | Le protocole en dix étapes | TikZ à créer |
| **4.2** | **Le geste central : dollars × élus — le consensus compte au carré** | schéma à créer (le cas fabriqué du §4.4) |
| 4.3 | D'où viennent les constantes — aucune calée sur nos rendements | tableau compact |

**B · ce que ça donne**

| réf | titre-message | figure |
|---|---|---|
| 4.4 | +3,40 %/an côté démocrate, +1,24 côté républicain — 9 années sur 13 | `figsM3/m3_nav.png` |
| **4.5** | **Le produit dépasse ses deux composantes** | `figsM3/m3_decomposition.png` ★ |
| 4.6 | Le risque : est-ce un pari de style ? α₄ +2,09 (t 2,08) | `figsM3/m3_facteurs.png` ★ |
| 4.7 | Année après année — *les fenêtres se chevauchent : ça décrit, ça ne teste pas* | `figsM3/m3_rolling.png` ★ |
| 4.8 | Le coût, et le frein — le frein ne mord que sur 1 % des coupes | `figsM3/m3_frein.png` ★ |
| 4.9 | Sans plafond, la plus grosse ligne monte à 87 % | `figs_arch/concentration_sans_plafond.png` ★ |
| 4.10 | Le marché ignore la publication — ρ 0,998 sur le volume au jour δ | `figs_arch/volume_divulgation.png` ★ |
| 4.11 | Le portefeuille unique — +2,51 %/an : aucune décision prise après coup | — |

**C · la version ETF**

| réf | titre-message | figure |
|---|---|---|
| **4.12** | **Y a-t-il seulement de l'information sectorielle ? \|t\| 2,06 contre 1,96** | — |
| 4.13 | L'instrument change, le moteur non — +1,45 %/an (t 2,05) | `figsM3/etf_livrable.png` |
| 4.14 | Où agréger, et la carte datée — sans elle, 15,2 % du portefeuille perdu | `figs_arch/m3_etf_ou_agreger.png` ★ + `figs_arch/m3_etf_manquant.png` ★ |
| 4.15 | Élargir à 32 instruments échoue — c'est l'instrument, pas le signal | — |

**D · le portefeuille deux poches**

| réf | titre-message | figure |
|---|---|---|
| 4.16 | Le bon objet n'est pas un vecteur de poids, c'est une série — et la dose s'en déduit | formule |
| **4.17** | **IR constant 0,637 à toutes les doses** — doser plus achète du rendement, jamais de la preuve | `figsM3/deux_poches.png` (panneau droit) |
| 4.18 | 98,8 % de la variance du signal est du marché — la justification des deux poches | — |
| 4.19 | Calibration : TE* 3 % se lit ≈ 3,8 % — et en mars 2020 la dose était pleine | `figsM3/deux_poches.png` (panneau central) |
| 4.20 | Le portefeuille tenu — 16,8 % SPY + 12 lignes | tableau des 11 poids |
| **4.21** | **TE*, le seul paramètre libre — la question à poser à Ramify** | — |

*(21 réfs, ~20 slides.)*

---

## Partie 5 · L'inventaire et les limites — 7 slides
### `PISTES_TESTEES.md` · `FICHE_M3` annexe D · `M3_table_pipeline.ipynb`

| réf | titre-message | figure |
|---|---|---|
| 5.1 | ~90 pistes testées, sept étapes datées — l'inventaire complet | frise TikZ |
| 5.2 | Chaque constante est fixée hors de toute performance | tableau compact |
| 5.3 | Comment on l'a vérifié — 16 contrôles, chacun avec le chiffre que le notebook imprime | — |
| 5.4 | 162 runs publiés, aucun seuil corrigé — et trois compteurs qui ne s'additionnent pas | — |
| 5.5 | Les deux chiffres qui franchissent un seuil, et pourquoi on ne les revendique pas | réserve |
| 5.6 | Ce qui n'est pas mesuré — impact de marché, capacité, liquidité, options | réserve |
| 5.7 | La lignée rejouée sur la table courante : aucune conclusion ne change ; et les 4 pistes ouvertes | tableau de passerelle |

---

## Annexes — le seul endroit à tableau dense

| réf | contenu |
|---|---|
| A1 | Le balayage θ en entier (10 / 20 / 50 / 100 / ∞) |
| A2 | Le balayage du frein · le choix de W (21 / 42 / 63 / 126 j) |
| A3 | Les 32 ETF fins, et les 6 qui battent leur secteur |
| A4 | Le tableau des constantes (`FICHE_M3` annexe B) |
| A5 | Les 16 contrôles (`FICHE_M3` annexe A) |
| A6 | L'inventaire des ~90 pistes, strate par strate |
| A7 | Les 8 portraits complets |
| A8 | La fiche membre en 12 figures (`figs_deck/fig_09_*`) |
| A9 | La liquidité des titres sélectionnés — le seul chiffrage de capacité (`figs/adv.png`) |

---

## Les figures

**57 figures locales citées, toutes vérifiées présentes.** 6 sont à copier depuis la branche
`presentation` vers `02_recherche_backtest/figs_archive/` :
`scenarios_fifo` · `concentration_sans_plafond` · `volume_divulgation` · `m3_etf_ou_agreger` ·
`m3_etf_manquant` · `_explication_burr_covid_2020`.

| clé | chemin (depuis `02_recherche_backtest/`) |
|---|---|
| `figs/` | `2_noter_les_titres/figs/` |
| `figsM3/` | `3_livrable_M3/figs/` |
| `figs_pop/` | `../00_recuperation_donnees/png/figs_pop/` |
| `figs_deck/` | `../00_recuperation_donnees/png/figs_deck/` |
| `figs_arch/` | `figs_archive/` — **à créer** |

### Les quatre pièges

1. **Deux plafonds, deux jeux de figures.** `figs/meth_*` = plafond **8,5 %** (672,35 / 612,25,
   la trace de recherche) · `figs/meth17_*` = **10 %** (661,57 / 573,57, les chiffres publiés).
   **Le deck n'utilise que `meth17_*`.**
2. **Deux `m3_nav.png`** de contenus différents. Ne jamais dédoublonner par nom.
3. **Doublons `figs_pop` / `figs_deck`** (`P3, P4a, P4b, P6` ≈ `A3, A4, A5, B6`) : préférer
   `figs_pop/`, dossier sous contrat asserté par `figures_du_deck.ipynb`.
4. **Une figure archivée se copie, ne se déplace pas** — son producteur peut la réécrire.

---

## ▲ Le seul point bloquant

**La slide 2.20** — « c'était mesurable d'avance » : IC du Sharpe passé 0,048, MDE ≈ 8 %/an,
160 essais et DSR 0,11. `PISTES_TESTEES.md` et `1_copier_les_membres/README.md` citent ces chiffres
comme établis aux **§13-§17 de `copier_les_membres.ipynb`** — or le notebook s'arrête à `§12.3`.

Sans cette slide, la Partie 2 dit « on n'a rien trouvé ». Avec elle, elle dit « personne n'aurait
pu trouver » — c'est une autre conclusion, et c'est la bonne.

**Trois options** : (a) retrouver les §13-§17 et produire la figure ; (b) faire la slide **sans
figure**, en citant `PISTES_TESTEES.md` ; (c) la retirer et cesser de citer ces chiffres.

---

## Pour démarrer

1. Créer `figs_archive/` et y copier les 6 figures.
2. Extraire le préambule de `SLIDES_DONNEES.tex` vers `SLIDES_RECHERCHE.tex`, resserré :
   2 couleurs de chrome, `\tuile` à filet, `\bandlecture` et `\reserve` en remplacement de
   `\repband` et `\choixbox`.
3. Construire la **carte du dossier** (slide 0.2) sur le modèle de `\pipefig{k}` — le même schéma
   redessiné à chaque intercalaire, curseur « vous êtes ici ».
4. Trancher ▲ 2.20.
