# Archive — `02_recherche_backtest/`

> **Le dossier parent a été renommé le 2026-07-31** : `00. S3S4 en cours/` → `02_recherche_backtest/`.
> Les commits, les PDF figés et les notes antérieurs à cette date parlent donc encore de « 00. S3S4 en cours ».
> C'est le même dossier. (Voir la table des trois renommages dans le `README.md` à la racine du dépôt.)

Rangement du 2026-07-21. Fichiers **déplacés** ici (jamais supprimés — récupérables dans git) parce qu'ils sont
**périmés, clos ou en doublon**. Le dossier actif ne garde que le **vivant** (notebooks qui alimentent le deck
de présentation) et les **références** encore utiles.

> ⚠️ Les `.tex` archivés ci-dessous ont leur **`.pdf` de rendu à côté** = le document figé consultable.
> **Depuis le 2026-07-31 ils recompilent aussi tels quels**, `tectonic` lancé depuis `_archive/` : leurs figures
> les ont rejoints (passe « les figures rangées », plus bas). Avant cette passe, **17 inclusions d'images sur 31
> étaient cassées** — un `.tex` écrit `figures/…` ou `\graphicspath{{figs_nb11/}}`, et **ce chemin est relatif au
> document**, pas au terminal : archiver un document sans ses images le rend muet.
>
> **Deux règles d'archive qui en découlent** — (1) un dossier `figs_nbXX/` **suit son notebook** quand il est
> archivé ; (2) une figure lue par un document **gelé** est **copiée** à côté de lui, jamais seulement déplacée,
> parce que son producteur peut encore vivre et la réécrire sous le même nom.
>
> ⚠️ **Ne jamais dédoublonner par nom de fichier**, seulement par empreinte — et de préférence pas du tout :
> `figs_nb16/m3_nav.png` (`9efec84d`) et `figs_nb13/m3_nav.png` (`9f00697a`) portent **le même nom pour deux
> contenus différents**. Un `fdupes` par nom détruirait l'état pré-fusion du 13.

## Socle périmé / doublon / non abouti

| Fichier | Ce que c'est | Pourquoi archivé |
|---|---|---|
| `NOTE_MATHS_PORTEFEUILLE_MEMBRE.tex` / `.pdf` | Spéc maths (2 col.) du portefeuille par membre (6/07) | Adossée à l'ancien `05_Portefeuille_Membre_V1` (déjà archivé dans `recherche_v1/`) ; ses formules sont reprises, plus développées, dans `RAPPORT_PORTEFEUILLE_MEMBRE` + le notebook `05b` (gardés) |
| `FICHE_09_PRESENTATION_v2.pdf` | 1er rendu « présentation » de la fiche du nb 09 (15/07) | Remplacé par la version finale `FICHE_09_ORATRICE.tex/.pdf` (gardée ; son PDF = `FICHE_09_PRESENTATION_v3.pdf`, octet-pour-octet) |
| `05b_Archives.ipynb` | Cellules retirées du notebook `05b` (ancien moteur semestriel, preuve d'équivalence) | Déjà une archive : non exécutable seul, outputs figés |
| `10_Stock_Divulgations_MathSpec.ipynb` | « Au-delà des PTR » — pré-enregistrement 2-chambres (E1/E2 gelés), §5 Résultats **verrouillée** (16/07) | Version antérieure non aboutie ; la lignée est menée à terme (House uniquement) dans `01_autres_filing_types/10_Stock_Divulgations_MathSpec.ipynb` (vivant). Garde le seul cadrage 2-chambres si une déclinaison Sénat est un jour voulue |

## Dossier 08 « Calendar-Time » (clos — verdict NO-GO)

Stratégie « copier les trades actions du Congrès » pré-enregistrée puis exécutée : **α net −0,77 %/an**,
11/12 tests négatifs → dossier **clos**. Unité isolée (aucun document gardé n'en dépend). Le récit reste
raconté dans `SLIDES_STRATEGIES_S3S4` (gardé).

| Fichier | Ce que c'est |
|---|---|
| `08_Strategie_Calendar_Time.ipynb` | Le notebook (pré-enregistré, résultats verrouillés) |
| `FICHE_PREENREGISTREMENT_08.tex` / `.pdf` | Protocole gelé AVANT calcul (grille fermée de 12 tests, gates, puissance) |
| `FICHE_08_CALENDAR_VW.tex` / `.pdf` | Fiche de résultat exécutant ce protocole → verdict NO-GO |
| `fig_08_forest.png` | La **seule** figure que `FICHE_08_CALENDAR_VW` inclut réellement — un `\includegraphics` (l.58), une image dans le PDF figé, vérifié. Co-localisée avec la fiche → son chemin relatif marche |
| ~~`fig_08_nav.png`~~, ~~`_explication_burr_covid_2020.png`~~ | ⚠️ **Cette ligne disait faux** (corrigé le 31/07) : ces deux images ne sont **utilisées par aucun document**. `fig_08_nav.png` est une figure **candidate écartée** de la fiche ; `_explication_burr_covid_2020.png` est un **schéma d'explication** (cité en prose par `00_recuperation_donnees/_archive/docs/PLAN_SLIDES_BACKTEST.md` l.147, jamais inclus) → déplacé dans `explications/`, voir plus bas |

## nb 06 + son rapport (superseded)

| Fichier | Ce que c'est | Pourquoi archivé |
|---|---|---|
| `06_Recherche_Strategie_2014_2026.ipynb` | Backtest de recherche initial, trade-based, copy-trading top-K annuel (5/07) | Le plus ancien ; question reprise et étendue par le `05b` (approche portefeuille) |
| `RAPPORT_RECHERCHE.tex` / `.pdf` | Rapport rédigé §1–§8 du nb 06 (« copier le Congrès bat-il le marché ? → non ») | Contenu désormais présenté dans la **Partie II** du deck vivant `00_recuperation_donnees/docs/SLIDES_DONNEES_S1S2_V2` ; le PDF reste ici comme version longue traçable |

## 2ᵉ passe (2026-07-23) — documents accumulés depuis

Le chantier actif est passé à la **stratégie ticker (notebook 11)**. Sont archivés ici les documents
antérieurs devenus **doublon, plan réalisé, brouillon supersédé ou note de décision figée**. Le dossier
actif ne garde que le **courant** : fiches ticker `FICHE_STRAT_TICKER_22JUIL` + `FICHE_13_REPONSE_CHEF`,
`RAPPORT_PORTEFEUILLE_MEMBRE`, `FICHE_09_ORATRICE`, `PAPIER_ETAT_DE_LART`, `SLIDES_STRATEGIES_S3S4`,
`ETAT_DE_L_ART_STRATEGIES.md`.

| Fichier | Ce que c'est | Pourquoi archivé |
|---|---|---|
| `FICHE_09_PRESENTATION_v3.pdf` | Rendu « présentation v3 » de la fiche du nb 09 | **Doublon octet-à-octet** de `FICHE_09_ORATRICE.pdf` (gardée) ; orphelin (pas de `.tex`) |
| `FICHE_09_TABLES.tex` / `.pdf` | Fiche « plan » du nb 09 (carte des 4 CSV, plan §-par-§) | Cadrage antérieur d'un notebook clos ; fiche 09 courante = `FICHE_09_ORATRICE` |
| `NOTE_NAV_PORTEFEUILLE_EN_PARTS.md` | Note de décision « NAV en parts » (méthode du chef) | Figée au §6 du `05b` (`NAVK`, `strategie_en_parts`) ; ancienne écriture dans `05b_Archives` |
| `NOTE_CHOIX_K_IS_OS.md` | Note de décision sur le choix du K (in/out-of-sample) | Verdict intégré au §11 du nb + `RAPPORT_PORTEFEUILLE_MEMBRE` §9-10 ; chantier 05b clos |
| `NOTE_PONDERATION_TOP_K.md` | Note maths : remplacer `1/K` par inverse-vol / ERC / GMV (risk parity) | Extension d'un chantier clos (05b), **jamais codée** ; non reprise côté ticker (choix Alice d'archiver) |
| `FICHE_11_PLAN_TICKER.tex` / `.pdf` | Chronologie/roadmap de pré-implémentation de la stratégie ticker | **Échafaudage réalisé** : `11_Strategie_Ticker.ipynb` construit + fiche 22JUIL écrite |
| `FICHE_11_STRAT_TICKER_V0.tex` / `.pdf` | Première spéc maths « V0, premier jet » (5 constantes, placebo) | Supersédée par `FICHE_STRAT_TICKER_22JUIL` (« LA SPÉCIFICATION » + purge FIFO γ) + nb 11 |
| `FICHE_STRAT_TICKER_22JUIL_v2.tex` / `.pdf` | Brouillon **texte-seul** de la fiche ticker du 22/07 | Antérieur à la version courante `FICHE_STRAT_TICKER_22JUIL` (07-23, avec figures) — piège « v2 » **inversé**. Seul contenu propre : l'encadré prose « borne haute, pas réplicable » (chiffres conservés dans la version courante) |
| `FICHE_REPONSES_CHEF.tex` / `.pdf` | 1ʳᵉ rédaction de la réponse aux remarques du chef (6 chantiers C1–C6) | Refondue et augmentée en `FICHE_13_REPONSE_CHEF` (9 remarques, appareil formel) — gardée |

---

*Voir aussi le sous-dossier `recherche_v1/` : l'archive de la toute première version de la recherche stratégie
(notebooks 02/03/04/05 + notes).*

## 2026-07-30 — les trois notebooks de M3 fusionnés en un seul

`FICHE_M3` exigeait **trois** notebooks pour être vérifiée (le 13 pour le protocole et les épreuves, le 15
pour les ETF, le 11 pour le netting). Chercher d'où venait un chiffre donnait donc plusieurs réponses — et
le 15 écrasait `m3_nav.png` **dans le dossier du 13**, si bien que `\graphicspath` désignait deux sources
pour une seule. Tout est désormais dans **`16_M3_Complet.ipynb`**, seul notebook de la fiche.

| archivé | pourquoi | ce qui l'a remplacé |
|---|---|---|
| `13_Methode_M3.ipynb` | socle, épreuves, §12.5 | §1--§10 et §19 du 16 |
| `15_Strategie_ETF.ipynb` | toute la partie ETF | §11--§18 du 16 |
| `14_M3_Alternatives.ipynb` | **aucune** valeur de la fiche n'en dépendait (0 exclusive sur 245 mesurée) | rien |
| `figs_nb13/`, `figs_nb15/` | figures | `figs_nb16/` |

**Ce qui n'a pas été porté**, et pourquoi : la variante ETF du §11 du 13 (elle substituait l'ETF *avant*
le `groupby`, rend $-2{,}37$ %/an et la fiche l'a abandonnée), les §12.1 à §12.4 (le diagnostic A/B/C qui l'a
réfutée), et le §12.5.1. Ils restent lisibles ici.

⚠️ **`11_Strategie_Ticker.ipynb` n'est PAS archivé** : il est la source des 8 tableaux de `PAPIER_METHODE`.
Seule sa machinerie de netting (FIFO $\gamma_3$, §17.1) a été copiée dans le 16.

**Contrôle de la fusion** : `FICHE_M3.tex` auditée contre le seul notebook 16 rend **38/38 lignes de
tableau conformes** et **0 chiffre en prose sans source**.

## 2026-07-31 — un PDF fusionné périmé

| archivé | pourquoi | ce qui le remplace |
|---|---|---|
| `FICHE_NANC_GOP_COMPLET.pdf` (387 p., 5,5 Mo) | Fabriqué le **28/07 10:51**, alors que sa source `FICHE_NANC_GOP.tex` a été recalée le **29/07 15:38** : il embarque les **45 nombres périmés** du commit `03e4053c`. Le plus grave — il publie t($\alpha_4$) NANC à **1,81** quand la valeur courante est **2,08**, c'est-à-dire le seul chiffre du dossier qui **franchit un seuil**, périmé dans le sens qui inverse la lecture | `FICHE_NANC_GOP.tex` / `.pdf` (4 p., à jour) — **eux-mêmes archivés le même jour**, quelques heures plus tard (passe ci-dessous). Le PDF fusionné n'est pas régénéré : ses 60 renvois `/GoToR` valaient pour un appareil de citation dont la fiche courante n'a plus besoin |

⚠️ **`AUDIT_FONDS_NANC_GOP_COMPLET.pdf` n'est PAS archivé** — il est la **pièce opposable** (la seule forme
où ses renvois s'ouvrent : 55 liens `/GoToR`, aucune URL de repli) et il est **régénéré** depuis le `.tex`
corrigé le 29/07 (`cff12f48` : cinq clauses du prospectus jamais lues, et deux gérants au lieu de trois).

## 2026-07-31 (2ᵉ passe du jour) — six documents rentrés, le dossier actif resserré sur M3

Choix d'Alice. Le chantier courant est la **ligne par titre** (méthode M3 + stratégie ETF), portée par
`16_M3_Complet.ipynb` et `11_Strategie_Ticker.ipynb`. Les six documents ci-dessous relèvent de lignes
**closes** (par membre, revue de littérature, réponse aux remarques du chef, répliques NANC/GOP) : rien de
ce qui reste actif ne s'appuie sur eux, chacun est un `.tex` autonome avec son `.pdf` figé à côté.

| archivé | ce que c'est | état à l'archivage |
|---|---|---|
| `PAPIER_ETAT_DE_LART.tex` / `.pdf` (7 p., 9/07) | La **synthèse** de la revue de littérature : ce que les papiers publiés trouvent sur les trades du Congrès | Sa **base de preuves reste active** : `ETAT_DE_L_ART_STRATEGIES.md` (62 chiffres confirmés / 9 corrigés / 0 introuvable) est **gardée dans le dossier actif**, avec les fiches domaine-par-domaine et la réplicabilité sur notre table |
| `RAPPORT_PORTEFEUILLE_MEMBRE.tex` / `.pdf` (4 p., 7/07) | Le rapport de la ligne **par membre** (§9-§10 : choix du K in/out-of-sample) | Ligne **close** : Sharpe 0,90 ≈ SPY 0,87, 20 significatifs bruts → 12 par appraisal ≈ 11 attendus par hasard, donc **pas d'$\alpha$**. Son notebook `05b_Portefeuille_Membre_MathSpec.ipynb` **reste actif** (il alimente le deck population/portraits) mais ne contient **aucun `savefig`** : ses 9 figures ont été extraites à la main, **aucun code ne les reproduit**. Elles l'ont rejoint le 31/07 (`figures/` archivé) → **le rapport recompile de nouveau**, 4 p. / 9 images, identique à son PDF figé |
| `SLIDES_STRATEGIES_S3S4.tex` / `.pdf` (21 p., 18/07) | Le deck des stratégies S3/S4 — dont le récit du dossier 08 « Calendar-Time » (NO-GO), qui n'était **raconté que là** | Antérieur au virage ticker. Son commentaire d'en-tête cite `ETAT_DE_L_ART_STRATEGIES.md`, **restée active** |
| `FICHE_NANC_GOP.tex` / `.pdf` (4 p.) | Nos **trois répliques** des fonds NANC et GOP, la fidélité mesurée, le diagnostic $\lambda$ | **`.tex` et `.pdf` d'accord** — le PDF a été **recompilé le 31/07** (`tectonic`) pour absorber le recalage du renvoi : les décompositions du IV(c)/IV(d) pointent `16_M3_Complet.ipynb` (§7 et §8) et non plus `13_Methode_M3.ipynb`, archivé lors de la fusion du 30/07. Contrôle : 4 pages comme avant, **6 lignes de texte changées et rien d'autre** (la phrase de renvoi et son re-découpage), t($\alpha_4$) NANC toujours à **2,08**, 0 overfull/underfull. Le `.tex` appelle `figs_nb11/`, dossier resté dans l'actif : sa figure `nanc_gop_v3.png` a donc été **copiée ici** le 31/07 (voir la passe « figures ») → **plus besoin du dossier temporaire et du lien symbolique** qu'il fallait bricoler ; la fiche recompile en place, 4 p. / 1 image |
| `FICHE_13_REPONSE_CHEF.tex` / `.pdf` (6 p.) | La réponse aux **9 remarques d'Olivier Herbout** (3 du message R + 6 annotées A), un opérateur à un paramètre par remarque | `.tex` et `.pdf` **cohérents** (tous deux du 31/07 14:41 ; vérifié dans le PDF : l'encadré « État au 22/07/2026 — document figé » et le renvoi « 84 runs, `FICHE_M3` annexe D » y sont). Le document **se déclare lui-même figé** : ses neuf opérateurs sont un pré-enregistrement dont **aucun run primaire n'a été exécuté** |
| `FICHE_09_ORATRICE.tex` / `.pdf` (2 p., 15/07) | La fiche de présentation orale du notebook 09 (les 4 tables CSV propres) | Notebook 09 clos ; il **reste actif** dans le dossier. Ses deux rendus antérieurs (`FICHE_09_PRESENTATION_v2/v3.pdf`) sont déjà ici |

**Ce qui reste dans le dossier actif**, côté documents : `FICHE_M3` (le livrable), `PAPIER_METHODE`,
`FICHE_STRAT_TICKER_22JUIL`, le dossier `AUDIT_FONDS_NANC_GOP` (`.tex`, `.pdf`, et `_COMPLET.pdf` opposable)
et `ETAT_DE_L_ART_STRATEGIES.md`.

⚠️ **Un renvoi devenu sortant** : `AUDIT_FONDS_NANC_GOP.tex` (actif, ligne 290) annonce que les répliques font
« l'objet d'un document distinct, `FICHE_NANC_GOP.pdf` » — ce document est désormais **ici**, dans `_archive/`.
Même chose pour les deux mentions de `docs_nanc_gop/README.md`. Ce sont des `\path{}` en prose, pas des liens
cliquables : rien n'est cassé, mais le chemin est à lire comme `_archive/FICHE_NANC_GOP.pdf`.

**Corrigé depuis** (passe de tri du 31/07) : les **trois** renvois sortants des documents restés actifs portent
désormais leur chemin d'archive — `AUDIT_FONDS_NANC_GOP.tex` l.290 (`_archive/FICHE_NANC_GOP.pdf`),
`FICHE_STRAT_TICKER_22JUIL.tex` l.332 (« désormais dans `_archive/` »), et le bandeau de
`ETAT_DE_L_ART_STRATEGIES.md`, qui dit maintenant pourquoi la base de preuves reste active quand sa synthèse
ne l'est plus. Vérifié : **aucun autre** des cinq documents actifs ne cite un document archivé, et la médiane
N-PORT de 10,3 % qui justifie le plafond de `FICHE_M3` est portée par la fiche elle-même (l.483, les treize
états SEC) — elle ne dépendait pas de `FICHE_NANC_GOP`.

**Ce que les documents archivés ont reçu avant de rentrer** — deux bandeaux de gel, pour qu'un lecteur ne les
prenne pas pour l'état courant : `FICHE_13_REPONSE_CHEF` (état au 22/07, ligne membre close, pré-enregistrement
dont aucun run primaire n'a été exécuté, et son compteur de 160 essais qui **ne s'additionne pas** aux 84 runs
de la ligne titre) et `FICHE_NANC_GOP` (son renvoi au notebook `13_Methode_M3.ipynb`, archivé le 30/07, pointe
maintenant `16_M3_Complet.ipynb` §7 et §8).

## 2026-07-31 (4ᵉ passe) — les figures rangées : chaque dossier suit son producteur

Le dossier actif mêlait **deux systèmes** : un `figures/` fourre-tout **et** un dossier par notebook. Le tri
s'est fait sur trois questions mesurables — *quel notebook l'écrit ?*, *quel document la lit ?*, *un code
peut-il la refaire ?* — et il a révélé que le désordre n'était pas qu'esthétique : **17 inclusions d'images
sur 31 étaient cassées** dans quatre documents de cette archive.

**La cause, en une phrase à retenir** : le chemin d'une image est relatif **au document qui l'inclut** —
`tectonic` cherche depuis le dossier du `.tex`, pas depuis le terminal. Les passes d'archivage précédentes ont
déplacé les documents en laissant leurs figures au niveau du dessus. Les PDF figés, eux, n'ont jamais menti
(vérifié image par image) : c'est la **recompilabilité** qui était perdue, donc la traçabilité.

| déplacé | n | ce que c'est | pourquoi | ce que ça répare |
|---|---|---|---|---|
| `figures/` → `_archive/figures/` | 32 (2,1 Mo) | Le fourre-tout de la ligne **par membre** : figures extraites à la main des notebooks 05, 05b et 06 au moment de rédiger les rapports | **Aucun notebook actif ne l'écrit ni ne le lit** ; ses trois seuls lecteurs sont ici (`RAPPORT_PORTEFEUILLE_MEMBRE`, `RAPPORT_RECHERCHE`, `NOTE_CHOIX_K_IS_OS`) | **16 inclusions**, d'un coup, **sans toucher une ligne de document** : les trois écrivent `figures/…`, la cible arrive à côté d'eux |
| `figs_nb14/` → `_archive/figs_nb14/` | 2 | Les deux figures du notebook 14 « M3 au crible » | Son notebook est archivé **depuis le 30/07** ; le dossier n'avait pas suivi, contrairement à `figs_nb13/` et `figs_nb15/` le même jour | rien (aucun lecteur) — c'est la **convention rattrapée** |
| 4 images → `_archive/explications/` | 4 | **Des schémas d'explication, pas des figures de résultat** (voir la table ci-dessous) | Aucun `savefig` ne les produit, aucun document ne les inclut : ce sont des dessins pédagogiques. Deux traînaient dans `figs_nb11/`, une dans `_archive/`, **une à la racine du dépôt** | `figs_nb11/` devient **exactement les 36 sorties du notebook 11** — un invariant qui se teste |
| `figs_nb11/nanc_gop_v3.png` → **copie** dans `_archive/` | 1 (62 Ko) | La figure des trois répliques NANC/GOP | `FICHE_NANC_GOP` est **gelée** mais lisait une image d'un dossier **vivant** : le notebook 11 la réécrit sous le même nom à chaque exécution. Une **copie**, donc, pas un déplacement | la **17ᵉ** inclusion, et le contournement « dossier temporaire + lien symbolique » disparaît du mode d'emploi |

### Les quatre schémas d'explication

Leurs noms sont **conservés tels quels** : `_explication_burr_covid_2020.png` est citée en prose ailleurs
(`00_recuperation_donnees/_archive/docs/PLAN_SLIDES_BACKTEST.md` l.147), et renommer aurait périmé la citation
pour un gain cosmétique.

| fichier | ce qu'il explique | venait de |
|---|---|---|
| `exemple_purge.png` | La **purge FIFO γ** en 4 panneaux, sur un exemple chiffré (2 lots AAPL, vente de 200 parts, γ = 0,5) : « la purge ne retire aucune part, elle pèse seulement la vente dans le signal du titre » | `figs_nb11/` |
| `scenarios_fifo.png` | Les **5 scénarios** S1–S5 d'appariement d'une vente : « une vente prend toujours le plus vieux lot d'abord — l'âge étiquette la part, il ne choisit pas le lot » | `figs_nb11/` |
| `_explication_burr_covid_2020.png` | Le cas Burr / COVID 2020 | `_archive/` (racine) |
| `_explication_purge_6ans.png` | Pourquoi la purge du site officiel ne nous atteint pas : « les 6 ans = un délai d'archivage imposé par la loi, rien à voir avec la durée d'un mandat » | **la racine du dépôt** |

### Ce qui est régénérable, et ce qui ne l'est pas

C'est la vraie question quand on archive une figure : une orpheline régénérable est remplaçable, une orpheline
unique est une **pièce**. Le décompte a été fait fichier par fichier.

| lot | n | régénérable ? |
|---|---|---|
| `figures/` | 32 | **NON pour 31 d'entre elles** — aucun notebook du dépôt ne cite leur nom. Seule `fig_10_gates.png` a un producteur (le notebook 10, archivé). ⚠️ Le notebook `05b` est **actif** mais compte **0 `savefig`** : ses 10 `fig_nb05b_*` et les 9 `fig_rap_*` du rapport ne sont **reproductibles par aucun code** |
| `explications/` | 4 | **NON** — dessins faits à la main |
| `figs_nb14/` | 2 | oui, par le notebook 14 archivé |
| `figs_nb13/`, `figs_nb15/` | 9 | oui, par les notebooks 13 et 15 archivés |
| `recherche_v1/figures/` | 6 | **NON** — aucun des notebooks V1 n'a de `savefig` |
| `fig_08_forest.png`, `fig_08_nav.png` | 2 | **NON** — le notebook 08 n'a plus de `savefig` |

**C'est la raison pour laquelle les dossiers de figures restent versionnés**, contrairement à `cache/` et
`build_cache/` qui sont ignorés : ceux-là se régénèrent, ceux-ci non. Ignorer `figs_*` perdrait pour de bon la
famille `fig_nb05b_*` — et ferait mentir la phrase qui justifie qu'on archive au lieu de supprimer.

### Les doublons d'empreinte : gardés, parce que cinq d'entre eux sont une preuve

| empreinte | fichiers | ce que l'égalité octet-à-octet prouve |
|---|---|---|
| `49f59be3` · `75cb2f96` · `540060ec` · `b09d40a8` | `figs_nb13/{m3_decomposition,m3_facteurs,m3_frein,m3_rolling}.png` ≡ `figs_nb16/` | que la **fusion du 30/07 n'a rien changé** à ces 4 figures : le notebook 16 régénère exactement ce que le 13 produisait. Un contrôle de non-régression, matérialisé |
| `db2c5056` | `figs_nb15/etf_livrable.png` ≡ `figs_nb16/etf_livrable.png` | idem pour la partie ETF |
| `8932f67a` | `figures/fig_nb05b_vt_membre.png` ≡ `figures/fig_rap_vt.png` | que les figures du rapport ont bien été **prélevées dans le vivier du 05b** : même image, deux conventions de nom |
| `91b5e5a8` | `_archive/nanc_gop_v3.png` ≡ `figs_nb11/nanc_gop_v3.png` | la copie volontaire de cette passe (contenu identique ⇒ **même blob git, 0 objet ajouté** à l'historique) |

### ⚠️ Le piège : les notebooks archivés recréent leur dossier au mauvais endroit

Les notebooks **10, 13, 14 et 15** écrivent leurs figures dans un chemin **absolu codé en dur** vers le dossier
**actif** (`{RACINE}/02_recherche_backtest/figs_nbXX`, `figures/`) suivi d'un `os.makedirs(..., exist_ok=True)`.
Les réexécuter recrée donc un dossier de figures **un niveau trop haut**. Ce n'est pas une régression : c'est le
prix de ne pas retoucher un notebook gelé, dont la sortie affichée imprime encore l'ancien chemin. Rattrapage :
`git mv figs_nbXX _archive/figs_nbXX`, et le contrôle ci-dessous le détecte.

### Le contrôle, rejouable

Ce README porte sa propre vérification. Le script `controle_figures.py` (scratchpad de la session) résout chaque
inclusion de chaque `.tex` et `.md` selon la vraie règle de recherche — dossier du document, puis
`\graphicspath`, avec repli d'extension, et il comprend la macro maison `\fig{}` y compris son préfixe.

| contrôle | attendu |
|---|---|
| inclusions résolues | **31 vérifiées, 0 manquante** (avant la passe : 17 manquantes) |
| `figs_nb11/` = sorties du notebook 11 | **36 = 36** |
| `figs_nb16/` = sorties du notebook 16 | **6 = 6** |
| `_archive/figs_nb14/` = sorties du 14 | **2 = 2** |
| documents **actifs** recompilés (`tectonic -o` hors du dépôt, pour ne pas écraser les PDF versionnés) | `FICHE_M3` 4 p./2 fig. · `PAPIER_METHODE` 2 p./3 · `FICHE_STRAT_TICKER_22JUIL` 3 p./8 · `AUDIT_FONDS_NANC_GOP` 2 p./0 — et **texte identique** au PDF versionné dans les quatre cas |
| documents **archivés**, recompilés **en place** | `RAPPORT_PORTEFEUILLE_MEMBRE` 4 p./9 fig. · `RAPPORT_RECHERCHE` 10 p./2 · `FICHE_NANC_GOP` 4 p./1 · `FICHE_08_CALENDAR_VW` 1 p./1 — tous **égaux à leur PDF figé** |
| nature du diff | 38 renommages **tous `R100`** (aucun contenu touché), 1 ajout (la copie), **0 suppression** |

⚠️ Toujours compiler avec `-o "$(mktemp -d)"` pour un contrôle : sans `-o`, `tectonic` écrit le PDF **à côté du
`.tex`** et écrase donc le rendu figé, c'est-à-dire précisément ce que cette archive garantit.
