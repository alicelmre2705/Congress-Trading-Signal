# Fiche de présentation orale — Congress Trading Signal · la couche données

*Support de présentation : vision d'ensemble + résultats clés. Le détail technique est dans le rapport.*

---

## 1. Le problème (l'accroche)
- Depuis le **STOCK Act (2012)**, les membres du Congrès américain doivent **déclarer publiquement** leurs transactions boursières, en principe sous **45 jours** (rapports appelés *PTR*).
- Hypothèse de recherche (littérature : Ziobrowski, Karadas) : par leur position (commissions clés, accès à l'information), ces déclarations pourraient contenir un **signal exploitable**.
- L'idée à terme : une stratégie de **copy-trading** qui réplique ces trades **après** leur publication (jamais avant — principe *anti-look-ahead*).
- **Mais** avant toute stratégie, il faut une **couche de données irréprochable**. C'est mon livrable.

## 2. Le livrable en une phrase
- Une base **propre, traçable et honnêtement validée** de **90 487 transactions**, sur les **2 chambres** (Chambre + Sénat), **2020–2026** : extraites, rattachées à leur auteur, enrichies, et validées contre une source externe.

## 3. D'où viennent les données
- **Chambre** : le site public du *House Clerk* → un index annuel → les **PDF** des déclarations.
- **Sénat** : le portail *eFD* (après acceptation d'un formulaire d'accès) → soit une **page web**, soit un **scan papier**.
- **Référentiel public des élus** : pour savoir qui est qui (identité, parti, commissions).
- **Deux services externes** : **Claude Vision** (pour lire les scans) et **Quiver** (pour valider — *jamais réinjecté*).
- **Deux dates** par déclaration : la date du **trade**, et la date de **divulgation** (publication). On date tout par la divulgation → anti-look-ahead.

## 4. Le défi central : électronique vs scanné
- Une déclaration arrive sous **2 formes** : du **texte** exploitable directement, ou une **image** qu'il faut « lire ».
- C'est la **fourche** du projet → **4 sous-corpus** : Chambre électronique, Chambre OCR, Sénat électronique, Sénat OCR.
- Volumes : Chambre **32 676** électronique + **48 970** scannés ; Sénat **7 161** + **1 680**.
- Point marquant : **la moitié des déclarations de la Chambre ne sont que des images** (scans) → d'où le recours à l'OCR.

## 5. Le parcours d'une transaction (le pipeline)
- **(1) Identité** : un nom libre (« Buddy Carter », « N. Pelosi »…) → un **identifiant officiel unique**. → **99,99 %** rattachées (Chambre), **100 %** (Sénat).
- **(2) Extraction**, selon la forme :
  - Texte (PDF lisibles, HTML) → **analyse déterministe**.
  - Images (scans) → **OCR par Claude Vision**, avec **redressement** des pages couchées.
- **(3) Enrichissement** : ticker → **secteur** (classification GICS, 11 secteurs) → **ETF** correspondant ; montant ramené au milieu de la fourchette ; ancienneté de l'élu.
- **(4) Table finale homogène** : **12 champs « métier » garantis** sur les deux chambres.
- **(5) Validation externe** contre Quiver.

## 6. Les résultats clés (à retenir)
- **90 487** transactions · 2 chambres · 7 ans.
- **Identité : 99,99 % / 100 %** rattachées.
- Couverture **ticker** ≈ 85 % (Chambre) / 71 % (Sénat) ; **secteur** ≈ 83 % / 62 %.
- Les « trous » de couverture sont surtout des **actifs non cotés** (obligations, *munis*) qui n'ont **légitimement pas** de ticker — pas un défaut.

## 7. La validation Quiver (le point subtil — à bien expliquer)
- On compare **au niveau transaction**, par **scope** : électronique seul / OCR seul / les deux.
- **Limite clé** : Quiver **ne suit que les ACTIONS cotées**. Le non-coté (munis, obligations) est **hors de son périmètre** → ni validable, ni une erreur.
- **Électronique : quasi parfait (98–99 %)** → confirme que l'analyse de texte est fiable.
- **OCR : à lire en 2 questions** :
  - *Le trade existe-t-il ?* Oui pour **78–88 %** des scans **tapés** ; mais **35 %** seulement pour le **manuscrit**.
  - *A-t-on lu la bonne date ?* C'est **LA** limite : date exacte **68 %** sur le tapé, **37 %** sur le manuscrit.
  - → Quiver **corrobore les trades tapés** ; notre vrai point faible est la **lecture des dates manuscrites** (d'où l'exclusion du manuscrit).
- **Sénat papier** : pas de contrôle externe possible (Quiver n'a pas ces déposants, et c'est surtout du non-coté).

## 8. Qualité & reproductibilité (la rigueur)
- Un **rapport de qualité automatique** (6 contrôles : cohérence des dates, délais légaux, montants, concentration, etc.).
- **Reproductibilité** : le pipeline n'est pas rejouable hors-ligne, donc on prouve la justesse autrement :
  - **« Golden »** : empreinte exacte de **toutes** les sorties (**125** fichiers Chambre, **76** Sénat) → toute modif involontaire est détectée.
  - Reproductions **fonction par fonction** + un audit qui **asserte les invariants** (totaux, identité).

## 9. Les limites assumées (l'honnêteté)
- **Manuscrit exclu** par défaut : lecture des dates trop incertaine.
- **Pas de ticker/secteur** pour les actifs non cotés (par nature).
- **Commissions** = photo actuelle, pas l'historique daté.
- **Baisse de couverture Sénat 2025–26** = changement de **composition** (plus de munis), pas une dégradation d'extraction.

## 10. Conclusion & suite
- Une couche de données **complète, identifiée, enrichie, validée honnêtement et reproductible** — sur laquelle une stratégie peut être bâtie **en connaissant ses limites**.
- **Suite (hors de ce livrable)** : la **stratégie et le backtest** (copy-trading actions, puis ETF sectoriels) — phases S3–S4.

---

## Phrases-chocs à placer (si besoin)
- « 90 487 transactions, deux chambres, sept ans. »
- « Le vrai défi : la moitié des déclarations ne sont que des images. »
- « On valide contre Quiver, mais on ne le réinjecte jamais. »
- « Notre seule vraie limite, ce sont les dates manuscrites. »
- « Tout est figé et reproductible à l'octet près. »

## Si on me pose la question…
- **« Pourquoi un LLM (Claude Vision) et pas un OCR classique ? »** → formulaires couchés, manuscrits, cases à cocher : il faut *lire* ET *structurer* d'un coup ; un OCR classique rend du texte brut sans structure.
- **« Comment vous savez que c'est juste ? »** → électronique validé à 98–99 % par Quiver ; OCR corroboré sur les actions ; et tout est figé/reproductible (golden).
- **« Pourquoi la couverture du Sénat baisse en 2025–26 ? »** → composition : plus d'obligations municipales (non cotées, donc sans ticker) ; ce n'est pas une dégradation.
- **« Quiver ne fausse pas la validation ? »** → non : on ne le réinjecte jamais, c'est seulement un point de comparaison externe.
