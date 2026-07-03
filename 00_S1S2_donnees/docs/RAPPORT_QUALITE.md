# Rapport qualité — Données de trading du Congrès américain
> Chambre des représentants + Sénat · 2014–2026 · généré par `python -m common.quality` (lecture seule des tables FINAL, aucun appel API) · Quiver Quantitative = vérité-terrain externe, **jamais réinjectée**. *Les % sont arrondis à 0,1 pt ; une somme de colonnes peut afficher 100,1.*

## Résumé exécutif

- **Périmètre** — 169 000 transactions uniques de membres élus (House 151 989 + Sénat 17 011), 2014–2026, en **4 sous-corpus** (chambre × voie d'acquisition : électronique déterministe / scan OCR).
- **Complétude vs Quiver** *(§6)* — dans notre fenêtre, on retrouve **93.5 % (House) / 92.1 % (Sénat)** des trades Quiver au niveau (déposant, ticker, sens). Le **trou coté est minuscule** — ≤ 31 House / 0 Sénat au niveau ticker (borne haute) ; une mesure COMPLÉMENTAIRE au trade daté (§6.5, clé différente — les deux comptes ne s'emboîtent pas) confirme **27 House / 11 Sénat vrais trous** ; le reste du résidu est de l'OCR récupérable ou du hors-périmètre.
- **On est plus complet que Quiver** — **+26524 combinaisons cotées (déposant, ticker, sens)** qu'on a et que Quiver n'a pas, contre 38 trous inverses → **sur-ensemble** de Quiver. ⚠ Cette avance est **inégale dans le temps** : bien corroborée après ~2017, elle repose avant sur des trades réels que **Quiver (mince pré-2017) ne peut pas confirmer** — détail par année en §6.2.
- **Les « écarts » de date ne sont pas des erreurs** — la réconciliation 1-à-1 (§6.3) montre que l'essentiel est du « nous-seul » (Quiver n'a pas le trade) ; seuls 545 candidats House (même déclaration) méritent l'œil, et le vrai contrôle des dates reste l'audit PDF (§3).
- **Données propres** — identité rattachée à 100.0 %, dates cohérentes 99.8 %, délai de divulgation médian 27 j, montants renseignés 99.4 %. *Anti-look-ahead : tout usage aval (backtest) entre sur `disclosure_date` (date de dépôt imprimée, fiable), jamais sur la `transaction_date` OCR — quelques dates OCR restent imprécises (§3).*

*Plan : §1 construction & validation · §2 composition & complétude · §3 qualité des dates · §4 montants · §5 activité & concentration · §6 complétude vs Quiver (vérité-terrain).*

## 1. Construction & validation du corpus

Avant toute statistique, voici **comment le corpus est construit**, dans l'ordre :

1. **Sources** — déclarations officielles : Chambre (*PTR*) et Sénat (*eFD*), chacune en deux voies — **électronique** (formulaire structuré, lecture déterministe) et **papier scanné** (PDF → **OCR** par modèle de vision).
2. **Extraction** — une ligne = une transaction (membre, date, actif, sens, fourchette de montant, détenteur).
3. **Enrichissement** — ticker (explicite dans la source · repris de l'électronique · résolu par LLM), secteur GICS (yfinance · LLM), identité (`bioguide_id`), ancienneté.
4. **Déduplication cross-année** — une même transaction re-divulguée une autre année (amendement, rapport annuel) ne compte qu'**une fois** (clé naturelle + rang d'occurrence).

**Réconciliation — des lignes brutes aux transactions uniques** (c'est notre corpus, pas Quiver) :

| chambre | lignes brutes | re-divulgations (dédup) | transactions uniques |
| --- | --- | --- | --- |
| house | 152081 | 92 | 151989 |
| senate | 18839 | 1828 | 17011 |
| TOTAL | 170920 | 1920 | 169000 |
*lignes brutes = FINAL concaténé 2014–2026 · re-divulgations = doublons cross-année retirés · transactions uniques = le corpus analysé dans tout ce rapport*

### Couverture vs l'univers officiel (House Clerk)

Chaque index annuel `{Y}FD.xml` du Clerk liste TOUS les dépôts de l'année ; les PTR ont `FilingType='P'`. Depuis l'audit du 2026-07-03, l'index est l'autorité d'appartenance (plus de filtre par fenêtre de dépôt — l'ancien filtre perdait 205 PTR déposés après le 31/12) : **100 % des PTR officiels sont traités** — parsés, OCRisés, ou écartés par une règle écrite (manuscrits, cf. §6.6).

| année | PTR officiels | avec transactions | gated manuscrit | sans txn retenue | couverts % |
| --- | --- | --- | --- | --- | --- |
| 2014 | 708 | 613 | 94 | 1 | 100.0 |
| 2015 | 728 | 627 | 97 | 4 | 100.0 |
| 2016 | 765 | 651 | 110 | 4 | 100.0 |
| 2017 | 801 | 708 | 82 | 11 | 100.0 |
| 2018 | 830 | 752 | 68 | 10 | 100.0 |
| 2019 | 683 | 616 | 52 | 15 | 100.0 |
| 2020 | 733 | 688 | 35 | 10 | 100.0 |
| 2021 | 680 | 653 | 15 | 12 | 100.0 |
| 2022 | 624 | 602 | 14 | 8 | 100.0 |
| 2023 | 460 | 447 | 2 | 11 | 100.0 |
| 2024 | 451 | 440 | 5 | 6 | 100.0 |
| 2025 | 515 | 503 | 6 | 6 | 100.0 |
| 2026 | 274 | 268 | 2 | 4 | 100.0 |
| TOTAL | 8252 | 7568 | 582 | 102 | 100.0 |
*PTR officiels = FilingType『P』 de l'index du Clerk · avec transactions = docs présents dans le FINAL de l'année · gated manuscrit = cluster C du census hors exceptions (politique §6.6, listes rejouables) · sans txn retenue = vides réels (« nothing to report »), amendements sans lignes ou échecs documentés (`05_parse_failures`). Sénat : pas d'index public re-vérifiable sans re-scraping eFD — le census interne fait foi (25 dépôts sans transaction tous motivés dans `06d_docs_sans_transaction.csv`).*

### Validation & reproductibilité

Tout est **rejouable hors-ligne** (lecture seule des tables FINAL, **0 appel API**), adossé à trois filets automatiques :

- **Golden octet-à-octet** — 368 tables CSV figées par SHA256 (230 House + 138 Sénat), rejouées à **zéro écart** (`tests/regression/check_golden.py`, `senate_check_golden.py`).
- **Invariants porteurs** — pour chaque chambre `digital + OCR = FINAL`, identité rattachée à **100.0 %**, 367 bioguides (House) / 78 (Sénat) recomptés (`tests/regression/audit_metrics.py`).
- **Transformations déterministes** — 11 tests reproduisent chaque étape (clé naturelle, montants, tickers, identité, ancienneté, cache Vision) depuis les colonnes figées.

### Les quatre sous-corpus

Toute la suite distingue **quatre familles** (chambre × voie), car leur qualité et leur composition diffèrent :

| sous-corpus | n | part % |
| --- | --- | --- |
| House électronique | 58728 | 34.8 |
| House OCR | 93261 | 55.2 |
| Sénat électronique | 13026 | 7.7 |
| Sénat OCR | 3985 | 2.4 |
*sous-corpus = chambre × voie (électronique déterministe / scan OCR) · n = transactions uniques · part % du total*

## 2. Composition & complétude

**Ce que contient le corpus** (opérations, détenteur, familles d'actifs), puis **à quel point les champs sont remplis**.

### Sens des opérations

| sous-corpus | n | achat % | vente % | échange % | autre % |
| --- | --- | --- | --- | --- | --- |
| House électronique | 58728 | 50.4 | 48.6 | 1.0 | 0.0 |
| House OCR | 93261 | 52.2 | 47.3 | 0.5 | 0.0 |
| Sénat électronique | 13026 | 50.2 | 48.8 | 1.0 | 0.0 |
| Sénat OCR | 3985 | 56.4 | 43.0 | 0.6 | 0.0 |
*achat = `operation_type` contient « Purchase » · vente = contient « Sale » (**inclut Sale (Partial) et (Full)**) · échange = « Exchange » · autre = reste*

![Mix achat/vente par sous-corpus](quality/mix_operations_par_corpus.png)

### Détenteur déclaré

| sous-corpus | n | perso % | conjoint % | joint % | enfant % | autre % |
| --- | --- | --- | --- | --- | --- | --- |
| House électronique | 58728 | 49.3 | 20.4 | 26.7 | 3.6 | 0.0 |
| House OCR | 93261 | 10.3 | 47.9 | 13.6 | 28.2 | 0.0 |
| Sénat électronique | 13026 | 16.8 | 38.7 | 42.1 | 2.4 | 0.0 |
| Sénat OCR | 3985 | 48.8 | 49.5 | 1.5 | 0.3 | 0.0 |
*titulaire du compte : perso = Self · conjoint = Spouse/SP · joint = Joint/JT · enfant = Dependent/Child/DC · autre = reste ou non déclaré*

### Familles d'actifs

Le non-coté (oblig. d'État, munis, obligations) domine l'OCR du Sénat :

| sous-corpus | n | action % | option % | oblig. État % | muni % | oblig. corp. % | fonds % | autre % | manquant % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 58728 | 58.5 | 1.2 | 4.1 | 0.0 | 0.0 | 0.0 | 4.9 | 31.3 |
| House OCR | 93261 | 79.2 | 0.0 | 0.8 | 0.0 | 0.4 | 3.2 | 0.3 | 16.2 |
| Sénat électronique | 13026 | 73.0 | 4.7 | 0.0 | 7.7 | 3.0 | 0.0 | 6.5 | 5.1 |
| Sénat OCR | 3985 | 40.4 | 0.0 | 0.0 | 0.7 | 2.2 | 0.0 | 41.2 | 15.5 |
*familles d'`asset_type` : action = Stock · option · oblig. État = Gov/Treasury · muni = Municipal · oblig. corp. = Bond · fonds = Fund/ETF · manquant = vide*

![Mix de types d'actifs par sous-corpus](quality/mix_actifs_par_corpus.png)

### Couverture des champs enrichis (taux de remplissage)

| sous-corpus | n | ticker % | secteur % | ETF % | commission % | identité % | ancienneté % | montant renseigné % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 58728 | 83.8 | 77.7 | 77.7 | 54.8 | 100.0 | 100.0 | 100.0 |
| House OCR | 93261 | 84.3 | 81.1 | 81.1 | 80.8 | 100.0 | 99.9 | 98.9 |
| Sénat électronique | 13026 | 84.1 | 77.8 | 77.8 | 53.0 | 100.0 | 99.9 | 100.0 |
| Sénat OCR | 3985 | 57.4 | 46.2 | 46.2 | 64.9 | 100.0 | 100.0 | 99.4 |
*% de lignes où le champ est renseigné · identité = rattachée à un `bioguide_id` · montant renseigné = `amount_midpoint` non vide · ticker/secteur/ETF vides = actif non coté (normal, pas un défaut)*

### Secteurs & origine des champs résolus

| sous-corpus | n | secteur renseigné % | ETF % | top 3 secteurs |
| --- | --- | --- | --- | --- |
| House électronique | 58728 | 77.7 | 77.7 | Information Technology 18%, Financials 14%, Health Care 13% |
| House OCR | 93261 | 81.1 | 81.1 | Information Technology 17%, Financials 15%, Health Care 13% |
| Sénat électronique | 13026 | 77.8 | 77.8 | Information Technology 19%, Financials 14%, Health Care 11% |
| Sénat OCR | 3985 | 46.2 | 46.2 | Financials 16%, Industrials 15%, Health Care 12% |
*secteur renseigné % / ETF % = taux de remplissage (vide = non coté) · top 3 = secteurs GICS dominants*

**Origine du ticker** (`ticker_source`) :

| sous-corpus | n | dico élec % | LLM % | nom d'actif % | récupéré % | explicite % | aucune % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 58728 | 0.0 | 0.0 | 0.0 | 3.2 | 80.5 | 16.2 |
| House OCR | 93261 | 35.9 | 40.2 | 0.0 | 0.7 | 7.5 | 15.7 |
| Sénat électronique | 13026 | 2.6 | 3.0 | 1.9 | 0.0 | 76.7 | 15.9 |
| Sénat OCR | 3985 | 21.0 | 25.7 | 0.0 | 0.0 | 10.6 | 42.6 |
*dico élec = repris de l'électronique · LLM = résolu par LLM · nom d'actif = déduit du nom d'actif · récupéré = rendu par la passe nom→ticker vérifiée (cf. §6.2) · explicite = déjà présent dans la source · aucune = non résolu*

**Origine du secteur** (`sector_source`) :

| sous-corpus | n | yfinance % | LLM % | manuel % | aucune % |
| --- | --- | --- | --- | --- | --- |
| House électronique | 58728 | 66.6 | 11.1 | 0.2 | 22.0 |
| House OCR | 93261 | 69.2 | 11.9 | 0.1 | 18.8 |
| Sénat électronique | 13026 | 62.7 | 14.9 | 0.8 | 21.6 |
| Sénat OCR | 3985 | 32.8 | 13.5 | 0.6 | 53.2 |
*yfinance = base factuelle · LLM · manuel = correction d'audit · aucune*

![Volume par secteur GICS](quality/volume_par_secteur.png)

## 3. Qualité des dates

Trois questions, de la plus faible à la plus forte : les dates sont-elles **lisibles et cohérentes** (divulgation ≥ transaction) ? le **délai légal** (STOCK Act ~45 j) est-il respecté ? reste-t-il des **anomalies** ?

### Cohérence (`disclosure_date ≥ transaction_date`)

| chambre | n | dates exploitables % | cohérentes % | incohérentes | année aberrante | date manquante |
| --- | --- | --- | --- | --- | --- | --- |
| house | 151989 | 98.1 | 99.9 | 219 | 101 | 2916 |
| senate | 17011 | 99.8 | 99.7 | 55 | 0 | 38 |

**Par sous-corpus :**

| sous-corpus | n | dates exploitables % | cohérentes % | incohérentes | année aberrante | date manquante |
| --- | --- | --- | --- | --- | --- | --- |
| House électronique | 58728 | 100.0 | 99.9 | 69 | 4 | 0 |
| House OCR | 93261 | 96.9 | 99.8 | 150 | 97 | 2916 |
| Sénat électronique | 13026 | 100.0 | 99.9 | 9 | 0 | 0 |
| Sénat OCR | 3985 | 99.0 | 98.8 | 46 | 0 | 38 |
*dates exploitables = parseables (% du total ; le reste = OCR illisible) · cohérentes = divulgation ≥ transaction, **% parmi les exploitables** (dénominateur = exploitables, pas le total → ce % peut dépasser « dates exploitables % ») · incohérentes = divulgation AVANT transaction (amendement/antidaté) · année aberrante = année impossible (postérieure au dépôt, ou < 2012) · date manquante = illisible. ⚠ Colonnes NON additives : une même ligne peut cumuler « incohérente » ET « année aberrante » (le décompte disjoint est plus petit que la somme). Des transactions 2013–2019 sont légitimes (divulgations tardives).*

### Délai légal de divulgation (STOCK Act ~45 j)

| chambre | n dates valides | ≤45j légal % | 45–75j % | >75j % | négatif % | délai médian (j) |
| --- | --- | --- | --- | --- | --- | --- |
| house | 149073 | 87.3 | 6.3 | 6.2 | 0.1 | 27 |
| senate | 16973 | 86.9 | 3.0 | 9.8 | 0.3 | 24 |

**Par sous-corpus :**

| sous-corpus | n dates valides | ≤45j légal % | 45–75j % | >75j % | négatif % | délai médian (j) |
| --- | --- | --- | --- | --- | --- | --- |
| House électronique | 58728 | 83.5 | 5.0 | 11.3 | 0.1 | 28 |
| House OCR | 90345 | 89.8 | 7.1 | 2.9 | 0.2 | 27 |
| Sénat électronique | 13026 | 90.6 | 1.6 | 7.7 | 0.1 | 23 |
| Sénat OCR | 3947 | 74.5 | 7.7 | 16.6 | 1.2 | 31 |
*n dates valides = transactions dont le délai est CALCULABLE (les deux dates présentes et lisibles ; « valide » = mesurable, pas « juste ») · délai = divulgation − transaction (j) · ≤45 j = délai légal STOCK Act · 45–75 j = marge tolérée · >75 j = retard · négatif = anomalie (divulgation avant transaction), comptée dans n dates valides · délai médian en j*

![Délai de divulgation](quality/delai_divulgation.png)

### Divulgations les plus tardives (> 365 j)

| déposant | chambre | date txn | date divulg. | délai (j) | ticker | opération |
| --- | --- | --- | --- | --- | --- | --- |
| Jefferson Shreve | house | 2015-05-08 | 2025-06-22 | 3698.0 | DAL | Purchase |
| Jefferson Shreve | house | 2015-05-08 | 2025-06-22 | 3698.0 | DHR | Purchase |
| Mike Kelly | house | 2007-08-31 | 2017-09-27 | 3680.0 |  | Purchase |
| Diane Black | house | 2006-02-06 | 2015-03-27 | 3336.0 |  | Sale |
| Richard W. Allen | house | 2017-02-03 | 2023-08-10 | 2379.0 |  | Purchase |
| Richard W. Allen | house | 2017-02-13 | 2023-08-10 | 2369.0 | O | Sale |
| Richard W. Allen | house | 2017-03-23 | 2023-08-10 | 2331.0 | BBT | Sale |
| Richard W. Allen | house | 2017-03-23 | 2023-08-10 | 2331.0 | BBT | Sale (Partial) |
| Richard W. Allen | house | 2017-04-27 | 2023-08-10 | 2296.0 | COST | Purchase |
| Richard W. Allen | house | 2017-04-27 | 2023-08-10 | 2296.0 | XOM | Sale |
| Richard W. Allen | house | 2017-05-16 | 2023-08-10 | 2277.0 | FDX | Purchase |
| Richard W. Allen | house | 2017-05-16 | 2023-08-10 | 2277.0 | GE | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | COO | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | PCLN | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | DFS | Sale |
*délai (j) = divulgation − transaction · divulgations > 1 an après la transaction (souvent des amendements ou de vieux comptes régularisés)*

**Audit des anomalies (échantillon de 12 PDF re-lus à la source).** ~½ sont FIDÈLES : coquilles du **déposant lui-même** (un PTR imprime littéralement `01/35/22`), cellules vides ou parts de société sans date de transaction — on les transcrit sans les inventer. ~⅓ = **notre OCR** (mois/jour mal lu), corrigé à la lecture **quand le formulaire est lisible** (4 dates vérifiées, clé doc+date, figé inchangé). ~⅙ = **provenance** (hallucination OCR ou pièce jointe absente du PDF). **On ne fabrique aucune date** : les illisibles restent flaggées.

## 4. Montants (`amount_midpoint`)

Le montant = **midpoint** de la fourchette déclarée (les déclarations donnent des tranches, pas un chiffre exact). Vue par sous-corpus :

| sous-corpus | n | médiane $ | moyenne $ | P25_$ | P75_$ | P95_$ | volume total M$ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 58728 | 8000 | 59205 | 8000 | 32500 | 175000 | 3477.0 |
| House OCR | 93261 | 8000 | 44018 | 8000 | 32500 | 175000 | 4061.7 |
| Sénat électronique | 13026 | 8000 | 81666 | 8000 | 32500 | 175000 | 1063.8 |
| Sénat OCR | 3985 | 32500 | 301252 | 8000 | 175000 | 750000 | 1193.6 |
*médiane/moyenne/P25/P75/P95 en $ · volume total = Σ midpoint (M$) · midpoint = milieu de la fourchette déclarée*

![Composition par tranche de montant](quality/mix_montants_par_corpus.png)

*la plus petite tranche (≤ 15 k$, midpoint 8 000 $) domine → dès qu'elle dépasse 50 %, le P25 ET la médiane y tombent ensemble (cas House/Sénat élec). Sénat OCR < 50 % → médiane 32 500 ≠ P25 8 000.*

**Ensemble** — 167 989 montants renseignés · médiane 8 000 $ · moyenne 58 314 $ · P90 75 000 $ · max 75 000 000 $.

![Distribution des montants](quality/distribution_montants.png)

## 5. Activité & concentration

**Qui trade, à quel point l'activité est concentrée, et ce que deviennent les positions.**

### Concentration du volume

| sous-corpus | n déposants | HHI | Gini | top10 volume % |
| --- | --- | --- | --- | --- |
| House électronique | 309 | 432.4 | 0.873 | 57.6 |
| House OCR | 125 | 2561.1 | 0.953 | 94.7 |
| Sénat électronique | 75 | 943.7 | 0.826 | 79.5 |
| Sénat OCR | 14 | 2671.5 | 0.753 | 100.0 |

`HHI` ∈ [0, 10000] et `Gini` ∈ [0, 1] mesurent la concentration du volume par déposant (plus c'est haut, plus quelques déposants dominent).

![Concentration du volume (Lorenz)](quality/concentration_lorenz.png)

### Où va le volume

**Top tickers par volume estimé :**

| ticker | n trades | volume M$ |
| --- | --- | --- |
| MSFT | 1516 | 550.1 |
| AAPL | 1297 | 120.4 |
| FDX | 366 | 119.9 |
| ICE | 209 | 94.5 |
| BRP | 7 | 87.8 |
| MET | 222 | 77.9 |
| T | 594 | 69.7 |
| AMZN | 1026 | 60.8 |
| NVDA | 692 | 57.6 |
| WFM | 127 | 52.9 |
| BRK.B | 450 | 49.9 |
| BOKF | 25 | 44.9 |
| GOOGL | 913 | 43.8 |
| DFS | 114 | 43.5 |
| MMM | 270 | 43.3 |
*volume M$ = Σ midpoint des trades du ticker · n trades = nombre de transactions*

**Volume par secteur GICS :**

| secteur | n trades | volume M$ |
| --- | --- | --- |
| Information Technology | 22687 | 1236.8 |
| Financials | 19451 | 875.8 |
| Industrials | 16003 | 525.0 |
| Health Care | 17233 | 478.1 |
| Consumer Discretionary | 15551 | 434.2 |
| Communication Services | 10545 | 425.8 |
| Energy | 8618 | 351.7 |
| Consumer Staples | 9547 | 291.2 |
| Materials | 5700 | 124.3 |
| Real Estate | 4649 | 104.2 |
| Utilities | 2574 | 59.4 |
### Top déposants

**Par volume estimé (Σ midpoint) :**

| déposant | chambre | n trades | volume estimé M$ |
| --- | --- | --- | --- |
| Michael T. McCaul | house | 26938 | 1766.3 |
| Rohit Khanna | house | 40716 | 891.9 |
| Diana Harshbarger | house | 3274 | 467.8 |
| RICHARD BLUMENTHAL | senate | 1527 | 452.5 |
| Josh Gottheimer | house | 3574 | 347.8 |
| Suzan K. DelBene | house | 861 | 338.1 |
| MARK R WARNER | senate | 145 | 275.3 |
| DIANNE FEINSTEIN | senate | 705 | 254.1 |
| Darrell E. Issa | house | 20 | 250.5 |
| Rick Scott | senate | 357 | 240.7 |
| Nancy Pelosi | house | 220 | 227.8 |
| Scott H. Peters | house | 992 | 213.5 |
| Jefferson Shreve | house | 631 | 192.9 |
| Scott Franklin | house | 68 | 188.2 |
| RICHARD M BURR | senate | 525 | 188.0 |
*volume estimé M$ = Σ midpoint des transactions du déposant · n trades = nombre de transactions*

**Par nombre de transactions** — 445 déposants distincts, dont **294** avec ≥ 10 transactions (éligibles au backtest) et **236** actifs sur ≥ 3 années :

| nom | total | dont OCR | OCR % | n années | 1re année | dern. année |
| --- | --- | --- | --- | --- | --- | --- |
| Rohit Khanna | 41080 | 41080 | 100 | 10 | 2017 | 2026 |
| Michael T. McCaul | 27123 | 27123 | 100 | 14 | 2013 | 2026 |
| James B. Renacci | 5453 | 5453 | 100 | 6 | 2013 | 2018 |
| Thomas MacArthur | 4995 | 0 | 0 | 5 | 2015 | 2019 |
| David P. Roe | 4680 | 4680 | 100 | 8 | 2013 | 2020 |
| Diana Harshbarger | 3666 | 3665 | 100 | 4 | 2021 | 2026 |
| Josh Gottheimer | 3574 | 21 | 1 | 10 | 2017 | 2026 |
| David A Perdue , Jr | 2611 | 0 | 0 | 6 | 2015 | 2020 |
| Gilbert Cisneros | 2597 | 0 | 0 | 4 | 2019 | 2026 |
| Kurt Schrader | 1899 | 1899 | 100 | 10 | 2013 | 2022 |
| Lois Frankel | 1725 | 54 | 3 | 11 | 2013 | 2023 |
| Alan S. Lowenthal | 1593 | 0 | 0 | 11 | 2012 | 2022 |
| K. Michael Conaway | 1593 | 3 | 0 | 8 | 2013 | 2020 |
| Thomas R Carper | 1557 | 9 | 1 | 13 | 2012 | 2024 |
| RICHARD BLUMENTHAL | 1543 | 1543 | 100 | 13 | 2014 | 2026 |
| Francis Rooney | 1536 | 1536 | 100 | 4 | 2017 | 2020 |
| Lisa McClain | 1532 | 109 | 7 | 3 | 2024 | 2026 |
| Greg Gianforte | 1490 | 0 | 0 | 4 | 2017 | 2020 |
| Thomas H Tuberville | 1369 | 0 | 0 | 5 | 2021 | 2025 |
| Daniel Goldman | 1291 | 0 | 0 | 2 | 2023 | 2025 |
*total = nb transactions · dont OCR / OCR % = part scannée · n années = années actives · 1re/dern. année = première/dernière année de transaction*

![Top déposants](quality/top_deposants.png)

![Transactions par an](quality/transactions_par_an.png)

### Devenir des achats à +12 mois (revente vs fermeture forcée, pour la stratégie)

Pour chaque achat (avec ticker), on suit la position : est-elle **revendue par le même membre sur le même ticker dans les 12 mois** (l'horizon de fermeture forcée de la stratégie) ? L'appariement se fait sur la **date de divulgation** — ce que la stratégie peut observer. Les achats divulgués il y a **moins de 12 mois** (après 2025-07-02) n'ont pas assez de recul pour juger : marqués *trop récents* et exclus des taux.

| chambre | achats (avec ticker) | trop récents | observables | revendu ≤12m | revendu ≤12m % | fermé de force | fermé de force +12m % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| house | 63652 | 2486 | 61166 | 41428 | 67.7 | 19738 | 32.3 |
| senate | 6328 | 236 | 6092 | 2944 | 48.3 | 3148 | 51.7 |

**Par sous-corpus :**

| sous-corpus | achats (avec ticker) | trop récents | observables | revendu ≤12m | revendu ≤12m % | fermé de force | fermé de force +12m % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 24362 | 1741 | 22621 | 11710 | 51.8 | 10911 | 48.2 |
| House OCR | 39290 | 745 | 38545 | 29718 | 77.1 | 8827 | 22.9 |
| Sénat électronique | 5188 | 231 | 4957 | 2358 | 47.6 | 2599 | 52.4 |
| Sénat OCR | 1140 | 5 | 1135 | 586 | 51.6 | 549 | 48.4 |
*achats (avec ticker) · trop récents = <12 mois de recul depuis la divulgation (indéterminé, hors dénominateur) · observables = achats − trop récents · revendu ≤12m = une vente du même ticker divulguée dans les 12 mois · fermé de force +12m = aucune vente sous 12 mois → la stratégie clôt la position · les deux % portent sur les observables*

## 6. Complétude vs Quiver (vérité-terrain externe)

> **Section clé.** Quiver est un fournisseur commercial des mêmes données = notre **juge externe**. But : montrer qu'on a **au moins tout ce que Quiver a** (Quiver ⊆ nous), qu'on est même **plus complet**, et que nos différences ne sont **pas des erreurs**. On procède comme un **entonnoir, de strictesse croissante** : Niveau 1 → 2 → 3. Chiffres recalculés par `common/quiver_diagnosis.py`, **jamais réinjectés**.

### 6.1 Méthode

Chaque transaction est confrontée à Quiver par une clé normalisée, en **trois niveaux de plus en plus stricts** : **N1** a-t-on le trade ? *(sans la date, §6.2)* → **N2** le même trade à la même date ? *(§6.3)* → **N3** qui corrige quoi ? *(§6.5)*.

| élément | définition |
| --- | --- |
| univers comparé | tous les trades Quiver `Filed` ∈ 2014–2026 (notre fenêtre de scrape) |
| clé d'appariement | (`bioguide`, ticker normalisé, sens) — **+ date** au Niveau 2, **sans date** au Niveau 1 |
| normalisation ticker | MAJ + trim ; rejette {vide, NAN, NONE, --} ; retire ` PUT`/` CALL` ; `.`/`-` → `_` |
| normalisation sens | 1re lettre p/s/e → Purchase / Sale / Exchange |
*Périmètre : le corpus FINAL dédupliqué cross-année (169 000 transactions uniques, cf. §1 « Construction & validation du corpus »).*


*Réf. : `house/quiver.py` (`norm_ticker`, `norm_sense`), `common/quiver_diagnosis.py`.*

### 6.2 Niveau 1 — A-t-on le trade ? (sans la date)

On compare des **combinaisons** `(membre, action, sens)`, en **ignorant volontairement la date ET le nombre** : `(Khanna, AAPL, Achat)` compte pour **un**, qu'il l'ait acheté 1 fois ou 50. La question est donc grossière **exprès** : *« a-t-on raté une combinaison ENTIÈRE que Quiver connaît ? »* — le comptage trade par trade, c'est le Niveau 2 (§6.3).

On retrouve **93.5 % (House)** et **92.1 % (Sénat)** des combinaisons Quiver. Le **trou coté** est minuscule (31 House / 0 Sénat) — c'est une **borne haute (sans date)** ; au trade près (§6.5), seule une partie sont de vrais trous confirmés. Le reste du résidu est récupérable ou hors périmètre :

| chambre | trades Quiver (fenêtre) | qu'on a | inclusion % | résidu | récupérable (OCR) | hors périmètre | trou coté (borne haute) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| house | 26175 | 24471 | 93.5 | 1704 | 1578 | 95 | 31 |
| senate | 4540 | 4180 | 92.1 | 360 | 7 | 353 | 0 |

*Le résidu se lit ainsi :* **récupérable (OCR)** = membre lu en OCR papier dont on a capté le trade mais **pas résolu le ticker** (nom lisible → récupérable, cf. note ; sinon non-coté déguisé/charabia OCR) · **hors périmètre** = « ticker » Quiver non-coté (CUSIP/fragment) + trade sous un ticker d'échange combiné (« PFE VTRS » couvre PFE) + membre de l'autre chambre polluant le cache · **trou coté (borne haute)** = combos manquants au niveau ticker (sans date) ; au trade près (§6.5), seul un sous-ensemble (`NOTRE_MANQUE`) sont de vrais trous confirmés.

*Note :* une passe de **récupération nom→ticker** (vérifiée, **hors Quiver**, appliquée à la lecture — golden intact) a rendu leur ticker à **2540 trades** d'actions que l'OCR/LLM avaient laissés vides (faux négatifs, ex. NEENAH PAPER→NP, TENCENT→TCEHY). Le « récupérable OCR » restant est surtout des **non-cotés déguisés** (préférentielles, fonds) et du **charabia OCR**, non mappables.

**Bilan net (au trade près)** — actions cotées qu'on a et que Quiver n'a PAS vs **vrais trous** (`NOTRE_MANQUE` = le sous-ensemble des « trous borne haute » ci-dessus réellement absents au trade près) → on est un **sur-ensemble** de Quiver :

| chambre | actions qu'on a en + | vrais trous | solde net |
| --- | --- | --- | --- |
| house | 23562 | 27 | 23535 |
| senate | 2962 | 11 | 2951 |

**⚠ Honnêteté par ère (corroboration au niveau ACTION, House `asset_type=Stock`).** Le taux global lisse une forte hétérogénéité : **2020-2026 = 87.2 %** d'actions corroborées par Quiver, mais **2014-2019 = 58.7 %** seulement (creux **2015-2016** ≈ 11-17 %). L'écart **ne reflète PAS une erreur de notre côté** : nos 15015 actions « en plus » pré-2020 portent des **tickers réels et d'époque** (vérifiés), mais **Quiver est mince avant ~2017** et ne peut pas les corroborer. En clair : **moins de vérité-terrain externe avant 2017**, à garder en tête pour tout usage aval (backtest).

| année | actions_corroborées | actions_only_nous | corroboration_pct |
| --- | --- | --- | --- |
| 2014.0 | 1930.0 | 3984.0 | 32.6 |
| 2015.0 | 540.0 | 2711.0 | 16.6 |
| 2016.0 | 291.0 | 1458.0 | 16.6 |
| 2017.0 | 3729.0 | 2241.0 | 62.5 |
| 2018.0 | 7243.0 | 2722.0 | 72.7 |
| 2019.0 | 7630.0 | 1899.0 | 80.1 |
| 2020.0 | 10025.0 | 2801.0 | 78.2 |
| 2021.0 | 6945.0 | 2803.0 | 71.2 |
| 2022.0 | 11011.0 | 1286.0 | 89.5 |
| 2023.0 | 7522.0 | 442.0 | 94.5 |
| 2024.0 | 6797.0 | 481.0 | 93.4 |
| 2025.0 | 11095.0 | 408.0 | 96.5 |
| 2026.0 | 4740.0 | 348.0 | 93.2 |
*actions_corroborées = appariées à Quiver (exact + date proche) · actions_only_nous = actions réelles qu'on a et que Quiver n'a pas (non corroborables) · corroboration_pct = corroborées / (corroborées + only_nous).*

### 6.3 Niveau 2 — Le même trade, à la même date ?

On descend au trade près. Comme un membre peut trader le même titre **plusieurs fois**, on ne demande PAS « ma date est-elle dans l'ensemble Quiver ? » : on **apparie 1-à-1** nos trades à ceux de Quiver, à l'intérieur de chaque `(membre, ticker, sens)`. Exemple :

```
Khanna, AAPL, Achat — dates :
  NOUS   : 08-jan-2020 · 13-fév-2020 · 01-juin-2020 · 10-mars-2023
  QUIVER : 08-jan-2020 · 12-fév-2020 ·                10-mars-2023

Étape 1 — on retire les dates IDENTIQUES (une par une) :
  08-jan ↔ 08-jan   et   10-mars-2023 ↔ 10-mars-2023   → 2 « apparié exact »
  (le trade 2023 s'apparie à SON 2023, jamais à un 2020)

Étape 2 — on apparie les RESTES au plus proche (plafond 90 j) :
  13-fév (nous) ↔ 12-fév (Quiver) = 1 j   → « apparié proche » (≤ 10 j, bruit de date)
  01-juin (nous) : aucun reste Quiver à < 90 j   → « NOUS-SEUL » (trade en plus)
```

Deux garde-fous répondent à « comment gérer qu'un membre ait plusieurs trades » : l'appariement **1-à-1 respecte les quantités** (si on a 50 trades et Quiver 40, **≥ 10 restent forcément en « nous-seul »**) ; le **plafond de 90 j** + l'**ancrage au dépôt** empêchent mécaniquement de confondre un trade 2020 et un trade 2023. Chaque trade tombe alors dans **une** catégorie :

| chambre | apparié exact | apparié proche (≤10j) | candidat écart | dont même déclaration | nous-seul | quiver-seul | candidat % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| house | 70265 | 845 | 2202 | 545 | 39207 | 9899 | 2.0 |
| senate | 8766 | 0 | 0 | 0 | 3140 | 581 | 0.0 |
*apparié exact = même date · apparié proche = écart des dates de TRANSACTION ≤ 10 j (bruit/convention de date Quiver, même trade) · candidat écart = paire à 10–90 j, à inspecter (§6.4) · dont même déclaration = les deux trades viennent du MÊME formulaire de déclaration (PTR) — notre `disclosure` ≈ `Filed` Quiver ≤ 10 j → même trade, donc l'écart de date est un vrai désaccord (seul signal fort) · nous-seul = Quiver n'a PAS le trade (on est plus complet) · quiver-seul = on a raté.*

**Pourquoi les chiffres semblent contredire le §6.2 : c'est le niveau de strictesse.** Au Niveau 1 (sans date), le trou coté (borne haute) est 31/0 ; au Niveau 2 (trade + date), on compte 39207 trades « nous-seul » — normal, on trade plus souvent que Quiver ne capte au trade près. **Les deux disent la même chose : on est plus complet.**

### 6.4 Les candidats d'écart de date (même déclaration)

Les **seuls** candidats honnêtes d'erreur de date = les paires issues de la **même déclaration (PTR)** (545 House / 0 Sénat). Prudence : un petit delta peut être une **convention de date Quiver**, pas notre erreur. **Le vrai contrôle des dates reste l'audit PDF (§3)**, pas Quiver. `doc_id` = pièce consultable :

| chambre | déposant | ticker | sens | notre date | date Quiver | delta (j) | doc_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| house | Michael T. McCaul | GOOGL | Purchase | 2018-07-26 | 2018-08-06 | 11 | 9113676 |
| house | Michael T. McCaul | PEP | Purchase | 2018-05-24 | 2018-06-04 | 11 | 9113406 |
| house | Michael T. McCaul | SIRI | Sale | 2018-06-25 | 2018-07-06 | 11 | 9113580 |
| house | Rohit Khanna | ADBE | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | AMT | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | BX | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | CDNS | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | CHTR | Sale | 2022-09-08 | 2022-09-19 | 11 | 8219242 |
| house | Rohit Khanna | CMG | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | DHR | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | DXC | Sale | 2020-03-25 | 2020-04-05 | 11 | 8217164 |
| house | Rohit Khanna | ETR | Sale | 2020-04-07 | 2020-04-18 | 11 | 8217213 |

*(Top 12 par delta croissant ; les 545 candidats sont dans `quiver_validation/candidats_ecart_date_meme_depot.csv`.)*

### 6.5 Niveau 3 — Que reste-t-il à corriger ?

On a vérifié l'**existence** (§6.2) et la **date** (§6.3). Restent deux choses : les **autres champs** des trades qu'on partage avec Quiver (sens, montant), et la **liste de ce qui est vraiment à corriger**.

**Autres champs — sens & montant.** Pour les trades qu'on a **tous les deux** (mêmes membre + ticker + date), est-on d'accord sur le sens (achat/vente) et le montant ?

| chambre | n paires | accord sens % | accord montant % |
| --- | --- | --- | --- |
| house | 86090 | 96.8 | 94.2 |
| senate | 9775 | 99.9 | 99.8 |
*on apparie les cellules (membre, ticker, date) présentes des DEUX côtés ; un désaccord = vraie erreur d'extraction, listée dans `desaccord_champ_*.csv`.*

**La to-do (à corriger).** Un seul chiffre est **dur** — les vrais trous `NOTRE_MANQUE` (le résidu après tous les filtres) ; les deux autres sont des **bornes hautes** ensemblistes = des listes à revoir cas par cas dans `docs/quiver_validation/`, pas des taux d'erreur :

| à corriger | House | Sénat | nature | annexe |
| --- | --- | --- | --- | --- |
| vrais trous cotés (`NOTRE_MANQUE`) | 27 | 11 | **DUR** — vrai trou confirmé au trade près (mesure au trade DATÉ, clé différente de la borne ticker-niveau du §6.2 : les deux comptes ne s'emboîtent pas) | `notre_manque_*` |
| lignes OCR papier (`MANQUANT_PAPIER`) | 3378 | 0 | borne haute — trades Quiver de déposants qu'on OCR, absents de nos clés exactes | `manquant_papier_*` |
| tickers à revoir (`ECART_TICKER`) | 8418 | 190 | borne haute — autre ticker ce jour-là (gonflée par la multiplicité, PAS un taux d'erreur) | `ecart_ticker_*` |
**Qui ?** — les déposants derrière les vrais trous (`NOTRE_MANQUE`), à investiguer :

| chambre | bioguide | nom | n trous |
| --- | --- | --- | --- |
| house | T000475 | David A. Trott | 8 |
| house | B001327 | Rob Bresnahan | 5 |
| house | W000797 | Debbie Wasserman Schultz | 3 |
| house | M001193 | Thomas MacArthur | 2 |
| house | S000250 | Pete Sessions | 2 |
| house | C001101 | Katherine M. Clark | 1 |
| house | F000461 | Bill Flores | 1 |
| house | J000307 | John James | 1 |
| senate | C001075 | William Cassidy | 5 |
| senate | M001198 | Roger W Marshall | 3 |
| senate | R000608 | Jacklyn S Rosen | 2 |
| senate | D000622 | Tammy Duckworth | 1 |

### 6.6 Annexe

Les tables **figées** `07c/07g/07h` reproduisent la même comparaison en *exact-date* (elles **sous-comptent**, cf. §6.3) ; conservées pour la lignée/régression, non re-rendues ici. Les autres figées (`07/07b/07d/07e/07f/06d`) sont des sorties historiques du pipeline.

**Profil des clusters de scan (House OCR)** — pourquoi le manuscrit est exclu (A = tapé droit, B = tapé tourné, C = manuscrit) :

| cluster | n lignes | n docs | date plausible % | ticker % | Quiver a le trade % |
| --- | --- | --- | --- | --- | --- |
| A_tape_droit | 5956 | 59 | 99.6 | 84.5 | 88.0 |
| B_tape_tourne | 84787 | 1517 | 96.4 | 84.3 | 65.2 |
| C_manuscrit | 2518 | 193 | 98.6 | 83.3 | 12.9 |
*`date plausible %` / `ticker %` = qualité INTERNE (sans Quiver) · `Quiver a le trade %` = part de nos trades cotés que Quiver possède AUSSI (appariée sur membre+ticker+sens, date ou non). Sur le manuscrit (C), la qualité interne reste haute mais `Quiver a le trade %` s'effondre (ticker/identité mal lus, ou Quiver mince sur le papier) → faute de pouvoir le confirmer contre la vérité-terrain, on l'exclut par défaut (conservateur). Exceptions CONSERVÉES et rejouables : 3 filers à forte perte corroborée (FILERS_C_A_RECUPERER) + 33 docs C du run 2020-2026 curés à la main AVANT cette politique (DOCS_C_HERITES_2020_2026, house/ocr.py) ; 70 manuscrits de l'acquisition 2026-07-03 gated selon la même règle.*

Listes actionnables complètes (ligne à ligne) → `docs/quiver_validation/` (`ecart_ticker_*`, `notre_manque_*`, `manquant_papier_*`, `desaccord_champ_*` [typé], `on_est_plus_complet_*`, `quiver_non_cote_*`, `candidats_ecart_date_meme_depot`). Hors golden.

