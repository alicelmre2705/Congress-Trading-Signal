# Choix du modèle : pourquoi Claude Sonnet 4.6 (et pas Opus)

*Note de justification pour le rapport final — mise à jour le 2026-06-25.*

Tout le pipeline d'extraction passe par l'**API Claude** (SDK `anthropic`, clé `ANTHROPIC_API_KEY`) :
OCR vision des formulaires scannés, extraction des PDF digitaux, et les passes LLM
nom→ticker et ticker→secteur GICS. Le modèle retenu partout est **`claude-sonnet-4-6`**.

## 1. Principe : le bon modèle par tâche, pas un seul partout

Anthropic propose plusieurs modèles à des prix très différents. Le bon réflexe n'est pas
« le plus puissant partout » (gaspillage) ni « le moins cher partout » (qualité insuffisante),
mais d'aligner le modèle sur la difficulté réelle de chaque étape.

| Modèle | Entrée ($/1M tok) | Sortie ($/1M tok) | Positionnement |
|---|---:|---:|---|
| Haiku 4.5 | 1 | 5 | le plus rapide / économe |
| **Sonnet 4.6** *(retenu)* | **3** | **15** | **milieu de gamme, meilleur rapport qualité/prix** |
| Opus 4.8 | 5 | 25 | le plus capable (raisonnement, vision haute résolution) |
| Fable 5 | 10 | 50 | le plus puissant, réservé au très exigeant |

Sonnet n'est donc **pas** le bas de gamme : en dessous il y a Haiku. C'est le « cheval de trait »,
~2× moins cher qu'Opus en sortie pour une qualité très proche sur le texte.

## 2. Pourquoi Sonnet 4.6 convient à toutes les étapes

- **Extraction digitale (texte propre)** : qualité validée contre Quiver à **98-99 %**. Passer à
  Opus n'apporterait quasi rien pour ~1,7× le prix.
- **Détection d'orientation (deskew)** : choisir laquelle de 4 rotations est droite — tâche triviale,
  Sonnet largement suffisant.
- **Passes LLM nom→ticker et secteur GICS→ETF** : pur raisonnement texte, mis en cache et batché ;
  Sonnet est large (la couverture ticker passe de ~46 % à ~90 %).
- **OCR vision des scans** : seul point réellement difficile (formulaires manuscrits) → testé
  explicitement contre Opus, cf. §3.

## 3. Vérification sur le point dur : test Opus 4.8 vs Sonnet 4.6 sur l'OCR manuscrit

Le cas où Opus *pouvait* aider est l'OCR des formulaires **manuscrits** (cluster C), car Opus accepte
une image plus haute résolution (~2576 px côté long contre ~1568 px pour Sonnet). Test mené sur
**5 PDF manuscrits** des déposants à plus fort enjeu (Schrader, Lamborn, Harshbarger), **même image
en entrée** pour les deux modèles, **30 transactions**, coût total **0,40 $**.

| Critère | Résultat |
|---|---|
| **Complétude** | **Identique** — même nombre de transactions par document (30 vs 30) |
| **Dates** (le goulot connu) | **Inchangées** — `transaction_date` identique partout ; Opus **ne corrige pas** l'ambiguïté de date manuscrite |
| **Noms d'actifs** | Opus **à peine meilleur** : 1 seul vrai gain sur 30 lignes (Sonnet « Senlld ADR » illisible → Opus « Sea Ltd ADR » = Sea Limited / SE). La passe ticker existante rattrape déjà l'essentiel |
| **Coût** | Opus ≈ **3×** Sonnet (0,30 $ vs 0,10 $ sur ces 5 docs) |

**Conclusion du test.** Opus lit les *noms* un peu plus proprement mais ne touche pas au vrai blocage
— **les dates**, dont l'erreur est une ambiguïté OCR intrinsèque, pas une affaire de modèle. Il ne
rend donc pas le cluster C fiable, pour 3× le prix.

## 4. Décision

> **On retient `claude-sonnet-4-6` pour l'ensemble du pipeline.** C'est le meilleur arbitrage
> qualité/prix : qualité validée sur le digital (98-99 % Quiver) et sur les passes LLM, et un gain
> nul-à-marginal d'Opus là où il pouvait théoriquement aider (OCR manuscrit), pour un surcoût ~3×.
> Le cluster C manuscrit reste exclu pour la raison documentée (dates peu fiables), qu'Opus confirme
> ne pas pouvoir corriger. Une montée en gamme ciblée (Opus sur un sous-ensemble dur) n'est à
> envisager que sous une nouvelle hypothèse — par exemple corriger les dates par recoupement
> Quiver/électronique, et non par un meilleur modèle.
