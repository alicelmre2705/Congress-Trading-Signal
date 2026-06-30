# Rapport — Notebook `02_construction_table_2014_2026.ipynb`

> **Ce que fait ce notebook, étape par étape (dans l'ordre des cellules).**
> Objectif : produire `table_congres_2014_2026.csv`, la table de transactions du Congrès US qui alimente le backtest.

---

## 0. Résumé exécutif

Le notebook construit une table **HYBRIDE** de **138 557 transactions** (2014-2026), assemblée à partir de **deux sources** :

| Période | Source | Transactions | Pourquoi cette source |
|---|---|---|---|
| **2020-2026** | **Le golden** (ton travail « partie 1 » : sources officielles + OCR papier + non-coté) | **90 487** | Plus complet que Quiver (Quiver n'a que ~65 k sur cette période : il rate le non-coté et une partie du papier) |
| **2014-2019** | **Quiver** (reconstruit en direct depuis l'API + enrichi) | **48 070** | Seule source disponible avant 2020 |
| **Total** | | **138 557** | |

À cela s'ajoute un **enrichissement cohérent sur toute la période** : identité (parti/État/district/ancienneté) et **commissions** en **point-in-time** (= valeur de l'époque du trade, pas d'aujourd'hui), secteur **GICS** + **ETF proxy**.

**En une phrase :** on *fetch + enrichit Quiver pour 2014-2019*, on *réutilise ton golden pour 2020-2026* (en lui recalculant les commissions point-in-time), et on *soude les deux* en une table propre.

---

## 1. Vue d'ensemble (le pipeline)

Le notebook suit **6 parties** dans l'ordre :

```
Partie 0  Imports / chemins autonomes / clés .env / silence yfinance
   │
Partie 1  JOURNAL  ── API Quiver (bulk) ──► normalisation ──► `journal` + `ASOF`
   │
Partie 2  IDENTITÉ point-in-time ── legislators terms[] ──► party/state/district/ancienneté
   │
Partie 3  COMMISSIONS point-in-time ── historique git ──► committee_membership / key_flag
   │
Partie 4  SECTEUR ── yfinance + repli LLM ──► sector_gics / etf_proxy
   │
Partie 5  ASSEMBLAGE  ── table Quiver (réf.) + golden 2020-26 ──► HYBRIDE ──► table_congres_2014_2026.csv
   │
Partie 6  VÉRIFICATIONS (composition, couvertures, concordance vs golden)
```

**Deux caches** (à ne pas confondre) :
- **`build_cache/`** = les caches *de ce notebook* (Quiver brut, référentiels, snapshots de commissions, ticker→secteur). Régénérables, gitignorés. Ils rendent les re-runs instantanés.
- **`cache/`** = le cache *du notebook de recherche* (prix yfinance + facteurs Fama-French). Rien à voir avec ce notebook-ci.

---

## 2. Partie 0 — Imports, chemins, clés

**But :** préparer l'environnement et permettre au notebook de tourner « tout seul ».

1. **Silence yfinance.** Une ligne neutralise le logger :
   ```python
   for _noisy in ('yfinance', 'urllib3'):
       logging.getLogger(_noisy).setLevel(logging.CRITICAL)
   ```
   *Pourquoi :* yfinance crie `HTTP Error 404` dès qu'un ticker est délisté. Ce sont des cas **attendus** (ils basculent ensuite sur le LLM), pas des erreurs — on ne veut pas en inonder la sortie.

2. **Localisation autonome** via `_find_paths()` : le notebook cherche lui-même le dossier `00. S3S4 en cours/` et la racine du dépôt, pour savoir **où écrire** (`OUT`) et où mettre ses caches (`CACHE = build_cache/`).

3. **Clés API** : lecture du `.env` → `QUIVER_API_KEY`, `ANTHROPIC_API_KEY`. Ouverture d'une session HTTP avec un `User-Agent` (sans lui, l'API Quiver **ferme la connexion**).

**Sortie de la partie :** `REPO`, `S3`, `OUT`, `CACHE`, `QUIVER_KEY`, `HAS_LLM`, session `S`.

---

## 3. Partie 1 — Le journal des transactions (Quiver, en direct)

**But :** récupérer toutes les transactions et les mettre dans un format propre.

### 3.1 Récupération (`fetch_quiver_live`)
Appel de l'API **bulk** de Quiver :
```python
QUIVER_URL = 'https://api.quiverquant.com/beta/bulk/congresstrading'
r = S.get(QUIVER_URL, headers={'Authorization': f'Bearer {QUIVER_KEY}'}, timeout=180)
```
- Renvoie **~113 682 lignes** (Chambre **et** Sénat, 2012-2026). On ne peut pas filtrer côté API : le bulk renvoie tout.
- Le résultat brut est mis en cache : `build_cache/quiver_raw.csv` → les re-runs ne re-téléchargent pas.

### 3.2 Normalisation (`normalize_quiver`)
On transforme le brut Quiver en colonnes propres :

| Colonne produite | Construction |
|---|---|
| `chamber` | `Representatives → house`, `Senate → senate` |
| `bioguide`, `name`, `party_quiver` | recopiés de Quiver |
| `ticker` | **normalisé** : `[A-Z]{1,5}` gardé, `BRK.B → BRK-B`, sinon `None` (non-coté) |
| `op` | `Purchase → buy`, `Sale → sell`, `Exchange → exch`, sinon `other` |
| `traded`, `filed` | dates (transaction / dépôt) |
| `size_usd` | `Trade_Size_USD` = **borne basse** de la fourchette (≥ 1001) |

Filtres : on ne garde que les lignes avec `traded` **et** `filed` valides, et **`filed.year ∈ [2014, 2026]`**.

### 3.3 La date de référence (`ASOF`)
```python
ASOF = journal['traded'].fillna(journal['filed'])
```
`ASOF` = la date du trade (à défaut, la date de dépôt). C'est **la** date utilisée partout ensuite pour le « point-in-time ».

**Sortie de la partie :** `journal` (~113 682 lignes, colonnes journal) + `ASOF`.

---

## 4. Partie 2 — Identité point-in-time (parti / État / district / ancienneté)

**But :** attacher à chaque transaction les infos du membre **telles qu'elles étaient à la date du trade**.

1. **`build_term_index()`** télécharge `legislators-current.json` + `legislators-historical.json`. Chaque élu a une liste de **mandats** (`terms`), chacun avec `start`, `end`, `party`, `state`, `district`, `type`.

2. **`term_at(bioguide, date)`** retrouve le **mandat actif à la date du trade** :
   ```python
   for st, en, party, state, dist, ch in terms:
       if st <= date <= en:
           return (party, state, dist, ch)
   ```
   On en tire `party`, `state`, `district`. Et :
   ```python
   years_in_office = trade_year - first_year(bioguide)   # ancienneté à la date du trade
   ```

**Pourquoi point-in-time :** si quelqu'un a changé de parti, on prend **le parti de l'époque**, pas l'actuel. (Le parti « courant » de Quiver est gardé à part dans `party_quiver` pour audit.)

**Sortie de la partie :** colonnes `party`, `state`, `district`, `years_in_office` (résolues à ~100 %).

---

## 5. Partie 3 — Commissions point-in-time (le détail malin)

**But :** donner à chaque transaction **la composition des commissions du Congrès de son époque**.

### 5.1 Le problème
Le référentiel officiel `committee-membership-current.yaml` ne contient que les commissions **du Congrès actuel**. Rétro-appliquer la photo actuelle à 2014 serait **faux** (les membres changent à chaque Congrès).

### 5.2 L'astuce : l'historique git
Le fichier `committee-membership-current.yaml` est **réécrit à chaque nouveau Congrès** → son **historique git EST une série de photos dans le temps**. On récupère donc, pour chaque Congrès, le fichier tel qu'il était à l'époque :
```python
# pour chaque Congrès 113→119, on prend un commit du milieu de mandat
SNAP_DATE = {113:'2014-06-01', 114:'2016-06-01', 115:'2018-06-01',
             116:'2020-06-01', 117:'2022-06-01', 118:'2024-06-01', 119:'2026-06-01'}
sha = _commit_before('committee-membership-current.yaml', until=SNAP_DATE[congress])
mem = yaml(raw.githubusercontent.com/<sha>/committee-membership-current.yaml)
com = yaml(raw.githubusercontent.com/<sha>/committees-current.yaml)   # même SHA, pour les noms
```
On construit alors, par Congrès, un dictionnaire `bioguide → liste de commissions`. (Mis en cache dans `build_cache/committees/{congress}/`.)

### 5.3 L'affectation
```python
def congress_of(year):  # 2014→113, 2015/16→114, …, 2025/26→119
    return 113 + (year - 2013) // 2
```
- `committees_at(bioguide, année)` donne les commissions du **bon Congrès**.
- `committees_key_flag` = le membre est-il dans une **commission clé** ?
  ```python
  KEY_PATTERNS = ('Financial Services', 'Committee on Finance', 'Ways and Means',
                  'Banking', 'Armed Services', 'Intelligence')
  ```
- **Repli explicite :** si un snapshot manque, on met `NaN` — **jamais** la photo actuelle.

**Sortie de la partie :** colonnes `committee_membership`, `committees_key_flag`, `congress` (couverture ~98-99 %/an).

---

## 6. Partie 4 — Secteur GICS + ETF proxy

**But :** donner à chaque ticker son **secteur GICS** (parmi 11) et l'**ETF SPDR** correspondant.

Pour chaque ticker distinct, en cascade :

1. **yfinance d'abord** (factuel) :
   ```python
   raw = yf.Ticker(t).info.get('sector')      # ex "Technology"
   gics = YF_SECTOR_TO_GICS.get(raw)          # → "Information Technology"
   ```
2. **Repli LLM** (Claude) pour ce que yfinance ne trouve pas. Le prompt reconnaît **explicitement les sociétés délistées / renommées** (TWTR, ANTM, TWX, KSU…) et leur donne quand même un secteur.
3. **Passe `retry_none`** : ré-essaie le LLM **une fois** sur les tickers restés vides (récupère les délistées que la 1ʳᵉ passe ratait).
4. **Overrides manuels** : quelques ETF larges → pas de secteur.
5. `etf_proxy` = l'ETF SPDR du secteur :
   ```python
   GICS_TO_ETF = {'Information Technology':'XLK', 'Financials':'XLF', 'Energy':'XLE', …}
   ```

Tout est mis en cache : `build_cache/ticker_sector.json`. La trace est gardée dans `sector_source ∈ {yfinance, llm, manual, none}`.

**Restent volontairement `none`** : les ETF/fonds **diversifiés ou obligataires** (SPY, QQQ, VOO, TIP…) — ils n'ont **pas** de secteur GICS unique. C'est correct.

**Sortie de la partie :** colonnes `sector_gics`, `etf_proxy`, `sector_source` (couverture ~97,5 % des lignes tickées).

---

## 7. Partie 5 — Table Quiver de référence **puis l'ASSEMBLAGE HYBRIDE** ⭐

C'est le cœur de la correction. Deux temps.

### 7.1 La table Quiver de référence
On assemble d'abord la **table Quiver pure 2014-2026** (avec tout l'enrichissement ci-dessus) et on l'écrit dans `build_cache/quiver_table_2014_2026.csv`.
*Elle n'est PAS le livrable* : elle sert de **référence** et de base pour la **vérification** (comparer Quiver ↔ golden), et elle fournit la portion 2014-2019.

### 7.2 L'assemblage hybride
1. **Charger ton golden FINAL 2020-2026** (officiel + OCR + non-coté) :
   ```python
   golden = concat(data/{house,senate}/tables/*/06_*_FINAL.csv)   # disclosure ≥ 2020
   ```

2. **Recalculer ses commissions en point-in-time** (snapshots 116-119) — avant, ton golden était sur la photo **actuelle**, donc anachronique :
   ```python
   golden_com = [committees_at(b, y) for b, y in zip(golden.bioguide_id, gtxn_year)]
   ```

3. **Harmoniser le golden au même schéma** (mapping de noms) :

   | Colonne unifiée | Vient de (golden) |
   |---|---|
   | `name` | `declarant_name` |
   | `op` | `_norm_op(operation_type)` → buy/sell/exch |
   | `traded` / `filed` | `transaction_date` / `disclosure_date` |
   | `size_usd` | **borne basse** de `amount_range` (regex, ≥ 1001) |
   | `ticker_type` | `asset_type` |
   | secteur, parti | gardés tels quels du golden |

4. **La coupe (anti double-comptage)** :
   ```python
   q1419 = table[ filed.year ≤ 2019 ]          # Quiver, 48 070
   gh    = golden[ disclosure.year ≥ 2020 ]    # golden, 90 487 (commissions PIT)
   hybride = concat([q1419, gh])               # 138 557
   ```
   La frontière est nette : **Quiver `filed ≤ 2019`** + **golden `disclosure ≥ 2020`** → **aucune ligne dans les deux**.

5. **Finitions** :
   - `size_usd` → défaut **1001** pour les ~0,6 % de lignes golden au montant OCR non capté (sinon `NaN` casserait les variantes pondérées par taille).
   - **Tickers normalisés au format du panel de prix** (`BRK.B → BRK-B`) — sinon les actions golden n'entreraient pas dans le backtest.
   - Colonne **`source`** (`golden-2020-2026` / `quiver-2014-2019`) pour tracer.

6. **Écriture** : `table_congres_2014_2026.csv` = le **livrable**.

---

## 8. Partie 6 — Vérifications (intégrées au notebook)

| # | Contrôle | Résultat attendu |
|---|---|---|
| **(0)** | composition par `source` | golden 2020-26 = **90 487** (= ton golden, **0 perte**) ; Quiver = 48 070 |
| **(1)** | lignes par année | 2014-19 = Quiver, 2020-26 = golden |
| **(2)** | couverture secteur | ~**97,5 %** des lignes tickées |
| **(3)** | couverture commissions par année | **98-99 %**/an, point-in-time partout |
| **(4)** | **concordance** méthode Quiver vs ton golden (2020-26) | secteur **≈ 98 %**, parti **100 %** |

Le contrôle (4) est la **preuve que l'enrichissement Quiver utilisé pour 2014-2019 « colle »** à la qualité de ton golden.

---

## 9. Schéma final de la table (22 colonnes)

| Colonne | Provenance |
|---|---|
| `chamber` | Quiver / golden |
| `bioguide`, `bioguide_id` | Quiver / golden (alias) |
| `name` | Quiver / golden (`declarant_name`) |
| `party` | **point-in-time** (terms) — golden : gardé |
| `state`, `district` | point-in-time (terms) / golden (`state_district`) |
| `committee_membership` | **point-in-time** (snapshots git, partout) |
| `committees_key_flag` | dérivé des commissions point-in-time |
| `years_in_office` | point-in-time (1ᵉʳ mandat) |
| `ticker` | normalisé (format panel) |
| `ticker_type` | Quiver `TickerType` / golden `asset_type` |
| `op` | normalisé (buy/sell/exch) |
| `traded`, `filed` | dates trade / dépôt |
| `size_usd` | borne basse du montant |
| `sector_gics`, `etf_proxy`, `sector_source` | secteur (yfinance + LLM) |
| `party_quiver` | parti « courant » Quiver (audit) |
| `congress` | n° de Congrès (113-119) |
| `source` | `golden-2020-2026` / `quiver-2014-2019` |

---

## 10. Limites assumées & prochaines étapes

- **2014-2019 = Quiver seul** : pas de papier OCR ni de non-coté sur cette période → l'univers pré-2020 est **plus mince** que 2020-26. **À compléter plus tard** en appliquant la méthodo OCR de la « partie 1 » à 2014-2019 (« si le backtest marche, on applique au reste »).
- **Prix (survivorship)** : le panel de prix (`cache/prices/`) ne contient que les tickers encore listés ; les délistés en sont absents → les rendements du backtest sont une **borne haute**. (Limite du notebook de recherche, pas de celui-ci.)
- **`size_usd` = borne basse** (la fourchette STOCK Act ne donne qu'un intervalle).

---

## Annexe — Mini-glossaire

- **Golden** : la table « partie 1 » d'Alice (2020-2026), reconstruite depuis les sources officielles + OCR des PDF papier, validée. Référence de qualité.
- **Point-in-time** : valeur **à la date du trade** (parti, commissions de l'époque), par opposition à la valeur actuelle.
- **GICS** : classification sectorielle standard (11 secteurs). **ETF proxy** : l'ETF SPDR Select Sector du secteur (XLK pour la tech, XLF pour la finance…), utilisé en V2 pour remplacer une action par « son secteur ».
- **Quiver** : agrégateur commercial des trades du Congrès (couverture ~2014+, surtout actions cotées).
- **`bioguide`** : identifiant officiel unique d'un membre du Congrès.

---

*Généré pour accompagner `02_construction_table_2014_2026.ipynb`. Données : table hybride 138 557 lignes (golden 90 487 + Quiver 48 070).*
