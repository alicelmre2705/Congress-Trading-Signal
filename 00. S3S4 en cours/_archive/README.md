# Archive — `00. S3S4 en cours/`

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
| `10_Stock_Divulgations_MathSpec.ipynb` | « Au-delà des PTR » — pré-enregistrement 2-chambres (E1/E2 gelés), §5 Résultats **verrouillée** (16/07) | Version antérieure non aboutie ; la lignée est menée à terme (House uniquement) dans `01_v1_house/10_Stock_Divulgations_MathSpec.ipynb` (vivant). Garde le seul cadrage 2-chambres si une déclinaison Sénat est un jour voulue |

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
| `RAPPORT_RECHERCHE.tex` / `.pdf` | Rapport rédigé §1–§8 du nb 06 (« copier le Congrès bat-il le marché ? → non ») | Contenu désormais présenté dans la **Partie II** du deck vivant `00_S1S2_donnees/docs/SLIDES_DONNEES_S1S2_V2` ; le PDF reste ici comme version longue traçable |

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
