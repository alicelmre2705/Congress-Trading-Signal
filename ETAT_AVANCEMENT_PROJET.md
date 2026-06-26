# Congress Trading Signal — État d'avancement & checklist

*Pipeline **data** House & Sénat — mis à jour le 2026-06-25.*

> **MD = source de vérité du suivi.** Les versions `.tex`/`.pdf` (mises de côté dans [`_pdf_tex/`](_pdf_tex/)) ne sont plus prioritaires : c'est ce fichier qui dit où on en est et ce qu'il reste.

---

## 1. Objectif et cadre

**But.** Construire une stratégie systématique de *copy trading* répliquant les transactions déclarées par les membres du Congrès américain (STOCK Act, 2012), puis la backtester sur le framework Ramify. 4 semaines, dont **2 entièrement consacrées à la donnée** (un backtest sur une donnée mal extraite ne vaut rien).

> **Où en est-on, en une phrase.** La **couche donnée** est largement construite et validée, étendue **toutes années 2020 → 2026** des deux côtés : **House digital 32 676 txns** (99 % Quiver) et **Sénat digital 7 161 txns** (98-100 % Quiver/an, 0 vrai raté, audit adversarial). Le **Sénat** est désormais à **parité House** sur le post-traitement (résolution ticker dict+LLM 67→71,4 %, secteur GICS→ETF, flag `date_confidence`, dédup amendements Quiver) → table **12/12 champs**, ET **restructuré en miroir** : package `senate/` (arbo plate) sur le cœur `congress_core`, données `data/senate/`, reproduction « zéro changement » prouvée (golden 68 fichiers / 8 841, `test_senate_repro` : natural_key_hash 8 841/8 841 via `congress_core`) — détail `docs/REFONTE_SENATE.md`. Côté **House** : **restructuré** (cœur `congress_core` + package `house/`, données `data/house/`) ; OCR complet (A+B+C), **dédup amendements corrigée** (non destructrice : −405 doublons cross-doc, multi-trust Khanna préservé), **FINAL 81 646** (digital 32 676 + OCR 48 970), identité 99,99 %, concordance Quiver 85,9 % — rapport superviseur `docs/RAPPORT_HOUSE.pdf`. Reste l'**enrichissement secteur** (table 12/12, différé, ~2 468 tickers). Puis **toute la partie stratégie + backtest** (semaines 3–4, non commencé).

**Légende.** ✅ fait et vérifié · 🟡 commencé / partiel · 🔴 non commencé · — hors périmètre actuel.

---

## 2. Tableau de bord global

| Bloc / livrable | Statut | Preuve / chiffre |
|---|:---:|---|
| **Semaine 1 — exploration, sourcing, architecture** | | |
| Audit des sources & décision d'architecture | ✅ | House Clerk + Quiver + eFD audités ; 37 445 dépôts / 8 248 PTR (2013–2026) |
| Téléchargement automatisé (House) | ✅ | PDF & index `ptr_index_{année}.csv` 2013–2026, 100 % succès |
| Pipeline d'extraction LLM (digital) | ✅ | Parsing PDF lisibles, rendement 99–100 % |
| Pipeline d'extraction LLM (OCR scans) | 🟡 | Claude Vision validée ; **deskew + validation honnête faits sur échantillon** ; scaling 547 restant |
| **Semaine 2 — nettoyage, validation, table finale** | | |
| Réconciliation tickers | 🟡 | Passe LLM nom→ticker (dict + LLM `is_equity`) : House 90 %, **Sénat 67 %→71,4 %** (reliquat = actifs non cotés, structurel) |
| Normalisation noms / identité déclarant | ✅ | Rattachement `BioGuideID` 100 % (House & Sénat) |
| Déduplication & règles documentées | ✅ | Dédup *per-lot* canonique, règles écrites |
| Validation qualité (dates, montants, couverture) | 🟡 | Quiver honnête (nous ≥ Quiver) ; **OCR : tolérance date ±3 j + `date_delta_days`** ; rapport qualité global à formaliser |
| Table finale — 12 champs garantis | 🟡 | **Sénat toutes_annees : 12/12** (`sector_gics`+`etf_proxy` ajoutés, secteur 62,1 %) ; House toutes_annees encore 10/12 |
| Métadonnées (chambre, parti, comités) | 🟡 | Présents via *congress-legislators* ; **snapshot actuel**, pas *point-in-time* |
| Mapping sectoriel GICS → ETF Ramify | 🟡 | `sector_enrich.py` (yfinance + repli LLM, SPDR Select Sector) appliqué **Q1 + Sénat toutes_annees** ; reste House toutes_annees + univers ETF Ramify final |
| Pipeline incrémental (mise à jour testée) | 🔴 | Non démontré |
| **Semaines 3–4 — stratégie & backtest** | | |
| Stratégie V1 — actions directes | 🔴 | Règle entrée/sortie spécifiée, non implémentée |
| Stratégie V2 — ETF sectoriels | 🔴 | Dépend du mapping GICS |
| Sélection annuelle des K congressmen | 🔴 | Critère (Sharpe / comités) à coder |
| Backtest sur framework Ramify | 🔴 | Non commencé |

---

## 3. Checklist détaillée

### 3.1 Semaine 1 — exploration, sourcing, architecture

- ✅ **Cartographie des sources primaires.** House via `disclosures-clerk.house.gov` (PDF + index XML) ; Sénat via `efts.senate.gov` (PDF souvent scannés) ; Quiver & Capitol Trades en *fallback*/validation.
- ✅ **Audit de couverture.** 14 années (2013–2026) : **37 445 dépôts**, **8 248 PTR**. Quiver : 113 673 transactions (licence non commerciale ⇒ validation/R&D uniquement).
- ✅ **Décision d'architecture documentée.** (1) House Clerk primaire, (2) Sénat eFD, (3) Quiver = fallback/validation 2014+, (4) Capitol Trades = vérification manuelle.
- ✅ **Téléchargement automatisé House** (PDF + index par année), stockage organisé, jamais re-téléchargé.
- ✅ **Pipeline LLM — volet digital.** Extraction structurée (*tool_use*, sans échec silencieux) ; montant = **midpoint**.
- 🟡 **Pipeline LLM — volet OCR (scans).** Claude Vision sur formulaires scannés. *Census* visuel complet des **547 PDF** (A tapé droit 13,5 %, B tapé tourné 58,9 %, C manuscrit 27,6 %). **Échantillon 70 docs traité avec deskew** (cf. §4 OCR). *Reste* : scaler aux 547 et fusionner dans les tables `_FINAL`.
- ✅ **Sénat digital 2020→2026.** eFD accédé **sans contournement** (agrément CSRF accepté une fois + scraping poli, pas de Playwright) : **7 161 txns**, 805 PTR, identité 100 %, couverture Quiver 98-100 %/an, **0 vrai raté** (audit adversarial). `senate/digital.py` + `data/senate/`. *Reste* : rapports **papier** (130, ~14 %) = chantier OCR séparé (Quiver-aveugle au papier).

### 3.2 Semaine 2 — nettoyage, validation, table finale

- 🟡 **Réconciliation tickers.** Passe LLM nom→ticker (dictionnaire nom→ticker + LLM filtré `is_equity`, cache versionné) : House 46 %→90 %, **Sénat 67 %→71,4 %** (`ticker_resolve.py`, dict +197 · llm +190). Manquants **conservés avec flag** (`ticker_source`), pas jetés. Le reliquat Sénat (28,6 %) est **structurellement non coté** (munis/Treasuries/privé, ~60 % du sans-ticker) → pas un défaut de la passe. Quiver ne sert qu'à *auditer*.
- ✅ **Identité des déclarants.** Rattachement `BioGuideID` **100 %** ; collisions homonymes résolues.
- ✅ **Déduplication.** Canonique *per-lot* (préserve les lots identiques intra-PTR via `occurrence_index`) ; dédup inter-sources seulement.
- 🟡 **Validation qualité systématique.** Méthode Quiver **honnête** (per-lot, par `BioGuideID`, exclusion papier des deux côtés) : **nous ≥ Quiver** sur ~95 % des déclarants/an, vrais-absents 0,03 %, tous expliqués. **OCR ajouté** : tolérance de date ±3 j (Quiver bruite ±1-2 j) + colonne `date_delta_days` graduée. *Reste* : rapport qualité synthétique (cohérence dates, délai 45 j, distributions, couverture/congressman, taux sans sortie).
- 🟡 **Table finale — 12 champs garantis.** **Sénat toutes_annees = 12/12** (`sector_gics` 62,1 % + `etf_proxy` ajoutés via `sector_enrich`, jointure sur ticker). House toutes_annees encore 10/12 (même branchement à reporter).
- 🟡 **Métadonnées de sélection.** `committee_membership` + `committees_key_flag` via *congress-legislators*. **Limite** : snapshot *actuel*, pas *point-in-time*.
- 🔴 **Mapping sectoriel GICS → ETF.** Secteur GICS dominant par ticker (yfinance/OpenBB) puis ETF sectoriel Ramify. À trancher : univers ETF, multi-secteurs.
- 🔴 **Pipeline incrémental.** Mise à jour simulée sans relancer l'extraction ; format de stockage final (CSV / SQLite / Parquet).

### 3.3 Semaines 3–4 — stratégie & backtest *(spécification cible, à implémenter)*

- 🔴 **Entrée/sortie.** Entrée à la `disclosure_date` d'un *Purchase* ; sortie à la `disclosure_date` du *Sale* du même déclarant/ticker, sinon sortie forcée à +12 mois.
- 🔴 **V1 — actions directes** (signal brut, track records individuels).
- 🔴 **V2 — ETF sectoriels** (même logique, instrument substitué via mapping GICS).
- 🔴 **Sélection annuelle des K congressmen** (K ∈ [4,10], min. 10 trades, Sharpe / alpha vs SPX ; filtre comités Finance/Défense/Renseignement sur ≥ la moitié des K).
- 🔴 **Backtest annoté sur framework Ramify**, V1 puis V2.

---

## 4. Couverture de la donnée (concret)

| Année | House digital | House OCR (scans) | Sénat digital |
|---|:---:|:---:|:---:|
| 2013–2015 | 🔴 | 🔴 | 🔴 |
| 2016–2019 | 🔴 (lot 2) | 🔴 | 🔴 |
| 2020 | ✅ 6 886 | 🟡 | ✅ 1 706 |
| 2021 | ✅ 5 457 | 🟡 | ✅ 1 098 |
| 2022 | ✅ 3 601 | 🟡 | ✅ 919 |
| 2023 | ✅ 4 161 | 🟡 | ✅ 1 062 |
| 2024 | ✅ 2 694 | 🟡 | ✅ 946 |
| 2025 | ✅ 7 577 | 🟡 | ✅ 943 |
| 2026 | ✅ 2 300 | 🟡 | ✅ 487 |
| **Total digital 2020–2026** | **32 676** txns | | **7 161** txns |

> **Sénat 2020→2026** (`senate/` + `data/senate/`) : **8 841 txns FINAL** = digital 7 161 (805 PTR,
> couverture Quiver 98-100 %/an, **0 vrai raté**, audit adversarial 7 agents) **+ OCR papier 1 680**
> (130 PTR Blumenthal/Boozman/Burr/Feinstein/Fetterman, validé hors-Quiver : régression 92 +
> spot-check + dates 98,8 % en période). 64 sénateurs, identité 100 %. 8 245 txns uniques (596
> amendements cross-année). Reste : Sénat 2013-2019, passe ticker LLM sur OCR.

**Deux pilotes Q1 2025 (archivés lors de la consolidation — récupérables : tag `archive/pre-cleanup-2026-06-26` + tarball `Jupiter_legacy`) :**
- **House Q1 2025** (ex-`0 HOUSE/2025_test/`) : **2 272** transactions, 56 déclarants — pilote validé vs Quiver (électronique 99,9 %). Logique absorbée dans `house/` + `congress_core/`.
- **Sénat Q1 2025** (ex-`1 SENAT/senat_2025_test/`) : **283** transactions, 17 sénateurs — identité 100 %, nous ≥ Quiver. Logique absorbée dans `senate/` + `congress_core/`, référentiel dans `data/senate/reference/`.

### OCR House — état au 2026-06-25 (désormais `house/` + `data/house/`)

**Politique : livrable = clusters A+B (tapés). Le manuscrit C est une catégorie CONSERVÉE mais NON EXÉCUTÉE par défaut** (27,6 % du corpus ; dates manuscrites peu fiables), avec **récupération ciblée** des 3 déposants à forte perte (cf. cross-val ci-dessous). Échantillon de mesure = **56 docs A+B** (70 − 14 C).

| Indicateur | Valeur | Note |
|---|---:|---|
| Transactions OCR (A+B) | 3 876 | C exclu |
| Couverture `ticker` | 80 % | explicit + dict digital + passe LLM |
| Concordance Quiver A+B (deskew + tol. ±3 j) | **69,0 %** | *65,4 % avec C ; 59,7 % avant deskew/tol.* |
| — cluster A tapé droit | 79,9 % | |
| — cluster B tapé tourné | 62,4 % | |
| `date_confidence` plausible / implausible | 94 % / 6 % | flag indépendant de Quiver |

**Trois correctifs livrés :**
1. **Validation honnête** — tolérance de date ±3 j (Quiver bruite ±1-2 j) + colonne `date_delta_days` graduée.
2. **Deskew** — orientation par pré-passe Vision « montage 4-rotations » (le modèle *choisit* l'image droite), **page par page** (docs *mixed*), redressement PIL avant extraction.
3. **Politique A+B + flag `date_confidence`** — cluster C non exécuté par défaut (catégorie conservée/tracée au census, récupération ciblée de 3 filers) ; flag = `implausible` si date hors fenêtre légale (après dépôt ou >75 j avant), qui attrape les dates **aberrantes** (24 % des dates fausses, 1 % faux positifs) sans certifier le reste.

> ⚠️ **Constat clé.** Le deskew améliore l'**extraction** et les **tickers** mais **ne corrige PAS les dates** : ~5 % de confusion d'année persistent sur images droites. **Les erreurs de date = ambiguïté OCR intrinsèque, pas la rotation.** Une fois C retiré, la précision-date par année grimpe (2020 : 0,54 → **0,90**) → **découper par cluster, pas par année** (2022/2024 sont les pires, pas les plus vieilles).

> 🔎 **Cross-validation C ↔ Quiver (ne pas l'abandonner pour autant).** Si on n'exécute pas C, Quiver a **~195–203 transactions distinctes** (déposants C) qu'on n'a pas (le brut 267 était gonflé ~25 % par les doublons Quiver), mais **~99 % tiennent à 3 déposants** quasi sans digital : **Schrader, Lamborn, Harshbarger**. 17/30 filers C = 0 trade Quiver. → **Récupération ciblée** de ces 3 filers (`FILERS_C_A_RECUPERER`, ~47 docs) capte l'essentiel ; le reste reste non exécuté avec flag. C est **conservé comme catégorie**, jamais supprimé.

**Reste sur l'OCR :** scaler aux PDF **A+B** + **récupération ciblée des 3 filers C** (Schrader/Lamborn/Harshbarger), fusionner dans les tables `_FINAL` en propageant `date_confidence`.

### Remplissage des 12 champs obligatoires (pilotes figés)

| Champ obligatoire | House Q1 2025 | Sénat Q1 2025 |
|---|:---:|:---:|
| `declarant_name` | 100 % | 100 % |
| `chamber` | 100 % | 100 % |
| `party` | 100 % | 100 % |
| `committee_membership` | 90 % | 76 % |
| `transaction_date` | 100 % | 100 % |
| `disclosure_date` | 100 % | 100 % |
| `ticker` | 90 % | 67 % |
| `sector_gics` | **absent** | **absent** |
| `etf_proxy` | **absent** | **absent** |
| `operation_type` | 100 % | 100 % |
| `amount_midpoint` | 100 % | 100 % |
| `asset_type` | 97 % | 100 % |

Les champs < 100 % (`ticker`, `committee_membership`) = actifs non cotés / membres hors snapshot, **flaggés, pas perdus**. Les deux champs **absents** (`sector_gics`, `etf_proxy`) sont le verrou principal de la table finale.

---

## 5. Chemin critique — ce qui reste, par priorité

1. **Mapping sectoriel GICS → ETF** (🟡) — *bloquant pour la table finale ET la V2*. Fait pour **Q1 + Sénat toutes_annees** (`sector_enrich.py`) ; **reste à brancher sur House** (FINAL 81 646 lignes `data/house/`, OCR scalé — simple enrichissement additif, ~2 468 tickers yfinance) + trancher univers ETF Ramify et cas multi-secteurs.
2. ~~**Finir l'OCR des scans**~~ ✅ **FAIT** — census complet A+B+C exécuté (546/547), fusionné dans `_FINAL` avec `date_confidence` ; dédup amendements corrigée (non destructrice) → **OCR 48 970 / FINAL 81 646**. **La date reste une limite intrinsèque** sur le manuscrit (flag `date_confidence`), pas corrigeable par rotation.
3. **Rapport qualité synthétique** (🟡) — graphiques & stats (cohérence dates, délai 45 j, distributions montants, couverture/congressman, taux sans sortie).
4. **Métadonnées point-in-time** (🟡) — historique des comités via `api.congress.gov` pour un backtest fidèle.
5. **Pipeline incrémental + format de stockage final** (🔴).
6. **Étendre la couverture** (🟡) — Sénat digital 2020→2026 **fait** (7 161 txns) ; restent House digital 2013–2019, Sénat 2013–2019 + OCR papier Sénat (~14 %).
7. **Stratégie V1 → V2 → sélection K → backtest Ramify** (🔴) — semaines 3–4.

---

## 6. Risques & points durs

- **OCR manuscrit (cluster C, 27,6 %) — non exécuté, conservé.** Catégorie gardée (census/cache), pas extraite par défaut (dates manuscrites peu fiables). Cross-val Quiver : perte réelle mais concentrée (~195–203 trades, ~99 % sur 3 filers) → récupération ciblée, pas un abandon. 17/30 filers C = 0 trade Quiver.
- **Dates OCR = ambiguïté intrinsèque.** Confirmé par le deskew : redresser ne corrige pas la lecture des chiffres de date (~5 % de confusion d'année résiduelle). Limite de fond, pas un bug. Mitigation = flag `date_confidence` (écarte les aberrations, pas le bruit jour/mois).
- **Comités non point-in-time.** Le snapshot actuel fausse un filtre de sélection appliqué à des années passées.
- **Licence Quiver non commerciale.** R&D / validation uniquement, jamais comme source de remplissage.
- **Sénat historique.** CSRF + Akamai non contournés ; 52 sénateurs hors fenêtre de rétention.
- **Multi-secteurs en V2.** Une entreprise à cheval sur plusieurs GICS demande une règle explicite de proxy ETF.
- **Pièges de backtest** (De Prado) : ne pas surinterpréter une sélection sur performance passée (overfitting), peu d'observations par personne (Grinold–Kahn).

---

*Statut reflétant la structure consolidée : `congress_core/` + `house/` + `senate/` + `data/` (les anciens dossiers `0 HOUSE/` · `1 SENAT/` · `_archive/` ont été archivés — tag `archive/pre-cleanup-2026-06-26` + tarball `Jupiter_legacy`).*
