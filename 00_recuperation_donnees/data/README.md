# `data/` — la couche données, dossier par dossier

Sept dossiers. Les trois premiers portent le produit ; les quatre autres, les référentiels et
les preuves.

| dossier | c'est quoi | régénérable ? |
|---|---|---|
| **`clean/`** (112 Mo) | **LE PRODUIT** : les 4 tables de recherche (brute · clean · gated · commissions) — [son README](clean/README.md) | oui — `python -m common.backtest_clean`, verrouillé par `tests/regression/test_backtest_clean.py` |
| **`house/`** (899 Mo) | la Chambre : source primaire (`pdfs/`, `index/`) + tables du pipeline (`tables/`) + caches Vision/LLM | tables : oui (depuis les PDF) · source primaire : figée |
| **`senate/`** (533 Mo) | le Sénat : source primaire (`reports/`) + tables (`tables/`) + caches Vision + mesures eFD datées (`_*.csv`) | idem |
| **`reference/`** (3 Mo) | les référentiels déclaratifs du nettoyage (tickers, secteurs, commissions) — [son README](reference/README.md) | non — se corrigent à la main, jamais en aveugle |
| **`external/`** (14 Mo) | les collectes tierces de corroboration (§8 du rapport) — **jamais réinjectées** — [son README](external/README.md) | non — instantanés téléchargés, datés |
| **`quiver_validation/`** (3 Mo) | les 13 CSV de preuve de la validation Quiver (§6) — [son README](quiver_validation/README.md) | oui — réécrits à chaque `python -m common.quality` |
| `filing_types/` | pièces de l'analyse des types de dépôt (branche `presentation` seulement) | — |

## La source primaire — embarquée en entier, pour les deux chambres

Deux noms pour la même chose (un par chambre) :

- **`house/pdfs/{2014..2026}/`** — **8 252 PDF = un par PTR officiel de l'index du Clerk**
  (708 · 728 · 765 · 801 · 830 · 683 · 733 · 680 · 624 · 460 · 451 · 515 · 274 — exactement la
  colonne « PTR officiels » du §1 du rapport). S'y ajoutent 13 `00_download_log.csv` (le journal
  d'acquisition) — d'où 8 265 entrées si on compte tout. `house/index/` = les 13 `{Y}FD.xml`
  instantanés du Clerk (le site purge les années anciennes : irremplaçables).
- **`senate/reports/`** — **2 150 pages HTML eFD couvrant 2 128 / 2 128 dépôts des tables FINAL**
  (les 22 de plus = dépôts sans transaction retenue, motivés dans `06d_docs_sans_transaction.csv`)
  + **`media/` : 1 638 scans `.gif`** du papier.

Chaque ligne des tables est donc **re-vérifiable contre son document source, sans rien
télécharger** ; la collecte se rejoue hors réseau (sauf dépôts nouveaux et validation Quiver).

## `{house,senate}/tables/` — les sorties du pipeline, figées au golden

```
tables/{2014..2026}/   une table par étape et par année (préfixes ci-dessous)
tables/00_*.csv        tableaux de bord (statut global)
tables/_*.csv          caches Quiver figés · census des scans · échantillons de validation
```

⚠️ **Tout `tables/` est verrouillé à l'octet** par le filet golden
(`tests/regression/{,senate_}golden_manifest.json` — 230 fichiers House, 138 Sénat ; le 139ᵉ CSV
Sénat, `_scan_census_senat.csv`, est volontairement hors manifest, ajouté après le gel). C'est
pourquoi certaines cellules d'époque y survivent telles quelles (ex. `00_year_status.csv` cite
encore « RAPPORT_QUALITE §6 », l'ancien nom du rapport) : **on ne réécrit jamais un fichier
gelé pour un libellé.**

### Le décodeur des préfixes

Le **préfixe** dit le **rôle** du fichier (pas l'ordre strict d'exécution) :

| Préfixe | Rôle | House | Sénat |
|---|---|---|---|
| `00_year_status` | tableau de bord annuel | ✓ | ✓ |
| `00_final_status` | tableau de bord de la fusion | — | ✓ |
| `00_backlog_ocr` | file d'attente OCR | ✓ | — |
| `03_ptr_index` | index des dépôts retenus (`FilingType=P`) | ✓ | — |
| `04_download_manifest` | verdict lisible / scanné / absent | ✓ | — |
| `05_parse_failures` | dépôts lisibles dont l'extraction a échoué | ✓ | ✓ |
| `06_…_transactions` | table **digitale** | ✓ | ✓ |
| `06_…_FINAL` | digital + OCR **fusionnés** — la table livrable | ✓ | ✓ |
| `06b_…_ocr_transactions` | table **OCR** (scans / papier) | ✓ | ✓ |
| `06c_ocr_failures` | échecs OCR — **vides partout = aucun échec** (le fichier Sénat est même à 0 octet, c'est normal) | ✓ | ✓ |
| `06d_ocr_quiver_comparison` | OCR confronté à Quiver | ✓ | — |
| `06d_docs_sans_transaction` | ⚠️ **autre sens au Sénat** : les 25 dépôts sans transaction, chacun motivé | — | ✓ |
| `07_quiver_comparison` | comparaison Quiver par déposant | ✓ | ✓ |
| `07b_quiver_missing_trades` | trades Quiver non retrouvés (clé brute, plancher) | ✓ | — |
| `07c_quiver_txn_reconciliation` | réconciliation fine, 3 scopes (`digital`/`ocr`/`both`, cf. `common/quiver_scopes.py`) | ✓ | ✓ |
| `07d_quiver_field_agreement` | accord champ par champ | ✓ | ✓ |
| `07e_quiver_ticker_per_member` / `…_per_senator` | tickers par déposant (⚠️ suffixe différent selon la chambre) | ✓ | ✓ |
| `07f_quiver_only_quiver_txn` | lignes vues par Quiver seul | ✓ | ✓ |
| `07g_quiver_match_by_asset` | décomposition par type d'actif | ✓ | ✓ |
| `07h_quiver_match_by_cluster` | décomposition par cluster de scan A/B/C | ✓ | — |
| `08_crosscheck_semaine1` | recoupement vs la baseline historique | ✓ | — |

### Les paires ancien / courant (gelées exprès)

- `_scan_census_547.csv` (547 scans, l'état 2020-2026 d'origine) **vs** `_scan_census.csv`
  (2 424, l'inventaire 2014-2026 courant) — l'ancien reste lu par `house/classify_scans.py` ;
- `_paper_index_2020_2026.csv` (130) **vs** `_paper_index_2014_2026.csv` (373, courant) ;
- `_scan_census_senat.csv` et `_paper_index_2014_2026.csv` couvrent la **même population**
  (les 373 PTR papier) sous deux angles : catégorie d'écriture vs index par UUID.

## Les 5 `senate/_*.csv` à la racine — des mesures eFD datées

`_report_types_2014_2026.csv` · `_filer_types_2014_2026.csv` · `_report_types_meta.csv`
(la date de mesure) · `_ptr_census.csv` · `_parser_probe.csv` : des **instantanés du portail
eFD**, pris hors pipeline par les collecteurs `senate/report_types_probe.py` et
`senate/census_probe.py` (réseau, à la demande). Ils alimentent le §10 du rapport ; le portail
ne se rejoue pas hors-ligne, donc la mesure est stockée avec sa date.

## Asymétries House / Sénat — justifiées

- **`04_` (House seul)** : la Chambre doit ouvrir chaque PDF pour décider lisible/scanné →
  un manifeste. Le Sénat reçoit le type directement de la liste eFD.
- **Scope `ocr` de la validation Quiver** : House — Quiver **voit** le papier (Khanna) → OCR
  validé en externe ; Sénat — Quiver est **aveugle** au papier (0 apparié sur 13 ans, §9 du
  rapport) → l'OCR Sénat est source unique, validé en interne.
- **`house/reference/` et `senate/reference/`** portent les **mêmes 4 YAML congress-legislators
  (copies volontaires, octet-identiques)** : chaque pipeline reste autonome.
