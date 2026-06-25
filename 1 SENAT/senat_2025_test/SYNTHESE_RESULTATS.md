# Sénat eFD Q1 2025 — Synthèse des résultats

Périmètre : 37 rapports PTR divulgués Q1 2025 (33 électroniques + 4 papier scannés).  
Validation externe : QuiverQuant (n'entre jamais dans la table).

---

## 1. Résultats bruts

|  | Électronique | OCR papier | **Total** |
|---|---:|---:|---:|
| Rapports traités | 33 | 4 | **37** |
| Transactions | 283 | 92 | **375** |
| Sénateurs | 17 | 1 (Blumenthal) | **18** |
| Bioguide attaché | 283/283 = **100 %** | 92/92 = **100 %** | **100 %** |
| Ticker renseigné | 191/283 = **67,5 %** | 0/92 = 0 % (actifs privés) | 191/375 = 51 % |
| Volume midpoint | $23,6 M | $18,0 M | **$41,6 M** |

### Ticker électronique : détail des sources

| Source | N | Mécanisme |
|---|---:|---|
| `explicit` | 152 | Colonne Ticker eFD renseignée |
| `asset_name` | 39 | Asset Name *est* le ticker (ex. « LLY », « CRWD PUT ») |
| `none` | 92 | Munis (70) + corporate bonds (18) + 4 cas nommés — pas de ticker boursier |

→ Sur les actifs qui *ont* un ticker (actions, ETF, options) : **≥ 99 %** couverture.  
→ Les 88 obligations n'ont pas de ticker par conception (CUSIP uniquement).  
→ Les 92 OCR sont tous des véhicules LP privés (Peter L Malkin Family LLC, etc.) — aucun ticker possible.

### Opérations

| Type | Électronique | OCR | Total |
|---|---:|---:|---:|
| Purchase | 165 | 68 | **233** |
| Sale (Full) | 73 | — | 73 |
| Sale (Partial) | 45 | — | 45 |
| Sale | — | 24 | 24 |

---

## 2. Validation vs QuiverQuant

Fenêtre comparable : Quiver filtré sur `Filed` Q1 2025 → **164 transactions**.

| Verdict | Sénateurs | Nos txns | Quiver txns | Delta |
|---|---:|---:|---:|---:|
| Concordant exact | **11** | 61 | 61 | 0 |
| Nous plus | 4 | 207 | 102 | +105 |
| Quiver sans donnée | 3 | 107 | 0 | +107 |
| Quiver seul | 1 | 0 | 1 | −1 |
| **Total** | **18** | **375** | **164** | **+211** |

**Aucun delta négatif réel.** Le seul cas négatif (Norton −1) est une erreur de chambre côté Quiver : Eleanor Holmes Norton est déléguée DC à la Chambre, pas sénatrice.

### Validation ticker-à-ticker (table `07b`)

1 seul écart sur l'ensemble du périmètre : Hagerty `AHL-C` (nous) vs `AHL.C` (Quiver) — même trade du 02/01/2025, ponctuation du ticker différente. **0 trade manqué.**

### Validation instrument-par-instrument (Boozman, cas test)

Boozman = concordant 38/38. Intersection tickers : **29/29 = 100 %**, 0 ticker nous-seul, 0 ticker Quiver-seul. Validation exhaustive sur instruments et comptage.

### Explication des deltas positifs

| Sénateur | Delta | Cause |
|---|---:|---|
| McCormick +61 | 61 | 52 munis PA + 9 corporate bonds — Quiver n'indexe pas les obligations |
| Moody +29 | 29 | Quiver sous-compte les ventes : 5 Sale Full vs nos 33 (biais connu) |
| Mullin +13 | 13 | Mêmes tickers (∆ tickers = 0), occurrences supplémentaires non capturées par Quiver |
| Blumenthal +92 | 92 | 100 % OCR papier — Quiver n'indexe aucun de ses dépôts (déposés via cabinet) |

---

## 3. Correctifs vs v1

| Problème v1 | Avant | Après |
|---|---|---|
| Validation Quiver jamais exécutée | variable `QUIVER_API_TOKEN` absente → skip silencieux | `QUIVER_API_KEY` + cache bulk filtré Sénat |
| Bioguide manquant | 77/280 = **27 %** non rattachés | **0/375 = 0 %** |
| Filtre chambre Quiver | `contains("Sen")` attrapait des représentants | Égalité exacte `Chamber == "Senate"` |
| Ticker | 54 % (estimation) | 67,5 % électronique (source `asset_name` +39) |
| Déduplication destructrice | 3 vraies transactions supprimées (Moody same-day) | `occurrence_index` — seuls les doublons cross-rapport fusionnés |
| 4 rapports papier ignorés | 0 transaction OCR | **92 transactions OCR**, 0 échec batch |

---

## 4. Limites assumées

- **Dates et montants** : Quiver stocke la date de dépôt comme date de trade et tronque les montants à $1 001 — cross-check date/montant impossible via Quiver.
- **Ticker électronique** : plafond réel = 56,8 % (88 obligations + 92 OCR privés = 180 txns sans ticker par construction). 67,5 % sur l'électronique est le vrai indicateur.
- **`asset_type` OCR** : inféré du nom (pas de colonne explicite sur le formulaire papier Sénat).
- **Accès eFD** : gate CSRF + Akamai — s'appuie sur le cache HTML local.
