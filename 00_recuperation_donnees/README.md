# 00 · Récupération & nettoyage des données — le pipeline

Congrès américain, **2014-2026** : les déclarations de transactions des élus (PTR Chambre +
eFD Sénat, électronique et papier scanné) → **une table de recherche propre**, régénérable de
bout en bout, avec son rapport et son deck.

## Les deux documents

| document | c'est quoi |
|---|---|
| [`RAPPORT_DONNEES.md`](RAPPORT_DONNEES.md) (+ [`.pdf`](RAPPORT_DONNEES.pdf)) | **LE rapport — régénérable** : toutes les stats (corpus, couverture vs l'index officiel, dates, montants, concentration, validation Quiver §6, nettoyage §7, corroboration externe §8, papier Sénat §9, types de dépôts Sénat §10). Relancer le pipeline le régénère : **si la donnée change, chaque chiffre suit.** |
| [`SLIDES_DONNEES.pdf`](SLIDES_DONNEES.pdf) | le deck de présentation (certifié le 18/07 ; ses figures d'entonnoir portent l'état d'alors de la table — 134 464 × 36. La table courante et les chiffres vivants sont dans le rapport ; l'écart, −12 lignes de tickers faux-positifs corrigés depuis, y est documenté au §7). |

## Lancer

```bash
pip install -e ".[quality]"                    # depuis la racine du dépôt
python -m common.pipeline --years 2020-2026    # la chaîne complète : acquisition → FINAL → nettoyage → rapport
python -m common.report_pdf                    # le PDF du rapport (Chrome headless)
```

Les deux derniers steps seuls — 100 % hors-ligne, rejouables depuis un simple clone :

```bash
python -m common.backtest_clean                # step 7 : les 4 tables de data/clean/
python -m common.quality                       # step 8 : RAPPORT_DONNEES.md + figures
```

## La structure

```
common/   le cœur partagé : schema (clé naturelle, corrections read-time) · pipeline (les steps) ·
          backtest_clean (step 7 : brute → clean) · quality (step 8 : LE rapport) · crosscheck ·
          quiver_diagnosis · sector_enrich · enrich_tenure · report_pdf
house/    pipeline Chambre : acquire · digital · ocr · …          ← jumeau de senate/
senate/   pipeline Sénat   : digital · ocr · fusion · … · report_types_probe (collecteur eFD, opt-in)
data/     house/ · senate/ (tables FINAL figées) · reference/ (référentiels déclaratifs) ·
          external/ (collectes tierces — jamais réinjectées) · clean/ (les 4 tables de recherche)
png/      les images — figs_deck/ (le deck) · quality/ (le rapport) · figs_pop/ (partie II du deck)
          (le README de png/ = la carte qui-produit-quoi, qui-consomme-quoi)
tests/    golden 230 + 138 fichiers (SHA256) + tests de régression — tout doit dire « ZÉRO ÉCART »
```

## Les 4 tables livrées (`data/clean/`)

| table | contenu |
|---|---|
| `transactions_brut_2014_2026.csv` (169 000 × 41) | **la brute** : tout le corpus, verdict d'entonnoir écrit sur chaque ligne écartée — rien d'écarté en silence |
| `transactions_backtest_2014_2026.csv` (134 452 × 39) | **la clean** : la table de recherche canonique |
| `transactions_gated_2014_2026.csv` (7 287 × 13) | les manuscrites écartées par la politique OCR, avec leur motif |
| `commissions_membre_congres.csv` | annexe : commissions et sous-commissions par élu × Congrès |

Le détail de chaque étape du nettoyage, son code (`module :: fonction`) et ses référentiels :
**§7 du rapport**.

## Vérifier

```bash
python tests/regression/check_golden.py         # House : « ZÉRO ÉCART » attendu
python tests/regression/senate_check_golden.py  # Sénat : « ZÉRO ÉCART » attendu
python tests/regression/test_backtest_clean.py  # les 4 tables : « ZÉRO ÉCART » attendu
```
