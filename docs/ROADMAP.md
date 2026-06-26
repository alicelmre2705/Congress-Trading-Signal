# Congress Trading Signal — Statut & Roadmap

> **Source de vérité du suivi** (remplace l'ancien `ETAT_AVANCEMENT_PROJET.md`, archivé à la consolidation du 2026-06-26).
> Dernière mise à jour : **2026-06-26**.

Projet mené pour **Ramify** : construire une **stratégie de copy-trading** fondée sur les déclarations
boursières (PTR / *STOCK Act*) des membres du Congrès US. Brief Ramify en 4 semaines —
**S1-S2 = couche données**, **S3-S4 = stratégie + backtest** (V1 actions, V2 ETF sectoriels).

**Constat central : la couche données est livrée ; la couche stratégie/backtest n'est pas commencée.**

**Cadrage retenu :** périmètre **2020-2026** (2013-2019 = extension optionnelle) · backtest = **moteur Python local** dans ce repo.

---

## 1. Ce qui est FAIT

### Données produites (2020 → 2026, 7 ans, 2 chambres)

| | House | Sénat | Total |
|---|---|---|---|
| Transactions FINAL | 81 646 | 8 841 | **90 487** |
| dont digital / OCR | 32 676 / 48 970 | 7 161 / 1 680 | 39 837 / 50 650 |
| Identité (bioguide) | 99,99 % | 100 % | — |
| Ticker | 85,3 % | 71,4 % | — |
| Secteur GICS→ETF | 83,2 % | 62,1 % | — |
| Validation Quiver | 85,9 %/an | 98–100 %/an | — |

### Architecture (refonte 2026-06-26, commits a8eb737 → 0546406)

- `congress_core/` (12 modules partagés) : schema, **identity★**, amounts, tickers, quiver, vision_ocr,
  llm_resolve, sector_enrich, crosscheck, reporting, paths.
- `house/` (4 modules) + `senate/` (11 modules) en miroir.
- `data/house/` + `data/senate/` : tables FINAL par année + référentiels autonomes + caches OCR/LLM/Quiver versionnés.
- `tests/regression/` : golden House (93-108 fichiers) + Sénat (68 fichiers), **zéro écart** ;
  reproduction fonction-par-fonction (natural_key 161 974/161 974, identité, montants, tickers).

### Table FINAL — 12 champs Ramify garantis (sur 27 colonnes)

`declarant_name`, `chamber`, `party`, `committee_membership`, `transaction_date`, `disclosure_date`,
`ticker`, `sector_gics`, `etf_proxy`, `operation_type`, `amount_midpoint`, `asset_type` —
**remplis pour les deux chambres.**

### Couverture du brief Ramify, Semaines 1–2 → ✅ complète

Audit sources · téléchargement automatisé (cache resumable) · pipeline LLM (Claude Vision OCR +
extraction structurée, midpoint, disclosure_date) · nettoyage (tickers, noms→bioguide, dédup non
destructrice, sans-ticker flaggé) · mapping GICS → ETF SPDR (11 secteurs) · table finale 12/12 +
reproductibilité prouvée.

---

## 2. Reste à faire (organisé, priorisé)

### 🔴 Priorité 1 — STRATÉGIE + BACKTEST (moteur Python local) — S3-S4 Ramify · **0 % fait · ~50 % du brief**

Nouveau package (ex. `strategy/`) consommant les tables FINAL. Étapes séquentielles :

1. **Construction des positions** — entrée = `disclosure_date` d'un *Purchase* ; sortie = `disclosure_date`
   du *Sale* correspondant (même déposant + ticker), sinon **+12 mois** forcés. Chaque trade = (entrée, sortie)
   explicite, sans ambiguïté.
2. **Prix point-in-time** — actions + **S&P 500** (benchmark alpha) via yfinance (déjà une dépendance).
   Gérer délistés / splits.
3. **V1 — actions directes** — trade le ticker exact ; track records individuels par congressman.
4. **Métriques** — hit rate, retour moyen/trade, **Sharpe** (série de trades), **alpha vs S&P 500**.
5. **Sélection annuelle de K congressmen** (K = 4..10, grid) — éligibilité ≥ 10 trades ; positions des
   sortants laissées courir jusqu'à sortie naturelle.
6. **Filtre commissions** — ≥ la moitié des K dans Finance / Defense / Intelligence (déjà dans `committees_key_flag`).
7. **V2 — ETF sectoriels** — substitution via `etf_proxy` (mapping GICS déjà fait) ; entrée/sortie identiques,
   instrument seul change.
8. **Garde-fous anti-biais** (De Prado) — look-ahead (entrée stricte disclosure_date), survivorship,
   surajustement, liquidité + **tests** dédiés.
9. **Rapport de backtest annoté** — livrable Ramify (V1 puis V2, par K, par critère).

### 🟢 Priorité 2 — Finitions données Semaine 1–2 → **CLÔTURÉ (2026-06-26)**

Les 4 chantiers gratuits (≈ 0 crédit API) sont faits ; reproductibilité préservée (golden re-figés,
zéro écart). Détails :

- ✅ **Rapport de qualité synthétique** — `congress_core/quality.py` → `docs/RAPPORT_QUALITE.md` +
  figures `docs/quality/*.png`. Couvre les 5 contrôles Ramify (cohérence dates, délai 45 j,
  distribution des montants, coverage par congressman + éligibles ≥10 trades, taux sans sortie déclarée).
- ✅ **Métadonnée « années en poste »** — colonne `years_in_office` (ancienneté à la date du trade)
  ajoutée aux 14 FINAL via `congress_core/enrich_tenure.py` (calcul offline depuis les `terms`
  embarqués) ; 99,9–100 % renseigné ; reproduction prouvée (`tests/regression/test_tenure.py`).
- ✅ **Pipeline end-to-end unifié** — `python -m congress_core.pipeline --years 2020-2026`
  (orchestre House/Sénat digital→OCR→fusion→enrichissement ; `--skip-ocr`, `--dry-run`).
- ✅ **Test de mise à jour incrémentale** — `tests/regression/test_incremental.py` prouve
  « 2ᵉ run = 0 appel Vision » (cache hit sans instanciation du client) + stabilité du `prompt_sha`.

**Reste (à part) :**

- **Commissions point-in-time** — aujourd'hui snapshot courant ; explique le `committee_membership`
  incomplet en début de période (ex. Sénat 2020 ≈ 34 %). Vrai correctif = données historiques de
  commissions par Congrès (`api.congress.gov`) → effort de sourcing/dev (sans crédit Claude). Non fait.
- **Clarification « 12 champs sans manquants »** — en pratique « 12 champs *présents* » : `ticker`,
  `sector_gics`/`etf_proxy` (non cotés par nature) et `committee_membership` (effet snapshot) ont des
  trous. À confirmer avec Ramify si « sans manquants » est strict. *(Décision, pas du dev.)*

> Note (résolu 2026-06-26) : `tests/regression/smoke_digital.py` a été **retiré**. Il importait
> `house_multiyear` (module supprimé à la refonte) et, surtout, ne pouvait pas reproduire le golden
> hors-ligne — les PDF digitaux lisibles sont absents (seuls les 547 scannés OCR restent). Son
> intention est couverte par les tests de reproduction depuis colonnes figées ; cf.
> `tests/regression/README.md`.

### 🟡 Priorité 3 — Différés assumés (à confirmer ou clore explicitement)

- **Cluster C manuscrit** (~63+ docs, dates peu fiables) — exclu, récupérable via cache.
- **`efd_client.py`** Sénat (fusion 3 copies scraping) — différé (non vérifiable hors-ligne).
- **Tolérance de date** appariement Quiver House (couverture 85,9 % = plancher, sous-estime sur dates OCR bruitées).

### ⚪ Optionnel — Extension historique 2013-2019

Ramify écrit « depuis 2013 ». Re-run complet du pipeline (scraping + OCR + validation) sur 6 ans.
**Hors périmètre retenu** — laissé en option, à rouvrir si Ramify l'exige.

---

## 3. Prochain jalon suggéré

Démarrer la **Priorité 1** (moteur de backtest) : commencer par les étapes 1–4 (positions → prix →
V1 → métriques) sur un congressman de référence (ex. un gros déposant à fort volume), puis généraliser
(sélection K, V2). Les étapes 2 et 4 réutilisent yfinance déjà présent ; le filtre commissions (étape 6)
réutilise `committees_key_flag` déjà calculé.
