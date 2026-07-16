# Corrections à faire — deck `SLIDES_DONNEES_S1S2.tex`

> **Registre vivant.** On accumule ici toutes les erreurs repérées au fil de la discussion,
> puis on corrige **en une seule passe**. Rien n'est modifié dans le deck tant que la liste
> n'est pas close (sauf mention « déjà édité »).
>
> Légende : 🔴 erreur confirmée (preuve code) · 🟠 à trancher · 🟡 manque / à ajouter · ✅ déjà édité (à committer)

---

## 🔴 1. Flux « bout en bout » — Sénat papier « déjà droite » (×2 sur la même slide)

**Ce qui est écrit** — deux fois sur la slide du flux :
- bloc *Tri* : « **image papier** `.gif`, **déjà droite** »
- bloc *Extraction* : « **OCR Claude Vision** — **image déjà droite** — 3 985 »

**Pourquoi c'est faux**
- Ta propre slide 14 affiche « tapé, **couché — 255/373** » : **2 rapports papier sur 3 ont la p.1 en paysage**
  (recensement exhaustif des 373, 2026-07-12). Le deck se contredit lui-même.
- Le code s'attend **explicitement** à des scans tournés — `senate/ocr_engine.py:101` :
  > « Le formulaire peut être scanné **à 90° ou 180°** — lis-le dans son orientation correcte. »

**Ce qui est vrai** (la vraie différence Chambre/Sénat) : il n'y a **pas d'étape de redressement
géométrique** au Sénat (la Chambre, elle, teste 4 rotations via `detect_rotation`). Vision se
débrouille avec la consigne du prompt.

**Correction proposée** : « image papier `.gif` » (sans « déjà droite ») et
« OCR Claude Vision — **sans redressement (Vision gère l'angle)** — 3 985 ».

---

## 🔴 2. Slide 22 « Lire le papier Sénat » — même formule fausse

**Ce qui est écrit** : « l'image `.gif`, **déjà droite** » (légende) et « même moteur Vision que la
Chambre, mais **plus simple : l'image est déjà droite** (aucun redressement) ».

**Même cause que le point 1** → même correction : ce n'est pas que l'image est droite, c'est qu'**on
ne la redresse pas** (Vision lit l'angle tel quel).

---

## 🔴 3. Slide 20 « Les deux pistes électroniques » — la bascule n'est pas 2020

**Ce qui est écrit** : « gère deux gabarits de formulaire (**2014-2019 et 2020+**) ».

**Pourquoi c'est faux** : le **nouveau format existe déjà en 2018** — preuve visuelle, le PTR Yarmuth
#20009426 (2018) porte les codes `[ST]` et la colonne « Cap. Gains ». (Le PTR Andrews #20000077 de
2014 ne les a pas.)

**Ce qui est vrai** : le routage se fait **document par document**, par **détection du code `[XX]`**
(`ATYPE_RE`, `house/digital.py:314`) — pas par une année fixe. L'année ≤ 2019 ne sert que de
garde-fou (mode « union des deux parseurs »).

**Correction proposée** : « gère **deux gabarits de formulaire** (l'ancien, sans code type d'actif ;
le moderne avec `[ST]`, apparu **vers 2018**) — **choisis par document**, pas par année ».

---

## 🔴 4. Slide 21 « OCR Chambre » — le 12,9 % est mal attribué

**Ce qui est écrit** : « Quiver ne corrobore que **12,9 %** du manuscrit (88 % du tapé droit) :
**dates cursives trop incertaines** → 582 écartés ».

**Pourquoi c'est faux** : le 12,9 % est mesuré **SANS exigence de date** (clé élu × ticker × sens) —
donc il **n'est pas causé par les dates**. Recompté depuis les 13 CSV `07h_quiver_match_by_cluster`
(formule `quiver_scopes.py:108`) :

| cluster | **sans** date | **avec** date exacte |
|---|---|---|
| manuscrit | **12,9 %** (269/2 091) | **4,8 %** (100/2 091) |
| tapé droit | **88,0 %** (4 414/5 014) | 75,5 % (3 784/5 014) |

**La lecture juste, en deux temps** :
1. **12,9 % sans date** = même en ignorant les dates, Quiver n'a que 12,9 % de nos trades manuscrits
   → le problème est plus large que la date (ticker/nom mal lus, ou Quiver ne les a pas) ;
2. **le passage 12,9 % → 4,8 %** = *ça*, c'est la date cursive mal lue.

**Correction proposée** : garder le 12,9 % vs 88 % comme **constat de non-corroboration**, et
mentionner la date comme **deuxième symptôme** (12,9 → 4,8), pas comme la cause du 12,9.

---

## ✅ 5. Slide 2 « Le plan » — phrase supprimée (déjà édité, **à committer**)

Phrase retirée du working tree, **pas encore commitée** :
> ~~« à la fin : vous saurez ce que contient la table, comment elle a été construite, et pourquoi on
> peut lui faire confiance — limites comprises. »~~

⚠️ Le `.tex` du working tree porte aussi la **refonte Partie III non commitée d'une autre session** →
au moment de la passe, ne committer que les hunks du deck données.

---

## 🟠 6. Conclusion backtest — « max t_appr +0,99, **toutes stratégies** »

Vérifié notebook `05b_Portefeuille_Membre_MathSpec.ipynb` : +0,99 = **0,988** (K=6, sélection Sharpe,
1/K, annuel — cellule [90]) = le max des **grilles §7→§12**. Mais deux **contrôles d'autopsie §13**
le dépassent : **1,036** (« K=5 · 1/K · Sharpe rétréci », cellule [104]) et 0,976.

**À trancher** : ce ne sont pas des « stratégies » de la grille — soit on assume « toutes stratégies »,
soit on écrit « toutes **les grilles testées** » pour être exact.

---

## 🟠 7. Conclusion backtest — β ≈ 1,20 et t = 1,58 ne sont pas la même config

- **t = 1,58** (tuile stratégie 1) = config **K walk-forward, sél. IR** → son **β = 1,169** (cellule [50]).
- **β ≈ 1,20** = **1,198**, mesuré sur le **top-4 K=4 fixe, sél. IR** (cellule [42]).

Les deux tuiles côte à côte laissent croire que c'est la même config. **À trancher** : préciser
« β du portefeuille phare (top-4) » ou aligner sur la config affichée.

---

## 🟡 8. Manque — l'asymétrie manuscrit Chambre / Sénat n'est nulle part

Le flux montre « scan manuscrit → **écarté** » côté Chambre, et **rien** côté Sénat — sans dire que
le manuscrit **sénatorial est gardé**. Or la raison n'est pas qu'il serait meilleur :

- **Chambre** : Quiver **voit** le papier → on a pu **mesurer** (12,9 %) → **gating** (582 écartés).
- **Sénat** : Quiver est **aveugle au papier** (`quiver_scopes.py:15` — « Blumenthal, Feinstein = **0
  ligne Quiver** ») → **aucun mètre externe** → on garde, avec des **garde-fous internes seulement**
  (borne de dates plausibles depuis la date de dépôt `ocr_engine.py:206`, filet `_fix_year` l.257,
  `date_confidence`).

**À ajouter (1 ligne)** : « au Sénat le manuscrit est **gardé faute de pouvoir le mesurer** (Quiver ne
voit pas ce papier) — garde-fous internes uniquement ». C'est exactement la limite qu'un quant
demandera. Volume concerné : marginal (373 rapports / 3 985 txns = 2,4 % du corpus).

---

## ✅ Vérifié OK — ne pas re-questionner

| Point | Verdict |
|---|---|
| « 255/373 couchés » (slide 14) | **exact** — recensement exhaustif des 373 |
| « 9 mêmes colonnes / 1 777 pages » (Sénat élec) | **exact** — vérifié `pd.read_html`, gabarit stable |
| Bob Casey `C000228` → `C001070` | **exact** — deux vraies personnes (Chambre TX ≠ Sénat PA) |
| Angie Craig 42 lignes read-time | **exact** (37+5), documenté, golden préservé |
| Khanna / McCaul / Harshbarger = Chambre | **exact** (K000389 CA-17 · M001157 TX-10 · H001086 TN-01) |
| secteur « 79,8 % / 70,4 % » | **exact** — % de **toutes les lignes** (moyennes pondérées recalculées) |
| Sénat papier ticker 57,4 % / secteur 46,2 % | **exact** — composition (Blumenthal 38,7 % du papier, non-coté) |
| « 582 écartés » | **exact** — 775 docs manuscrits − 193 exceptions (160 docs de Schrader/Lamborn/Harshbarger + 33 curés) ; ce sont des **documents**, pas des transactions |
| Slide 61 « mêmes K membres » | **exact** — K=4 **fixe**, sélection point-in-time top-4 sous t>1,645, sélection identique entre 1/K et inverse-vol/ERC/GMV (assert dans le code) |
| « GMV × sél. appraisal : −4,5 %/an » | **exact** — t = −2,76, sélection appraisal, annuel |
| t = 1,58 / t = 1,22 | **exact** — 1,584 (K wf, sél IR) · 1,215 (Sharpe K=6, balayage) |

---

## 🗒️ À corriger aussi hors deck (dette)

- `tests/regression/README.md` affiche encore « golden House (125) / Sénat (76) » — **périmé**, les
  manifests disent **230 / 138**. Le deck (368 = 230+138) est juste ; c'est le README qui ment.
