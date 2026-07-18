# Les types de rapports du Sénat — quelle part le PTR pèse-t-il ?

> Branche `presentation` · 2026-07-18 · périmètre : **Sénat uniquement**.
> Pendant : `docs/ANALYSE_FILING_TYPES_HOUSE.md` (Chambre, 35 315 dépôts, P = 8 252 = 23,4 %).
> Question : notre collecteur ne récupère que les **PTR** (`report_types=[11]`) → 2 153 PTR.
> Quelle est la part des PTR **parmi tous les types de rapports** déposés au Sénat ?
>
> 🔬 **Notebook reproductible** : `Analyse_Types_Rapports_Senat.ipynb` (racine du module) rejoue le
> scrape (Report Types + Filer Types), valide les sommes et produit la figure `slides/fig_senat_types.png`
> de la slide 1e.

## 1. Réponse en bref

- Le portail **eFD** (`efdsearch.senate.gov`) permet de filtrer par type de rapport. Notre
  collecteur (`senate/census_probe.py:70`, `senate/digital.py:71`, `senate/ocr.py:122`) coche
  **toujours `report_types="[11]"` (PTR seul)** → on ne connaissait pas les autres types.
- **Mesure directe (2026-07-18)** en re-interrogeant le portail sans filtre de type
  (`report_types=[]`, `filer_types=[]`, fenêtre 2014-2026) :

| | dépôts | source |
|---|---:|---|
| **Tous types** (report_types=[]) | **5 096** | `recordsTotal` eFD |
| **PTR** (report_types=[11]) | **2 160** (portail) · **2 153** (notre census, contre-vérif.) | eFD / census PTR |
| **→ part des PTR** | **≈ 42 %** (2 160 / 5 096) | — |

Le ratio principal est **2 160 / 5 096** (numérateur et dénominateur du **même** portail, **même**
fenêtre) ; notre census 2 153 sert de contre-vérification indépendante (écart 7, cf. §3).

- **Au Sénat, le PTR pèse ~42 % des dépôts — presque 2× plus qu'à la Chambre (23,4 %).**

> **Comparabilité House ↔ Sénat (apples-to-apples).** Les deux chiffres sont « PTR ÷ **tous** les
> dépôts » sur **la même fenêtre 2014-2026** et **le même périmètre de déposants** (élus + anciens
> élus + candidats, tous inclus au dénominateur des deux côtés). Deux asymétries de **méthode** (pas
> de périmètre) subsistent, à garder en tête : (a) la répartition par déposant est **native** au
> Sénat (le portail expose 3 _Filer Types_) mais seulement **dérivée** à la Chambre (aucun champ de
> statut ; un ancien élu y apparaît comme un dépôt ordinaire, repéré par matching de noms) ;
> (b) « candidat » est un **type de document** à la Chambre (type C = 10 105) mais un **type de
> déposant** au Sénat (510) ; (c) le 35 315 Chambre est **rejouable hors-ligne** (index XML) alors
> que le 5 096 Sénat vient d'un **scrape ponctuel** du portail.

## 2. Détail par type de rapport (PROPRE — somme exacte)

Le formulaire eFD expose **exactement 5 _Report Types_** : _Annual_, _Periodic Transactions_,
_Due Date Extension_, _Blind Trusts_, _Other Documents_. En interrogeant les bons codes, ces
catégories **partitionnent proprement** les 5 096 dépôts (somme exacte, pas de recoupement) :

| _Report Type_ (nom formulaire) | code | dépôts | part |
|---|---:|---:|---:|
| **Annual** (déclaration annuelle + _Candidate Report_) | 7 | 2 165 | 42 % |
| **Periodic Transactions** (PTR) — confirmé `census_probe.py:70` | 11 | 2 160 | 42 % |
| **Due Date Extension** | 10 | 753 | 15 % |
| **Blind Trusts** | 14 | 18 | 0,4 % |
| **Other Documents** | — | ~0 | ~0 |
| **Total** | | **5 096** | 100 % |

Vérif : 2 165 + 2 160 + 753 + 18 = **5 096** = `report_types=[]`. **Aucun recoupement.**

⚠ **Correction d'une erreur antérieure.** Une première sonde avait additionné des **sous-codes
d'amendement/variantes** (codes 5 = 465, 12 = 118, 8 = 33, 13 = 20, 6 = 11) qui sont **comptés à
l'intérieur** d'_Annual_ (amendements de déclarations annuelles, versions papier…), d'où une somme
gonflée (5 743 > 5 096) et une fausse conclusion « les types se recoupent ». Les **5 codes de la
partition** sont 7/11/10/14 (+ _Other_ ≈ 0). Seul **11 = PTR** est attesté dans le repo ; les 4
autres sont identifiés par le slug d'URL (`annual`, `ptr`) et les libellés de cellule
(« Due Date Extension », « Blind Trust »).

## 2bis. Par type de DÉPOSANT (propre — somme exacte)

Le formulaire expose **exactement 3 _Filer Types_** : _Senator_, _Candidate_, _Former Senator_.
Codes découverts : **1 = Senator, 4 = Candidate, 5 = Former Senator** (les autres codes renvoient un
total parasite). Ces 3 catégories **somment exactement** :

| déposant | tous types | part | dont PTR | part des PTR |
|---|---:|---:|---:|---:|
| **Senator** | 3 370 | 66 % | 1 479 | 69 % |
| **Former Senator** | 1 216 | 24 % | 668 | **31 %** |
| **Candidate** | 510 | 10 % | **13** | 0,6 % |
| **Total** | **5 096** | 100 % | **2 160** | 100 % |

Deux faits saillants : (1) les **candidats ne tradent quasi pas** (13 PTR) — les exclure ne
changerait presque rien ; (2) les **anciens sénateurs pèsent 31 % des PTR** (mandat de 6 ans +
obligation de déclarer après le départ), bien plus que l'intuition.

**Périmètre vs Chambre** : le 23,4 % de la Chambre inclut **déjà** les candidats (type C = 10 105,
28,6 % de ses 35 315) **et** les anciens élus (« membres actuels ou passés »). Donc le 42 % brut
du Sénat (tous filers) est **déjà à périmètre égal**. Variante « élus seulement » (hors candidats) :
Sénat **47 %** (2 147 / 4 586) vs Chambre **~33 %** (8 252 / 25 210) — le rapport ~1,4× tient.

## 3. Méthode & reproductibilité

- Réutilise l'infra de `senate/census_probe.py` : `accept_agreement()` (barrière CSRF + accord),
  session `requests`, endpoint `EFD_DATA` (`/search/report/data/`), lecture de `recordsTotal`,
  pauses polies. Aucune évasion, lecture seule (comptes uniquement).
- ⚠ **Chiffre issu d'un scrape ponctuel du portail** — il n'est PAS re-dérivable hors-ligne
  (contrairement à la Chambre, dont l'index XML `{Y}FD.xml` liste tous les types). Le portail
  peut évoluer ; re-scraper `report_types=[]` pour rafraîchir.
- Écart PTR portail (2 160) vs census (2 153) = 7 dépôts (fenêtre/dédup ; négligeable pour la part).
- **Preuve que la fenêtre 2014-2026 est réellement appliquée (le 5 096 n'est PAS « tout »)** —
  contrôle direct (2026-07-18, `scratchpad/efd_datefilter_control.py`) :
  - `report_types=[]` **all-time** (2000-2030) = **6 045** > **5 096** (2014-2026) → 949 dépôts
    hors fenêtre (surtout pré-2014) sont bien **exclus** ; si le filtre de date était ignoré, on
    lirait 6 045.
  - Split additif PTR : 2014-2019 = **1 215** + 2020-2026 = **945** = **2 160** = PTR 2014-2026.
    Les deux sous-fenêtres se **partagent** exactement (au lieu de renvoyer chacune ~2 160) → le
    filtre partitionne bien par date. Ceci prouve aussi que le census (2 153) couvre 2014-2026.

## 4. Ce qui va dans le deck

Slide **1e · Tri Sénat** : badge « 2 160 _Periodic Transactions_ = **42 %** des **5 096** dépôts »,
sous-ligne « **corpus 2014-2026 — tous types** » (rend la fenêtre et le périmètre explicites,
comme House 1a), + deux barres aux **noms exacts du formulaire** :
- **par _Report Type_** (somme = 100 %) : _Annual_ 42 % · _Periodic Transactions_ 42 % ·
  _Due Date Extension_ 15 % · _Blind Trusts_ · _Other_ < 1 %.
- **par _Filer Type_** (**tous déposants** · somme = 5 096) : _Senator_ 66 % · _Former Senator_
  24 % · _Candidate_ 10 %.

Note de bas : le PTR est un type parmi d'autres → on choisit les PTR, les autres dans une autre
partie ; les candidats ne tradent quasi pas (13 PTR) ; 31 % des PTR = anciens sénateurs.
