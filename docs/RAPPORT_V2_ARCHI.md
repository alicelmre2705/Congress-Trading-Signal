# Architecture du code — diagnostic certifié & plan de consolidation

> Revue **d'architecture** (pas le fond/les résultats). Diagnostic **vérifié par grep exhaustif**, pas
> une hypothèse. Contrainte dure : le **golden** (sorties FINAL octet-à-octet) doit rester intact.

## 1. Le constat central (certifié)

**`congress_core` n'est PAS la « boîte à outils partagée par les deux chambres » que les docstrings
annoncent.** En réalité :

- **`senate/` n'importe RIEN de `congress_core`.** Tous les imports de `senate/*.py` sont stdlib/tiers
  ou `from senate.*`. La seule occurrence de « congress_core » sous `senate/` est dans le **docstring**
  de `senate/__init__.py`. Les deux `__init__.py` décrivent l'architecture **voulue**, pas le code réel.
  (Vérifié : aucun import indirect — `senate` n'importe jamais `house` — et aucun `sys.path`/import dynamique.)
- C'est une **refonte à moitié faite** : `congress_core/__init__.py` le dit lui-même —
  « Construit d'abord pour House ; **le Sénat le consommera après sa finalisation** ». Ce câblage n'a
  jamais été fait.

**Nuance (pour être juste)** — `congress_core` *est* réellement partagé, mais seulement au niveau
**transversal** :

| Module cœur | Statut réel |
|---|---|
| `pipeline`, `enrich_tenure`, `quality` | **Partagés** : tournent sur les FINAL des **2** chambres. |
| `identity`, `schema`, `amounts`, `tickers`, `sector_enrich` | Utilisés **par House**, **dupliqués** par le Sénat. |
| `quiver` | 3 implémentations (`congress_core/quiver` via quality/tests · `house/digital:validate_quiver` · `senate/quiver_audit:reconcile`). |
| `vision_ocr` | 3 implémentations (`congress_core/vision_ocr` **tests only** · `house/ocr` inliné · `senate/ocr_engine` figé Q1). |
| `crosscheck`, `reporting` | Utilisés seulement par `quality`/tests. |
| **`paths`, `llm_resolve`** | **Code mort : 0 importeur** où que ce soit. |

## 2. La duplication est ACCIDENTELLE, pas une divergence de fond (→ consolidation faisable)

- `senate/identity.py:natural_key` est **fonctionnellement identique** à `congress_core/schema.py`
  (mêmes 7 champs, SHA-256, ticker exclu).
- Les deux `make_matcher` partagent **le même algorithme** (cascade `name_exact`/`name_by_last` +
  override). Seules différences : le dict `_MANUAL_BIO` (`Taylor` vs `JD Vance`, **fusionnable**) et la
  désambiguïsation par chambre — **pour laquelle le cœur a DÉJÀ le paramètre `chamber_priority`**
  (réservé, inutilisé).

→ Le cœur a été **conçu** pour absorber le Sénat ; il ne manque que le câblage.

## 3. Artefacts incohérents

- **5 tables orphelines + `_ocr_gate`** : `07_quiver_q1style`, `07b_quiver_truly_absent`,
  `07c_truly_absent_*`, `00_concordance_finale`, `00_quiver_q1style_status` — **aucun writer** dans le
  code courant, mais **gelées dans `tests/regression/golden_manifest.json`** (le golden valide des
  fichiers que plus rien ne produit).
- **Cache Quiver** : House dans `tables/`, Sénat dans `reference/` (incohérent).
- **House** n'a pas de `00_final_status` (le Sénat oui).
- **Hors `build_steps`** (outils ponctuels) : `house/echantillon.py`, `senate/census_probe.py`,
  `senate/revalidate_quiver.py` (réécrit des `07c-f` déjà produits par `senate/digital.py`).

## 4. Contrainte dure : le GOLDEN

FINAL octet-à-octet (**108** fichiers House / **69** Sénat) + reproductions = règle d'or. Tout
changement préserve les sorties à l'octet. **Validation de chaque item** : `check_golden.py` /
`senate_check_golden.py` = **ZÉRO ÉCART** + `tests/regression/test_*` verts.

## 5. Cible — l'architecture « juste »

```
congress_core/   schema · identity(param chambre) · amounts · tickers · llm_resolve · vision_ocr ·
                 sector_enrich · quiver(reconcile unique) · crosscheck · reporting · [paths?] ·
                 pipeline · enrich_tenure · quality        ← importé par les DEUX chambres
house/           digital.py (Clerk : ZIP→XML→PDF + manifeste) · ocr.py (clusters/deskew Chambre)
senate/          digital.py (eFD : CSRF→liste→HTML) · ocr.py (papier .gif) · fusion.py (corpus)
                 → identity / ticker_resolve / sector_enrich / quiver_audit / ocr_engine
                   SUPPRIMÉS une fois la migration faite
tools/ (ou _archive/)   echantillon.py · census_probe.py · revalidate_quiver.py   (outils ponctuels)
```

## 6. Le plan, en 3 paliers de risque

### Palier 1 — nettoyage sans risque (aucune sortie FINAL ne change)
1. **Code mort** : supprimer `congress_core/paths.py`. **Conserver `congress_core/llm_resolve.py`**
   *(c'est la cible du Palier 2 item 8 — le supprimer serait contradictoire)*.
2. **Artefacts orphelins** (5 tables + `_ocr_gate`) : les retirer du disque **et** du
   `golden_manifest.json`, re-figer (ou les re-générer par un vrai writer).
3. **Sortir** les modules hors-pipeline dans `tools/`/`_archive/`.
4. **Standardiser** le cache Quiver House → `data/house/reference/`.
5. **Corriger les docstrings** des deux `__init__.py` (architecture annoncée ≠ réelle).
6. **Aligner le rapport** (le « cœur partagé par les 2 chambres » est inexact pour l'extraction).

### Palier 2 — consolidations à sortie identique (golden-gated)
7. **Fusionner les 2 `sector_enrich`** → un module paramétré importé par les deux.
8. **Brancher la passe LLM ticker** (House + Sénat) sur `congress_core/llm_resolve.py`.
9. **Parité dashboards** : `00_final_status` côté House (additif).
10. **Harmoniser** numérotation & vocabulaire (lié au rapport).

### Palier 3 — achever la refonte : Sénat sur `congress_core` (ambitieux, golden-gated, faisable)
11. **Migrer `senate/identity` → `congress_core/identity`** (fusion `_MANUAL_BIO`, activer
    `chamber_priority`) ; `natural_key`/`SCHEMA` → `congress_core/schema` ; `amount_midpoint` →
    `congress_core/amounts` ; `recover_ticker` → `congress_core/tickers`. Golden re-prouvé à chaque pas.
12. **Validation Quiver unique** : `congress_core/quiver.py:reconcile` (riche) des deux côtés.
13. **Moteur OCR unique** : House + Sénat sur `congress_core/vision_ocr.py` ; retirer les copies
    (le `senate/ocr_engine.py` figé en dernier, golden re-prouvé). *(le plus risqué.)*
14. Uniformiser le pattern de fusion. **Garder** l'asymétrie par-an (House) vs corpus (Sénat) —
    **justifiée** par le volume — mais la **documenter**.

## 7. Recommandation
**Palier 1 + 2** d'abord (fort gain de cohérence, risque ~nul). **Palier 3** = chantier décidé,
golden-gardé, élément par élément. Chaque changement re-validé contre le golden **avant** de continuer.

---
*Diagnostic vérifié sur le code source réel. Aucune exécution n'est décrite ici comme « faite » : ce
document est la trace de référence ; les changements sont appliqués ensuite, item par item.*
