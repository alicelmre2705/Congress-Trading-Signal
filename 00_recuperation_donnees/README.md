# 00 · Récupération & nettoyage des données — le pipeline

Les déclarations de transactions des élus du Congrès américain (PTR Chambre + eFD Sénat,
électronique et papier scanné), **2014-2026**. Le fil en une ligne :

> **169 000 transactions uniques** collectées et validées → entonnoir de nettoyage →
> **134 452 exploitables** (la table de recherche). La coupe vers ~113 600 qu'on voit côté
> recherche n'est **pas** du nettoyage : c'est un choix d'étude (actions seules, prix
> exploitable), fait dans `../02_recherche_backtest/`.

## Les deux documents

| document | c'est quoi |
|---|---|
| [`RAPPORT_DONNEES.md`](RAPPORT_DONNEES.md) (+ [`.pdf`](RAPPORT_DONNEES.pdf)) | **LE rapport — régénérable** : toutes les stats (corpus, couverture officielle, dates, montants, concentration, validation Quiver §6, nettoyage §7, corroboration externe §8, papier Sénat §9, types de dépôts Sénat §10). Relancer le pipeline le régénère : **si la donnée change, chaque chiffre suit.** |
| [`SLIDES_DONNEES.pdf`](SLIDES_DONNEES.pdf) | le deck de présentation, certifié le 18/07. |

*Le deck est un cliché daté : ses figures d'entonnoir portent l'état d'alors de la table
(134 464 × 36) ; l'écart avec la table courante (−12 tickers faux-positifs corrigés depuis) est
documenté au §7 du rapport.*

## Les 4 tables livrées (`data/clean/`)

| table | contenu |
|---|---|
| `transactions_brut_2014_2026.csv` (169 000 × 41) | **la brute** : tout le corpus, verdict d'entonnoir écrit sur chaque ligne écartée — rien d'écarté en silence |
| `transactions_backtest_2014_2026.csv` (134 452 × 39) | **la clean** : la table de recherche canonique |
| `transactions_gated_2014_2026.csv` (7 287 × 13) | les scans manuscrits écartés par la politique OCR, avec leur motif |
| `commissions_membre_congres.csv` | annexe : commissions et sous-commissions par élu × Congrès |

**Une ligne = une transaction déclarée** : qui (`member_name`, `bioguide_id`, chambre) · quoi
(`ticker` fidèle à la déclaration + `ticker_yahoo` prêt pour le join prix, classe d'actif,
secteur GICS) · quand (`transaction_date` **et** `disclosure_date`) · sens (`direction`) ·
combien (`amount_midpoint`, milieu de la fourchette STOCK Act) · contexte à la date du trade
(parti, Congrès, commissions clés) · flags (dépôt tardif, délisté, prudence prix, lots
multi-comptes) · traçabilité (`doc_id`, clé naturelle). Le détail de chaque étape du nettoyage,
son code (`module :: fonction`) et ses référentiels : **§7 du rapport**.

## Comment la donnée est validée — quatre étages de preuve

| étage | contre quoi | résultat | où c'est prouvé |
|---|---|---|---|
| 1 · **L'univers officiel** | l'index annuel du House Clerk (`{Y}FD.xml`, versionnés dans `data/house/index/`) | **100 % des 8 252 PTR officiels 2014-2026 traités** — parsés, OCRisés, ou écartés par une règle écrite | rapport **§1** · `common/quality.py :: official_coverage` |
| 2 · **Quiver Quantitative** | la vérité-terrain commerciale — **jamais réinjectée** dans nos tables | **93,5 % (House) / 92,1 % (Sénat)** des combinaisons Quiver (déposant, ticker, sens) retrouvées dans la fenêtre commune ; le solde net est **en notre faveur** (on a plus de trades cotés que Quiver) ; chaque désaccord de date ou de champ est typé un à un | rapport **§6** (6.1 → 6.6) · `common/quiver_diagnosis.py` · les preuves ligne à ligne : `data/quiver_validation/` (13 CSV, régénérés avec le rapport) |
| 3 · **Deux collectes tierces indépendantes** | *senate-stock-watcher* et *house-stock-watcher*, qui re-lisent les mêmes sources officielles (JSON versionnés dans `data/external/`) | **99,7 % / 99,6 %** de nos lignes d'actions retrouvées **à la transaction près** (déposant · ticker · sens · date) | rapport **§8** · `common/crosscheck.py` |
| 4 · **Le filet interne** | le dépôt lui-même, rejoué hors-ligne depuis un clone | golden **230 + 138 fichiers** verrouillés par SHA256 ; les 4 tables de `data/clean/` reconstruites à l'identique | les trois commandes ci-dessous — chacune doit dire « **ZÉRO ÉCART** » |

```bash
python tests/regression/check_golden.py         # House
python tests/regression/senate_check_golden.py  # Sénat
python tests/regression/test_backtest_clean.py  # les 4 tables
```

*Le principe : une source qui sert à construire ne peut pas servir à vérifier — Quiver et les
collectes tierces ne font que mesurer.*

## Lancer

```bash
pip install -e ".[quality]"                    # depuis la racine du dépôt
python -m common.pipeline --years 2020-2026    # la chaîne complète : acquisition → FINAL → nettoyage → rapport
python -m common.report_pdf                    # le PDF du rapport (Chrome headless)
```

**`--years` ne borne que la collecte** (les années à re-traiter) : le nettoyage et le rapport
relisent toujours les 26 tables FINAL 2014-2026 en entier.

- **La source primaire House est embarquée en entier, sans différence entre les années** : les
  13 index `{Y}FD.xml` **et les PDF bruts des PTR 2014-2026** vivent dans `data/house/` — la
  collecte House se rejoue sans rien télécharger. `--acquire` ne sert qu'à compléter une année
  nouvelle (idempotent : ne re-télécharge jamais un fichier présent).
- **La source primaire Sénat est embarquée aussi** : `data/senate/reports/` — un HTML par dépôt
  des tables FINAL (2 128 / 2 128, vérifié) + les scans `.gif` du papier (`media/`). La collecte
  se rejoue depuis ces pages ; le réseau ne sert qu'aux dépôts nouveaux et à la validation
  Quiver (désactivable par `--no-quiver`). Clés dans le `.env` à la racine :
  `ANTHROPIC_API_KEY` (OCR Vision + repli LLM ticker/secteur), `QUIVER_API_KEY`.
- **Le nettoyage et le rapport (steps 7-8) sont 100 % hors-ligne**, rejouables depuis un simple
  clone : `python -m common.backtest_clean` puis `python -m common.quality`.

## La structure

```
common/   le cœur partagé : schema (clé naturelle, corrections read-time) · pipeline (les steps) ·
          backtest_clean (step 7 : brute → clean) · quality (step 8 : LE rapport) · crosscheck ·
          quiver_diagnosis · sector_enrich · enrich_tenure · report_pdf
house/    pipeline Chambre : acquire · digital · ocr · …          ← jumeau de senate/
senate/   pipeline Sénat   : digital · ocr · fusion · … · report_types_probe (collecteur eFD, à la demande)
data/     house/ (tables FINAL figées · index/ les 13 {Y}FD.xml · pdfs/ TOUS les PTR bruts
          2014-2026) · senate/ (tables FINAL figées · reports/ TOUTES les pages eFD brutes,
          HTML + scans .gif) · reference/ (référentiels déclaratifs) ·
          external/ (collectes tierces — jamais réinjectées) · quiver_validation/ (les preuves
          ligne à ligne de la validation Quiver, 13 CSV) · clean/ (les 4 tables de recherche)
png/      les images — figs_deck/ (le deck) · quality/ (le rapport) · figs_pop/ (partie II du deck)
          (le README de png/ = la carte qui-produit-quoi, qui-consomme-quoi)
tests/    golden 230 + 138 fichiers (SHA256) + tests de régression
```

## À savoir avant d'utiliser la table

- **Anti-look-ahead** : on n'entre jamais sur `transaction_date` — l'information n'est publique
  qu'à `disclosure_date` (délai médian **27 j**). Tout usage aval doit entrer à la divulgation.
- **Les manuscrits gated existent** : 7 287 transactions écartées par la politique OCR sont
  livrées à part (`transactions_gated_*`), avec leur motif — rien n'a disparu en silence.
- **Les titres délistés sont gardés** (et flagués) : les retirer serait un biais de survie caché.
  C'est au join prix, côté recherche, que ce biais apparaît — et il y est documenté.

La recherche qui consomme cette table : [`../02_recherche_backtest/`](../02_recherche_backtest/README.md).
