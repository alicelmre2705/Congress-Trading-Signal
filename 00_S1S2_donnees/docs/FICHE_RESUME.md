# Fiche récapitulative — Congress Trading Signal · la couche données

*Résumé explicatif du projet : vision d'ensemble et résultats clés, sans le détail des fonctions. Le détail technique complet est dans le rapport.*

---

## 1. Le problème
- Depuis le **STOCK Act (2012)**, les membres du Congrès américain doivent **déclarer publiquement** leurs transactions boursières, en principe sous **45 jours** (rapports appelés *PTR*).
- Hypothèse de recherche (littérature : Ziobrowski, Karadas) : par leur position (commissions clés, accès à l'information), ces déclarations pourraient contenir un **signal exploitable**.
- L'idée à terme : une stratégie de **copy-trading** qui réplique ces trades **après** leur publication (jamais avant — principe *anti-look-ahead*).
- **Mais** avant toute stratégie, il faut une **couche de données irréprochable**. C'est mon livrable.

## 2. Le livrable en une phrase
- Une base **propre, traçable et honnêtement validée** de **89 852 transactions uniques de membres élus** (le pipeline produit 90 483 lignes brutes ; après exclusion d'une déclaration de collaborateur non-élu et dédup cross-année des re-divulgations tardives), sur les **2 chambres** (Chambre + Sénat), **2020–2026** : extraites, rattachées à leur auteur, enrichies, et validées contre une source externe.

## 3. D'où viennent les données
- **Chambre** : le site public du *House Clerk* → un index annuel → les **PDF** des déclarations.
- **Sénat** : le portail *eFD* (après acceptation d'un formulaire d'accès) → soit une **page web**, soit un **scan papier**.
- **Référentiel public des élus** : pour savoir qui est qui (identité, parti, commissions).
- **Deux services externes** : **Claude Vision** (pour lire les scans) et **Quiver** (pour valider — *jamais réinjecté*).
- **Deux dates** par déclaration : la date du **trade**, et la date de **divulgation** (publication). On date tout par la divulgation → anti-look-ahead.

## 4. Le défi central : électronique vs scanné
- Une déclaration arrive sous **2 formes** : du **texte** exploitable directement, ou une **image** qu'il faut « lire ».
- C'est la **fourche** du projet → **4 sous-corpus** : Chambre électronique, Chambre OCR, Sénat électronique, Sénat OCR.
- Volumes : Chambre **32 676** électronique + **48 966** scannés ; Sénat **7 161** + **1 680**.
- Point marquant : **la moitié des déclarations de la Chambre ne sont que des images** (scans) → d'où le recours à l'OCR.

## 5. La construction de la donnée, étape par étape

*Pour chaque étape : le **problème** concret, **comment** on le résout, le **résultat**.*

### 5.1 — D'abord : qui a déclaré ? (résolution d'identité)
- **Problème** : une déclaration ne donne qu'un **nom libre**, écrit différemment selon les dépôts (« Hon. Earl L. Carter » / « Buddy Carter » ; « N. Pelosi »). Sans clé stable, on compte un même élu plusieurs fois et on ne peut pas le rattacher à son parti/ses commissions.
- **Comment** : on ramène chaque nom à l'**identifiant officiel unique** du membre (le même partout), via le référentiel des élus + un **matcher tolérant** (gère surnoms, accents, titres, et les homonymes au Sénat). Chaque chambre a son propre matcher, car les pièges diffèrent.
- **Résultat** : **100 %** des lignes Chambre et **100 %** du Sénat rattachées (une déclaration de collaborateur non-élu — HASC — écartée du périmètre membres). À la Chambre, **256 identifiants pour 274 graphies** = exactement les variantes d'un même élu, ramenées à une seule clé.

### 5.2 — Ensuite : trier les formats (électronique ou scanné ?)
- **Problème** : une déclaration est soit du **texte** (analysable directement), soit une **image** (à lire par OCR). Se tromper de piste = perdre des transactions ou gaspiller des appels d'API.
- **Comment** : **Chambre** → on **ouvre chaque PDF** et on teste s'il a une couche de texte (lisible vs scanné). **Sénat** → le portail eFD **indique déjà** le type (page web vs papier).
- C'est la **fourche** du pipeline ; elle fixe la composition finale (Chambre 32 676 élec + 48 966 scannés ; Sénat 7 161 + 1 680).

### 5.3 — Piste Chambre électronique (PDF lisibles)
- **Problème** : sur ces PDF, une transaction n'est pas un tableau propre — elle s'étale sur plusieurs lignes, le montant déborde, le ticker se cache entre parenthèses.
- **Comment** : un **parsing déterministe** qui **reconstitue** chaque transaction (recolle les lignes coupées, repère le motif « opération + 2 dates + fourchette de montant », récupère ticker et libellé autour).
- **Résultat** : **32 676** transactions, taux d'extraction **99–100 %**.

### 5.4 — Piste Sénat électronique (pages HTML)
- **Problème** : pas de PDF, mais des **tableaux web** dont l'intitulé et l'ordre des colonnes **changent** d'une déclaration à l'autre.
- **Comment** : on lit les tableaux et on retrouve les bonnes colonnes par **appariement flou** (la colonne qui contient « ticker », ou « asset » + « name »…) — seule méthode robuste face à des en-têtes irréguliers.
- **Résultat** : **7 161** transactions.

### 5.5 — Piste Chambre scannée (OCR Claude Vision)
- **Problème** : l'autre moitié n'est que des **images**. Un recensement des **547 scans** distingue 3 familles : **tapé droit** (74 docs), **tapé mais couché** (322, le gros du volume), **manuscrit** (151).
- **Comment** :
  - **Redressement** : on montre la page sous 4 orientations et on fait **reconnaître** la bonne (plus fiable que de demander l'angle au modèle).
  - **Lecture** : Claude Vision **lit ET structure** directement en transactions (réponse en format strict, mise en cache → un re-run ne re-paie rien).
  - **Ticker** : absent des formulaires papier → **ré-associé** depuis les symboles vus en électronique, complété par un LLM.
  - **Manuscrit (cluster C) exclu par défaut** : dates trop incertaines pour une stratégie datée.
- **Résultat** : **48 966** lignes, très **concentrées** — Khanna **63 %** à lui seul, le top-3 (Khanna, McCaul, Harshbarger) **92 %** : de gros déposants qui déclarent **exclusivement sur papier**.

### 5.6 — Piste Sénat papier (images .gif)
- **Problème** : marginal (5 sénateurs) mais bien réel ; des images **droites** (pas besoin de redressement). Surtout : trop peu de données pour bâtir un dictionnaire de tickers année par année.
- **Comment** : même moteur Vision ; et **enrichissement sur tout le corpus en une passe** (un symbole vu une année sert aux autres). C'est **la seule vraie asymétrie d'architecture**, justifiée par le faible volume.
- **Résultat** : **1 680** lignes, surtout **Blumenthal (~73 %)**, massivement des **obligations municipales** (non cotées) → c'est ce qui explique la couverture plus basse du Sénat.

### 5.7 — Donner un secteur à chaque ticker (GICS → ETF)
- **Pourquoi** : la stratégie visée copie **secteur par secteur**, via des **ETF** (fonds cotés qui répliquent tout un secteur), pas action par action.
- **Comment** : on classe chaque société dans l'un des **11 secteurs GICS**, puis on mappe **1:1** vers l'ETF correspondant. Le secteur est trouvé par une **cascade** (base factuelle → LLM si besoin → corrections manuelles), en gardant la trace de qui a tranché.
- **Précision** : **« couverture » = taux de remplissage**, pas d'exactitude. Les actifs non cotés n'ont **ni ticker ni secteur par nature** — donc < 100 % est normal.
- **Résultat** : secteur renseigné à **83 % (Chambre) / 62 % (Sénat)** ; ancienneté à **100 %**.

### 5.8 — La table finale : le contrat « 12/12 »
- **Ce qui assemble tout** : une **clé naturelle de 7 champs** qui exclut volontairement le ticker (ajouté après) et la date de divulgation (pour qu'un dépôt et son amendement restent **une** transaction).
- **Déduplication non destructrice** : on retire les vrais doublons mais on **préserve les lots multi-comptes réels** (ex. Khanna déclarant plusieurs fois via plusieurs comptes).
- **Le contrat** : **28 colonnes**, dont **12 champs « métier » garantis** identiques sur les deux chambres.
- **Nuance d'honnêteté** : *« présent »* n'est pas *« sans valeur manquante »* — ticker/secteur vides pour le non-coté (légitime), commissions = **photo actuelle**, pas l'historique daté.

## 6. Les résultats clés
- **89 852** transactions uniques de membres (90 483 brutes − 631 re-divulgations cross-année) · 2 chambres · 7 ans.
- **Identité : 100 % / 100 %** rattachées (staffer non-élu exclu).
- Couverture **ticker** ≈ 85 % (Chambre) / 71 % (Sénat) ; **secteur** ≈ 83 % / 62 %.
- Les « trous » de couverture sont surtout des **actifs non cotés** (obligations, *munis*) qui n'ont **légitimement pas** de ticker — pas un défaut.

## 7. La validation Quiver
- On compare **au niveau transaction**, par **scope** : électronique seul / OCR seul / les deux.
- **Limite clé** : Quiver **ne suit que les ACTIONS cotées**. Le non-coté (munis, obligations) est **hors de son périmètre** → ni validable, ni une erreur.
- **Électronique : quasi parfait (98–99 %)** → confirme que l'analyse de texte est fiable.
- **OCR : à lire en 2 questions** :
  - *Le trade existe-t-il ?* Oui pour **78–88 %** des scans **tapés** ; mais **35 %** seulement pour le **manuscrit**.
  - *A-t-on lu la bonne date ?* C'est **LA** limite : date exacte **68 %** sur le tapé, **37 %** sur le manuscrit.
  - → Quiver **corrobore les trades tapés** ; notre vrai point faible est la **lecture des dates manuscrites** (d'où l'exclusion du manuscrit).
- **Sénat papier** : pas de contrôle externe possible (Quiver n'a pas ces déposants, et c'est surtout du non-coté).

## 8. Qualité & reproductibilité
- Un **rapport de qualité automatique** (6 contrôles : cohérence des dates, délais légaux, montants, concentration, etc.).
- **Reproductibilité** : le pipeline n'est pas rejouable hors-ligne, donc on prouve la justesse autrement :
  - **« Golden »** : empreinte exacte de **toutes** les sorties (**125** fichiers Chambre, **76** Sénat) → toute modif involontaire est détectée.
  - Reproductions **fonction par fonction** + un audit qui **asserte les invariants** (totaux, identité).

## 9. Les limites assumées
- **Manuscrit exclu** par défaut : lecture des dates trop incertaine.
- **Pas de ticker/secteur** pour les actifs non cotés (par nature).
- **Commissions** = photo actuelle, pas l'historique daté.
- **Baisse de couverture Sénat 2025–26** = changement de **composition** (plus de munis), pas une dégradation d'extraction.

## 10. Conclusion & suite
- Une couche de données **complète, identifiée, enrichie, validée honnêtement et reproductible** — sur laquelle une stratégie peut être bâtie **en connaissant ses limites**.
- **Suite (hors de ce livrable)** : la **stratégie et le backtest** (copy-trading actions, puis ETF sectoriels) — phases S3–S4.
