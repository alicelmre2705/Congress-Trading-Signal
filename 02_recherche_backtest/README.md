# La carte de la recherche — `02_recherche_backtest/`

> **Le but de ce document** : qu'on n'ait jamais à ré-explorer une piste morte. Tout ce qui a été
> tenté est ici, strate par strate, avec son résultat chiffré et l'endroit exact où c'est prouvé.
> Conventions : τ = date de transaction (non investissable, borne haute) · δ = date de
> **divulgation** (le seul régime réplicable) · « excès » = moyenne des écarts annuels au SPY,
> 2014-2026, brut de frais sauf mention · seuils de Student : **2,18** (13 années), **1,96**
> (α journaliers).

---

## 1 · Ce qui fait foi aujourd'hui

Le livrable est le couple **[`M3_preuve_complete.ipynb`](3_livrable_M3/M3_preuve_complete.ipynb) + [`FICHE_M3.pdf`](3_livrable_M3/FICHE_M3.pdf)**
— tout ce que la fiche affirme est établi dans ce notebook, et rien d'ailleurs. (Depuis le 11/08
son socle est importé de [`tools/`](tools/README.md) et il a été **ré-exécuté en entier** :
chaque validation passe, mêmes ancres — cf. §6.)

- **M3 sur les titres** — pondérer chaque titre par (dollars déclarés × nombre d'élus distincts),
  achats seuls, 3 ans à δ, top-150, plafond 10 % : **+3,40 %/an** (t 1,61, NAV 662) côté démocrate,
  **+1,24 %/an** (t 1,61, NAV 574) côté républicain, 9 années gagnantes sur 13 des deux côtés.
  Le produit **dépasse ses deux composantes** (équipondéré −1,38 · élus seuls −0,65 · dollars
  seuls +1,43).
- **Le portefeuille unique** (les deux partis fusionnés, aucun choix de camp *a posteriori*) :
  **+2,51 %/an** (t 1,93, NAV 629).
- **La version ETF, carte sectorielle datée** (11 SPDR, XLRE/XLC aux dates de bascule d'indice) :
  unique **+1,45 %/an** (t 2,05, NAV 577).
- **Le portefeuille final « deux poches »** (§20) : une poche SPY + une poche signal sectoriel,
  dose analytique a = min(1, TE\*/σ̂) sur 756 j, bande morte 20 %. **IR constant 0,637 à toutes
  les doses** — doser plus achète du rendement, jamais de la preuve. Le seul paramètre libre est
  **TE\***, publié en profil {1, 2, 3} % : c'est le budget de risque du client — **la question à
  poser à Ramify**.
- **L'honnêteté d'ensemble** (FICHE_M3, annexe D) : aucun excès sur 13 ans ne franchit son seuil ;
  **162 runs publiés**, aucun seuil corrigé — le protocole se protège par les constantes fixées
  hors de toute performance et les balayages publiés en entier.

Autour du livrable, quatre documents actifs : [`PAPIER_METHODE.pdf`](2_noter_les_titres/PAPIER_METHODE.pdf) (M1→M4
côte à côte, notebook 11) · [`FICHE_NOTER_LES_TITRES.pdf`](2_noter_les_titres/FICHE_NOTER_LES_TITRES.pdf) (la
ligne ticker et ses six tests) · [`AUDIT_FONDS_NANC_GOP.pdf`](2_noter_les_titres/AUDIT_FONDS_NANC_GOP.pdf) (ce que
disent les documents officiels des ETF NANC/GOP — version auto-portante `_COMPLET.pdf`, 798 p.) ·
[`ETAT_DE_L_ART_STRATEGIES.md`](2_noter_les_titres/ETAT_DE_L_ART_STRATEGIES.md) (69 fiches de littérature vérifiées
en source primaire).

## 2 · Comment lire le dossier

**Deux lignées disjointes, pas six notebooks.** La lignée **« membre »** (05b → 07, 09, 12) copie
des élus : 2013-2026, toutes classes d'actifs, 118 029 trades, résultat *pas d'alpha*. La lignée
**« titre »** (11 → 16) note des titres : 2014-2026, actions seules, 113 369 opérations, résultat
*M3*. Elles ne partagent pas trois lignes de code — et c'est voulu (cf. §6).

**Le dossier est organisé en trois dossiers numérotés dans l'ordre de lecture** (qui est aussi
l'ordre chronologique de la recherche) — chacun contient ses notebooks, ses figures (`figs/`) et
ses documents, et a son README de résultats :

```
02_recherche_backtest/
├── README.md                        ← ce document, la carte
├── tables_membres_tickers.ipynb     le socle : le producteur des 4 tables propres, à côté de tables/
├── tables/                          membres · tickers · membres_annees + dictionnaire
├── 1_copier_les_membres/            copier_les_membres (la spec math + l'autopsie, §13-§17)
│   └── etudes/                      etude_population (6 portraits) · etude_portraits (l'usine à images du deck)
├── 2_noter_les_titres/              noter_les_titres (socle, 6 tests, M1→M4) · replique_NANC_GOP ·
│                                    repliques_quiver + PAPIER_METHODE · FICHE_NOTER_LES_TITRES ·
│                                    AUDIT_FONDS_NANC_GOP(_COMPLET) · ETAT_DE_L_ART · figs/ ·
│                                    docs_nanc_gop(_surlignes)/
├── 3_livrable_M3/                   M3_preuve_complete (LE LIVRABLE, §1→§20) · M3_table_pipeline
│                                    (la table courante) + FICHE_M3 + figs/ + ancres_table_courante.json
└── tools/                           le moteur commun, prouvé sur les ancres (pour la strate 8)
```

La carte cite les pistes par leurs **numéros historiques** de notebooks (05b, 07, 09, 11, 16…) —
la correspondance avec les fichiers (renommés le 11/08 pour dire ce qu'ils contiennent) :

| notebook historique | fichier aujourd'hui |
|---|---|
| 09 | `tables_membres_tickers.ipynb` |
| 05b | `1_copier_les_membres/copier_les_membres.ipynb` |
| 07 · 12 | `1_copier_les_membres/etudes/etude_population.ipynb` · `etude_portraits.ipynb` |
| 11 · 11b · 11c | `2_noter_les_titres/noter_les_titres.ipynb` · `replique_NANC_GOP.ipynb` · `repliques_quiver.ipynb` |
| 16 | `3_livrable_M3/M3_preuve_complete.ipynb` |
| 17 | `3_livrable_M3/M3_table_pipeline.ipynb` |
| FICHE_STRAT_TICKER_22JUIL | `2_noter_les_titres/FICHE_NOTER_LES_TITRES.pdf` |

Les strates closes (0, 1, 3, 4, 6) vivent dans `_archive/` — sur la branche `presentation`, avec
son journal d'archivage détaillé (`_archive/README.md`).

---

## 3 · Le chemin — toutes les pistes testées, strate par strate

### Strate 0 — les premiers backtests (`_archive/recherche_v0/`, données Quiver brutes, juin)

⚠️ Univers de prix sans délistés → tous les chiffres de cette strate sont des bornes hautes.

| piste | où | résultat | statut |
|---|---|---|---|
| Copy-trading « brief Ramify » V1 (K membres au Sharpe rétréci) | `RAMIFY_V1_actions` §3-5 | meilleur K=8 : α₄ +4,0 %/an, **t 0,88** ; aucun K ne bat le Sharpe SPY | close — non significatif |
| Persistance des track records | `RAMIFY_V1` §7 | top-10 IS +22,8 % → OOS **+3,8 %** | close — sur-apprentissage |
| Niveau trade | `RAMIFY_V1` §6 | hit 47,6 %, **médiane négative** | close — loterie à queue droite |
| V2 substitution GICS→SPDR | `RAMIFY_V2_ETF` §3-4 | α **−3,8 %/an** ; dilution −4,5 à −5,8 pt à chaque K | close — l'edge est *firm-specific* |
| 9 variantes de pondération/horizon | `SUPP_A` §3-5 | toutes : \|t\| < 1,2 | close |
| **Information Coefficient de la breadth** | `SUPP_B` | IC **+0,023** à 6 m (t_NW 2,42), **+0,026** à 12 m (t_NW 3,59) ; le montant $ : t < 1,3 | **seul survivant de la strate** — minuscule |
| Event-study par taille · long-short neutre · commissions↔secteur · caractéristiques · ML | `SUPP_B` | grosses ventes montent aussi · β≈0 sans α · artefact défense · s'effondre au clustering · **AUC 0,50** | closes |
| V2 pilotée breadth, sans sélection | `SUPP_C` §2 | Sharpe 0,75 > 0,45 (sélection) mais α **−1,50 %** (t −1,99) | close — leçon : *ne pas sélectionner vaut mieux* |
| Plafond théorique Grinold-Kahn | `SUPP_C` §3 | avec IC ≈ 0,02, **IR plafonné à 0,2-0,3** | l'edge est structurellement petit |

### Strate 1 — les critères de sélection (`_archive/recherche_v1/`, nb 02-05, table hybride)

| piste | où | résultat | statut |
|---|---|---|---|
| **Le t clusterisé par membre** — l'arbitre de la strate | `03` §3.0 | commission clé **t 11,33 → 1,42** ; « ≥ 250 k$ » 1,59 → −0,33 | les t naïfs étaient gonflés par le chevauchement |
| Coupes chambre/parti/taille/durée/commission/timing | `03` §3.1 | rien ne survit au clustering + résidualisation | closes |
| Concentration | `03` §3.2-3.3 | NVDA = 2,8 % des gains, 8 membres = 59,9 % des jackpots | pari tech d'une poignée |
| Placebo achats vs ventes | `03` §3.4a | gros achats +2,39 ≈ grosses ventes +3,40 | tilt de style, pas de direction |
| Copier tout le Congrès (3 pondérations) | `03` §4 | Sharpe ≤ 0,68 < SPY 0,92 ; α₄ négatifs significatifs | close — le marché en pire |
| GRS joint | `03` §4.4 | p 0,24 | on ne rejette pas « tous les α nuls » |
| **11 critères de sélection + composite, walk-forward** | `03` §5.1-5.3 | meilleur Sharpe 0,65 < 0,92 ; **sélectionner sur l'α individuel : −11,9 %/an (t −2,30)** | close — le data-snooping en action |
| Grille K + Deflated Sharpe (44 essais) | `03` §5.4 | **DSR 0,79 < 0,95** | le gagnant = du hasard |
| Persistance IS/OOS | `03` §5.5 | top-10 → **0/10** éligibles OOS ; Spearman −0,11 | close |
| **Jugement au plafond (entrée à τ, info parfaite)** | `03` §5bis | 4 % battent leur style, **0 %** le Sharpe SPY ; rendement actif −2,3 %/an | *même avec l'information parfaite*, pas de talent |
| Version grand public (copier tout vs top-10) | `04` | B +16,2 %/an mais Sharpe 0,82 < SPY 0,86 | le surplus est du risque |
| Portefeuille par membre v1, top-4 IR | `05` | 20 significatifs vs ~11 attendus ; top-4 +3,6 %, t 1,14 | supersédé par le 05b |
| Garde-fou tickers corrompus | `05` conclusion | un seul glitch (`DAIUF`) fabriquait **+12 %/an** | leçon conservée partout |

### Strate 2 — la ligne membre à terme (`1_copier_les_membres/` · `06` archivé)

Le rapport de clôture : `_archive/RAPPORT_PORTEFEUILLE_MEMBRE.pdf` — **20 significatifs bruts →
12 par appraisal ≈ 11 attendus par hasard ⇒ pas d'α.**

| piste | où | résultat | statut |
|---|---|---|---|
| Event-study sur la table canonique | `06` §3 | achats **−0,76 %** à 6 m (t −8), même à τ | aucun spread directionnel |
| Le drift post-publication 1 mois | `06` §3 | **+7 bps (t 1,9)** — réel, mais 6× sous les coûts | → repris proprement au nb 08 |
| Copy-trading non sélectif · top-K Sharpe | `06` §4 | −0,42 %/trade net · t ≤ 1,3 sur 8 essais | closes |
| Les 3 artefacts de backtest | `06` §4 | chaque correction fait tomber le t (2,5 → ≤ 1,3) | point de méthode fondateur |
| Les 12 leaders de parti (Wei & Zhou) | `06` §5a | **89 % des achats = une seule personne** (2025) | **non testable** sur notre fenêtre |
| Passage trade → compte (NAV, coûts) | `06` §7 | +1,9 à +2,3 %/an, t ≤ 0,9 ; Sharpe 0,74 < SPY 0,82 | close |
| Classement IR vs appraisal | `05b` §4 | 20 → 12 ≈ hasard | le surnombre = du marché |
| Top-K, K walk-forward | `05b` §7 | max du notebook : **+4,07 %/an, t 1,584** | enterré au §14 : max de 160 essais, DSR 0,106 |
| Cadence 6 mois · inverse-vol/ERC/GMV · Ledoit-Wolf | `05b` §8-§10 | max t_appraisal **+0,48** ; GMV −4,5 %/an (t −2,76) | le résultat est invariant au *qui/combien/comment* |
| Sélection par le Sharpe brut | `05b` §11-§12 | max t 1,215 ; dilution +3,5 → −0,2 % à K=20 | close |
| **§13 — le Sharpe passé prédit-il ?** | `05b` §13 | **IC +0,047 (t 0,82)** ; il faudrait IC ≥ 0,15 pour espérer t > 1,81 | le dead-end était écrit d'avance |
| **§14 — puissance, essais, placebo** | `05b` §14 | MDE ≈ **8 %/an** (détecter +2 % ⇒ ~170 ans) ; **160 essais**, E[max t\|H₀] 2,69 ; placebo q95 **1,43** > tous nos t | personne n'a la puissance de valider un α réaliste |
| **§15 — l'autopsie du style (jumeau sectoriel)** | `05b` §15 | +3,5 = **+6,9 sélection − 3,5 allocation** ; mais le placebo « sélectionne » déjà +1,8 %, et le panier est AMZN/MSFT/NVDA à 22-25 % | l'excès brut = loterie idiosyncratique concentrée |
| **§16 — commissions, test intra-membre** (le plus propre du projet) | `05b` §16.2 | le même élu dans le périmètre de ses commissions : **Wilcoxon p 0,54**, répliqué sur les 2 ères | la dernière hypothèse mécaniste meurt |
| §17 — six dimensions jamais lues | `05b` §17.2 | ère p 0,053 · **conjoint p 0,063 (cohérent 2 ères)** · **ventes p 0,002 mais en NÉGATIF** · taille p 0,052 non répliqué · délai p 0,22 · parti/chambre/leadership p ≥ 0,21 | une conclusion (les sorties détruisent un peu), une piste dormante (conjoint), le reste : folklore |

### Strate 3 — le NO-GO pré-enregistré (`_archive/08_Strategie_Calendar_Time`)

Protocole **gelé avant calcul** (`_archive/FICHE_PREENREGISTREMENT_08`), résultat mécanique
(`_archive/FICHE_08_CALENDAR_VW`) : test primaire **α₄ net −0,77 %/an (t −0,48)**, 11/12 cellules
de la grille fermée négatives (max \|t\| 2,63 ≈ E[max\|H₀]), **DSR 0,04**, coût de break-even
**≈ 5 bps** par jambe pour un turnover de 16,5×/an, placebos de falsification échoués. Ce dossier
**ferme** « le drift post-disclosure value-weighted existe-t-il chez nous ? » — avec sa puissance
affichée. Les diagnostics hors protocole (équipondéré −3,06 %, Sénat +1,33 % sur 15 noms, ancrage
décalé ≤ +0,91 %) étaient pré-déclarés *jamais revendicables*.

### Strate 4 — le stock des divulgations (`_archive/10`, lignée aboutie au dossier `01_autres_filing_types/`)

Sept gates mesurées avant tout backtest (recalage photo→photo 94,1 % · apport O/A/T 17,3 % ·
73 membres · MDE 7,3 %/an ⇒ jugement au niveau *classement*, jamais NAV · concentration ·
couverture prix 76,4 %). **Fermé définitivement** : « copier le stock agrégé » (valeur tickérisée
**17,8 %** seulement — l'assiette est inobservable) et « le flux annuel-seul en événements » (lag
médian **374 jours**). Les tests E1/E2 pré-enregistrés n'ont jamais été dévoilés : le chantier a
été redirigé vers le dossier 01 (notebook 10 House, `FICHE_10` de l'époque).

### Strate 5 — la ligne titre (`2_noter_les_titres/`)

Le socle retenu : **purge FIFO γ** (89,5 % de la masse vendue alimente le signal) et **W = 42 j
choisi sur la concentration, jamais sur le rendement**.

**Les six tests fondateurs** (fiche du 22 juillet) :

| test | résultat | leçon |
|---|---|---|
| T1 base à τ | +1,71 %/an (t 1,03, NAV 622) | borne haute non réplicable |
| T2 + cap 25 %/mois | +0,27 % | sans frais, freiner coûte |
| T3 jambe short | **−12,8 %/an (t −3,19)** | les titres net-vendus **montent** après la vente |
| T4 short-only | **−26,6 %/an** (NAV 16) | le marché à l'envers |
| **T5 base à δ — le vrai test** | **+0,35 %/an (t 0,18, NAV 530)** | **à la divulgation, « une voix par membre » ≈ le marché** — le résultat qui commande tout |
| T6 comités (§12.2) | τ +7,67 % (t 1,60) mais **δ −3,65 %** ; **le placebo comité fait aussi bien** (max des 20 tirages +8,31 > réel) | c'est le tilt sectoriel, pas l'information |

**Les autres pistes du §12** (18 essais, E[max\|t\|] ≈ 2,40 sous H₀) : allonger l'horizon dégrade
de façon monotone (H=12 m : −0,89 à δ) · marché neutralisé : α **+0,03 % (t 0,02)** à δ — pas d'α
caché sous le β · Sénat seul −3,72 % · **dépôts tardifs −8,25 % (t −1,98)** — l'hypothèse « un
trade qu'on cache » est renversée.

**§13 (volet `replique_NANC_GOP`) — la réplique NANC/GOP, six versions** (l'audit documentaire est dans
`AUDIT_FONDS_NANC_GOP.pdf`) : la version au net brut est *fausse* (le prospectus dit de ne pas
soustraire les vieux lots) ; **A** (score, régime Subversive) NVDA à 8,5 % exact, ρ 0,73 ;
**B** (livre événementiel, régime Tidal) turnover 13 % ≈ leur 10 % ; **C** (bascule au
02/08/2024) ρ 0,75 — la lecture qui suit l'histoire réelle du fonds. Réparer notre donnée ne
rapproche pas du fonds (§13.6) ; l'hypothèse Schedule A est réfutée par la source primaire ;
et le chiffre qui clôt le dossier : **leurs positions valent jusqu'à 25× le flux déclaré**
(§13.12) — leur fournisseur n'est pas les fourchettes publiques. La règle *dite* par les gérants
tranche différemment selon le fonds (§13.13) : le facteur mᵢ reste notre invention.

**§14 (volet `repliques_quiver`) — les stratégies Quiver, répliquées fidèlement** : Congress Buys ≈ **22,6 %/an à τ,
21,4 % à δ** contre SPY 21,1 % (2020-26) — leur page annonce 36,2 %. Les cinq leviers testés un
par un (pondération, ETF écartés, couverture, fenêtre W, accumulation) ne comblent jamais l'écart ;
leur panneau est **incohérent** (vol affichée 4,63 %/an incompatible avec β 1,14) ; le
rebalancement hebdomadaire (le seul paramètre divulgué restant) ne change rien (§14.2). Idem pour
House Long-Short : notre réplique +267 % contre leurs +628 % annoncés. **On matche tout ce qu'ils
divulguent ; l'écart est entièrement dans leur boîte noire.** Le 130/30 : les deux jambes ≈ le
marché ⇒ du marché levé.

**§16-§17 — la méthode retenue** : M1 (une voix) +0,12 % t 0,06 — et rotation 715 %/an ⇒ net
négatif · M2 (dollars purs) +1,43/+0,49 · **M3 (dollars × élus) retenue** · M4 (θ=50) +5,14 mais
β instable 0,96→1,51 — écarté ; balayage de θ publié en entier, aucune valeur ne domine. Le
netting isolé (§17.1) : **−2,09 pt côté NANC** — non retenu par la règle des deux camps. Plafond
8,5 → **10 %** (médiane des 13 N-PORT 10,3 % + limite UCITS — deux sources hors rendement).

### Strate 6 — les trois notebooks fusionnés (`_archive/13, 14, 15` → nb 16, 30/07)

**nb 13 (variantes ETF écartées)** : « ETF·score » avec cap 10 % ≡ **l'équipondéré sectoriel**
(ρ 0,9986 — 9 lignes sur 11 au plafond : le plafond efface le score) ; au niveau secteur, m
va de 17 à 2,37 ⇒ **M3 dégénère en M2** ; la variante **C** (M3 entière puis agrégation des
*poids* — une seule chose change : l'instrument) est la seule retenue ; « sans plafond »
+5,95 % (t 2,35) refusé pour trois raisons écrites (BRK-B à 87 % en 2015).

**nb 14 (les attaques contre M3 — aucune valeur de la fiche n'en dépend)** : M3 **survit** au
facteur profitabilité (α₆ +2,02, t 2,09), aux 4 sous-échantillons de données douteuses (positif
partout, canal électronique seul +3,78), et au contrôle de volume au jour δ (ρ 0,998 : le marché
ignore la publication). Le prospectus appliqué strictement **dégrade** (−1,19 pt) ; le montant
rapporté au **patrimoine** améliore (le geste varie de ×32 entre quartiles) mais couverture 35 %
non aléatoire — non retenu ; le 130/30 : **prédiction « du levier, pas de l'alpha » écrite
d'avance et vérifiée** ; le plafond est **monotone** des deux côtés ⇒ la valeur retenue n'est pas
accidentelle. **Promu : le portefeuille unique** (+2,51 %/an, t 1,93) — le seul qui ne demande
aucune décision prise après avoir vu les résultats.

### Strate 7 — le livrable (`3_livrable_M3/`)

- **§11** — y a-t-il de l'information sectorielle ? \|t\| groupé par date = **2,06** contre 1,96 :
  le test qui autorise tout le reste, passé de justesse ;
- **§12** — élargir à 32 instruments **ÉCHOUE** (+0,31/−0,60 contre +1,50/+0,45) ; §12.2 : seuls
  **6 ETF fins sur 21** battent le secteur qu'ils découpent (−1,61 pt/an en moyenne) —
  **c'est l'instrument, pas le signal** : ce qui a payé, c'est la concentration des méga-caps ;
- **§18** — la **carte datée** (XLRE quitte XLF le 16/09/2016, XLC quitte XLK/XLY le 21/09/2018 —
  dates de bascule d'*indice*, sources SEC primaires) : sans elle, 15,2 % du portefeuille en
  médiane était perdu avant 2018. 26 titres non tranchés dont **8 fonds mal étiquetés** — le
  chantier consigné (cf. §5) ;
- **§19** — le score sectoriel n'est pas la taille des secteurs : le classement oui (ρ 0,85-0,88),
  **les poids non**, et en sens *opposés* sur la tech (31,7 % NANC / 19,8 % GOP pour un marché
  à 29,4) — c'est cet écart que la version ETF achète ;
- **§20** — le tilt λ **retiré** (levier déguisé, cœur ≠ marché, IR croissant = artefact) au
  profit des **deux poches** : décomposition du risque (14,1 % de bêta), IR constant 0,637,
  calibration honnête (TE\* 3 % se lit ≈ 3,8 % réalisé), limite structurelle dite (mars 2020 :
  dose pleine), transfer coefficient 0,947, portefeuille tenu 12 lignes (a = 0,832 à la dernière
  coupe). Voir `FICHE_M3` partie III.

## 4 · Les pistes encore ouvertes — les seules sans résultat

1. **Le drift court post-disclosure, hors value-weighted** — la construction VW est fermée par le
   NO-GO du nb 08 ; d'autres constructions ne sont ni testées ni promises.
2. **Les 12 leaders de parti** (Wei & Zhou) — non testable ici : 89 % des achats de la fenêtre
   viennent d'une seule personne. Exigerait la liste CRS point-in-time.
3. **Conjoint vs élu** — la seule dimension cohérente en signe sur les deux ères (médianes
   +0,07/+0,08), p 0,063, sous le critère. À re-regarder si la table s'allonge.
4. **Les angles morts de données** : le champ *options* des PTR, les jalons législatifs
   (congress.gov), les votes, l'event-study comité×industrie — littérature dans
   `ETAT_DE_L_ART_STRATEGIES.md`, aucun testé faute de données.

**Et le chantier consigné, non traité** : retirer du flux les **8 fonds étiquetés
`asset_class="stock"` / `asset_type="Mutual Fund"`** (EDR, FDN, IXP, PNQI, VOX, VNQ, IYR, SCHH) —
« la vraie correction, mais elle déplacerait toutes les ancres du projet » (FICHE_M3, annexe D).

## 5 · Les pièges de navigation

- **Trois compteurs d'essais qui ne s'additionnent pas** : 160 (ligne membre, 05b §14.2) ·
  **162** (ligne titre, FICHE_M3 annexe D — l'ETAT_DE_L_ART cite encore l'ancien 84) · 155
  (nb 13+14 avant fusion).
- **Deux plafonds coexistent dans le nb 11** : avant le §17 tout est à **8,5 %** (ancres 672,35 /
  612,25 — la trace de recherche) ; le §17 et tout le nb 16 sont à **10 %** (ancres 661,57 /
  573,57).
- `_archive/FICHE_STRAT_TICKER_22JUIL_v2` est **antérieure** à la version courante (renommée
  depuis `FICHE_NOTER_LES_TITRES` — piège « v2 »).
- `3_livrable_M3/figs/m3_nav.png` ≠ `_archive/…/figs_nb13/m3_nav.png` : même nom, contenus
  différents — **ne jamais dédoublonner par nom**.
- `_archive/FICHE_NANC_GOP_COMPLET.pdf` publie un t(α₄) NANC **périmé** (1,81 ; la valeur courante
  est 2,08 — le seul chiffre du dossier qui franchit un seuil).
- `ETAT_DE_L_ART_STRATEGIES.md` empile deux documents : la note du 04/07 (non revérifiée) puis
  **l'annexe du 09/07 qui fait foi**.
- Les notebooks archivés 10/13/14/15 recréent leurs dossiers de figures **dans l'actif** si on les
  ré-exécute (chemins absolus codés en dur).

## 6 · Pourquoi il n'y a pas de `tools.py` — la doctrine

Un module commun a **déjà existé** (les 7 `.py` de `_archive/recherche_v0/`) et a été supprimé
par décision : commit `d477c473` (27/06) — *« un seul notebook de recherche AUTONOME (zéro .py) »*.
Depuis, **zéro import local dans les notebooks aux sorties figées**, et une discipline de copie
*documentée* (bannières « COPIE EXACTE 05b — cellule N »). Les raisons tiennent toujours :

1. **il n'y a pas UN alpha, il y en a deux** — la lignée membre régresse le rendement brut
   (annualisation géométrique), la lignée titre un vrai Jensen en excès du taux sans risque
   (annualisation arithmétique). Une fonction commune imposerait un choix qui changerait des
   chiffres publiés dans quatre PDF ;
2. **les constantes qui divergent sont des résultats** (purge γ à 504 j au nb 11 contre 756 au
   nb 16 ; plafond 8,5 contre 10 %) — les fondre dans des défauts de fonction, c'est enterrer le
   résultat ;
3. **les notebooks 07 et 12 valent parce qu'ils réimplémentent** (recalcul de Pelosi en double
   boucle naïve, validé à 10⁻¹² ; `beh` recalé sur `membres.csv` à 10⁻⁶). Un oracle qui importe
   ce qu'il vérifie ne prouve plus rien ;
4. **les sorties figées font preuve** — refactorer sans tout ré-exécuter dissocierait le code de
   ses sorties ; tout ré-exécuter risquerait de déplacer des ancres publiées.

Le gisement honnêtement factorisable mesuré : ~150 lignes sur 9 490 (1,6 %).
**Pour la suite** (une strate 8), le module [`tools/`](tools/README.md) fournit le moteur de la
lignée titre extrait du nb 16 et **validé contre les ancres gelées**.

**La seule exception, prouvée par ré-exécution (11/08)** : les deux notebooks *vivants* de
`3_livrable_M3/` tournent sur `tools/`. `M3_preuve_complete` (génération 2) importe le socle et
**garde toutes ses cellules de validation**, qui re-dérivent indépendamment ce que tools calcule
(la règle de démarrage recalculée == `tools.donnees`, l'oracle du nb 11 à 18 chiffres, la carte
identité, les identités du §20) ; ré-exécuté en entier, chaque assert passe et les ancres sont
identiques (661,57 / 573,57 · 162 runs). La doctrine reste entière pour les notebooks figés —
la lignée membre et les trois volets du 11 ne sont pas touchés.

Quatre défauts mineurs connus, documentés ici et laissés en l'état (les sorties sont figées) :
`_mode` diverge entre 09 (`dropna()`) et 07/12 ; le nb 11 relit `ff_factors.csv` à chaque appel de
`bilan()` (le 16 a corrigé) ; `exces_spy` est défini deux fois dans le 12 et `rotation` deux fois
dans le 16 (corps identiques).

## 7 · Temps 2 — la table du pipeline, et la passerelle

Le nettoyage vit désormais dans le pipeline (`common/backtest_clean.py`, step 7) et la table
courante corrige des tickers que la v1 du 04/07 ratait (`NOTE_DIFF_TABLE_CLEAN.md`, branche
`presentation` ; le §7 de `RAPPORT_DONNEES.md` recense les étapes). **Les
documents publiés restent adossés à la v1, archivée** ; la ré-exécution complète de la lignée
titre sur la table courante est le notebook
[`M3_table_pipeline`](3_livrable_M3/M3_table_pipeline.ipynb) — mince, entièrement
sur [`tools/`](tools/README.md) :

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
franchit son seuil, l'identité de l'IR tient, TE\* reste la question du client. Toute strate
future travaille sur la table courante, avec `tools/` — et se mesure contre
`3_livrable_M3/ancres_table_courante.json`.
