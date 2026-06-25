# Pipeline Sénat — Transactions boursières des sénateurs (PTR)
## Volume 2 : années 2020 → 2026 — digital + OCR papier, synthèse complète

Reconstruction des *Periodic Transaction Reports* du Sénat américain, extraite directement de l'eFD
(efdsearch.senate.gov), au standard House toutes_annees. **Digital** (HTML électronique, Quiver-validé)
**+ OCR papier** (Claude Vision, validé hors-Quiver). Quiver = vérification externe, jamais réinjecté.

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
| Couverture ticker (FINAL) | **67,0 %** (digital 79,1 % · OCR 15 %) |
| Volume (midpoint, FINAL) | **$979 M** |
| **Couverture Quiver digital / an** | **98,0 → 100 %** — **0 vrai raté** (audit adversarial) |
| Validation OCR | période + cohérence + spot-check (Quiver **aveugle au papier**) |

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

| Année | digital | + OCR | = FINAL | sénateurs | ticker % | volume $M |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | 1 706 | 255 | **1 961** | 33 | 80,4 % | 304 |
| 2021 | 1 098 | 281 | **1 379** | 35 | 70,1 % | 134 |
| 2022 | 919 | 182 | **1 101** | 27 | 74,8 % | 98 |
| 2023 | 1 062 | 97 | **1 159** | 30 | 77,1 % | 73 |
| 2024 | 946 | 84 | **1 030** | 24 | 67,3 % | 95 |
| 2025 | 943 | 478 | **1 421** | 31 | 44,6 % | 188 |
| 2026 | 487 | 303 | **790** | 22 | 42,5 % | 87 |
| **Total** | **7 161** | **1 680** | **8 841** | **64** | **67,0 %** | **$979 M** |

Fusion **non destructrice** (`merge_ocr.py`, dédup sur `natural_key_hash + occurrence_index`) :
**0 doublon inter-sources** (papier et électronique disjoints). **`asset_type`** : Stock 5 027 ·
Other 1 812 · Municipal 766 · Option 517 · Corporate Bond 246 · … **Opérations** : Purchase 4 341 ·
Sale (Full) 2 404 · Sale (Partial) 1 265 · Sale 769 · Exchange 62.

---

## 5. Limites connues (honnêteté)

- **Amendements cross-année (596 lignes).** Le jeu est organisé par **année de divulgation** ; un trade
  amendé/re-déposé une année ultérieure apparaît dans les deux dépôts (ex. Perdue re-déclare une vente
  Oracle de 2020 dans un PTR 2021). Chaque table annuelle est **interne propre** ; le total **8 841
  lignes** ↔ **8 245 transactions uniques** (595 digital + 1 OCR). *(Même caractéristique côté House.)*
- **OCR invalidable par Quiver.** Le papier est absent de Quiver → validation par période + cohérence
  + spot-check, pas de cross-check externe. C'est la donnée **unique** (Blumenthal n'est *que* papier).
- **Ticker** : FINAL 67 % (digital 79 %, OCR 15 %). Le reste = obligations/munis/véhicules privés sans
  ticker, et papier sans symbole imprimé. Une passe LLM nom→ticker (comme House) serait un ajout.
- **Tickers composites** sur 62 lignes `Exchange` (actions de société, fidèles mais non atomiques).
- **Sénateurs en transition de chambre** : trades pré-Sénat = dépôts House, hors périmètre.

---

## 6. Reproductibilité & fichiers

Réutilise le code Q1 figé (`senat_2025_test/`) — identité (`enrich`), validation (`reconcile`), OCR
(`senate_ocr`) — via import + monkeypatch des chemins ; zéro duplication de logique.

```
python senat_multiyear.py      --years 2020,...,2026   # digital + validation Quiver/an
python senat_ocr_multiyear.py  --mode full             # OCR papier (130 rapports)
python merge_ocr.py                                     # fusion → 06_FINAL/an
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
0 vrai raté + 1 680 OCR papier validé hors-Quiver), **64 sénateurs**, identité **100 %**, ticker 67 %,
$979 M. Le papier (Blumenthal, Boozman…) capte la donnée **unique** que Quiver n'a pas.
