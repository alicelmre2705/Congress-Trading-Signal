# Rapport qualité — Données de trading du Congrès américain
> Chambre des représentants + Sénat · 2014–2026 · généré par `python -m common.quality` (lecture seule des tables FINAL, aucun appel API) · Quiver Quantitative = vérité-terrain externe, **jamais réinjectée**. *Les % sont arrondis à 0,1 pt ; une somme de colonnes peut afficher 100,1.*

## Résumé exécutif

- **Périmètre** — 158 172 transactions uniques de membres élus (House 141 161 + Sénat 17 011), 2014–2026, en **4 sous-corpus** (chambre × voie d'acquisition : électronique déterministe / scan OCR).
- **Complétude vs Quiver** *(§6)* — dans notre fenêtre, on retrouve **88.1 % (House) / 92.1 % (Sénat)** des trades Quiver au niveau (déposant, ticker, sens). Le **trou coté est minuscule** — ≤ 838 House / 0 Sénat au niveau ticker (borne haute), dont **1019 / 11 vrais trous confirmés au trade près** (§6.5) ; le reste du résidu est de l'OCR récupérable ou du hors-périmètre.
- **On est plus complet que Quiver** — **+24017 combinaisons cotées (déposant, ticker, sens)** qu'on a et que Quiver n'a pas, contre 1030 trous inverses → **sur-ensemble** de Quiver. ⚠ Cette avance est **inégale dans le temps** : bien corroborée après ~2017, elle repose avant sur des trades réels que **Quiver (mince pré-2017) ne peut pas confirmer** — détail par année en §6.2.
- **Les « écarts » de date ne sont pas des erreurs** — la réconciliation 1-à-1 (§6.3) montre que l'essentiel est du « nous-seul » (Quiver n'a pas le trade) ; seuls 508 candidats House (même déclaration) méritent l'œil, et le vrai contrôle des dates reste l'audit PDF (§3).
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
| house | 141225 | 64 | 141161 |
| senate | 18839 | 1828 | 17011 |
| TOTAL | 160064 | 1892 | 158172 |
*lignes brutes = FINAL concaténé 2014–2026 · re-divulgations = doublons cross-année retirés · transactions uniques = le corpus analysé dans tout ce rapport*

### Validation & reproductibilité

Tout est **rejouable hors-ligne** (lecture seule des tables FINAL, **0 appel API**), adossé à trois filets automatiques :

- **Golden octet-à-octet** — 361 tables CSV figées par SHA256 (224 House + 137 Sénat), rejouées à **zéro écart** (`tests/regression/check_golden.py`, `senate_check_golden.py`).
- **Invariants porteurs** — pour chaque chambre `digital + OCR = FINAL`, identité rattachée à **100.0 %**, 358 bioguides (House) / 76 (Sénat) recomptés (`tests/regression/audit_metrics.py`).
- **Transformations déterministes** — 11 tests reproduisent chaque étape (clé naturelle, montants, tickers, identité, ancienneté, cache Vision) depuis les colonnes figées.

### Les quatre sous-corpus

Toute la suite distingue **quatre familles** (chambre × voie), car leur qualité et leur composition diffèrent :

| sous-corpus | n | part % |
| --- | --- | --- |
| House électronique | 54150 | 34.2 |
| House OCR | 87011 | 55.0 |
| Sénat électronique | 13026 | 8.2 |
| Sénat OCR | 3985 | 2.5 |
*sous-corpus = chambre × voie (électronique déterministe / scan OCR) · n = transactions uniques · part % du total*

## 2. Composition & complétude

**Ce que contient le corpus** (opérations, détenteur, familles d'actifs), puis **à quel point les champs sont remplis**.

### Sens des opérations

| sous-corpus | n | achat % | vente % | échange % | autre % |
| --- | --- | --- | --- | --- | --- |
| House électronique | 54150 | 51.6 | 47.3 | 1.0 | 0.0 |
| House OCR | 87011 | 53.1 | 46.5 | 0.5 | 0.0 |
| Sénat électronique | 13026 | 50.2 | 48.8 | 1.0 | 0.0 |
| Sénat OCR | 3985 | 56.4 | 43.0 | 0.6 | 0.0 |
*achat = `operation_type` contient « Purchase » · vente = contient « Sale » (**inclut Sale (Partial) et (Full)**) · échange = « Exchange » · autre = reste*

![Mix achat/vente par sous-corpus](quality/mix_operations_par_corpus.png)

### Détenteur déclaré

| sous-corpus | n | perso % | conjoint % | joint % | enfant % | autre % |
| --- | --- | --- | --- | --- | --- | --- |
| House électronique | 54150 | 48.8 | 20.4 | 27.3 | 3.5 | 0.0 |
| House OCR | 87011 | 10.4 | 48.1 | 13.5 | 27.9 | 0.0 |
| Sénat électronique | 13026 | 16.8 | 38.7 | 42.1 | 2.4 | 0.0 |
| Sénat OCR | 3985 | 48.8 | 49.5 | 1.5 | 0.3 | 0.0 |
*titulaire du compte : perso = Self · conjoint = Spouse/SP · joint = Joint/JT · enfant = Dependent/Child/DC · autre = reste ou non déclaré*

### Familles d'actifs

Le non-coté (oblig. d'État, munis, obligations) domine l'OCR du Sénat :

| sous-corpus | n | action % | option % | oblig. État % | muni % | oblig. corp. % | fonds % | autre % | manquant % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 54150 | 63.3 | 1.3 | 4.4 | 0.0 | 0.0 | 0.0 | 5.3 | 25.6 |
| House OCR | 87011 | 79.8 | 0.0 | 0.8 | 0.0 | 0.4 | 3.0 | 0.3 | 15.6 |
| Sénat électronique | 13026 | 73.0 | 4.7 | 0.0 | 7.7 | 3.0 | 0.0 | 6.5 | 5.1 |
| Sénat OCR | 3985 | 40.4 | 0.0 | 0.0 | 0.7 | 2.2 | 0.0 | 41.2 | 15.5 |
*familles d'`asset_type` : action = Stock · option · oblig. État = Gov/Treasury · muni = Municipal · oblig. corp. = Bond · fonds = Fund/ETF · manquant = vide*

![Mix de types d'actifs par sous-corpus](quality/mix_actifs_par_corpus.png)

### Couverture des champs enrichis (taux de remplissage)

| sous-corpus | n | ticker % | secteur % | ETF % | commission % | identité % | ancienneté % | montant renseigné % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 54150 | 80.3 | 78.0 | 78.0 | 57.5 | 100.0 | 100.0 | 100.0 |
| House OCR | 87011 | 84.7 | 81.6 | 81.6 | 81.1 | 100.0 | 99.9 | 98.9 |
| Sénat électronique | 13026 | 84.1 | 77.8 | 77.8 | 53.0 | 99.9 | 99.9 | 100.0 |
| Sénat OCR | 3985 | 57.4 | 46.2 | 46.2 | 64.9 | 100.0 | 100.0 | 99.4 |
*% de lignes où le champ est renseigné · identité = rattachée à un `bioguide_id` · montant renseigné = `amount_midpoint` non vide · ticker/secteur/ETF vides = actif non coté (normal, pas un défaut)*

### Secteurs & origine des champs résolus

| sous-corpus | n | secteur renseigné % | ETF % | top 3 secteurs |
| --- | --- | --- | --- | --- |
| House électronique | 54150 | 78.0 | 78.0 | Information Technology 18%, Financials 14%, Health Care 13% |
| House OCR | 87011 | 81.6 | 81.6 | Information Technology 17%, Financials 15%, Health Care 13% |
| Sénat électronique | 13026 | 77.8 | 77.8 | Information Technology 19%, Financials 14%, Health Care 11% |
| Sénat OCR | 3985 | 46.2 | 46.2 | Financials 16%, Industrials 15%, Health Care 12% |
*secteur renseigné % / ETF % = taux de remplissage (vide = non coté) · top 3 = secteurs GICS dominants*

**Origine du ticker** (`ticker_source`) :

| sous-corpus | n | dico élec % | LLM % | nom d'actif % | récupéré % | explicite % | aucune % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 54150 | 0.0 | 0.0 | 0.0 | 0.0 | 80.3 | 19.7 |
| House OCR | 87011 | 35.8 | 40.5 | 0.0 | 0.7 | 7.7 | 15.3 |
| Sénat électronique | 13026 | 2.6 | 3.0 | 1.9 | 0.0 | 76.7 | 15.9 |
| Sénat OCR | 3985 | 21.0 | 25.7 | 0.0 | 0.0 | 10.6 | 42.6 |
*dico élec = repris de l'électronique · LLM = résolu par LLM · nom d'actif = déduit du nom d'actif · récupéré = rendu par la passe nom→ticker vérifiée (cf. §6.2) · explicite = déjà présent dans la source · aucune = non résolu*

**Origine du secteur** (`sector_source`) :

| sous-corpus | n | yfinance % | LLM % | manuel % | aucune % |
| --- | --- | --- | --- | --- | --- |
| House électronique | 54150 | 67.9 | 10.1 | 0.3 | 21.8 |
| House OCR | 87011 | 69.7 | 11.9 | 0.1 | 18.3 |
| Sénat électronique | 13026 | 62.7 | 14.9 | 0.8 | 21.6 |
| Sénat OCR | 3985 | 32.8 | 13.5 | 0.6 | 53.2 |
*yfinance = base factuelle · LLM · manuel = correction d'audit · aucune*

![Volume par secteur GICS](quality/volume_par_secteur.png)

## 3. Qualité des dates

Trois questions, de la plus faible à la plus forte : les dates sont-elles **lisibles et cohérentes** (divulgation ≥ transaction) ? le **délai légal** (STOCK Act ~45 j) est-il respecté ? reste-t-il des **anomalies** ?

### Cohérence (`disclosure_date ≥ transaction_date`)

| chambre | n | dates exploitables % | cohérentes % | incohérentes | année aberrante | date manquante |
| --- | --- | --- | --- | --- | --- | --- |
| house | 141161 | 99.8 | 99.9 | 203 | 6 | 259 |
| senate | 17011 | 99.8 | 99.7 | 55 | 0 | 38 |

**Par sous-corpus :**

| sous-corpus | n | dates exploitables % | cohérentes % | incohérentes | année aberrante | date manquante |
| --- | --- | --- | --- | --- | --- | --- |
| House électronique | 54150 | 100.0 | 99.9 | 56 | 3 | 0 |
| House OCR | 87011 | 99.7 | 99.8 | 147 | 3 | 259 |
| Sénat électronique | 13026 | 100.0 | 99.9 | 9 | 0 | 0 |
| Sénat OCR | 3985 | 99.0 | 98.8 | 46 | 0 | 38 |
*dates exploitables = parseables (% du total ; le reste = OCR illisible) · cohérentes = divulgation ≥ transaction, **% parmi les exploitables** (dénominateur = exploitables, pas le total → ce % peut dépasser « dates exploitables % ») · incohérentes = divulgation AVANT transaction (amendement/antidaté) · année aberrante = année impossible (postérieure au dépôt, ou < 2012) · date manquante = illisible. Des transactions 2013–2019 sont légitimes (divulgations tardives).*

### Délai légal de divulgation (STOCK Act ~45 j)

| chambre | n dates valides | ≤45j légal % | 45–75j % | >75j % | négatif % | délai médian (j) |
| --- | --- | --- | --- | --- | --- | --- |
| house | 140902 | 87.7 | 6.0 | 6.1 | 0.1 | 27 |
| senate | 16973 | 86.9 | 3.0 | 9.8 | 0.3 | 24 |

**Par sous-corpus :**

| sous-corpus | n dates valides | ≤45j légal % | 45–75j % | >75j % | négatif % | délai médian (j) |
| --- | --- | --- | --- | --- | --- | --- |
| House électronique | 54150 | 82.9 | 5.2 | 11.8 | 0.1 | 28 |
| House OCR | 86752 | 90.7 | 6.5 | 2.6 | 0.2 | 27 |
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
| Richard W. Allen | house | 2017-04-27 | 2023-08-10 | 2296.0 | XOM | Sale |
| Richard W. Allen | house | 2017-04-27 | 2023-08-10 | 2296.0 | COST | Purchase |
| Richard W. Allen | house | 2017-05-16 | 2023-08-10 | 2277.0 | GE | Sale |
| Richard W. Allen | house | 2017-05-16 | 2023-08-10 | 2277.0 | FDX | Purchase |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | GOOGL | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | BLK | Sale |
| Thomas Suozzi | house | 2017-01-05 | 2022-12-19 | 2174.0 | FB | Sale |
*délai (j) = divulgation − transaction · divulgations > 1 an après la transaction (souvent des amendements ou de vieux comptes régularisés)*

**Audit des anomalies (échantillon de 12 PDF re-lus à la source).** ~½ sont FIDÈLES : coquilles du **déposant lui-même** (un PTR imprime littéralement `01/35/22`), cellules vides ou parts de société sans date de transaction — on les transcrit sans les inventer. ~⅓ = **notre OCR** (mois/jour mal lu), corrigé à la lecture **quand le formulaire est lisible** (4 dates vérifiées, clé doc+date, figé inchangé). ~⅙ = **provenance** (hallucination OCR ou pièce jointe absente du PDF). **On ne fabrique aucune date** : les illisibles restent flaggées.

## 4. Montants (`amount_midpoint`)

Le montant = **midpoint** de la fourchette déclarée (les déclarations donnent des tranches, pas un chiffre exact). Vue par sous-corpus :

| sous-corpus | n | médiane $ | moyenne $ | P25_$ | P75_$ | P95_$ | volume total M$ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 54150 | 8000 | 46863 | 8000 | 15001 | 100001 | 2537.6 |
| House OCR | 87011 | 8000 | 43209 | 8000 | 32500 | 175000 | 3717.8 |
| Sénat électronique | 13026 | 8000 | 81666 | 8000 | 32500 | 175000 | 1063.8 |
| Sénat OCR | 3985 | 32500 | 301252 | 8000 | 175000 | 750000 | 1193.6 |
*médiane/moyenne/P25/P75/P95 en $ · volume total = Σ midpoint (M$) · midpoint = milieu de la fourchette déclarée*

![Composition par tranche de montant](quality/mix_montants_par_corpus.png)

*la plus petite tranche (≤ 15 k$, midpoint 8 000 $) domine → dès qu'elle dépasse 50 %, le P25 ET la médiane y tombent ensemble (cas House/Sénat élec). Sénat OCR < 50 % → médiane 32 500 ≠ P25 8 000.*

**Ensemble** — 157 179 montants renseignés · médiane 8 000 $ · moyenne 54 159 $ · P90 75 000 $ · max 75 000 000 $.

![Distribution des montants](quality/distribution_montants.png)

## 5. Activité & concentration

**Qui trade, à quel point l'activité est concentrée, et ce que deviennent les positions.**

### Concentration du volume

| sous-corpus | n déposants | HHI | Gini | top10 volume % |
| --- | --- | --- | --- | --- |
| House électronique | 302 | 439.3 | 0.871 | 58.2 |
| House OCR | 119 | 2504.4 | 0.952 | 94.7 |
| Sénat électronique | 73 | 944.0 | 0.821 | 79.5 |
| Sénat OCR | 14 | 2671.5 | 0.753 | 100.0 |

`HHI` ∈ [0, 10000] et `Gini` ∈ [0, 1] mesurent la concentration du volume par déposant (plus c'est haut, plus quelques déposants dominent).

![Concentration du volume (Lorenz)](quality/concentration_lorenz.png)

### Où va le volume

**Top tickers par volume estimé :**

| ticker | n trades | volume M$ |
| --- | --- | --- |
| MSFT | 1469 | 301.5 |
| FDX | 352 | 117.9 |
| AAPL | 1241 | 94.6 |
| ICE | 205 | 94.5 |
| BRP | 7 | 81.8 |
| MET | 211 | 77.6 |
| T | 556 | 67.7 |
| AMZN | 998 | 52.3 |
| WFM | 123 | 52.2 |
| BRK.B | 436 | 49.0 |
| NVDA | 684 | 48.0 |
| DFS | 113 | 43.4 |
| MMM | 246 | 42.9 |
| HBI | 159 | 41.1 |
| KITE | 20 | 41.1 |
*volume M$ = Σ midpoint des trades du ticker · n trades = nombre de transactions*

**Volume par secteur GICS :**

| secteur | n trades | volume M$ |
| --- | --- | --- |
| Information Technology | 21543 | 912.1 |
| Financials | 18328 | 785.7 |
| Industrials | 14979 | 488.0 |
| Health Care | 16194 | 437.4 |
| Consumer Discretionary | 14796 | 394.7 |
| Communication Services | 9891 | 380.5 |
| Energy | 7764 | 272.4 |
| Consumer Staples | 8926 | 268.2 |
| Materials | 5340 | 113.1 |
| Real Estate | 4373 | 95.1 |
| Utilities | 2408 | 52.3 |
### Top déposants

**Par volume estimé (Σ midpoint) :**

| déposant | chambre | n trades | volume estimé M$ |
| --- | --- | --- | --- |
| Michael T. McCaul | house | 24021 | 1554.7 |
| Rohit Khanna | house | 39176 | 867.1 |
| Diana Harshbarger | house | 3124 | 464.5 |
| RICHARD BLUMENTHAL | senate | 1527 | 452.5 |
| MARK R WARNER | senate | 145 | 275.3 |
| DIANNE FEINSTEIN | senate | 705 | 254.1 |
| Darrell E. Issa | house | 20 | 250.5 |
| Rick Scott | senate | 357 | 240.7 |
| Josh Gottheimer | house | 3574 | 217.0 |
| Suzan K. DelBene | house | 835 | 209.8 |
| Jefferson Shreve | house | 631 | 191.7 |
| RICHARD M BURR | senate | 525 | 188.0 |
| Scott Franklin | house | 68 | 182.1 |
| Scott H. Peters | house | 937 | 158.2 |
| Nancy Pelosi | house | 199 | 153.6 |
*volume estimé M$ = Σ midpoint des transactions du déposant · n trades = nombre de transactions*

**Par nombre de transactions** — 434 déposants distincts, dont **288** avec ≥ 10 transactions (éligibles au backtest) et **231** actifs sur ≥ 3 années :

| nom | total | dont OCR | OCR % | n années | 1re année | dern. année |
| --- | --- | --- | --- | --- | --- | --- |
| Rohit Khanna | 39538 | 39538 | 100 | 10 | 2017 | 2026 |
| Michael T. McCaul | 24192 | 24192 | 100 | 14 | 2013 | 2026 |
| James B. Renacci | 5201 | 5201 | 100 | 6 | 2013 | 2018 |
| David P. Roe | 4192 | 4192 | 100 | 8 | 2013 | 2020 |
| Thomas MacArthur | 4185 | 0 | 0 | 5 | 2015 | 2019 |
| Josh Gottheimer | 3574 | 21 | 1 | 10 | 2017 | 2026 |
| Diana Harshbarger | 3515 | 3514 | 100 | 4 | 2021 | 2026 |
| David A Perdue , Jr | 2611 | 0 | 0 | 6 | 2015 | 2020 |
| Gilbert Cisneros | 2535 | 0 | 0 | 4 | 2019 | 2026 |
| Kurt Schrader | 1754 | 1754 | 100 | 10 | 2013 | 2022 |
| Thomas R Carper | 1557 | 9 | 1 | 13 | 2012 | 2024 |
| RICHARD BLUMENTHAL | 1543 | 1543 | 100 | 13 | 2014 | 2026 |
| Lisa McClain | 1532 | 109 | 7 | 3 | 2024 | 2026 |
| Alan S. Lowenthal | 1505 | 0 | 0 | 11 | 2012 | 2022 |
| Francis Rooney | 1460 | 1460 | 100 | 4 | 2017 | 2020 |
| Greg Gianforte | 1415 | 0 | 0 | 4 | 2017 | 2020 |
| Thomas H Tuberville | 1369 | 0 | 0 | 5 | 2021 | 2025 |
| Lois Frankel | 1297 | 54 | 4 | 11 | 2013 | 2023 |
| Daniel Goldman | 1291 | 0 | 0 | 2 | 2023 | 2025 |
| Susie Lee | 1281 | 0 | 0 | 8 | 2019 | 2026 |
*total = nb transactions · dont OCR / OCR % = part scannée · n années = années actives · 1re/dern. année = première/dernière année de transaction*

![Top déposants](quality/top_deposants.png)

![Transactions par an](quality/transactions_par_an.png)

### Devenir des achats à +12 mois (revente vs fermeture forcée, pour la stratégie)

Pour chaque achat (avec ticker), on suit la position : est-elle **revendue par le même membre sur le même ticker dans les 12 mois** (l'horizon de fermeture forcée de la stratégie) ? L'appariement se fait sur la **date de divulgation** — ce que la stratégie peut observer. Les achats divulgués il y a **moins de 12 mois** (après 2025-06-25) n'ont pas assez de recul pour juger : marqués *trop récents* et exclus des taux.

| chambre | achats (avec ticker) | trop récents | observables | revendu ≤12m | revendu ≤12m % | fermé de force | fermé de force +12m % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| house | 60085 | 2509 | 57576 | 38136 | 66.2 | 19440 | 33.8 |
| senate | 6328 | 236 | 6092 | 2944 | 48.3 | 3148 | 51.7 |

**Par sous-corpus :**

| sous-corpus | achats (avec ticker) | trop récents | observables | revendu ≤12m | revendu ≤12m % | fermé de force | fermé de force +12m % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 21894 | 1764 | 20130 | 10001 | 49.7 | 10129 | 50.3 |
| House OCR | 38191 | 745 | 37446 | 28135 | 75.1 | 9311 | 24.9 |
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
*Périmètre : le corpus FINAL dédupliqué cross-année (158 172 transactions uniques, cf. §1 « Construction & validation du corpus »).*


*Réf. : `house/quiver.py` (`norm_ticker`, `norm_sense`), `common/quiver_diagnosis.py`.*

### 6.2 Niveau 1 — A-t-on le trade ? (sans la date)

On compare des **combinaisons** `(membre, action, sens)`, en **ignorant volontairement la date ET le nombre** : `(Khanna, AAPL, Achat)` compte pour **un**, qu'il l'ait acheté 1 fois ou 50. La question est donc grossière **exprès** : *« a-t-on raté une combinaison ENTIÈRE que Quiver connaît ? »* — le comptage trade par trade, c'est le Niveau 2 (§6.3).

On retrouve **88.1 % (House)** et **92.1 % (Sénat)** des combinaisons Quiver. Le **trou coté** est minuscule (838 House / 0 Sénat) — c'est une **borne haute (sans date)** ; au trade près (§6.5), seule une partie sont de vrais trous confirmés. Le reste du résidu est récupérable ou hors périmètre :

| chambre | trades Quiver (fenêtre) | qu'on a | inclusion % | résidu | récupérable (OCR) | hors périmètre | trou coté (borne haute) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| house | 26169 | 23060 | 88.1 | 3109 | 2174 | 97 | 838 |
| senate | 4540 | 4180 | 92.1 | 360 | 7 | 353 | 0 |

*Le résidu se lit ainsi :* **récupérable (OCR)** = membre lu en OCR papier dont on a capté le trade mais **pas résolu le ticker** (nom lisible → récupérable, cf. note ; sinon non-coté déguisé/charabia OCR) · **hors périmètre** = « ticker » Quiver non-coté (CUSIP/fragment) + trade sous un ticker d'échange combiné (« PFE VTRS » couvre PFE) + membre de l'autre chambre polluant le cache · **trou coté (borne haute)** = combos manquants au niveau ticker (sans date) ; au trade près (§6.5), seul un sous-ensemble (`NOTRE_MANQUE`) sont de vrais trous confirmés.

*Note :* une passe de **récupération nom→ticker** (vérifiée, **hors Quiver**, appliquée à la lecture — golden intact) a rendu leur ticker à **621 trades** d'actions que l'OCR/LLM avaient laissés vides (faux négatifs, ex. NEENAH PAPER→NP, TENCENT→TCEHY). Le « récupérable OCR » restant est surtout des **non-cotés déguisés** (préférentielles, fonds) et du **charabia OCR**, non mappables.

**Bilan net (au trade près)** — actions cotées qu'on a et que Quiver n'a PAS vs **vrais trous** (`NOTRE_MANQUE` = le sous-ensemble des « trous borne haute » ci-dessus réellement absents au trade près) → on est un **sur-ensemble** de Quiver :

| chambre | actions qu'on a en + | vrais trous | solde net |
| --- | --- | --- | --- |
| house | 21055 | 1019 | 20036 |
| senate | 2962 | 11 | 2951 |

**⚠ Honnêteté par ère (corroboration au niveau ACTION, House `asset_type=Stock`).** Le taux global lisse une forte hétérogénéité : **2020-2026 = 87.5 %** d'actions corroborées par Quiver, mais **2014-2019 = 59.8 %** seulement (creux **2015-2016** ≈ 11-17 %). L'écart **ne reflète PAS une erreur de notre côté** : nos 13717 actions « en plus » pré-2020 portent des **tickers réels et d'époque** (vérifiés), mais **Quiver est mince avant ~2017** et ne peut pas les corroborer. En clair : **moins de vérité-terrain externe avant 2017**, à garder en tête pour tout usage aval (backtest).

| année | actions_corroborées | actions_only_nous | corroboration_pct |
| --- | --- | --- | --- |
| 2014.0 | 1755.0 | 3673.0 | 32.3 |
| 2015.0 | 536.0 | 2548.0 | 17.4 |
| 2016.0 | 172.0 | 1329.0 | 11.5 |
| 2017.0 | 3558.0 | 2017.0 | 63.8 |
| 2018.0 | 6846.0 | 2482.0 | 73.4 |
| 2019.0 | 7521.0 | 1668.0 | 81.8 |
| 2020.0 | 9912.0 | 2627.0 | 79.0 |
| 2021.0 | 6893.0 | 2773.0 | 71.3 |
| 2022.0 | 10488.0 | 1152.0 | 90.1 |
| 2023.0 | 7334.0 | 421.0 | 94.6 |
| 2024.0 | 6372.0 | 415.0 | 93.9 |
| 2025.0 | 11082.0 | 394.0 | 96.6 |
| 2026.0 | 4695.0 | 323.0 | 93.6 |
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
| house | 65772 | 870 | 2529 | 508 | 33849 | 14034 | 2.5 |
| senate | 8766 | 0 | 0 | 0 | 3140 | 581 | 0.0 |
*apparié exact = même date · apparié proche = écart des dates de TRANSACTION ≤ 10 j (bruit/convention de date Quiver, même trade) · candidat écart = paire à 10–90 j, à inspecter (§6.4) · dont même déclaration = les deux trades viennent du MÊME formulaire de déclaration (PTR) — notre `disclosure` ≈ `Filed` Quiver ≤ 10 j → même trade, donc l'écart de date est un vrai désaccord (seul signal fort) · nous-seul = Quiver n'a PAS le trade (on est plus complet) · quiver-seul = on a raté.*

**Pourquoi les chiffres semblent contredire le §6.2 : c'est le niveau de strictesse.** Au Niveau 1 (sans date), le trou coté (borne haute) est 838/0 ; au Niveau 2 (trade + date), on compte 33849 trades « nous-seul » — normal, on trade plus souvent que Quiver ne capte au trade près. **Les deux disent la même chose : on est plus complet.**

### 6.4 Les candidats d'écart de date (même déclaration)

Les **seuls** candidats honnêtes d'erreur de date = les paires issues de la **même déclaration (PTR)** (508 House / 0 Sénat). Prudence : un petit delta peut être une **convention de date Quiver**, pas notre erreur. **Le vrai contrôle des dates reste l'audit PDF (§3)**, pas Quiver. `doc_id` = pièce consultable :

| chambre | déposant | ticker | sens | notre date | date Quiver | delta (j) | doc_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| house | Michael T. McCaul | GOOGL | Purchase | 2018-07-26 | 2018-08-06 | 11 | 9113676 |
| house | Rohit Khanna | ETR | Sale | 2020-04-07 | 2020-04-18 | 11 | 8217213 |
| house | Rohit Khanna | VRSK | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | IT | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | CDNS | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | AMT | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | NKE | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | PG | Sale | 2025-04-04 | 2025-04-15 | 11 | 8220906 |
| house | Rohit Khanna | UNP | Sale | 2025-04-04 | 2025-04-15 | 11 | 8220906 |
| house | Rohit Khanna | DHR | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | MSCI | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |
| house | Rohit Khanna | EW | Sale | 2023-10-26 | 2023-11-06 | 11 | 8220039 |

*(Top 12 par delta croissant ; les 508 candidats sont dans `quiver_validation/candidats_ecart_date_meme_depot.csv`.)*

### 6.5 Niveau 3 — Que reste-t-il à corriger ?

On a vérifié l'**existence** (§6.2) et la **date** (§6.3). Restent deux choses : les **autres champs** des trades qu'on partage avec Quiver (sens, montant), et la **liste de ce qui est vraiment à corriger**.

**Autres champs — sens & montant.** Pour les trades qu'on a **tous les deux** (mêmes membre + ticker + date), est-on d'accord sur le sens (achat/vente) et le montant ?

| chambre | n paires | accord sens % | accord montant % |
| --- | --- | --- | --- |
| house | 80628 | 96.6 | 93.8 |
| senate | 9775 | 99.9 | 99.8 |
*on apparie les cellules (membre, ticker, date) présentes des DEUX côtés ; un désaccord = vraie erreur d'extraction, listée dans `desaccord_champ_*.csv`.*

**La to-do (à corriger).** Un seul chiffre est **dur** — les vrais trous `NOTRE_MANQUE` (le résidu après tous les filtres) ; les deux autres sont des **bornes hautes** ensemblistes = des listes à revoir cas par cas dans `docs/quiver_validation/`, pas des taux d'erreur :

| à corriger | House | Sénat | nature | annexe |
| --- | --- | --- | --- | --- |
| vrais trous cotés (`NOTRE_MANQUE`) | 1019 | 11 | **DUR** — vrai trou confirmé au trade près (le sous-ensemble des « trous borne haute » du §6.2 réellement absents) | `notre_manque_*` |
| lignes OCR papier (`MANQUANT_PAPIER`) | 4302 | 0 | borne haute — trades Quiver de déposants qu'on OCR, absents de nos clés exactes | `manquant_papier_*` |
| tickers à revoir (`ECART_TICKER`) | 8408 | 190 | borne haute — autre ticker ce jour-là (gonflée par la multiplicité, PAS un taux d'erreur) | `ecart_ticker_*` |
**Qui ?** — les déposants derrière les vrais trous (`NOTRE_MANQUE`), à investiguer :

| chambre | bioguide | nom | n trous |
| --- | --- | --- | --- |
| house | M001193 | Thomas MacArthur | 228 |
| house | T000475 | David A. Trott | 172 |
| house | F000461 | Bill Flores | 152 |
| house | Y000062 | John A. Yarmuth | 83 |
| house | S000583 | Lamar Smith | 58 |
| house | R000583 | Thomas J. Rooney | 45 |
| house | L000579 | Alan S. Lowenthal | 44 |
| house | H001051 | Richard L. Hanna | 28 |
| senate | C001075 | William Cassidy | 5 |
| senate | M001198 | Roger W Marshall | 3 |
| senate | R000608 | Jacklyn S Rosen | 2 |
| senate | D000622 | Tammy Duckworth | 1 |

### 6.6 Annexe

Les tables **figées** `07c/07g/07h` reproduisent la même comparaison en *exact-date* (elles **sous-comptent**, cf. §6.3) ; conservées pour la lignée/régression, non re-rendues ici. Les autres figées (`07/07b/07d/07e/07f/06d`) sont des sorties historiques du pipeline.

**Profil des clusters de scan (House OCR)** — pourquoi le manuscrit est exclu (A = tapé droit, B = tapé tourné, C = manuscrit) :

| cluster | n lignes | n docs | date plausible % | ticker % | Quiver a le trade % |
| --- | --- | --- | --- | --- | --- |
| A_tape_droit | 5957 | 59 | 99.6 | 84.5 | 88.0 |
| B_tape_tourne | 78678 | 1397 | 96.7 | 84.7 | 66.1 |
| C_manuscrit | 2376 | 183 | 98.5 | 84.3 | 13.5 |
*`date plausible %` / `ticker %` = qualité INTERNE (sans Quiver) · `Quiver a le trade %` = part de nos trades cotés que Quiver possède AUSSI (appariée sur membre+ticker+sens, date ou non). Sur le manuscrit (C), la qualité interne reste haute mais `Quiver a le trade %` s'effondre (ticker/identité mal lus, ou Quiver mince sur le papier) → faute de pouvoir le confirmer contre la vérité-terrain, on l'exclut par défaut (conservateur).*

Listes actionnables complètes (ligne à ligne) → `docs/quiver_validation/` (`ecart_ticker_*`, `notre_manque_*`, `manquant_papier_*`, `desaccord_champ_*` [typé], `on_est_plus_complet_*`, `quiver_non_cote_*`, `candidats_ecart_date_meme_depot`). Hors golden.

