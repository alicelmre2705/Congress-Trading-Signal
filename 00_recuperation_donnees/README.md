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

**NB : `--years` ne borne que la collecte** (scraping + OCR — les années à rafraîchir) ; le
nettoyage et le rapport relisent **toujours les 26 tables FINAL 2014-2026 en entier** — la
commande ci-dessus produit donc bien la table clean et le rapport complets. Les années 2014-2019
se re-collectent avec `--acquire` (leurs index et PDF bruts ne sont pas embarqués ici, et déjà
figées en FINAL elles sont verrouillées par le filet golden).

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
          external/ (collectes tierces — jamais réinjectées) · quiver_validation/ (les preuves
          ligne à ligne de la validation Quiver, 13 CSV) · clean/ (les 4 tables de recherche)
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

## Comment la donnée est validée — quatre étages de preuve

| étage | contre quoi | résultat | où c'est prouvé |
|---|---|---|---|
| 1 · **L'univers officiel** | l'index annuel du House Clerk (`{Y}FD.xml`, versionnés dans `data/house/index/`) | **100 % des 8 252 PTR officiels 2014-2026 traités** — parsés, OCRisés, ou écartés par une règle écrite | rapport **§1** · `common/quality.py :: official_coverage` |
| 2 · **Quiver Quantitative** | la vérité-terrain commerciale — **jamais réinjectée** dans nos tables | **93,5 % (House) / 92,1 % (Sénat)** des combinaisons Quiver (déposant, ticker, sens) retrouvées dans la fenêtre commune ; le solde net est **en notre faveur** (on a plus de trades cotés que Quiver) ; chaque désaccord de date ou de champ est typé un à un | rapport **§6** (6.1 → 6.6) · `common/quiver_diagnosis.py` · les preuves ligne à ligne : `data/quiver_validation/` (13 CSV, régénérés avec le rapport) |
| 3 · **Deux collectes tierces indépendantes** | *senate-stock-watcher* et *house-stock-watcher*, qui re-lisent les mêmes sources officielles (JSON versionnés dans `data/external/`) | **99,7 % / 99,6 %** de nos lignes d'actions retrouvées **à la transaction près** (déposant · ticker · sens · date) | rapport **§8** · `common/crosscheck.py` |
| 4 · **Le filet interne** | le dépôt lui-même, rejoué hors-ligne depuis un clone | golden **230 + 138 fichiers** verrouillés par SHA256, « ZÉRO ÉCART » ; les 4 tables de `data/clean/` reconstruites à l'identique | `tests/regression/` (les trois commandes ci-dessous) |

Pourquoi Quiver et les collectes tierces ne sont **jamais réinjectés** : une source qui servirait
à la fois à construire et à vérifier ne prouverait rien. Elles ne servent qu'à **mesurer** —
et les mesures sont recalculées à chaque régénération du rapport.

## Vérifier

```bash
python tests/regression/check_golden.py         # House : « ZÉRO ÉCART » attendu
python tests/regression/senate_check_golden.py  # Sénat : « ZÉRO ÉCART » attendu
python tests/regression/test_backtest_clean.py  # les 4 tables : « ZÉRO ÉCART » attendu
```
