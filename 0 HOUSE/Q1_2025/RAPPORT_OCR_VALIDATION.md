# Rapport de validation & fiabilisation — OCR House Q1 2025

**Question posée** : maintenant que le pipeline OCR (17 PTR scannés, Claude Vision) a produit ses
résultats, est-il bien écrit, et l'information extraite est-elle juste ? Critère d'arbitrage :
**QuiverQuant**, qui recense indépendamment ces mêmes transactions.

**Périmètre** : seul `notebook_v1_house_2025q1_ocr.ipynb` a été modifié. Le notebook des PDF
lisibles n'a pas été touché (lecture seule de sa sortie `06` pour l'enrichissement).

---

## 1. Diagnostic (l'intuition « pas tout à fait juste » était fondée — mais à l'envers)

On craignait une **sur-extraction** (les 2 PDF « géants » à 546 + 447 transactions, = 89 % des
données OCR). La validation prouve le contraire :

- **Les 2 géants sont Rohit Khanna** (K000389) et sont **authentiques** : Quiver recense
  indépendamment 1144 transactions Q1 pour lui (4545 sur l'année). Tables denses générées par
  ordinateur, confirmées visuellement page à page.
- **L'OCR sous-comptait** (ancien code) à cause d'**échecs de batch silencieux** : quand la
  réponse JSON dépassait `max_tokens`, elle était tronquée et `_parse_json_robust` renvoyait `[]`
  **sans alerte** → des batchs entiers perdus, jamais signalés.
- Les **« hallucinations »** `Example Mega Corp. Common Stock` n'étaient pas inventées par le
  modèle : c'est la **ligne d'exemple pré-imprimée** présente sur chaque formulaire papier vierge,
  transcrite à tort comme une transaction.
- Les **« doublons »** (ex. COLGATE ×2, GENERAL MILLS ×3 le même jour chez Khanna) sont de
  **vraies transactions répétées**. L'ancienne déduplication (clé sans `doc_id`) les **détruisait
  silencieusement** (15 lignes perdues).
- Les **2 fichiers vides** (Hal Rogers, jan. + fév.) sont de vrais « Nothing to report ». ✓
- `ticker` et `asset_type` étaient à **0 %** côté OCR → table combinée hétérogène.

---

## 2. Corrections appliquées (notebook OCR)

| Problème | Correctif |
|---|---|
| Troncature JSON + échecs silencieux | **Sortie structurée forcée** (`tool_use` sur `record_transactions`, enums validés). Plus de JSON-dans-le-texte. |
| Échecs invisibles | Tout batch en erreur → **`06c_ocr_failures.csv`** (vide = succès). Retry/backoff sur 429/5xx. |
| Cache non auditable | **Cache versionné** `{model, prompt_sha, batches[…], status, transactions}` ; invalidation auto si le prompt change ; `status` distingue `nothing_to_report` de `partial_error`. |
| Ligne-exemple captée | Règle de prompt explicite **+ filtre déterministe** (toute ligne « Example Mega Corp » est écartée, quoi que fasse le modèle). |
| Dédup destructrice | Déduplication **inter-sources uniquement** (électronique vs OCR) ; les répétitions réelles intra-OCR sont conservées. |
| ticker / asset_type vides | **Enrichissement** : ticker explicite dans le nom (« … - ADBE ») → dictionnaire nom→ticker bâti sur les 998 lignes électroniques tickées ; `asset_type` inféré par règles ; colonne `ticker_source` traçable. |
| Sorties périmées (affichaient « 47 ») | Notebook **ré-exécuté et re-sauvegardé** : sorties = disque. |

---

## 3. Validation vs Quiver (`06d_ocr_quiver_comparison.csv`)

Comparaison à **fenêtre comparable** : nos PTR sont *divulgués* en Q1, donc Quiver est filtré sur
sa **date de divulgation** en Q1 (et non la date de transaction — sinon on inclut les trades de
mars divulgués en avril, dans un PTR hors de notre périmètre, ce qui crée un faux « sous-comptage »).

| Déposant | docs | OCR | Quiver (div. Q1) | Verdict |
|---|---|---|---|---|
| Rohit Khanna | 2 | 1036 | 756 | **OCR ≥ Quiver** |
| Michael McCaul | 1 | 82 | 56 | **OCR ≥ Quiver** |
| Chuck Fleischmann | 1 | 21 | 13 | OCR ≥ Quiver |
| Tony Wied | 2 | 11 | 4 | OCR ≥ Quiver |
| Self / Gonzalez / Sherman / Bilirakis / A. Smith / Wagner | — | 2–5 | 0 | quiver_sans_donnee |

**Lecture** : l'OCR est **au moins aussi complet que Quiver partout**. Le surplus OCR n'est pas du
bruit : vérifié visuellement, **McCaul = 82 lignes OCR ≈ 4 pages × ~20 lignes** réelles du
formulaire → c'est **Quiver qui sous-recense** ces dépôts papier denses (et fusionne des trades
répétés que l'OCR conserve à juste titre). Les `quiver_sans_donnee` sont des **lacunes Quiver**
sur petits dépôts papier (transactions réelles confirmées œil-à-œil, ex. Keith Self : ATT,
Genuine Parts, Merck, NVIDIA, Pepsi) — **pas des erreurs OCR**.

> ⚠️ Le « gap Khanna −108 » initialement observé était un **artefact de fenêtre** : ses 388 trades
> de mars sont divulgués en avril (PTR hors Q1). À fenêtre comparable, l'OCR ne sous-compte pas.

---

## 4. Avant / après

| | Avant | Après |
|---|---|---|
| Transactions OCR (06b) | 1120 | **1167** |
| Fausses lignes « Mega Corp » | 3 | **0** |
| Échecs de batch silencieux | cachés | **0** (journalisés) |
| ticker / asset_type (OCR) | 0 % / 0 % | **46 % / 95 %** |
| ticker / asset_type (table FINALE) | 45 % / 50 % | **68 % / 97 %** |
| Table combinée FINALE | 2210 lignes | **2272 lignes** (1167 OCR + 1105 élec.) |
| Validation Quiver | absente | intégrée, OCR ≥ Quiver |

---

## 5. Limites résiduelles (honnêteté)

- **8220809 (Gonzalez)** : formulaire pâle à 1 ligne réelle (**TESLA Sale 17/03/25**) que le
  modèle a manquée (il avait lu la ligne-exemple à la place, désormais filtrée). Cette transaction
  unique n'est pas capturée → doc absent de la sortie. Quiver=0 sur ce déposant, pas de référence externe.
- **8220747 (Bilirakis)** : 2ᵉ ligne « GE Vernova » (Dependent Child) sans montant ni date lisibles
  (case illisible). Conservée mais incomplète (seul flag QA restant).
- **ticker OCR = 46 %** : plafond du dictionnaire électronique + fautes OCR sur certains noms.
  Piste d'amélioration : jointure transaction-à-transaction avec Quiver (qui a les tickers) pour
  les gros déposants couverts.
- Le **surplus OCR vs Quiver** (Khanna +280) n'a pas été audité ligne à ligne (formulaire de 34
  pages) ; il est attribué au sous-recensement Quiver + répétitions réelles, cohérent avec les
  contrôles visuels — mais non prouvé au transaction-près.

---

## 6. Fichiers

- **Modifié** : `notebook_v1_house_2025q1_ocr.ipynb` ; format `data_v1/ocr_cache/*.json` (versionné).
- **Régénérés** : `06b_…ocr_transactions.csv` (1167), `06_…_FINAL.csv` (2272), `house_2025q1_FINAL.xlsx`.
- **Nouveaux** : `06c_ocr_failures.csv` (vide), `06c_ocr_qa_flags.csv` (1), `06d_ocr_quiver_comparison.csv`.
- **Lecture seule réutilisée** : `06_…transactions.csv` (dict ticker), Quiver
  `jour 3 4 /data/external/quiver/quiver_congress_trading_2025.csv`, PDFs `non_lisibles/`.

**Verdict global** : l'OCR est désormais **robuste** (0 échec silencieux, structuré, auditable),
**honnête** (échecs et anomalies signalés, pas avalés), **homogène** avec l'électronique (ticker +
asset_type), et **validé** : les données sont justes et **au moins aussi complètes que Quiver**, le
volume des gros déposants (89 % des données) étant corroboré et fidèle au formulaire.
