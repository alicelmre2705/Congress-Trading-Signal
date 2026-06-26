# Pipeline Sénat — Transactions boursières des sénateurs (PTR)
## Volume 2 : années 2020 → 2026 — digital + OCR papier, synthèse complète

Reconstruction des *Periodic Transaction Reports* du Sénat américain, extraite directement de l'eFD
(efdsearch.senate.gov), au standard House toutes_annees. **Digital** (HTML électronique, Quiver-validé)
**+ OCR papier** (Claude Vision, validé hors-Quiver). Quiver = vérification externe, jamais réinjecté.

> **Parité House (màj 2026-06-26).** Trois raffinements House manquants ont été portés au stade FINAL :
> **résolution ticker** (dictionnaire nom→ticker + passe LLM `is_equity`, `ticker_resolve.py`) →
> 67,0 %→**71,4 %** ; **secteur GICS → ETF SPDR** (`sector_enrich`, champs `sector_gics`/`etf_proxy`)
> → table **12/12 champs** ; **flag `date_confidence`** (fenêtre légale 75 j). La validation Quiver a
> reçu la **dédup des amendements** (couverture inchangée, 554 doublons de comptage retirés).

---

## ► Résultat à utiliser

| Source | Fichier | Transactions |
|---|---|---|
| **Table FINALE par an** | `data/{année}/06_senate_{année}_FINAL.csv` × 7 | **8 841** (digital + OCR) |
| Digital seul | `data/{année}/06_senate_{année}_transactions.csv` | 7 161 |
| OCR papier seul | `data/{année}/06b_senate_{année}_ocr_transactions.csv` | 1 680 |
| Dashboards | `data/00_year_status.csv` (digital+Quiver) · `data/00_final_status.csv` (FINAL) | — |

---

## 1. Vue d'ensemble

| Indicateur | Valeur |
|---|---|
| Période | 2020 → 2026 (7 années) |
| **Transactions FINALES (digital + OCR)** | **8 841** lignes · **8 245** uniques (cf. §5 amendements) |
| — digital électronique | 7 161 (805 PTR, 0 échec parse) |
| — OCR papier | 1 680 (130 PTR, 0 échec batch) |
| Sénateurs distincts | **64** |
| **Identité (bioguide rattaché)** | **100 %** (0 non rattaché) |
| Couverture ticker (FINAL) | **71,4 %** (6 310/8 841) — dict +197, LLM +190 vs 67,0 % |
| — sources ticker | explicit 5 858 · elec_dict 197 · llm 190 · asset_name 65 · none 2 531 |
| **Couverture secteur (`sector_gics`/`etf_proxy`)** | **62,1 %** — yfinance 4 670 · llm 803 · manual 83 · none 3 285 |
| Volume (midpoint, FINAL) | **$979 M** |
| **Couverture Quiver digital / an** | **98,0 → 100 %** — **0 vrai raté** (audit adversarial) |
| Validation OCR | période + cohérence + spot-check (Quiver **aveugle au papier**) |
| `date_confidence` (fenêtre 75 j) | majorité *plausible* ; les *implausible* = divulgations **tardives/amendées** réelles (ex. lot Perdue 2021), pas des erreurs OCR |

---

## 2. Couche digitale 2020 → 2026 (Quiver-validée)

| Année | digital | sénateurs | ticker % | couverture Quiver | only_quiver | vrais ratés |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | 1 706 | 29 | 89,4 % | 99,4 % | 8 | 0 |
| 2021 | 1 098 | 31 | 85,8 % | 98,0 % | 8 | 0 |
| 2022 | 919 | 24 | 81,2 % | 99,4 % | 4 | 0 |
| 2023 | 1 062 | 29 | 76,8 % | 99,7 % | 2 | 0 |
| 2024 | 946 | 23 | 71,9 % | 99,6 % | 2 | 0 |
| 2025 | 943 | 30 | 65,6 % | 99,8 % | 1 | 0 |
| 2026 | 487 | 21 | 69,0 % | 100,0 % | 0 | 0 |
| **Total** | **7 161** | **61** | **79,1 %** | **≥ 98 %/an** | **25** | **0** |

**Audit adversarial** (7 agents indépendants, un par année, relisant les PTR bruts) → **0 vrai raté**.
Les 25 `only_quiver` = actions de société (`Exchange` à ticker composite « FTV  VNT » ≠ atomique Quiver)
ou transitions de chambre (Marshall/Curtis/Vance, trades ex-House).

**Dédup des amendements Quiver (parité House, màj 2026-06-26).** `reconcile()` ne garde qu'un exemplaire
par (sénateur, ticker, date tradée, sens) avant comptage : **554 doublons d'amendements** retirés sur les
7 ans. La **couverture transaction-niveau est inchangée** (98,0→100 %/an, calculée sur des ensembles) et
`only_quiver` reste **25** — seuls les compteurs de deltas par sénateur sont nettoyés.

---

## 3. Couche OCR papier (validée hors-Quiver)

Les **130 PTR papier** (Claude Vision, même moteur que le Q1) — extraits par `senat_ocr_multiyear.py`.
Déposants : **Blumenthal 1 233 · Boozman 379 · Burr 52 · Feinstein 14 · Fetterman 2**.

| Année | OCR txns | rapports papier |
|---|---:|---:|
| 2020 | 255 | 33 |
| 2021 | 281 | 22 |
| 2022 | 182 | 19 |
| 2023 | 97 | 15 |
| 2024 | 84 | 14 |
| 2025 | 478 | 21 |
| 2026 | 303 | 6 |
| **Total** | **1 680** | **130** |

### Validation (pas de vérité-terrain Quiver — Blumenthal = 0 ligne Quiver sur 2014→2026)

- **Pilote dé-risqué** : régression Blumenthal Q1 **= 92 txns** (reproduit le pilote figé) ; généralisation
  confirmée sur 4 autres sénateurs (Boozman, Feinstein, Burr, Fetterman).
- **Bug attrapé par le pilote** : collision de cache image (les `.gif` sont nommés `000000010/11/12`
  *par rapport*) → corrigé (indexation par hash d'URL). Sans le pilote, le run aurait été corrompu.
- **Spot-check manuel** : page 2 de Boozman (achats ETF, déc. 2019) confrontée à l'image scannée →
  match ligne-par-ligne.
- **Cohérence** : identité **100 %**, **dates 98,8 % dans la période déclarée** (lettres
  d'accompagnement + garde-fou millésime), **0 échec batch**.
- **Limite** : ticker ≈ 15 % (le formulaire papier n'imprime pas les symboles) ; `asset_type` inféré
  du nom (239 lignes non inférées) — moins précis que l'électronique.

---

## 4. Table FINALE (digital + OCR)

| Année | digital | + OCR | = FINAL | sénateurs | ticker % (avant→après) | secteur % | volume $M |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 1 706 | 255 | **1 961** | 33 | 80,4 → **88,1 %** | 80,5 % | 304 |
| 2021 | 1 098 | 281 | **1 379** | 35 | 70,1 → **80,9 %** | 70,1 % | 134 |
| 2022 | 919 | 182 | **1 101** | 27 | 74,8 → **79,7 %** | 65,3 % | 98 |
| 2023 | 1 062 | 97 | **1 159** | 30 | 77,1 → **77,7 %** | 69,5 % | 73 |
| 2024 | 946 | 84 | **1 030** | 24 | 67,3 → **68,0 %** | 59,2 % | 95 |
| 2025 | 943 | 478 | **1 421** | 31 | 44,6 → **45,4 %** | 37,2 % | 188 |
| 2026 | 487 | 303 | **790** | 22 | 42,5 → **43,7 %** | 35,7 % | 87 |
| **Total** | **7 161** | **1 680** | **8 841** | **64** | 67,0 → **71,4 %** | **62,1 %** | **$979 M** |

> Le lift ticker est **fort sur les années digital-lourdes** (2020 +7,7 pts, 2021 +10,8 pts) et **faible
> sur 2025-2026** : ces années sont dominées par l'OCR papier de Blumenthal (munis/Treasuries sans ticker)
> → reliquat **structurellement non coté**, pas une lacune de la passe (cf. §5).

Fusion **non destructrice** (`merge_ocr.py`, dédup sur `natural_key_hash + occurrence_index`) :
**0 doublon inter-sources** (papier et électronique disjoints). **`asset_type`** : Stock 5 027 ·
Other 1 812 · Municipal 766 · Option 517 · Corporate Bond 246 · … **Opérations** : Purchase 4 341 ·
Sale (Full) 2 404 · Sale (Partial) 1 265 · Sale 769 · Exchange 62. **12/12 champs obligatoires** remplis
(`sector_gics` + `etf_proxy` ajoutés, jointure sur ticker stabilisé).

---

## 5. Limites connues (honnêteté)

- **Amendements cross-année (596 lignes).** Le jeu est organisé par **année de divulgation** ; un trade
  amendé/re-déposé une année ultérieure apparaît dans les deux dépôts (ex. Perdue re-déclare une vente
  Oracle de 2020 dans un PTR 2021). Chaque table annuelle est **interne propre** ; le total **8 841
  lignes** ↔ **8 245 transactions uniques** (595 digital + 1 OCR). *(Même caractéristique côté House.)*
- **OCR invalidable par Quiver.** Le papier est absent de Quiver → validation par période + cohérence
  + spot-check, pas de cross-check externe. C'est la donnée **unique** (Blumenthal n'est *que* papier).
- **Ticker** : FINAL **71,4 %** après la passe dict + LLM (parité House). Le reliquat **28,6 %** est
  **structurellement non coté** — sondage des 2 531 lignes sans ticker : ~60 % obligations municipales /
  Treasuries / LLC privées (sans symbole *par nature*), le reste papier sans symbole imprimé. Le « 90 %
  House » n'est **pas atteignable** : le corpus Sénat (Blumenthal = 1 233 lignes OCR, gros détenteur de
  munis) est bien plus obligataire. La passe LLM filtre `is_equity` → ne tickerise jamais un bond/muni.
- **Tickers composites** sur 62 lignes `Exchange` (actions de société, fidèles mais non atomiques).
- **`date_confidence`** : flag de fenêtre légale (75 j), pas un certificat. Les *implausible* (surtout
  2021) sont des **divulgations tardives/amendées réelles** (lot Perdue : trades 2020 déclarés en 2021,
  délai médian 382 j) — utile pour le backtest (signal connu très tard ≠ exploitable), pas un défaut OCR.
- **Sénateurs en transition de chambre** : trades pré-Sénat = dépôts House, hors périmètre.

---

## 6. Reproductibilité & fichiers

Réutilise le code Q1 figé (`senat_2025_test/`) — identité (`enrich`), validation (`reconcile`), OCR
(`senate_ocr`) — via import + monkeypatch des chemins ; zéro duplication de logique.

```
python senat_multiyear.py      --years 2020,...,2026   # digital + validation Quiver/an
python senat_ocr_multiyear.py  --mode full             # OCR papier (130 rapports)
python merge_ocr.py                                     # fusion + ticker(dict+LLM) + secteur + date → 06_FINAL/an
python revalidate_quiver.py                             # dédup amendements Quiver → 07c-f + dashboard (offline)
```
*Idempotent : HTML eFD + images + extractions Vision cachés sur disque (reprise gratuite, résiliente
aux timeouts). Quiver servi depuis le cache local, jamais réinjecté.*

| Fichier | Rôle |
|---|---|
| `data/{an}/06_senate_{an}_FINAL.csv` × 7 | **Tables finales digital + OCR** (8 841) |
| `data/{an}/06_…_transactions.csv` / `06b_…_ocr_…csv` | digital / OCR seul |
| `data/{an}/07_*` / `07c-07f` | validation Quiver par an (digital) |
| `data/00_year_status.csv` · `data/00_final_status.csv` | dashboards digital / FINAL |
| `data/_paper_index_2020_2026.csv` | index des 130 PTR papier |
| `data/reports/*.html` · `reports/media/*` · `ocr_cache/*.json` | caches offline |

**Vérification** : digital audité adversarialement (0 vrai raté, couverture Quiver ≥ 98 %/an) ; OCR
validé par régression (92), généralisation (4 sénateurs), spot-check visuel, dates 98,8 % en période,
0 échec batch.

---

**En une ligne.** Sénat **2020→2026** : **8 841 transactions** (7 161 digital Quiver-validé à ≥ 98 %/an,
0 vrai raté + 1 680 OCR papier validé hors-Quiver), **64 sénateurs**, identité **100 %**, ticker **71,4 %**,
secteur **62,1 %** (table **12/12 champs**), $979 M. Le papier (Blumenthal, Boozman…) capte la donnée
**unique** que Quiver n'a pas ; le reliquat ticker est structurellement non coté (munis/Treasuries).
