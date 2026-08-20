# `SLIDES_RECHERCHE` — la suite de la recherche

> **32 pages.** `tectonic -X compile SLIDES_RECHERCHE.tex` depuis `02_recherche_backtest/`.

Le deck reprend la grammaire de la partie recherche de `SLIDES_DONNEES` — celle qui a été
présentée et qui a fonctionné :

1. **un plan-schéma en tête** : une chaîne de boîtes, chaque étape vers la suivante ;
2. **des chapitres lettrés** (A à E) et des **stratégies numérotées** ;
3. **une stratégie ne change qu'UNE chose** — le reste est figé et testé à l'identique ;
4. **un verdict final** en quatre tuiles.

Il se présente **seul** : il repart à Stratégie 1 et ne suppose pas qu'on ait vu le deck données.

## Le fil

```
A · Construire     B · Stratégie 1    C · Stratégie 2    D · Stratégie 3     E · Le livrable
  le signal    →   une voix par   →   pondérer aux   →   dollars × élus  →   deux poches
le titre, pas        membre            dollars          ← celle qui tient
    l'élu            pas d'α           pas d'α
```

Une seule chose distingue les trois stratégies : **comment on pondère**. La fenêtre, l'univers,
le plafond et l'exécution sont figés.

## Les 32 pages

| | contenu | pages |
|---|---|---|
| — | titre · **le plan** | 1–2 |
| **A** | changer d'objet · le périmètre · le FIFO et γ · **τ contre δ** | 3–7 |
| **B** | la règle · à τ : +1,71 % · **à δ : +0,35 %** · les extensions · bilan | 8–13 |
| **C** | ce qui change · +1,43 / +0,49 | 14–16 |
| **D** | **le consensus au carré** · +3,40 / +1,24 · **le produit dépasse ses composantes** · quatre épreuves · le portefeuille unique · la version ETF | 17–23 |
| **E** | la dose · **IR constant 0,637** · le portefeuille tenu · **TE\*** | 24–28 |
| — | verdict : les produits qui existent · les trois stratégies · ce que ça n'établit pas | 29–32 |

## Les six figures

`univers.png` · `figs_archive/scenarios_fifo.png` · `figs_pop/P4b_delai.png` · `selection.png` ·
`nav.png` + `exces.png` · `divulgation.png` · `extensions.png` + `comites.png` · `m3_nav.png` ·
`m3_decomposition.png` · `m3_facteurs.png` · `deux_poches.png` · `quiver.png`

**Deux figures écartées volontairement** — elles induisaient en erreur :

- `meth17_nav.png` ne porte qu'un panneau (côté démocrate) et affiche **déjà M3 et M4** : elle
  divulguait la suite au moment de la stratégie 2. Remplacée par un tableau.
- `etf_livrable.png` porte à droite le **tilt λ**, une forme *retirée* du livrable. Remplacée par
  un tableau titres / ETF.

## Ce qui a été supprimé de la version longue

La version 111 pages (commit `7cab4dd`, toujours dans l'historique) portait six parties. Sont
sortis : l'ouverture longue, le glossaire, les conventions de mesure, le chapitre socle
(`tables/`, `tools/`), les 26 slides « copier les membres » (déjà dans le deck données), l'état
de l'art, les portraits, l'inventaire `PISTES_TESTEES`, les annexes, et les 9 slides NANC/GOP +
Quiver — réduites à **une seule slide** de contrôle externe.

`figs_archive/` garde ses six fichiers ; seul `scenarios_fifo.png` est encore utilisé par le deck.
