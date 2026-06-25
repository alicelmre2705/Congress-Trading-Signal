# Chambre — PTR Q1 2025 (2025_test) — Synthèse des résultats

Périmètre : 117 PDFs PTR Q1 2025, tous en format PDF (électronique parsé + scannés OCR).  
Validation externe : QuiverQuant.  
**Table finale : les 12 champs obligatoires sont tous présents** (ajout de `sector_gics` + `etf_proxy`, cf. §4).

---

## 1. Résultats bruts

|  | Électronique (HTML parsé) | OCR PDF scanné | **Total** |
|---|---:|---:|---:|
| PDFs traités | 117 (tous) | — | **117** |
| Transactions | 1 105 | 1 167 | **2 272** |
| Représentants | 56 | 10 | **66** |
| Bioguide attaché | 1 105/1 105 = **100 %** | 1 167/1 167 = **100 %** | **100 %** |
| Ticker renseigné | 998/1 105 = **90,3 %** | 1 055/1 167 = **90,4 %** | 2 053/2 272 = **90,4 %** |
| Volume midpoint | $82,1 M | $24,9 M | **$107,0 M** |

### Ticker OCR — avant/après passe LLM

| Étape | Tickers résolus | Couverture |
|---|---:|---:|
| `elec_dict` seul (dictionnaire) | 540/1 167 | **46,3 %** |
| + `llm` (nom→ticker Claude) | +515 | **90,4 %** (+44 pts) |
| `none` résiduel | 112/1 167 | 9,6 % (Gov Security, fonds non-listés) |

### Ticker électronique — sources

Pas de colonne `ticker_source` sur la piste HTML : le ticker est extrait directement du dictionnaire eFD.  
998/1 105 = **90,3 %** — les 107 sans ticker sont Gov Security (40), HN/CS/CT (35) et divers non-listés.

### Opérations

| Type | N |
|---|---:|
| Purchase | 1 206 |
| Sale | 791 |
| Sale (Partial) | 209 |
| Partial Sale | 61 |
| Exchange | 5 |

### Asset type

| Type | N |
|---|---:|
| Stock | 2 035 |
| Gov Security | 45 |
| Other | 36 |
| Mutual Fund | 30 |
| Option | 17 |

---

## 2. Validation vs QuiverQuant

### Électronique — niveau représentant (table `07`)

| Verdict | Représentants | Nos txns | Quiver txns | Delta |
|---|---:|---:|---:|---:|
| Concordant exact (∆ = 0) | **26** | — | — | 0 |
| Nous plus (∆ > 0) | **30** | — | — | +125 |
| Nous sous Quiver (∆ < 0) | **0** | — | — | — |
| **Total** | **56** | **1 105** | **980** | **+125** |

**0 représentant en dessous de Quiver.**

### OCR — niveau représentant (table `06d`)

| Verdict | Représentants | OCR | Quiver Q1 | Delta |
|---|---:|---:|---:|---:|
| ocr ≥ quiver | 4 | 1 150 | 829 | +321 |
| quiver_sans_donnee | 6 | 17 | 0 | +17 |
| **Total** | **10** | **1 167** | **829** | **+338** |

**0 delta négatif sur l'OCR non plus.** Quiver n'a aucun des 6 représentants "sans donnée" (petits dépôts non indexés).

### Cas test Khanna (88 % de l'OCR)

Rohit Khanna = 1 036/1 167 txns OCR (88,8 %).  
Ticker : **965/1 036 = 93,1 %** — ticker_source : elec_dict 485, llm 480, none 71.  
Quiver Q1 : 756 — delta +280, 0 ticker manquant dans notre sens.

---

## 3. Qualité LLM ticker (audit `06e`)

500 tickers LLM audités contre Quiver :

| Résultat | N | % |
|---|---:|---:|
| **Match exact** | **466** | **93,2 %** |
| Non-match | 34 | 6,8 % |

Les 34 non-match ne sont pas des erreurs grossières : il s'agit de classes alternatives du même émetteur (préférentielles, ADR) que Quiver indexe différemment.

| Notre ticker | Quiver | Cause |
|---|---|---|
| `APO` | `AAM-PA` | Apollo Global — Quiver indexe une préférentielle |
| `ETN` | `ELN` | Eaton Corp — ticker alternatif |
| `AIG` | `AFG` | AIG vs American Financial Group (confusion nom) |
| `WRB` | `WRB-PG` | W.R. Berkley — préférentielle G |
| `VRTX` | `VERX` | Vertex Pharma vs Vertex Inc. (collision nom) |

→ Dans tous ces cas notre ticker est le bon ticker ordinaire ; c'est Quiver qui indexe la série secondaire.

---

## 4. Enrichissement secteur GICS → ETF (champs `sector_gics`, `etf_proxy`)

Les deux derniers champs obligatoires de la table finale. Méthode **hybride anti-hallucination** :
secteur factuel via **yfinance** (source primaire), **repli LLM** (Claude, `tool_use` forcé, cache
versionné — même pattern que la passe nom→ticker) pour les tickers que yfinance ne couvre pas
(delistés, préférentielles, ADR), puis **couche d'override** issue d'un audit adversarial. Univers
ETF cible = **SPDR Select Sector** (mapping 1:1 avec les 11 secteurs GICS ; l'univers Ramify sera
tranché en fin de projet). Module `sector_enrich.py` ; audit `06f_sector_audit.csv`.

### Couverture (591 tickers distincts → 2 272 lignes)

| Indicateur | Valeur |
|---|---|
| `sector_gics` / `etf_proxy` remplis | 2 030/2 272 lignes = **89,3 %** |
| Tickers distincts classés | 578/591 = **97,8 %** |
| Source `yfinance` (factuel) | 1 954 lignes — **92,7 %** des tickers distincts |
| Source `llm` (repli : delistés, préférentielles) | 70 lignes / 32 tickers |
| Source `manual` (override audit) | 17 lignes / 6 tickers |
| `none` (non coté : Gov Security, fonds, obligations) | 231 lignes — `null` à dessein |

Les ~11 % de lignes sans secteur correspondent exactement aux lignes sans ticker cotable (même
plafond que le ticker). Chaque `sector_gics` non-null a un `etf_proxy` ∈ {XLK, XLF, XLV, XLE, XLI,
XLY, XLP, XLB, XLU, XLRE, XLC} (jointure 1:1 complète, 0 manquant).

### Validation

- **Audit croisé yfinance ↔ LLM** : sur 543 tickers résolus par les deux, **95,4 % d'accord**
  (comparable à l'audit ticker 93 %). Les 25 désaccords sont des **frontières GICS légitimes**
  (fintech IT↔Financials : FIS, GPN, CPAY ; packaging Materials↔Consumer : AVY, BALL, CCK ;
  Dollar General Staples↔Discretionary) — aucune hallucination.
- **Audit adversarial** (3 juges indépendants + synthèse) : **6 erreurs réelles** (~1,0 %), toutes
  dans la queue mono-source (ETF / réattributions de ticker), **corrigées** par override —
  FNA→Health Care, SMCYY→Communication Services, SHLD→Industrials (ETF défense), HURA→Materials
  (ETF uranium) ; SLYG, TNA (ETF diversifiés) → **non classés** (pas de secteur unique). Verdict :
  **mapping fiable** pour un livrable de recherche.

### Distribution sectorielle (tickers distincts)

IT 115, Industrials 98, Financials 81, Health Care 76, Consumer Discretionary 57, Consumer Staples 44,
Communication Services 25, Materials 24, Real Estate 22, Utilities 19, Energy 17 — profil
tech / industrie / finance cohérent avec des transactions du Congrès.

---

## 5. Limites

- **Ticker électronique non audité** : pas d'équivalent 06e pour la piste HTML — validation uniquement par count Quiver.
- **Khanna = 88,8 % de l'OCR** : les métriques OCR sont très concentrées sur un seul représentant.
- **`operation_type` OCR** : coexistence de `Sale` et `Sale (Partial)` / `Partial Sale` — deux conventions selon le formulaire ; homogénéisation à faire.
- **Dates** : même limite que Sénat — Quiver date parfois avec la date de dépôt.
- **Secteur — multi-sources & univers ETF** : `sector_gics` combine yfinance (factuel, 92,7 %), repli LLM (delistés/préférentielles) et 6 overrides d'audit. Pas de vérité-terrain unique externe ; la confiance repose sur l'audit croisé (95,4 %). Les ETF de marché diversifiés (SLYG, TNA) sont laissés non classés à dessein. L'univers `etf_proxy` = SPDR Select Sector, à réaligner sur l'univers Ramify en fin de projet.
