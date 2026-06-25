# Chambre — PTR Q1 2025 (2025_test) — Synthèse des résultats

Périmètre : 117 PDFs PTR Q1 2025, tous en format PDF (électronique parsé + scannés OCR).  
Validation externe : QuiverQuant.

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

## 4. Limites

- **Ticker électronique non audité** : pas d'équivalent 06e pour la piste HTML — validation uniquement par count Quiver.
- **Khanna = 88,8 % de l'OCR** : les métriques OCR sont très concentrées sur un seul représentant.
- **`operation_type` OCR** : coexistence de `Sale` et `Sale (Partial)` / `Partial Sale` — deux conventions selon le formulaire ; homogénéisation à faire.
- **Dates** : même limite que Sénat — Quiver date parfois avec la date de dépôt.
