# `analyses/` — Le code derrière chaque conclusion (reproductible)

Chaque script ci-dessous est **autonome, documenté et reproductible** : il réutilise `../data.py` (journal
Quiver 2014-2026) et `../prices.py` (prix yfinance + facteurs Fama-French, **en cache** → exécution en
< 2 min), puis imprime les chiffres clés qui justifient sa conclusion. **Aucun n'est une boîte noire** :
on peut lire la méthode (docstring en tête) et relancer pour vérifier.

> **But** : ne pas conclure « ce n'est pas une bonne voie parce qu'une IA l'a dit », mais **montrer
> pourquoi**, avec du code vérifiable. Lancer : `.venv/bin/python "00. S3S4 en cours/analyses/<nom>.py"`.

## Les 6 angles (chacun cherche ACTIVEMENT du signal)

| Script | Question | Conclusion (chiffre clé reproduit) |
|---|---|---|
| **`ic.py`** | Y a-t-il de l'**information** (corrélation signal↔rendement, indépendante du portefeuille) ? | **OUI, faible.** Le **nb d'acheteurs distincts** (breadth) prédit : IC ≈ **0,02**, t_NW **1,95** (6 m) à **2,86** (12 m). Seuls les **achats** informent ; le **montant $** ne marche pas ; spread breadth **+1,9 %/an, t=1,88**, instable (négatif 2020/24/25). |
| **`event_study.py`** | Les achats battent-ils le marché (CAR vs SPY, court & long terme) ? | **Agrégé : non** (médianes négatives). Gros achats ≥50k : **+4 % @252j** mais les **ventes ≥50k aussi** (+2,5 %) → tilt de style, pas d'info directionnelle. Alpha FF-Carhart calendar-time **t=1,7 (NS)**. Concentré **2019-2021**. |
| **`long_short.py`** | Un alpha est-il **caché par le beta** (market-neutral) ? | **NON.** Long-short : alpha **t < 1,3** (1/3/6 m), beta marché ≈ 0. Décile net-buying plat à négatif. Variante date-trade nulle. → hypothèse « le beta cache l'alpha » **rejetée**. |
| **`committee.py`** | Les achats **alignés sur la juridiction de commission** surperforment-ils ? | **NON** (la thèse la plus citée). Brut spectaculaire (+2,3 pts, t≈3,1) **mais** à secteur×année constant l'effet **disparaît/s'inverse** (beta défense) ; **~86 %** des alignés viennent de **2 personnes** (Khanna+McCaul) ; au niveau membre, non favorable. |
| **`characteristics.py`** | Quelle **caractéristique de trade** porte du signal (taille, chambre, vitesse de déclaration, nouveauté) ? | **Faible et non généralisable.** Taille >250k / House / divulgation ≤10 j semblent porter (t naïf >2,5) **mais s'effondrent sous |t|=2 en clusterisant par membre** → porté par une poignée (Green, Khanna, Perdue). Nouveauté ≈ 0. |
| **`ml.py`** | Une **structure prédictive** quelconque (gradient boosting, OOS strict) ? | **Quasi rien.** AUC **OOS ≈ 0,52** (train ≈ 0,74 = sur-apprentissage), sous la baseline ; la permutation ne retient que le **beta** (aucune feature « initié ») ; quartile haute-confiance de **médiane négative**. |

## Synthèse

Il existe une **information faible mais réelle** — la *breadth* d'achat du Congrès (`ic.py`) — qui n'est
**ni du beta, ni du bruit**. Mais elle est **sous le seuil d'exploitabilité** : IC minuscule, **instable
selon les régimes**, **survivorship** (panel = 1188/4847 tickers cotés, délistés exclus → optimiste),
**coûts** non couverts qui l'absorberaient, et chaque « thèse d'edge » (taille, commission, leadership,
conviction) se **dissout** en beta sectoriel ou en quelques individus. C'est pourquoi l'écosystème
(Quiver…) a de la valeur comme **produit de données** (il y a une info à faire remonter) sans pour autant
fournir un **alpha net** suivable. Le verdict net-de-coûts du portefeuille est dans `../RAPPORT_STRATEGIE.md`.

## Limites communes à toutes les analyses (à dire au chef de recherche)
- **Survivorship** : seuls les tickers encore cotés (prix yfinance) sont dans le cache → les CAR
  long-horizon sont des **bornes hautes** (les faillites/délistés manquent).
- **Fenêtres chevauchantes** : les t-stats « naïfs » de coupe transversale sont gonflés ; on rapporte
  systématiquement une version robuste (**Newey-West** ou **clustering par membre**) — c'est elle qui
  dégonfle le signal.
- **Multiple testing** : des dizaines de coupes testées ; sans correction Bonferroni/FDR, ~1 « significatif »
  est attendu par hasard. On l'a noté partout.
- **`size_usd`** = borne basse de la fourchette STOCK Act (montant réel inconnu) → le tri par taille est bruité.
- **Entrée `filed`** (date publique) = ce qu'un suiveur peut réellement faire ; l'edge éventuel à `traded`
  (avant divulgation) n'est pas exploitable légalement.
