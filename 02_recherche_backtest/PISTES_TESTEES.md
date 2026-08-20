# Toutes les pistes testées — l'inventaire de la recherche

> **Le but de ce document** : qu'on n'ait jamais à ré-explorer une piste morte. Tout ce qui a été
> tenté est ici, étape par étape, avec son résultat chiffré et l'endroit exact où c'est prouvé.
> La vue d'ensemble et les résultats retenus : [le README du dossier](README.md).

**Conventions.** τ = date de la transaction (non investissable — un chiffre mesuré à τ est un
plafond théorique) · δ = date de **divulgation** (la seule date où l'information est publique,
donc le seul régime réplicable) · « excès » = moyenne des écarts annuels au SPY, 2014-2026, brut
de frais sauf mention · seuils de Student : **2,18** (13 années), **1,96** (α journaliers).
Une **strate** = une étape datée et close de la recherche ; les strates 0, 1, 3, 4 et 6 vivent
dans `_archive/` (branche `presentation`, journal : `_archive/README.md`), les strates 2, 5 et 7
sont les trois dossiers actifs `1_copier_les_membres/`, `2_noter_les_titres/`, `3_livrable_M3/`.

**Deux familles de travaux disjointes, pas six notebooks.** La famille **« membre »**
(`copier_les_membres` + les études) copie des élus : 2013-2026, toutes classes d'actifs,
118 316 trades (table courante ; 118 029 sur la v1), résultat *pas d'alpha*. La famille
**« titre »** (`noter_les_titres` → `M3_preuve_complete`) note des titres : 2014-2026, actions
seules, 113 369 opérations, résultat *M3*. Elles ne partagent pas trois lignes de code — et
c'est voulu (cf. « la doctrine », plus bas).

**Les noms historiques.** Les archives, les fiches et les sorties figées citent les notebooks par
leurs anciens numéros. La correspondance avec les fichiers d'aujourd'hui (renommés le 11/08) :

| nom historique | fichier aujourd'hui |
|---|---|
| 09 | `tables_membres_tickers.ipynb` |
| 05b | `1_copier_les_membres/copier_les_membres.ipynb` |
| 07 · 12 | `1_copier_les_membres/etudes/etude_population.ipynb` · `etude_portraits.ipynb` |
| 11 · 11b · 11c | `2_noter_les_titres/noter_les_titres.ipynb` · `replique_NANC_GOP.ipynb` · `repliques_quiver.ipynb` |
| 16 | `3_livrable_M3/M3_preuve_complete.ipynb` |
| 17 | `3_livrable_M3/M3_table_pipeline.ipynb` |
| FICHE_STRAT_TICKER_22JUIL | `2_noter_les_titres/FICHE_NOTER_LES_TITRES.pdf` |

---

## Strate 0 — les premiers backtests (`_archive/recherche_v0/`, données Quiver brutes, juin)

⚠️ Univers de prix sans les sociétés délistées → tous les chiffres de cette strate sont optimistes.

| piste | où | résultat | statut |
|---|---|---|---|
| Copy-trading « brief Ramify » V1 (K membres au Sharpe rétréci) | `RAMIFY_V1_actions` §3-5 | meilleur K=8 : α₄ +4,0 %/an, **t 0,88** ; aucun K ne bat le Sharpe SPY | close — non significatif |
| Persistance des track records | `RAMIFY_V1` §7 | top-10 IS +22,8 % → OOS **+3,8 %** | close — sur-apprentissage |
| Niveau trade | `RAMIFY_V1` §6 | hit 47,6 %, **médiane négative** | close — les gains tiennent à quelques coups extrêmes |
| V2 substitution GICS→SPDR | `RAMIFY_V2_ETF` §3-4 | α **−3,8 %/an** ; dilution −4,5 à −5,8 pt à chaque K | close — l'edge est *firm-specific* |
| 9 variantes de pondération/horizon | `SUPP_A` §3-5 | toutes : \|t\| < 1,2 | close |
| **Information Coefficient de la breadth** | `SUPP_B` | IC **+0,023** à 6 m (t_NW 2,42), **+0,026** à 12 m (t_NW 3,59) ; le montant $ : t < 1,3 | **seul survivant de la strate** — minuscule |
| Event-study par taille · long-short neutre · commissions↔secteur · caractéristiques · ML | `SUPP_B` | grosses ventes montent aussi · β≈0 sans α · artefact défense · s'effondre au clustering · **AUC 0,50** | closes |
| V2 pilotée breadth, sans sélection | `SUPP_C` §2 | Sharpe 0,75 > 0,45 (sélection) mais α **−1,50 %** (t −1,99) | close — leçon : *ne pas sélectionner vaut mieux* |
| Plafond théorique Grinold-Kahn | `SUPP_C` §3 | avec IC ≈ 0,02, **IR plafonné à 0,2-0,3** | l'edge est structurellement petit |

## Strate 1 — les critères de sélection (`_archive/recherche_v1/`, table hybride)

Dans cette table, `03` = `_archive/recherche_v1/03_Recherche_Signal_2014_2026.ipynb`,
`04` = `…/04_Copier_Congres_Simple.ipynb`, `05` = `…/05_Portefeuille_Membre_V1.ipynb`.

| piste | où | résultat | statut |
|---|---|---|---|
| **Le t clusterisé par membre** — l'arbitre de la strate | `03` §3.0 | commission clé **t 11,33 → 1,42** ; « ≥ 250 k$ » 1,59 → −0,33 | les t naïfs étaient gonflés par le chevauchement |
| Découpages chambre/parti/taille/durée/commission/timing | `03` §3.1 | rien ne survit au clustering + résidualisation | closes |
| Concentration | `03` §3.2-3.3 | NVDA = 2,8 % des gains, 8 membres = 59,9 % des très gros gains | pari tech d'une poignée |
| Contrôle achats contre ventes | `03` §3.4a | gros achats +2,39 ≈ grosses ventes +3,40 | tilt de style, pas de direction |
| Copier tout le Congrès (3 pondérations) | `03` §4 | Sharpe ≤ 0,68 < SPY 0,92 ; α₄ négatifs significatifs | close — le marché en pire |
| GRS joint | `03` §4.4 | p 0,24 | on ne rejette pas « tous les α nuls » |
| **11 critères de sélection + composite, walk-forward** | `03` §5.1-5.3 | meilleur Sharpe 0,65 < 0,92 ; **sélectionner sur l'α individuel : −11,9 %/an (t −2,30)** | close — le data-snooping en action |
| Grille K + Deflated Sharpe (44 essais) | `03` §5.4 | **DSR 0,79 < 0,95** | le gagnant = du hasard |
| Persistance IS/OOS | `03` §5.5 | top-10 → **0/10** éligibles OOS ; Spearman −0,11 | close |
| **Jugement au plafond (entrée à τ, info parfaite)** | `03` §5bis | 4 % battent leur style, **0 %** le Sharpe SPY ; rendement actif −2,3 %/an | *même avec l'information parfaite*, pas de talent |
| Version grand public (copier tout vs top-10) | `04` | B +16,2 %/an mais Sharpe 0,82 < SPY 0,86 | le surplus est du risque |
| Portefeuille par membre v1, top-4 IR | `05` | 20 significatifs vs ~11 attendus ; top-4 +3,6 %, t 1,14 | supersédé par `copier_les_membres` |
| Garde-fou tickers corrompus | `05` conclusion | un seul glitch (`DAIUF`) fabriquait **+12 %/an** | leçon conservée partout |

## Strate 2 — la ligne membre à terme (`1_copier_les_membres/`)

Dans cette table, `06` = `_archive/06_Recherche_Strategie_2014_2026.ipynb` (le premier passage) ;
les §4-§17 sont les sections de `copier_les_membres.ipynb` — en **génération 2** depuis le 11/08 :
socle importé de `tools/membre`, ré-exécuté en entier sur la **table courante** du pipeline, et
les chiffres ci-dessous sont les re-certifiés (le passage v1 → courante, consigné plus bas, ne
change aucune conclusion). Le rapport de clôture :
`_archive/RAPPORT_PORTEFEUILLE_MEMBRE.pdf` (chiffres v1 d'époque) — **20 élus « significatifs »
bruts → 12 une fois le marché retiré ≈ 11 attendus par pur hasard ⇒ pas d'α.**

| piste | où | résultat | statut |
|---|---|---|---|
| Event-study sur la table canonique | `06` §3 | achats **−0,76 %** à 6 m (t −8), même à τ | aucun spread directionnel |
| Le drift post-publication 1 mois | `06` §3 | **+7 bps (t 1,9)** — réel, mais 6× sous les coûts | → repris proprement en strate 3 |
| Copy-trading non sélectif · top-K Sharpe | `06` §4 | −0,42 %/trade net · t ≤ 1,3 sur 8 essais | closes |
| Les 3 artefacts de backtest | `06` §4 | chaque correction fait tomber le t (2,5 → ≤ 1,3) | point de méthode fondateur |
| Les 12 leaders de parti (Wei & Zhou) | `06` §5a | **89 % des achats = une seule personne** (2025) | **non testable** sur notre fenêtre |
| Passage trade → compte (NAV, coûts) | `06` §7 | +1,9 à +2,3 %/an, t ≤ 0,9 ; Sharpe 0,74 < SPY 0,82 | close |
| Classement IR vs appraisal | `copier_les_membres` §4 | 20 → 12 ≈ hasard | le surnombre = du marché |
| Top-K, K walk-forward | §7 | max du notebook : **+4,06 %/an, t 1,581** | enterré par l'autopsie ⚰ : max de 160 essais, DSR 0,106 |
| Cadence 6 mois · inverse-vol/ERC/GMV · Ledoit-Wolf | §8-§10 | max t_appraisal **+0,48** ; GMV −4,5 %/an (t −2,76) | le résultat est invariant au *qui/combien/comment* |
| Sélection par le Sharpe brut | §11-§12 | max t 1,215 ; dilution +3,5 → −0,2 % à K=20 | close |
| **Le Sharpe passé prédit-il ?** | ⚰ §13 | **IC +0,048 (t 0,83)** ; il faudrait IC ≥ 0,15 pour espérer t > 1,81 | l'impasse était écrite d'avance |
| **Puissance et multiplicité** | ⚰ §14 | MDE ≈ **8 %/an** (détecter +2 % ⇒ ~170 ans de données) ; **160 essais**, E[max t\|H₀] 2,69 | personne n'a la puissance de valider un α réaliste |
| **L'analyse d'après-coup du style** | ⚰ §15 | +3,5 = **+6,9 sélection − 3,5 allocation** ; le panier est AMZN/MSFT/NVDA à 22-25 % | l'excès brut = des gains concentrés sur quelques titres, non reproductibles |
| **Commissions, test intra-membre** (le plus propre du projet) | ⚰ §16.2 | le même élu dans le périmètre de ses commissions : **Wilcoxon p 0,48**, répliqué sur les 2 ères (avant/après 2020) | la dernière hypothèse mécaniste meurt |
| Six dimensions jamais lues | ⚰ §17.2 | p (test de signe) — ère 0,064 · **conjoint 0,063 (cohérent 2 ères)** · **ventes 0,001 mais en NÉGATIF** · taille 0,052 non répliqué · délai 0,22 · parti/chambre/leadership ≥ 0,21 | une conclusion (les sorties détruisent un peu), une piste en sommeil (conjoint), le reste ne montre rien |

> ⚰ **L'autopsie (§13-§17) a été retirée de `copier_les_membres.ipynb` le 2026-08-20** — elle
> n'avait aucune contrepartie dans le deck `SLIDES_DONNEES`. **Les résultats ci-dessus restent
> acquis** : ce sont eux qui closent les pistes commissions et conjoint, et c'est la raison
> d'être de ce fichier de ne pas les rouvrir. La preuve rejouable est dans l'historique git :
> ```
> git show 13a6b075:02_recherche_backtest/1_copier_les_membres/copier_les_membres.ipynb
> ```

## Strate 3 — le NO-GO pré-enregistré (`_archive/08_Strategie_Calendar_Time`)

Protocole **gelé avant calcul** (`_archive/FICHE_PREENREGISTREMENT_08`), résultat mécanique
(`_archive/FICHE_08_CALENDAR_VW`) : test primaire **α₄ net −0,77 %/an (t −0,48)**, 11/12 cellules
de la grille fermée négatives (max \|t\| 2,63 ≈ E[max\|H₀]), **DSR 0,04**, coût de rentabilité
**≈ 5 bps** par jambe pour un turnover de 16,5×/an. Ce dossier **ferme** « le drift
post-disclosure value-weighted existe-t-il chez nous ? » — avec sa puissance affichée. Les
diagnostics hors protocole (équipondéré −3,06 %, Sénat +1,33 % sur 15 noms, date d'entrée décalée
≤ +0,91 %) étaient pré-déclarés *jamais revendicables*.

## Strate 4 — le stock des divulgations (`_archive/10_Stock_Divulgations_MathSpec.ipynb`, lignée aboutie au dossier `01_autres_filing_types/`)

Sept conditions de recevabilité mesurées avant tout backtest (recalage photo→photo 94,1 % ·
apport O/A/T 17,3 % · 73 membres · MDE 7,3 %/an ⇒ jugement au niveau *classement*, jamais NAV ·
concentration · couverture prix 76,4 %). **Fermé définitivement** : « copier le stock agrégé »
(la valeur convertible en tickers ne couvre que **17,8 %** du patrimoine — la base de calcul est
inobservable) et « le flux annuel-seul en événements » (lag médian **374 jours**). Les tests
E1/E2 pré-enregistrés n'ont jamais été dévoilés : le chantier a été redirigé vers le dossier 01
(son notebook 10 House ; les `FICHE_10_*` de l'époque sont dans `01_autres_filing_types/_archive/`).

## Strate 5 — la ligne titre (`2_noter_les_titres/`)

Les § de cette section sont ceux de `noter_les_titres.ipynb` et de ses deux volets. Le socle
retenu : **purge FIFO γ** (γ = la part d'une vente qui compte encore ; 89,5 % de la masse vendue
alimente le signal) et **W = 42 j choisi sur la concentration, jamais sur le rendement**.

**Les six tests fondateurs** (fiche du 22 juillet — aujourd'hui `FICHE_NOTER_LES_TITRES.pdf`) :

| test | résultat | leçon |
|---|---|---|
| T1 base à τ | +1,71 %/an (t 1,03, NAV 622) | plafond théorique, non réplicable |
| T2 + cap 25 %/mois | +0,27 % | sans frais, freiner coûte |
| T3 jambe short | **−12,8 %/an (t −3,19)** | les titres net-vendus **montent** après la vente |
| T4 short-only | **−26,6 %/an** (NAV 16) | le marché à l'envers |
| **T5 base à δ — le vrai test** | **+0,35 %/an (t 0,18, NAV 530)** | **à la divulgation, « une voix par membre » ≈ le marché** — le résultat qui commande tout |
| T6 comités (§12.2) | τ +7,67 % (t 1,60) mais **δ −3,65 %** | c'est le tilt sectoriel, pas l'information |

**Les autres pistes du §12** (18 essais, E[max\|t\|] ≈ 2,40 sous H₀) : allonger l'horizon dégrade
de façon monotone (H=12 m : −0,89 à δ) · marché neutralisé : α **+0,03 % (t 0,02)** à δ — pas d'α
caché sous le β · Sénat seul −3,72 % · **dépôts tardifs −8,25 % (t −1,98)** — l'hypothèse « un
trade qu'on cache » est renversée.

**La réplique NANC/GOP, six versions** (§13, volet `replique_NANC_GOP.ipynb` ; l'audit
documentaire est dans `AUDIT_FONDS_NANC_GOP.pdf`) : la version au net brut est *fausse* (le
prospectus dit de ne pas soustraire les vieux lots) ; **A** (score, période du premier
administrateur Subversive) NVDA à 8,5 % exact, ρ 0,73 ; **B** (livre événementiel, période du
second administrateur Tidal) turnover 13 % ≈ leur 10 % ; **C** (bascule au 02/08/2024) ρ 0,75 —
la lecture qui suit l'histoire réelle du fonds. Réparer notre donnée ne rapproche pas du fonds
(§13.6) ; l'hypothèse Schedule A est réfutée par la source primaire ; et le chiffre qui clôt le
dossier : **leurs positions valent jusqu'à 25× le flux déclaré** (§13.12) — leur fournisseur
n'est pas les fourchettes publiques. La règle *dite* par les gérants tranche différemment selon
le fonds (§13.13) : le facteur « nombre d'élus » reste notre invention.

**Les stratégies Quiver, répliquées fidèlement** (§14, volet `repliques_quiver.ipynb`) :
Congress Buys ≈ **22,6 %/an à τ, 21,4 % à δ** contre SPY 21,1 % (2020-26) — leur page annonce
36,2 %. Les cinq leviers testés un par un (pondération, ETF écartés, couverture, fenêtre W,
accumulation) ne comblent jamais l'écart ; leur panneau est **incohérent** (vol affichée
4,63 %/an incompatible avec β 1,14) ; le rebalancement hebdomadaire (le seul paramètre divulgué
restant) ne change rien (§14.2). Idem pour House Long-Short : notre réplique +267 % contre leurs
+628 % annoncés. **On matche tout ce qu'ils divulguent ; l'écart est entièrement dans leur boîte
noire.** Le 130/30 : les deux jambes ≈ le marché ⇒ du marché levé.

**La méthode retenue** (§16-§17) : M1 (une voix) +0,12 % t 0,06 — et rotation 715 %/an ⇒ net
négatif · M2 (dollars purs) +1,43/+0,49 · **M3 (dollars × élus) retenue** · M4 (θ=50) +5,14 mais
β instable 0,96→1,51 — écarté ; balayage de θ publié en entier, aucune valeur ne domine. La
compensation achats-ventes isolée (§17.1) : **−2,09 pt côté NANC** — non retenue par la règle des
deux camps. (θ = plafond de taille d'un dépôt groupé : un élu qui déclare θ lignes ou plus le
même jour est écarté du signal.) Plafond 8,5 → **10 %** (médiane des 13 N-PORT 10,3 % + limite
UCITS — deux sources hors rendement).

## Strate 6 — les trois notebooks fusionnés dans `M3_preuve_complete` (30/07)

Dans cette section, `13` = `_archive/13_Methode_M3.ipynb`, `14` = `_archive/14_M3_Alternatives.ipynb`,
`15` = `_archive/15_Strategie_ETF.ipynb`.

**`13` (variantes ETF écartées)** : « ETF·score » avec cap 10 % ≡ **l'équipondéré sectoriel**
(ρ 0,9986 — 9 lignes sur 11 au plafond : le plafond efface le score) ; au niveau secteur, le
nombre d'élus par ligne va de 17 à 2,37 ⇒ **M3 dégénère en M2** ; la variante **C** (M3 entière
puis agrégation des *poids* — une seule chose change : l'instrument) est la seule retenue ;
« sans plafond » +5,95 % (t 2,35) refusé pour trois raisons écrites (BRK-B à 87 % en 2015).

**`14` (les attaques contre M3 — aucune valeur de la fiche n'en dépend)** : M3 **survit** au
facteur profitabilité (α₆ +2,02, t 2,09), aux 4 sous-échantillons de données douteuses (positif
partout, canal électronique seul +3,78), et au contrôle de volume au jour δ (ρ 0,998 : le marché
ignore la publication). Le prospectus appliqué strictement **dégrade** (−1,19 pt) ; le montant
rapporté au **patrimoine** améliore (le geste varie de ×32 entre quartiles) mais couverture 35 %
non aléatoire — non retenu ; le 130/30 : **prédiction « du levier, pas de l'alpha » écrite
d'avance et vérifiée** ; le plafond est **monotone** des deux côtés ⇒ la valeur retenue n'est pas
accidentelle. **Promu : le portefeuille unique** (+2,51 %/an, t 1,93) — le seul qui ne demande
aucune décision prise après avoir vu les résultats.

## Strate 7 — le livrable (`3_livrable_M3/`)

Les § sont ceux de `M3_preuve_complete.ipynb`.

- **§11** — y a-t-il de l'information sectorielle ? \|t\| groupé par date = **2,06** contre 1,96 :
  le test qui autorise tout le reste, passé de justesse ;
- **§12** — élargir à 32 instruments **ÉCHOUE** (+0,31/−0,60 contre +1,50/+0,45) ; §12.2 : seuls
  **6 ETF fins sur 21** battent le secteur qu'ils découpent (−1,61 pt/an en moyenne) —
  **c'est l'instrument, pas le signal** : ce qui a payé, c'est la concentration des méga-caps ;
- **§18** — la **carte sectorielle datée** (la table titre→ETF tient compte des changements
  d'indice : XLRE quitte XLF le 16/09/2016, XLC quitte XLK/XLY le 21/09/2018 — sources SEC
  primaires) : sans elle, 15,2 % du portefeuille en médiane était perdu avant 2018. 26 titres non
  tranchés dont **8 fonds mal étiquetés** — le chantier consigné (cf. les pièges, plus bas) ;
- **§19** — le score sectoriel n'est pas la taille des secteurs : le classement oui (ρ 0,85-0,88),
  **les poids non**, et en sens *opposés* sur la tech (31,7 % NANC / 19,8 % GOP pour un marché
  à 29,4) — c'est cet écart que la version ETF achète ;
- **§20 — le portefeuille final « deux poches »**, qui remplace le tilt λ (retiré : levier
  déguisé, cœur ≠ marché, IR croissant = artefact) :
  - la dose : a = min(1, TE\*/σ̂), risque σ̂ estimé sur 756 jours, seuil d'inaction 20 % ;
    TE\* publié en profil {1, 2, 3} % ;
  - décomposition du risque : 14,1 % de bêta seulement ;
  - IR constant 0,637 à toutes les doses ;
  - calibration honnête : un budget TE\* de 3 % se lit ≈ 3,8 % réalisé ;
  - limite structurelle dite : en mars 2020, la dose est déjà pleine ;
  - transfer coefficient 0,947 ; portefeuille tenu 12 lignes (a = 0,832 à la dernière date de
    rééquilibrage). Voir `FICHE_M3` partie III.

---

## Les pièges de navigation

- **Trois compteurs d'essais qui ne s'additionnent pas** : 160 (ligne membre,
  `copier_les_membres` §14.2) · **162** (ligne titre, FICHE_M3 annexe D — l'ETAT_DE_L_ART cite
  encore l'ancien 84) · 155 (les archives `13`+`14` avant fusion).
- **Deux plafonds coexistent dans `noter_les_titres`** : avant le §17 tout est à **8,5 %**
  (chiffres témoins 672,35 / 612,25 — la trace de recherche) ; le §17 et tout
  `M3_preuve_complete` sont à **10 %** (661,57 / 573,57).
- `_archive/FICHE_STRAT_TICKER_22JUIL_v2` est **antérieure** à la version courante (renommée
  depuis `FICHE_NOTER_LES_TITRES` — piège « v2 »).
- `3_livrable_M3/figs/m3_nav.png` ≠ `_archive/figs_nb13/m3_nav.png` : même nom, contenus
  différents — **ne jamais dédoublonner par nom**.
- `_archive/FICHE_NANC_GOP_COMPLET.pdf` publie un t(α₄) NANC **périmé** (1,81 ; la valeur courante
  est 2,08 — le seul chiffre du dossier qui franchit un seuil).
- `ETAT_DE_L_ART_STRATEGIES.md` empile deux documents : la note du 04/07 (non revérifiée) puis
  **l'annexe du 09/07 qui fait foi**.
- Les notebooks archivés (les `_archive/10_*, 13_*, 14_*, 15_*.ipynb`) recréent leurs dossiers
  de figures **dans l'actif** si on les ré-exécute (chemins absolus codés en dur).
- **Le chantier consigné, non traité** : retirer du flux les **8 fonds étiquetés
  `asset_class="stock"` / `asset_type="Mutual Fund"`** (EDR, FDN, IXP, PNQI, VOX, VNQ, IYR,
  SCHH) — « la vraie correction, mais elle déplacerait tous les chiffres témoins du projet »
  (FICHE_M3, annexe D).

## Pourquoi les notebooks figés n'importent aucun module — la doctrine

Un module commun a **déjà existé** (les 7 `.py` de `_archive/recherche_v0/`) et a été supprimé
par décision : commit `d477c473` (27/06) — *« un seul notebook de recherche AUTONOME (zéro .py) »*.
Depuis, **zéro import local dans les notebooks aux sorties figées**, et une discipline de copie
*documentée* (bannières « COPIE EXACTE 05b — cellule N » — 05b = `copier_les_membres`).
Les raisons tiennent toujours :

1. **il n'y a pas UN alpha, il y en a deux** — la famille membre régresse le rendement brut
   (annualisation géométrique), la famille titre un vrai Jensen en excès du taux sans risque
   (annualisation arithmétique). Une fonction commune imposerait un choix qui changerait des
   chiffres publiés dans quatre PDF ;
2. **les constantes qui divergent sont des résultats** (purge γ à 504 j dans `noter_les_titres`
   contre 756 dans `M3_preuve_complete` ; plafond 8,5 contre 10 %) — les fondre dans des défauts
   de fonction, c'est enterrer le résultat ;
3. **un recalcul de contrôle qui importe ce qu'il vérifie ne prouve plus rien** — les
   contre-preuves historiques du moteur (le recalcul Pelosi en double boucle naïve à 10⁻¹², la
   conservation FIFO) vivent dans les études archivées (`_archive/etudes_v1_20260720/`, sorties
   figées v1) ; la preuve vivante du socle est `python -m tools.membre.test_ancres_membre` ;
4. **les sorties figées font preuve** — refactorer sans tout ré-exécuter dissocierait le code de
   ses sorties ; tout ré-exécuter risquerait de déplacer des chiffres publiés.

**Pour la suite**, le paquet [`tools/`](tools/README.md) fournit les DEUX moteurs, jamais
mélangés : la famille titre (racine du paquet, extraite de `M3_preuve_complete`, prouvée par
`python -m tools.test_ancres` sur la v1) et la famille membre (`tools/membre/`, extraite de
`copier_les_membres`/`tables_membres_tickers`, prouvée par
`python -m tools.membre.test_ancres_membre` sur la table courante).

**Les exceptions, chacune prouvée par ré-exécution complète (11/08)** : quatre notebooks
*vivants* tournent sur `tools/` — `M3_preuve_complete` (génération 2 : socle importé, toutes les
validations conservées, mêmes chiffres 661,57 / 573,57 · 162 runs), `M3_table_pipeline` (la table
courante), et depuis le même soir **`tables_membres_tickers` + `copier_les_membres`** (génération
2 famille membre : socle `tools/membre`, table courante, plus aucun re-nettoyage local — le
passage v1 → courante est consigné dans la passerelle plus bas ; aucune conclusion ne change).
S'y ajoute depuis le 12/08 `etudes/figures_du_deck.ipynb` (les 10 figures à prix de la partie
II du deck, sur tools + membres.csv ; les 7 sans-prix : la chaîne du rapport). La doctrine reste
entière pour les notebooks figés — les études exploratoires (archivées avec leurs 24 figures
jamais présentées dans `_archive/etudes_v1_20260720/`) et les trois volets de
`2_noter_les_titres/` ne sont pas touchés.

Quatre défauts mineurs connus, documentés ici et laissés en l'état (les sorties sont figées) :
`_mode` diverge entre `tables_membres_tickers` (`dropna()`) et les deux études ;
`noter_les_titres` relit `ff_factors.csv` à chaque appel de `bilan()` (`M3_preuve_complete` a
corrigé) ; `exces_spy` est défini deux fois dans `etude_portraits` et `rotation` deux fois dans
`M3_preuve_complete` (corps identiques).

## La table du pipeline, et la passerelle

Le nettoyage vit désormais dans le pipeline (`common/backtest_clean.py`, step 7) et la table
courante corrige des tickers que la v1 du 04/07 ratait (`00_recuperation_donnees/NOTE_DIFF_TABLE_CLEAN.md`,
branche `presentation` ; le §7 de `00_recuperation_donnees/RAPPORT_DONNEES.md` recense les étapes). **Les documents publiés
restent adossés à la v1, archivée** ; la ré-exécution complète de la famille titre sur la table
courante est le notebook [`M3_table_pipeline`](3_livrable_M3/M3_table_pipeline.ipynb) — mince,
entièrement sur [`tools/`](tools/README.md) :

| mesure | v1 (publié) | courante |
|---|---|---|
| flux | 113 369 | 113 645 |
| M3 NANC — excès (NAV) | +3,40 (661,57) | **+3,42 (662,37)** |
| M3 GOP — excès (NAV) | +1,24 (573,57) | **+1,21 (572,10)** |
| M3 UNIQUE — excès (NAV) | +2,51 (629,09) | **+2,51 (628,75)** |
| ETF carte datée, unique | +1,45 (577) | **+1,49 (578,78)** |
| IR deux poches (constant) | 0,637 | **0,648** |
| calibration (médiane) | 1,257 | **1,276** |

**Aucune conclusion ne change** : le produit dépasse toujours ses composantes, aucun excès ne
franchit son seuil, l'identité de l'IR tient, TE\* reste la question du client. Toute recherche
future travaille sur la table courante, avec `tools/` — et se mesure contre
`3_livrable_M3/ancres_table_courante.json`.

**La même passerelle pour la famille membre** (génération 2 du 11/08, notebooks ré-exécutés sur
la table courante ; l'état v1 reste dans git, ses tables dans `_archive/tables_v20260704/`) :

| mesure | v1 (04/07) | courante |
|---|---|---|
| 𝒯^brut (fenêtre 2013-2026) | 134 429 | **134 417** |
| trades exploitables | 118 029 | **118 316** |
| tickers (dont couverts prix) | 4 618 (3 289) | **4 607 (3 286)** |
| membres bruts / prix / reconstruits / éligibles | 372 / 359 / 266 / 223 | identiques |
| meilleur cas (K walk-forward, §7) | +4,07 %/an, t 1,584 | **+4,06 %/an, t 1,581** |
| IC du Sharpe passé (⚰ §13) | +0,047 (t 0,82) | **+0,048 (t 0,83)** |
| décomposition ⚰ §15 (K=5) | +6,9 sélection − 3,5 allocation | **+6,9 − 3,5** (inchangé à l'arrondi) |
| commissions intra-membre (⚰ §16) | Wilcoxon p 0,54 | **p 0,48** |
| conjoint − élu (⚰ §17 ②) | p 0,063, médianes +0,07/+0,08 | **identiques** |
| ventes (⚰ §17 ③, en négatif) | p 0,002 | **p 0,001** |

**Aucune conclusion ne change là non plus** : toujours pas d'alpha, mêmes pistes closes, même
piste en sommeil (conjoint). La preuve rejouable : `python -m tools.membre.test_ancres_membre`.
Les lignes marquées ⚰ ont été certifiées sur l'autopsie §13-§17, retirée du notebook depuis
(voir l'encadré de la strate 2 pour la récupérer dans git).

**12/08 — l'entonnoir absorbe les filtres de la recherche.** La table clean du pipeline est
désormais PROPRE au sens plein (étapes E fenêtre et F couverture prix — référentiel versionné
`couverture_prix_v20260812.csv`) : **118 316 × 39**, zéro re-filtrage au chargement. Aucun
périmètre de recherche ne change (portes vérifiées : flux titre 113 645 identique, famille
membre 118 316/266/223 identiques) ; le 𝒯^brut (134 417 · 372 membres) se lit dans la table
BRUTE (lignes marquées ∅ ou F par l’entonnoir). Les tableaux v1 → courante ci-dessus restent la passerelle historique.
