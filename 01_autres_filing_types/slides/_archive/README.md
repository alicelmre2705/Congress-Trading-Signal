# slides/_archive/ — decks supplantés

Les decks courants sont dans `../` : **`SLIDES_DONNEE_HOUSE_court`** (39 p., 22/07 — l'élagage du
80 p.) et **`SLIDES_AUTRES_DEPOTS`** (35 p., 21/07).

| deck | pages | motif d'archivage |
|---|---|---|
| `SLIDES_DONNEE_HOUSE.pdf/.tex` | 80 | le deck complet livré le 22/07 (`99ba8c95`), remplacé le jour même par sa version courte ; archivé le 23/07 |
| `SLIDES_HOUSE.pdf/.tex` | 42 | deck du 14/07, antérieur à la refonte donnée-house |
| `SLIDES_HOUSE_V2.pdf/.tex` | 23 | resserrage du 14-17/07, antérieur lui aussi |

**Réparation 2026-08-11** : `SLIDES_DONNEE_HOUSE.tex` avait déménagé sans réécrire son
`\graphicspath{{../figures/}{figs/}}` → 12 inclusions cassées. Le graphicspath est réduit à
`{figs/}` (une ligne, commentée dans le fichier) et **toutes les figures des trois decks sont
copiées dans `figs/`** (27 fichiers) : l'archive est auto-contenue. Les trois `.tex` compilent
depuis ce dossier (vérifié tectonic, 2026-08-11).
