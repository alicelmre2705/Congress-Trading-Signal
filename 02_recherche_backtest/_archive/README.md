# Archive — `02_recherche_backtest/`

> **Le dossier parent a été renommé le 2026-07-31** : `00. S3S4 en cours/` → `02_recherche_backtest/`.
> Les commits, les PDF figés et les notes antérieurs à cette date parlent donc encore de « 00. S3S4 en cours ».
> C'est le même dossier. (Voir la table des trois renommages dans le `README.md` à la racine du dépôt.)

Rangement du 2026-07-21. Fichiers **déplacés** ici (jamais supprimés — récupérables dans git) parce qu'ils sont
**périmés, clos ou en doublon**. Le dossier actif ne garde que le **vivant** (notebooks qui alimentent le deck
de présentation) et les **références** encore utiles.

> ⚠️ Les `.tex` archivés ci-dessous ont leur **`.pdf` de rendu à côté** = le document figé consultable.
> Ils ne recompilent pas *tels quels* depuis `_archive/` s'ils pointaient vers `../figures/` (chemin relatif à
> retoucher) ; ce n'est pas nécessaire, l'archive n'a pas vocation à être recompilée.

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
| `fig_08_forest.png`, `fig_08_nav.png`, `_explication_burr_covid_2020.png` | Figures utilisées **uniquement** par `FICHE_08_CALENDAR_VW` (co-localisées → chemins relatifs OK ici) |

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
| `RAPPORT_PORTEFEUILLE_MEMBRE.tex` / `.pdf` (4 p., 7/07) | Le rapport de la ligne **par membre** (§9-§10 : choix du K in/out-of-sample) | Ligne **close** : Sharpe 0,90 ≈ SPY 0,87, 20 significatifs bruts → 12 par appraisal ≈ 11 attendus par hasard, donc **pas d'$\alpha$**. Son notebook `05b_Portefeuille_Membre_MathSpec.ipynb` **reste actif** (il alimente le deck population/portraits). Le `.tex` appelle `figures/` → depuis `_archive/` le chemin serait `../figures/` |
| `SLIDES_STRATEGIES_S3S4.tex` / `.pdf` (21 p., 18/07) | Le deck des stratégies S3/S4 — dont le récit du dossier 08 « Calendar-Time » (NO-GO), qui n'était **raconté que là** | Antérieur au virage ticker. Son commentaire d'en-tête cite `ETAT_DE_L_ART_STRATEGIES.md`, **restée active** |
| `FICHE_NANC_GOP.tex` / `.pdf` (4 p.) | Nos **trois répliques** des fonds NANC et GOP, la fidélité mesurée, le diagnostic $\lambda$ | **`.tex` et `.pdf` d'accord** — le PDF a été **recompilé le 31/07** (`tectonic`) pour absorber le recalage du renvoi : les décompositions du IV(c)/IV(d) pointent `16_M3_Complet.ipynb` (§7 et §8) et non plus `13_Methode_M3.ipynb`, archivé lors de la fusion du 30/07. Contrôle : 4 pages comme avant, **6 lignes de texte changées et rien d'autre** (la phrase de renvoi et son re-découpage), t($\alpha_4$) NANC toujours à **2,08**, 0 overfull/underfull. Le `.tex` appelle `figs_nb11/` → compilé depuis un dossier temporaire avec un lien vers `../figs_nb11/` |
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
