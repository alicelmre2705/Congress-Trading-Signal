# Tests de non-régression

Filet de la refonte **« zéro changement »** : prouver, à l'octet près et **hors-ligne**, que le code
re-logé dans `house/`, `senate/` et le cœur `congress_core/` reproduit À L'IDENTIQUE les tables
figées, sans rien re-télécharger ni re-jouer un pipeline réseau.

Lancer toute la suite :

```bash
.venv/bin/python tests/regression/check_golden.py        # golden House (sha256 octet-à-octet)
for t in test_schema test_amounts_tickers test_identity test_tenure \
         test_crosscheck test_vision_sha test_incremental test_senate_repro; do
  .venv/bin/python tests/regression/$t.py || echo "ÉCHEC: $t"
done
```

## Principe : les pipelines NE sont PAS re-jouables hors-ligne

Seuls les **artefacts figés** (tables CSV, index XML, caches Vision/Quiver, référentiels YAML) sont
embarqués dans `data/`. Les **sources brutes** des deux pistes digitales sont absentes :

- **House digital** — les PDF *lisibles* (numériques) ont été parsés puis écartés ; il ne reste sous
  `data/house/pdfs/` que les **547 PDF scannés** (le backlog OCR, non lisibles). Re-jouer une année
  produirait donc une table digitale **vide** (0 doc lisible), jamais égale au golden.
- **Senate** — le scraping eFD exige le réseau (cf. en-tête de `test_senate_repro.py`).

On ne teste donc pas le bout-en-bout PDF→table ; on **reproduit chaque transformation depuis les
colonnes figées** et on la compare à la valeur stockée. C'est une preuve plus forte et déterministe :
elle isole le code refondu des aléas réseau/OCR.

## Index des tests

| Test | Prouve |
|------|--------|
| `check_golden.py` / `build_golden.py` | Toutes les sorties House reproduisent le golden (sha256) ; `build_golden.py` (re)gèle l'empreinte. |
| `test_schema.py` | `congress_core.schema.natural_key_hash` = drop-in exact des deux moteurs (équivalence unitaire + repro CSV). |
| `test_amounts_tickers.py` | `amount_midpoint` / `infer_asset_type` reproduisent les colonnes figées (06 digital + 06b OCR), sans PDF. |
| `test_identity.py` | Le matcher `congress_core.identity` == `house.digital.match_bioguide` original ; bioguides figés reproduits. |
| `test_tenure.py` | `years_in_office` recomputé depuis (bioguide, date) + référentiel embarqué == valeur figée des FINAL. |
| `test_crosscheck.py` | Smoke Quiver + crosscheck : les déposants papier ressortent `ocr_unique` (l'OCR est bien source unique). |
| `test_vision_sha.py` | `VisionExtractor.prompt_sha` == SHA original == `prompt_sha` des caches (déplacer l'OCR n'invalide pas le cache). |
| `test_incremental.py` | Mise à jour incrémentale : 2ᵉ run OCR = 0 appel Vision (cache versionné par `(prompt_sha, model)`). |
| `test_senate_repro.py` | Pipeline Sénat re-logé (`senate/` + `congress_core`) reproduit les colonnes des FINAL gelées. |

## Note : `smoke_digital.py` retiré (2026-06-26)

Cet ancien test re-générait une année digitale House dans `/tmp` et la comparait au golden. Deux
raisons de fond le rendaient caduc :

1. Il faisait `import house_multiyear`, module **supprimé** lors de la refonte (remplacé par
   `house/digital.py`) → `ModuleNotFoundError`, donc toujours rouge.
2. Même repointé sur `house.digital`, il **ne pouvait pas** reproduire le golden hors-ligne : les PDF
   digitaux lisibles sont absents (cf. *Principe* ci-dessus), donc le re-run sortirait une table vide.

Son intention — « le rebranchement sur `congress_core` ne change rien en bout de chaîne » — est
désormais couverte, en mieux, par les tests de **reproduction depuis colonnes figées**
(`test_schema`, `test_amounts_tickers`, `test_identity`, `test_tenure`) + le golden octet-à-octet,
qui valident chaque transformation sans dépendre des PDF sources.
