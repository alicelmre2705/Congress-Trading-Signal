# Strate 5 — noter les titres

Le virage du projet : on ne copie plus des élus, on **score des titres** (dollars déclarés ×
nombre d'élus, purge FIFO γ, fenêtre choisie sur la concentration). Trois volets, découpés du
même run (sorties figées) :

| volet | contenu | rendu |
|---|---|---|
| [`11_Strategie_Ticker.ipynb`](11_Strategie_Ticker.ipynb) | le socle (§1-§7), les 6 tests (§8-§11), les autres pistes (§12), les méthodes M1→M4 (§16-§17) | [HTML](11_Strategie_Ticker.html) |
| [`11b_Replique_NANC_GOP.ipynb`](11b_Replique_NANC_GOP.ipynb) | la réplique des ETF NANC/GOP — six versions, le diagnostic λ (§13.0-§13.15) | [HTML](11b_Replique_NANC_GOP.html) |
| [`11c_Strategies_Quiver.ipynb`](11c_Strategies_Quiver.ipynb) | les stratégies Quiver répliquées (§14-§14.2) | [HTML](11c_Strategies_Quiver.html) |

Documents : [`PAPIER_METHODE.pdf`](PAPIER_METHODE.pdf) · [`FICHE_STRAT_TICKER_22JUIL.pdf`](FICHE_STRAT_TICKER_22JUIL.pdf) ·
[`AUDIT_FONDS_NANC_GOP.pdf`](AUDIT_FONDS_NANC_GOP.pdf) (+ `_COMPLET.pdf`, 798 p., pièces incluses) ·
[`ETAT_DE_L_ART_STRATEGIES.md`](ETAT_DE_L_ART_STRATEGIES.md). Les 18 pièces officielles :
`docs_nanc_gop/` (brutes) et `docs_nanc_gop_surlignes/`.

## Les résultats

**Les six tests** (2014-2026, brut) : à τ +1,71 %/an (t 1,03) — mais **à la divulgation δ :
+0,35 %/an (t 0,18)**, le résultat qui commande tout ; short −12,8 %/an (les titres vendus
montent) ; comités +7,67 à τ mais le placebo fait aussi bien, et −3,65 à δ ; dépôts tardifs
−8,25 %/an.

![À la transaction contre à la divulgation](figs_nb11/divulgation.png)

**Les quatre méthodes** (achats seuls, 3 ans à δ, top-150, plafond 10 %) :

| méthode | démocrates | républicains |
|---|---|---|
| M1 · une voix par membre | +0,12 % (t 0,06) | — |
| M2 · dollars purs | +1,43 % (t 1,04) | +0,49 % (t 0,26) |
| **M3 · dollars × élus (retenue)** | **+3,40 % (t 1,61)** | **+1,24 % (t 1,61)** |
| M4 · M3 + filtre θ=50 | +5,14 % (t 1,30, β instable) | +1,44 % (t 0,98) |

![Les méthodes, NAV](figs_nb11/meth17_nav.png)

![D'où vient l'excès — la cascade](figs_nb11/meth17_cascade.png)

**NANC/GOP** : trois versions retenues (A score · B livre · C bascule), ρ ≈ 0,73-0,75 — et le
chiffre qui clôt le dossier : leurs positions valent jusqu'à **25× le flux déclaré**, leur
fournisseur n'est pas les fourchettes publiques.

![Nos répliques contre les fonds réels](figs_nb11/nanc_gop_v3.png)

**Quiver** : réplique fidèle ≈ **22 %/an** (2020-26) contre **36,2 % annoncés** — tous leurs
paramètres divulgués sont matchés, leur panneau de métriques est incohérent (vol 4,63 % avec
β 1,14) ; l'écart vit dans leur boîte noire.

![La réplique Quiver](figs_nb11/quiver.png)

*Le détail piste par piste : [la carte de la recherche](../README.md), strate 5.*
