# La recherche — `02_recherche_backtest/`

Treize ans de déclarations boursières du Congrès (2014-2026), une question : peut-on en tirer une
stratégie ? Ce README donne le résultat et le chemin. L'inventaire complet de tout ce qui a été
essayé — pour ne jamais ré-explorer une piste morte — est dans
**[PISTES_TESTEES.md](PISTES_TESTEES.md)**.

## Le résultat

**Le livrable** : [`FICHE_M3.pdf`](3_livrable_M3/FICHE_M3.pdf) (4 pages), adossée au notebook
[`M3_preuve_complete.ipynb`](3_livrable_M3/M3_preuve_complete.ipynb) — tout ce que la fiche
affirme y est établi, et rien d'ailleurs.

- **M3** — pondérer chaque titre acheté par (dollars déclarés × nombre d'élus distincts),
  fenêtre 3 ans à la date de divulgation, 150 titres, plafond 10 % par ligne :
  **+3,40 %/an** au-dessus du SPY côté démocrate (t 1,61), **+1,24 %/an** côté républicain
  (t 1,61), 9 années gagnantes sur 13 des deux côtés. Le produit dépasse ses deux composantes
  (équipondéré −1,38 · élus seuls −0,65 · dollars seuls +1,43).
- **Le portefeuille unique** (les deux partis fusionnés — aucun choix de camp après coup) :
  **+2,51 %/an** (t 1,93).
- **La version ETF** (11 secteurs SPDR, table sectorielle fidèle aux dates de changement
  d'indice) : **+1,45 %/an** (t 2,05).
- **Le portefeuille final « deux poches »** : un bloc SPY + un bloc signal sectoriel, la part du
  signal calculée par formule — a = min(1, TE\*/σ̂), risque σ̂ estimé sur 756 jours, seuil
  d'inaction de 20 % — depuis le budget de risque du client TE\* (publié en profil
  {1, 2, 3} %). Le ratio d'information est le même à toutes les doses (0,637) : doser plus
  achète du rendement, jamais de la preuve. **Le seul paramètre libre, TE\*, est la question à
  poser à Ramify.**
- **L'honnêteté d'ensemble** : aucun excès sur 13 ans ne franchit son seuil de Student (2,18) ;
  **162 configurations testées, toutes publiées, aucun seuil ajusté après coup** — le protocole
  se protège par des constantes fixées avant de regarder la performance.

Autour de la fiche : [`PAPIER_METHODE.pdf`](2_noter_les_titres/PAPIER_METHODE.pdf) (les quatre
méthodes comparées) · [`FICHE_NOTER_LES_TITRES.pdf`](2_noter_les_titres/FICHE_NOTER_LES_TITRES.pdf)
(la ligne « par titre » et ses six tests) ·
[`AUDIT_FONDS_NANC_GOP.pdf`](2_noter_les_titres/AUDIT_FONDS_NANC_GOP.pdf) (ce que disent les
documents officiels des ETF NANC/GOP — version auto-portante `_COMPLET.pdf`, 798 p.) ·
[`ETAT_DE_L_ART_STRATEGIES.md`](2_noter_les_titres/ETAT_DE_L_ART_STRATEGIES.md) (69 fiches de
littérature vérifiées en source primaire).

**Le deck** : [`SLIDES_RECHERCHE.pdf`](SLIDES_RECHERCHE.pdf) (25 pages, source `.tex` à côté) —
la recherche présentée en trois parties : M1 et la construction du signal ; M2, M3, M4 et leurs
deux épreuves ; la version qui n'achète que des ETF. Ses figures viennent des dossiers `figs/` des
trois sous-dossiers, plus [`figs_archive/`](figs_archive/README.md) pour celles que produisent des
notebooks archivés sur la branche `presentation`.

## Le chemin — trois dossiers, dans l'ordre

| dossier | la question | la réponse |
|---|---|---|
| [`1_copier_les_membres/`](1_copier_les_membres/README.md) | copier les meilleurs élus bat-il le marché ? | **Non** — les « bons » élus sont au nombre attendu par hasard, et le protocole n'a pas la puissance d'en juger autrement. Dossier clos, démonstration complète. |
| [`2_noter_les_titres/`](2_noter_les_titres/README.md) | et si on notait les **titres** plutôt que les élus ? | Le virage du projet : score = dollars × élus. Quatre méthodes comparées, **M3 retenue** ; répliques des ETF NANC/GOP et des stratégies Quiver (leurs 36 % annoncés ne se reproduisent pas). |
| [`3_livrable_M3/`](3_livrable_M3/README.md) | que vaut M3, et comment la tenir en portefeuille ? | La preuve complète, la version ETF, le portefeuille deux poches — et [`M3_table_pipeline`](3_livrable_M3/M3_table_pipeline.ipynb), qui rejoue tout sur la table courante du pipeline : **aucune conclusion ne change**. |

Le socle des trois : [`tables_membres_tickers.ipynb`](tables_membres_tickers.ipynb) produit les
4 tables propres de `tables/` (membres, titres, membre×année, dictionnaire). Les moteurs de
calcul des deux familles de recherche, extraits des notebooks et validés contre leurs chiffres
témoins — les valeurs gelées que tout re-calcul doit retrouver à l'identique :
[`tools/`](tools/README.md) (`python -m tools.test_ancres` ·
`python -m tools.membre.test_ancres_membre`).

## Ce qui reste ouvert

1. **Le drift court après divulgation, hors pondération par la capitalisation** — la version
   pondérée-capi est fermée par un protocole pré-enregistré (strate 3 de
   [l'inventaire](PISTES_TESTEES.md)) ; d'autres constructions ne sont ni testées ni promises.
2. **Les 12 leaders de parti** (littérature Wei & Zhou) — non testable ici : 89 % des achats de
   la fenêtre viennent d'une seule personne. Exigerait la liste CRS point-in-time.
3. **Conjoint contre élu** — la seule dimension cohérente sur les deux périodes (médianes
   +0,07/+0,08, p 0,063, sous le seuil). À re-regarder si la table s'allonge.
4. **Les angles morts de données** : le champ *options* des déclarations, les jalons législatifs
   (congress.gov), les votes, l'event-study comité×industrie — littérature recensée, rien de
   testé faute de données.

## Pour aller plus loin

- **[PISTES_TESTEES.md](PISTES_TESTEES.md)** — l'inventaire : ~90 pistes en 7 étapes datées,
  chacune avec son résultat chiffré et l'endroit exact où c'est prouvé ; les pièges de
  navigation ; pourquoi les notebooks figés n'importent aucun module ; la passerelle vers la
  table courante du pipeline.
- Chaque dossier a son README de résultats, avec les graphiques.

*Re-exécuter les notebooks exige des caches de prix locaux non versionnés — ils se reconstruisent
via yfinance. Les tables gelées de `tables/` et les caches non re-téléchargeables (N-PORT, OCR
récupéré, prix de tickers disparus) sont, eux, embarqués. Les sorties restent lisibles dans les
`.ipynb` sans rien exécuter.*
