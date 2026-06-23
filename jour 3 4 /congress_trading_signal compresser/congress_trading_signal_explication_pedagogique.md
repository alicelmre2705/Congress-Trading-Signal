# Congress Trading Signal — Explication pédagogique du livrable House J1–J4

## 1. Résumé exécutif

Le livrable actuel construit une première base de données officielle **House** pour le projet “Congress Trading Signal”.

Il ne construit pas encore une stratégie. Il ne fait pas encore de backtest. Il prépare la donnée.

La source canonique est la House : index XML officiels + PDF PTR. Quiver est utilisé seulement comme contrôle externe.

Le pipeline a reconstruit l’index House 2013–2026, identifié les PTR, téléchargé et audité les PDF de l’année testée, puis diagnostiqué l’accès Quiver.

| Point | Statut |
|---|---|
| Ce qui est validé | Index House 2013–2026, 8 248 PTR identifiés, 515 PDF 2025 téléchargés, audit qualité PDF, diagnostic Quiver V2. |
| Ce qui reste à faire | Télécharger tous les PDF 2013–2026, extraire les transactions, traiter les PDF `no_text`, améliorer la validation Quiver, puis seulement ensuite préparer la stratégie. |

---

## 2. Contexte du projet

Le projet “Congress Trading Signal” cherche à transformer les déclarations financières publiques des membres du Congrès américain en signal exploitable.

Un membre du Congrès peut acheter ou vendre des actifs financiers. Après une transaction, il doit déclarer publiquement certaines opérations dans un formulaire appelé **PTR**.

Un **PTR**, ou *Periodic Transaction Report*, contient les informations de base d’une transaction déclarée : actif, type d’opération, fourchette de montant, date de transaction et date de dépôt.

Ces déclarations peuvent être intéressantes car certains élus siègent dans des commissions sensibles : Finance, Defense, Intelligence. L’hypothèse du projet est que certaines transactions déclarées pourraient contenir un signal. À ce stade, ce n’est qu’une hypothèse de recherche. Le livrable actuel ne prouve pas encore qu’il existe un alpha.

Le point le plus important est la gestion des dates. Une transaction peut avoir lieu plusieurs jours ou semaines avant sa publication. Pour un futur backtest, il faudra donc utiliser la date de publication, pas la date réelle du trade.

House est traitée avant Senate parce que la source House est plus propre techniquement : index XML annuel, PDF accessibles par `DocID`, et fichiers souvent lisibles en texte. Senate est hors scope ici car la source est plus hétérogène et peut nécessiter OCR.

---

## 3. Scope exact du livrable actuel

### 3.1 Ce qui est dans le scope

Le livrable actuel couvre :

- House uniquement ;
- index House 2013–2026 ;
- PTR uniquement, donc `FilingType = P` ;
- construction des URL PDF House ;
- téléchargement des PDF pour l’année testée ;
- production d’un manifest ;
- audit qualité PDF ;
- smoke test regex léger ;
- diagnostic Quiver ;
- comparaison House vs Quiver au niveau déclarants/dates.

### 3.2 Ce qui est hors scope

| Hors scope | Pourquoi ce n’est pas traité maintenant |
|---|---|
| Senate | La source Senate est plus complexe : HTML + PDF scannés possibles. Elle doit être isolée plus tard. |
| OCR | Le livrable actuel teste d’abord les PDF House lisibles en texte. L’OCR n’est pas encore intégré. |
| Extraction LLM | On ne lance pas encore d’extraction massive transaction par transaction. |
| Transaction-level extraction | Le pipeline ne produit pas encore une ligne propre par transaction. |
| Backtest | Il serait prématuré sans table transactionnelle propre. |
| Stratégie | Les règles d’entrée/sortie ne sont pas encore implémentées. |
| Mapping ETF | Il faut d’abord extraire les tickers et les nettoyer. |
| Commissions | Les commissions ne sont pas dans les PTR et demandent une autre source. |
| Nettoyage tickers | Les tickers ne sont pas encore reconstruits de façon robuste. |

---

## 4. Structure du dossier livré

Arborescence principale :

```text
congress_trading_signal/
├── README.md
├── DELIVERABLES.md
├── .env.example
├── .gitignore
├── requirements.txt
├── notebooks/
├── src/
├── data/
├── docs/
└── reports/
```

### Fichiers racine

| Élément | Rôle |
|---|---|
| `README.md` | Explique le projet, le scope, l’installation, l’ordre d’exécution et les règles critiques. |
| `DELIVERABLES.md` | Liste les livrables créés : notebooks, modules, docs, configuration. |
| `.env.example` | Modèle de fichier d’environnement. Il contient seulement `QUIVER_API_TOKEN=`. |
| `.gitignore` | Empêche de versionner les secrets, les caches, les fichiers temporaires, les PDF bruts et les données externes lourdes. |
| `requirements.txt` | Liste les dépendances Python nécessaires. |

### Dossiers

| Dossier | Rôle | Versionné ou généré |
|---|---|---|
| `notebooks/` | Livrables principaux. Chaque notebook correspond à une étape du pipeline. | Versionné. |
| `src/` | Fonctions Python réutilisables. Elles gardent les notebooks courts. | Versionné. |
| `data/processed/house/` | Index House propres : filings, PTR, fichiers par année. | Présent dans le zip. |
| `data/audit/` | Manifest, audit qualité PDF, diagnostics Quiver, comparaisons. | Présent dans le zip. |
| `data/raw/` | PDF bruts House. | Ignoré par Git ; peut être absent du zip. |
| `data/external/` | Données Quiver téléchargées. | Ignoré par Git ; peut être absent du zip. |
| `docs/` | Documentation courte du projet. | Versionné. |
| `reports/` | Rapports Markdown produits par les notebooks. | Versionné. |

---

## 5. Vue d’ensemble du pipeline

```text
00_setup_scope
    ↓
01_house_index_audit
    ↓
02_house_pdf_download_manifest
    ↓
03_house_pdf_quality_smoke_test
    ↓
04_quiver_access_validation
```

### Rôle de chaque étape

| Étape | Rôle |
|---|---|
| `00_setup_scope` | Prépare l’environnement, crée les dossiers, vérifie la présence du token Quiver sans l’afficher. |
| `01_house_index_audit` | Télécharge les index XML House, parse tous les filings, filtre les PTR, construit la checklist des PDF attendus. |
| `02_house_pdf_download_manifest` | Télécharge les PDF PTR de l’année testée et produit un manifest de complétude. |
| `03_house_pdf_quality_smoke_test` | Vérifie si les PDF sont lisibles en texte et lance un test regex léger sur un échantillon. |
| `04_quiver_access_validation` | Teste Quiver, normalise les champs, compare House et Quiver au niveau déclarants/dates. |

### Pourquoi cet ordre est important

On ne télécharge pas les PDF avant d’avoir la checklist officielle des `DocID`.

On ne fait pas d’extraction transactionnelle avant d’avoir audité la qualité des PDF.

On ne compare pas à Quiver avant de savoir ce que la source officielle House contient.

Cet ordre évite de construire une pipeline sur une base non vérifiée.

---

## 6. Notebook 00 — Setup & scope

### Objectif

Le notebook `00_setup_scope.ipynb` prépare l’environnement du projet.

Il ne télécharge aucune donnée. Il ne valide pas encore la qualité de la data.

### Ce qu’il vérifie

Il vérifie :

- que les imports fonctionnent ;
- que le chemin racine du projet est bien détecté ;
- que les dossiers nécessaires existent ;
- que le token Quiver est présent ou absent, sans jamais l’afficher ;
- que le scope est bien rappelé.

### Sorties observées

Chemin racine observé :

```text
/Users/lemairealice/Downloads/Jupiter/congress_trading_signal
```

Dossiers créés ou vérifiés :

```text
data/raw/house/index
data/raw/house/ptr_pdfs
data/processed/house
data/external/quiver
data/audit
reports
src
```

Token Quiver :

```text
QUIVER_API_TOKEN present: True
```

Fichier produit :

```text
reports/setup_status.md
```

### Interprétation

Le setup est correct.

Le token Quiver était présent dans l’environnement local au moment de l’exécution. Il n’a pas été affiché. C’est le comportement attendu.

Ce notebook prépare le terrain. Il ne prouve encore rien sur les données House.

---

## 7. Notebook 01 — House index audit

### Objectif

Le notebook `01_house_index_audit.ipynb` reconstruit l’index officiel House.

Il part des ZIP annuels House, extrait les XML, parse les entrées, puis filtre les PTR.

### Source utilisée

Pour chaque année, la House publie un ZIP :

```text
https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{YEAR}FD.zip
```

Le ZIP contient normalement :

```text
{YEAR}FD.xml
```

Le XML contient des entrées avec notamment :

```text
Last
First
FilingType
FilingDate
DocID
StateDst
```

Les PTR sont les lignes où :

```text
FilingType = P
```

L’URL PDF est construite ainsi :

```text
https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{YEAR}/{DOCID}.pdf
```

### Résultats principaux

Sorties observées :

```text
df_all shape: (37445, 11)
df_ptr shape: (8248, 11)
```

Interprétation :

- `37 445` = nombre total de filings House parsés sur 2013–2026 ;
- `8 248` = nombre total de PTR House identifiés ;
- un PTR est un filing où `FilingType = P` ;
- ces chiffres ont été reconstruits par le pipeline, pas hardcodés.

### PTR par année

| Année | Nombre de PTR |
|---:|---:|
| 2013 | 8 |
| 2014 | 708 |
| 2015 | 728 |
| 2016 | 765 |
| 2017 | 801 |
| 2018 | 830 |
| 2019 | 683 |
| 2020 | 733 |
| 2021 | 680 |
| 2022 | 624 |
| 2023 | 460 |
| 2024 | 451 |
| 2025 | 515 |
| 2026 | 262 |

### Interprétation des années

2013 est très faible avec seulement 8 PTR.

2014–2025 forment une série beaucoup plus dense.

2026 est partielle dans ce run. Il ne faut donc pas la comparer mécaniquement aux années complètes.

2025 contient 515 PTR.

### Checks qualité observés

```text
missing_doc_id: 0
missing_filing_date: 699
duplicates_year_doc_id: 18
```

Interprétation :

- `missing_doc_id = 0` : très bon point. Chaque filing a un identifiant document.
- `missing_filing_date = 699` : concerne l’index complet. Dans les données chargées, les PTR ont `0` date manquante.
- `duplicates_year_doc_id = 18` : concerne l’index complet. Dans les données chargées, les PTR ont `0` doublon `year + doc_id`.

Le point important pour la suite est que la checklist PTR est propre : chaque PDF PTR attendu peut être identifié par `year + doc_id`.

### Fichiers produits

```text
data/processed/house/house_filings_index.csv
data/processed/house/house_ptr_index.csv
data/processed/house/ptr_index_2013.csv
...
data/processed/house/ptr_index_2026.csv
data/audit/house_index_download_logs.csv
reports/house_index_audit.md
```

### Ce que ce notebook valide

Il valide que l’index House 2013–2026 est reconstruit et que les PTR officiels sont identifiés.

Il valide aussi la checklist des PDF attendus au niveau `year + doc_id`.

### Ce qu’il ne valide pas encore

Il ne télécharge pas encore tous les PDF.

Il ne lit pas encore les transactions dans les PDF.

Il ne produit pas encore de table transactionnelle.

---

## 8. Notebook 02 — House PDF download & manifest

### Objectif

Le notebook `02_house_pdf_download_manifest.ipynb` télécharge les PDF PTR listés dans l’index PTR.

Il produit surtout un **manifest**.

### Ce qu’est un manifest

Un manifest est un fichier de contrôle.

Il dit, ligne par ligne, si chaque PDF attendu a été obtenu.

Il contient notamment :

- l’année ;
- le `DocID` ;
- le nom du déclarant ;
- l’URL PDF ;
- le chemin local ;
- le statut de téléchargement ;
- le code HTTP ;
- la taille du fichier ;
- le hash SHA256 ;
- le nombre de pages ;
- une erreur éventuelle.

Le manifest est plus important qu’un simple dossier de PDF, car il prouve la complétude.

### Paramètre important du run

Le notebook a été exécuté avec :

```text
TARGET_YEAR = 2025
```

Donc il n’a pas téléchargé les 8 248 PDF PTR de 2013–2026.

Il a téléchargé les PDF PTR de l’année 2025.

### Résultats observés

```text
expected_pdf_count: 515
manifest_rows: 515
downloaded_or_existing_count: 515
missing_count: 0
invalid_pdf_count: 0
zero_byte_count: 0
exception_count: 0
http_error_count: 0
success_rate: 1.0
status_counts: ok = 515
```

### Interprétation

Pour 2025, le téléchargement est complet.

Cela signifie :

- 515 PDF étaient attendus ;
- 515 PDF sont présents ;
- aucun PDF manquant ;
- aucun PDF vide ;
- aucun PDF invalide ;
- aucune erreur HTTP ;
- aucun crash bloquant.

Limite importante : ce résultat ne prouve pas encore que tous les PDF House 2013–2026 ont été téléchargés.

Il prouve seulement que l’année testée 2025 est complète dans ce run.

### Statistiques de pages

| Statistique | Valeur |
|---|---:|
| Nombre de PDF | 515 |
| Moyenne | 3,54 pages |
| Médiane | 2 pages |
| Minimum | 1 page |
| Maximum | 81 pages |

### PDF les plus longs observés

| Déclarant | DocID | Pages |
|---|---:|---:|
| Lisa McClain | 20030891 | 81 |
| Lisa McClain | 20033446 | 53 |
| Rohit Khanna | 8220906 | 51 |
| Jefferson Shreve | 20030387 | 41 |
| Rohit Khanna | 8220750 | 34 |

### Pourquoi les PDF longs sont importants

Un PDF long peut contenir beaucoup de transactions.

Il peut aussi être plus difficile à extraire proprement.

Ces PDF devront être surveillés dans l’extraction transactionnelle future.

### Fichiers produits

```text
data/audit/house_pdf_manifest.csv
reports/house_download_audit.md
```

Les PDF bruts sont produits localement sous :

```text
data/raw/house/ptr_pdfs/YYYY/DOCID.pdf
```

Mais `data/raw/` est ignoré par Git. Les PDF bruts peuvent donc être absents du zip livré.

---

## 9. Notebook 03 — House PDF quality & smoke test

### Objectif

Le notebook `03_house_pdf_quality_smoke_test.ipynb` vérifie si les PDF téléchargés sont techniquement exploitables.

Il ne fait pas d’extraction complète des transactions.

Il mesure :

- si le PDF existe ;
- si le texte est extractible ;
- si certains marqueurs simples sont détectés ;
- si des regex trouvent des tickers, dates ou montants sur un échantillon.

### Donnée en entrée

Il lit :

```text
data/audit/house_pdf_manifest.csv
```

Comme le manifest contient uniquement 2025 dans ce run, l’audit qualité porte sur les 515 PDF 2025.

### Résultat qualité PDF

```text
quality shape: (515, 12)
n_pdf_audited: 515
ok_text: 449
no_text: 66
weak_text: 0
unreadable_pdf: 0
ok_text_rate: 87.18%
no_text_rate: 12.82%
```

### Interprétation

Les 515 PDF existent et sont lisibles comme fichiers PDF.

Mais seulement 449 donnent du texte exploitable avec `pypdf`.

Les 66 fichiers `no_text` ne sont pas absents. Ils existent, mais l’extraction texte renvoie presque rien.

`unreadable_pdf = 0` signifie que les fichiers ne sont pas corrompus au sens PDF.

### Déclarants avec plusieurs PDF `no_text`

| Déclarant | Nombre de PDF `no_text` |
|---|---:|
| Michael T. McCaul | 12 |
| Rohit Khanna | 12 |
| Harold Dallas Rogers | 12 |
| Tony Wied | 8 |
| Charles J. "Chuck" Fleischmann | 4 |
| Vicente Gonzalez | 3 |
| Brad Sherman | 3 |
| Adrian Smith | 3 |
| Keith Alan Self | 2 |
| Nicole Malliotakis | 2 |
| Ann Wagner | 2 |
| Gus M. Bilirakis | 1 |
| Lisa McClain | 1 |
| Jamie Raskin | 1 |

### Marqueurs détectés

| Marqueur | Nombre `True` | Nombre `False` |
|---|---:|---:|
| `contains_periodic_transaction_report` | 344 | 171 |
| `contains_filer_information` | 0 | 515 |
| `contains_transactions` | 342 | 173 |
| `contains_amount` | 449 | 66 |
| `text_extractable_flag` | 449 | 66 |

### Interprétation des marqueurs

`contains_amount` suit exactement le nombre de PDF `ok_text`. C’est cohérent : quand du texte est extractible, les montants sont souvent visibles.

`contains_filer_information = 0` ne veut pas dire que la section n’existe pas dans les PDF.

Cela signifie plutôt que le test texte est trop strict ou que le texte extrait est dégradé.

Ce check devra être amélioré avant l’extraction finale.

### Smoke test regex

Le smoke test est un test léger sur un échantillon.

Il ne crée pas une table finale de transactions.

Il cherche seulement des motifs simples :

- tickers ;
- dates ;
- montants.

Résultats observés :

```text
sample shape: (47, 16)
smoke shape: (47, 9)
47 PDF testés
23 / 47 avec tickers détectés
24 / 47 avec dates détectées
34 / 47 avec montants détectés
```

Exemple observé dans l’échantillon :

```text
Rob Bresnahan
Tickers détectés : ALAB|BABA|HOOD|INTC|META|ORCL|RDDT
Date détectée : 03/10/2025
Montant détecté : $1,001 - $15,000
```

### Interprétation du smoke test

Le résultat est utile mais limité.

Il montre que certains PDF contiennent du texte assez propre pour détecter des motifs.

Il ne prouve pas que les transactions sont extraites correctement.

Les regex peuvent rater des tickers ou détecter du bruit.

Les PDF `no_text` restent problématiques.

### Fichiers produits

```text
data/audit/house_pdf_text_quality.csv
data/audit/house_sample_extraction_smoke_test.csv
reports/house_download_audit.md
```

---

## 10. Notebook 04 — Quiver access validation

### Objectif

Le notebook `04_quiver_access_validation_2024.ipynb` teste l’accès réel à Quiver et compare Quiver à House.

Quiver n’est pas la source canonique.

Quiver sert seulement à vérifier certains champs et à faire une validation externe exploratoire.

Aucune correction automatique de House ne doit venir de Quiver.

### Endpoint Quiver utilisé

```text
GET https://api.quiverquant.com/beta/bulk/congresstrading
```

Paramètres importants :

```text
version = V2 ou V1
normalized = true
nonstock = false
page
page_size
```

### Champs importants en V2

| Champ Quiver V2 | Sens dans notre pipeline |
|---|---|
| `Name` | Déclarant |
| `BioGuideID` | Identifiant utile pour la réconciliation future |
| `Chamber` | House ou Senate |
| `Ticker` | Ticker |
| `Transaction` | Achat ou vente |
| `Traded` | `transaction_date` côté Quiver |
| `Filed` | `disclosure_date` côté Quiver |
| `Trade_Size_USD` | Fourchette ou montant brut côté Quiver |

### Diagnostic observé

```text
QUIVER_API_TOKEN present: True
diagnostic status: ok
accessible version: V2
endpoint: /beta/bulk/congresstrading
status_code: 200
n_records test: 5
```

Colonnes V2 observées :

```text
BioGuideID
Chamber
Comments
Company
Description
District
Filed
Name
Party
Quiver_Upload_Time
State
Status
Subholding
Ticker
TickerType
Trade_Size_USD
Traded
Transaction
excess_return
last_modified
```

### Interprétation du diagnostic

Quiver V2 était accessible dans ce run.

Les champs nécessaires à une première validation externe sont présents.

Cela ne prouve pas que Quiver est complet.

Cela prouve seulement que l’endpoint répond, que V2 est accessible, et que les champs attendus sont disponibles sur l’échantillon testé.

### Fetch paginé observé

Paramètres :

```text
PAGE_SIZE = 500
MAX_PAGES = 45
```

Résultat :

```text
records fetched: 22500
quiver_df shape: (22500, 20)
```

Interprétation :

- 22 500 lignes ont été récupérées ;
- cela correspond à 45 pages de 500 lignes ;
- `MAX_PAGES` limite volontairement la récupération ;
- ce résultat ne garantit pas que tout l’historique Quiver a été téléchargé.

### Point critique : incohérence 2024 / 2025

Le notebook s’appelle :

```text
04_quiver_access_validation_2024.ipynb
```

Mais le paramètre réel observé dans le notebook est :

```text
YEAR = 2025
```

Donc les sorties Quiver produites dans ce run sont sur 2025, pas sur 2024.

Le README et certains noms de fichiers attendus mentionnent 2024. Ils doivent être alignés avec l’exécution réelle.

### Comparaison House vs Quiver 2025

Résultats observés :

| Métrique | Valeur |
|---|---:|
| `n_house_ptr_filings_2025` | 515 |
| `n_quiver_house_transactions_2025` | 12 527 |
| `n_unique_house_declarants_2025` | 108 |
| `n_unique_quiver_declarants_2025` | 84 |
| `overlap_declarants_count` | 80 |
| `house_only_declarants_count` | 28 |
| `quiver_only_declarants_count` | 4 |
| `house_disclosure_date_min` | 2025-01-01 |
| `house_disclosure_date_max` | 2026-01-16 |
| `quiver_disclosure_date_min` | 2025-01-06 |
| `quiver_disclosure_date_max` | 2025-12-29 |

### Interprétation de la comparaison

La comparaison est au niveau déclarants/dates.

Elle n’est pas transaction-level.

On ne peut donc pas dire que les transactions House et Quiver matchent ligne à ligne.

Ce que l’on peut dire :

- 80 déclarants sont communs entre House et Quiver avec la clé de nom simple ;
- 28 déclarants apparaissent côté House seulement avec cette clé ;
- 4 déclarants apparaissent côté Quiver seulement avec cette clé ;
- les écarts peuvent venir de différences de noms, pas forcément d’un vrai manque de couverture.

Exemples de divergences de noms observées :

```text
Rohit Khanna vs Ro Khanna
August Lee Pfluger vs August Lee Pfluger II
Thomas H. Kean vs Thomas H. Kean Jr
```

### Conclusion Quiver

Quiver est utile comme sanity-check.

Il ne remplace pas House.

La réconciliation des noms devra être améliorée avant de conclure sur la couverture réelle.

### Fichiers produits

```text
data/audit/quiver_api_access_diagnostic.json
data/audit/quiver_house_validation_2025.csv
reports/house_quiver_validation_report.md
```

Le fichier suivant a été produit localement si l’accès Quiver était disponible :

```text
data/external/quiver/quiver_congress_trading_2025.csv
```

Mais `data/external/` est ignoré par Git. Ce fichier peut donc être absent du zip livré.

---

## 11. Modules `src` — explication simple

Les notebooks sont les livrables principaux.

Les fichiers `src/` contiennent les fonctions réutilisables. Cela évite d’avoir des notebooks trop longs.

### `src/utils.py`

Ce fichier contient les fonctions communes :

- trouver la racine du projet ;
- créer les dossiers ;
- écrire du JSON ;
- écrire du Markdown ;
- convertir les dates ;
- normaliser simplement les noms ;
- vérifier la présence du token.

### `src/house_index.py`

Ce fichier gère l’index House :

- construire les URL ZIP ;
- construire les URL PDF ;
- télécharger les ZIP ;
- extraire les XML ;
- parser les filings ;
- filtrer `FilingType = P` ;
- sauvegarder les index ;
- produire un rapport d’audit.

### `src/house_download.py`

Ce fichier gère les PDF :

- télécharger un PDF ;
- utiliser un téléchargement atomique `.tmp` puis renommage ;
- calculer le SHA256 ;
- vérifier qu’un fichier est un PDF valide ;
- compter les pages ;
- produire le manifest ;
- résumer la complétude.

### `src/pdf_quality.py`

Ce fichier gère l’audit texte :

- extraire le texte des premières pages ;
- compter les caractères ;
- détecter des marqueurs simples ;
- classer les PDF en `ok_text`, `weak_text`, `no_text`, `unreadable_pdf`, `missing_file` ;
- construire un échantillon ;
- lancer un smoke test regex.

### `src/quiver_client.py`

Ce fichier gère Quiver :

- lire le token depuis l’environnement ;
- appeler l’API sans afficher le token ;
- diagnostiquer l’accès V2/V1 ;
- récupérer des pages ;
- normaliser les champs Quiver ;
- filtrer House et année ;
- comparer House et Quiver au niveau déclarants/dates ;
- écrire le rapport Quiver.

---

## 12. Les fichiers produits et leur rôle

| Fichier | Produit par | Rôle | Comment l’interpréter | Limites |
|---|---|---|---|---|
| `data/processed/house/house_filings_index.csv` | Notebook 01 | Tous les filings House parsés. | Base complète index House. | Ce n’est pas uniquement les PTR. |
| `data/processed/house/house_ptr_index.csv` | Notebook 01 | Tous les PTR House filtrés. | Checklist officielle des PDF PTR attendus. | Ce n’est pas une table de transactions. |
| `data/processed/house/ptr_index_YYYY.csv` | Notebook 01 | PTR d’une année donnée. | Sert à lancer un téléchargement année par année. | Un fichier par année, pas une extraction PDF. |
| `data/audit/house_index_download_logs.csv` | Notebook 01 | Logs de téléchargement/parsing des ZIP XML. | Permet de vérifier les années OK, codes HTTP et volumes. | Ne valide pas les PDF. |
| `data/audit/house_pdf_manifest.csv` | Notebook 02 | Manifest de complétude PDF. | Prouve les PDF attendus/obtenus pour l’année téléchargée. | Dans ce run : 2025 seulement. |
| `data/audit/house_pdf_text_quality.csv` | Notebook 03 | Audit qualité texte des PDF. | Dit quels PDF sont text-extractables. | Ne produit pas les transactions. |
| `data/audit/house_sample_extraction_smoke_test.csv` | Notebook 03 | Test regex sur échantillon. | Indique si tickers/dates/montants sont détectables. | Test approximatif, pas une extraction finale. |
| `data/audit/quiver_api_access_diagnostic.json` | Notebook 04 | Diagnostic d’accès Quiver. | Dit si V2/V1 répond et quelles colonnes sont présentes. | Ne prouve pas la couverture complète. |
| `data/audit/quiver_house_validation_2025.csv` | Notebook 04 | Comparaison House/Quiver 2025. | Mesure l’overlap déclarants/dates. | Pas de match transaction par transaction. |
| `reports/setup_status.md` | Notebook 00 | Rapport setup. | Confirme dossiers, scope, token présent/absent. | Ne valide pas la data. |
| `reports/house_index_audit.md` | Notebook 01 | Rapport index House. | Résume filings, PTR, anomalies, fichiers produits. | Ne valide pas les PDF. |
| `reports/house_download_audit.md` | Notebook 02/03 | Rapport téléchargement + qualité PDF. | Résume complétude 2025 et qualité texte. | Ne couvre pas tout 2013–2026 dans ce run. |
| `reports/house_quiver_validation_report.md` | Notebook 04 | Rapport Quiver. | Résume accès Quiver et comparaison 2025. | Le nom du notebook/README mentionne 2024, mais le run est 2025. |

Les PDF bruts dans `data/raw/` peuvent être absents du zip car ce dossier est ignoré par Git.

Les données Quiver dans `data/external/` peuvent aussi être absentes du zip car ce dossier est ignoré par Git.

---

## 13. Ce qui est validé

### 13.1 Validé solidement

- La structure projet est créée.
- Les notebooks sont organisés par étapes.
- L’index House 2013–2026 est reconstruit.
- 37 445 filings House sont parsés.
- 8 248 PTR House sont identifiés.
- Aucun `DocID` ne manque dans l’index chargé.
- Aucun `FilingDate` ne manque dans la table PTR chargée.
- Aucun doublon `year + doc_id` n’est présent dans la table PTR chargée.
- Les PDF 2025 sont téléchargés : 515/515.
- Le manifest 2025 est complet.
- Quiver V2 est accessible dans ce run.
- Le diagnostic Quiver est produit.

### 13.2 Validé partiellement

- La qualité texte des PDF 2025 est mesurée : 449/515 sont `ok_text`.
- Le smoke test regex a été lancé sur 47 PDF.
- La comparaison Quiver est faite au niveau déclarants/dates.
- 22 500 records Quiver ont été récupérés avec `MAX_PAGES = 45`.

### 13.3 Non validé encore

- Téléchargement complet 2013–2026 des 8 248 PDF.
- Extraction transaction par transaction.
- OCR.
- Senate.
- Nettoyage des tickers.
- Mapping GICS/ETF.
- Commissions.
- Backtest.
- Stratégie investissable.

---

## 14. Points d’attention critiques

| Point | Problème | Pourquoi c’est important | Action recommandée |
|---|---|---|---|
| 1 | Le téléchargement complet n’est pas encore fait. | Le manifest actuel couvre 2025, pas les 8 248 PTR. | Lancer le notebook 02 année par année ou avec `TARGET_YEAR = None` si le code est adapté. |
| 2 | Le notebook Quiver est nommé 2024 mais exécuté en 2025. | Cela crée une confusion dans les rapports et le README. | Renommer le notebook ou remettre `YEAR = 2024`. |
| 3 | Le README mentionne encore Quiver 2024. | Les sorties réelles sont 2025. | Aligner README, noms de fichiers et rapports. |
| 4 | Des chemins absolus locaux apparaissent dans les fichiers. | Ils ne seront pas valides sur une autre machine. | Stocker des chemins relatifs ou les recalculer. |
| 5 | 66 PDF sont `no_text`. | Ils existent mais ne sont pas exploitables avec `pypdf`. | Tester une autre méthode d’extraction ou prévoir un traitement ciblé plus tard. |
| 6 | Le smoke test n’est pas une extraction finale. | Il peut détecter du bruit ou rater des lignes. | Ne pas l’utiliser comme table transactionnelle. |
| 7 | Quiver ne doit pas corriger House. | House reste la source officielle. | Garder Quiver comme sanity-check uniquement. |
| 8 | Les divergences de noms peuvent créer de faux écarts. | `Rohit Khanna` et `Ro Khanna` peuvent désigner la même personne. | Améliorer la réconciliation avec `BioGuideID` si possible. |
| 9 | Les données actuelles ne permettent pas encore un backtest. | Il manque la table transactionnelle propre. | Finir extraction et validation avant toute stratégie. |
| 10 | La règle `disclosure_date` est non négociable. | Entrer à `transaction_date` créerait un look-ahead bias. | Toujours utiliser `FilingDate` XML House comme date publique côté House. |

---

## 15. Lecture pédagogique des résultats

### 8 248 PTR ne veut pas dire 8 248 transactions

Un PTR est un document.

Un même PDF peut contenir une transaction ou plusieurs transactions.

Donc 8 248 PTR signifie 8 248 documents PTR attendus, pas 8 248 lignes de trade.

### 515 PDF 2025 téléchargés ne veut pas dire tous les PDF House téléchargés

Le notebook 02 a été exécuté avec `TARGET_YEAR = 2025`.

Il a donc validé 2025 seulement.

La complétude 2013–2026 reste à faire.

### 449 `ok_text` ne veut pas dire 449 transactions extraites

`ok_text` signifie que le texte du PDF est extractible.

Cela ne signifie pas que les transactions sont propres, structurées ou validées.

### 66 `no_text` ne veut pas dire 66 fichiers absents

Les fichiers existent.

Mais l’extraction texte avec `pypdf` ne donne pas de texte utile.

Ces fichiers demanderont un traitement particulier.

### 12 527 transactions Quiver 2025 ne se comparent pas directement à 515 PTR House

Côté House, on compte des documents PTR.

Côté Quiver, on compte des transactions déjà structurées.

Comparer directement 12 527 à 515 serait une erreur.

### 80 déclarants en overlap ne veut pas dire que toutes les transactions matchent

L’overlap est calculé au niveau déclarant.

Il ne valide pas encore les tickers, montants, dates de transaction ou opérations ligne à ligne.

---

## 16. Ce qu’on doit faire ensuite

### Étape 1 — Aligner les paramètres et les noms

Corriger l’incohérence 2024/2025 :

- soit renommer le notebook Quiver en 2025 ;
- soit remettre `YEAR = 2024` ;
- aligner README, rapports et noms de fichiers.

### Étape 2 — Télécharger tous les PDF House 2013–2026

Objectif : produire un manifest complet pour les 8 248 PTR.

Action : lancer le téléchargement année par année ou adapter le notebook pour couvrir toutes les années.

Résultat attendu : nombre attendu vs nombre obtenu sur toute la période.

### Étape 3 — Améliorer l’audit PDF

Comprendre les 66 PDF `no_text` observés en 2025.

Tester une autre méthode d’extraction texte si nécessaire.

Ne pas activer l’OCR globalement trop tôt. Le faire seulement si le besoin est confirmé.

### Étape 4 — Préparer l’extraction transactionnelle

Construire un échantillon représentatif :

- PDF simples ;
- PDF longs ;
- PDF `no_text` ;
- PDF avec tickers ambigus ;
- PDF avec descriptions répétées.

Définir ensuite le schéma transactionnel.

Tester l’extraction sur petit échantillon avant toute extraction massive.

### Étape 5 — Renforcer la validation Quiver

Améliorer le matching des noms.

Utiliser `BioGuideID` quand c’est possible.

Ne faire une comparaison transaction-level qu’après extraction House.

Le backtest vient plus tard.

---

## 17. Glossaire minimal

| Terme | Définition |
|---|---|
| PTR | *Periodic Transaction Report*. Document dans lequel un membre du Congrès déclare une transaction financière. |
| `FilingType` | Code du type de filing dans l’index House. Les PTR sont `FilingType = P`. |
| `FilingDate` | Date de dépôt public dans l’index XML House. Elle sert de `disclosure_date` côté House. |
| `DocID` | Identifiant du document dans l’index House. Il permet de construire l’URL du PDF. |
| `transaction_date` | Date réelle de la transaction. Elle n’est pas publique au moment du trade. |
| `disclosure_date` | Date à laquelle la transaction devient publique. C’est la date utilisable dans une stratégie future. |
| `Notification Date` | Colonne présente dans certains PDF House. Elle ne doit pas être utilisée comme `disclosure_date` stratégique. |
| Manifest | Fichier d’audit qui liste les fichiers attendus, obtenus, manquants, invalides et leurs métadonnées. |
| Text-extractable | Se dit d’un PDF dont le texte peut être extrait automatiquement. |
| Smoke test | Test rapide pour vérifier une faisabilité technique, sans prétendre produire un résultat final. |
| Quiver | Agrégateur externe de données financières et politiques. Ici, il sert seulement de validation externe. |
| Source canonique | Source considérée comme vérité principale. Ici : House XML + PDF. |
| Validation externe | Contrôle par une source tierce. Ici : Quiver. |
| Look-ahead bias | Erreur de backtest qui consiste à utiliser une information qui n’était pas disponible à la date simulée. |
| House | Chambre des représentants américaine. Source officielle prioritaire dans ce livrable. |
| Senate | Sénat américain. Hors scope dans cette phase. |

---

## 18. Conclusion finale

Le livrable actuel a réussi à reconstruire l’index House officiel 2013–2026 et à produire une première chaîne robuste sur l’année testée 2025 : téléchargement PDF, manifest, qualité texte, smoke test et diagnostic Quiver.

La base est bonne pour continuer.

Mais elle ne constitue pas encore une base transactionnelle finale.

Elle ne permet pas encore un backtest.

La priorité suivante est d’étendre le téléchargement à toutes les années House, de traiter les problèmes de qualité texte, puis de construire l’extraction transactionnelle sur un petit échantillon validé avant tout passage à l’échelle.
