# Congress Trading Signal — mémoire projet (LIS-MOI EN PREMIER)

Tu reprends un projet de recherche quant (Ramify / QIS / Valhyr). Objectif final : backtester une stratégie de copy-trading des transactions boursières déclarées par les membres du Congrès US. **Cette session = UNIQUEMENT le bloc DONNÉES** (voir Mission).

## Mission de cette session
Amener le pipeline de données à sa version **la plus propre, reproductible et explicable**, par **exécution réelle de bout en bout** des notebooks `00 → 09` :
1. Tout réexécuter en local (ici, les sites .gov, theunitedstates.io et l'API Quiver sont accessibles, contrairement à l'environnement où le squelette a été construit).
2. **Mesurer le VRAI taux de parsing House** sur le corpus complet (jamais mesuré jusqu'ici).
3. Combler les trous réels — notamment la **queue Sénat 2021 → aujourd'hui**.
4. **Challenger** les choix, corriger les bugs, produire une **note critique** + une structure finale claire.

Hors-périmètre (sessions ultérieures, NE PAS commencer) : mapping GICS→ETF, stratégie, backtest.

## RÈGLES NON-NÉGOCIABLES (ne jamais enfreindre)
1. **Transparence** : tout le code de transformation vit DANS les notebooks, inspectable. Aucune API boîte noire comme source canonique. Réutiliser de l'open source est encouragé (le porter dans le notebook).
2. **Quiver = vérification externe UNIQUEMENT.** Jamais réinjecté dans la table finale.
3. **Aucun contournement anti-bot.** Pas de proxy résidentiel, pas de CAPTCHA, pas d'automatisation du gate d'agrément eFD. Si un site bloque l'accès programmatique → données ouvertes ou accès manuel. Pas d'exception.
4. **Conventions notebooks** : cellules courtes mono-tâche, **chacune précédée d'une cellule markdown d'une phrase**. Le notebook doit se lire comme une histoire claire.
5. **Aucune règle de nettoyage silencieuse.** Chaque transformation est documentée + journalisée (compte avant/après).
6. **`disclosure_date` ≠ date du PDF.** House = FilingDate de l'index XML ; Sénat = `date_recieved` des daily summaries. C'est la date anti look-ahead : ne JAMAIS la dériver de la "Notification Date" du PDF.

## Façon de travailler (TRÈS IMPORTANT)
- **Commence par NE PAS coder.** Lis tout (`README.md`, `reports/EXECUTION_REPORT.md`, `docs/`, les 10 notebooks), puis **re-restitue le plan + tes questions/désaccords** à l'utilisateur, et **attends son feu vert**.
- Avance ensuite par petits incréments, avec un **point d'étape à chaque décision**. Pas de fuite en avant. C'est le rythme attendu.
- Si, après avoir vu les vraies sorties, tu es en désaccord avec une décision ci-dessous : **argumente avec les données**, ne l'écrase pas en silence.

## Architecture (et pourquoi)
- **House** (gros du volume) : source primaire officielle `disclosures-clerk.house.gov` (ZIP annuels → index XML → `FilingType=P` (PTR) → PDF). Parsing ancré sur marqueurs `(TICKER) [TYPE]`.
- **Sénat** : pas de bulk machine-readable + Akamai + gate d'agrément. Donc socle via **données ouvertes** — Senate Stock Watcher `all_daily_summaries.json` (fournit `date_recieved` ET `bioguide`). Queue récente via **kadoa** (à vérifier). Provenance vérifiée sur échantillons eFD **téléchargés manuellement** (notebook 06).
- **Identité** : `unitedstates/congress-legislators` (BioGuideID + commissions). Sénat rattaché par bioguide fourni ; House par nom normalisé → BioGuideID.
- **Sortie canonique** : `data/processed/congress_transactions.csv` (+ parquet). Quiver (08) vérifie, ne nourrit pas.

## État courant (run partiel déjà fait, sandbox SANS accès .gov/Quiver)
Exécuté réellement : Sénat + référentiel + unification + qualité.
- Référentiel : **12 767** législateurs (197 sur commission clé).
- Sénat (daily summaries) : **8 030** transactions → **6 933** après dédup ; `disclosure_date` 0 manquant ; **BioGuideID 100%** ; ~1 073 sans ticker.
- **Couverture Sénat s'arrête ~mars 2021** (dataset ouvert périmé).
NON exécuté (bloqué) : House `02-04` (parser validé sur **1 seul** vrai PTR Pelosi), Quiver `08`, provenance `06`.
→ Détails/chiffres : `reports/EXECUTION_REPORT.md`.

## Décisions déjà tranchées (à APPLIQUER, sauf contre-preuve par les données)
1. **§105(c)** (usage commercial des déclarations) : **bloquant pour la PRODUCTION, pas pour la R&D.** Continuer la R&D ; rappeler que c'est à faire valider par la direction/juridique avant tout usage client. Ne PAS le traiter comme résolu.
2. **Déduplication** (la clé actuelle sur-fusionne — 1 097 lignes perdues). Nouvelle règle :
   - clé = `(bioguide_id | nom normalisé) + transaction_date + ticker + operation_type + amount_range + owner + index d'occurrence intra-dépôt` → préserve deux lots distincts identiques d'un même PTR ;
   - dédup des **vrais doublons** (même `doc_id`/`ptr_link`, ou copie cross-source) en **préférant la source primaire** ;
   - **dépôts amendés** : garder le plus récent, marquer l'ancien `superseded`, ne pas fusionner en silence ;
   - **reporter les comptes retirés par règle** + 3 vérifs manuelles sur des cas "même jour / même ticker".
3. **Queue Sénat récente** : primaire = **kadoa** (open, MIT) SI vérification montre une vraie couverture 2021→présent avec disclosure date ; sinon **signaler le trou honnêtement** (pas de scraping eFD). Splicer kadoa (≥2021) sur Stock Watcher (≤2021), dédup sur la jointure. Porter une note `data_freshness` par source.
4. **Complétude** = **ère électronique, niveau Member** : House ~2014→présent + Sénat ~2014→présent. Exclus/backlog **documentés et comptés** : papier/scanné pré-2014 ; PDF House `no_text` (→OCR) ; lignes sans ticker résoluble (obligations/options/fonds → backlog résolution, **NON supprimées**). "Complet" = "tout l'électronique Member-level avec provenance, chaque exclusion comptée et expliquée".

## Definition of done (cette session)
- `00 → 09` tournent de bout en bout sur un clone propre (réseau + token fournis), **sans patch manuel**.
- **Taux de parsing House mesuré et reporté** (cible ≈ ≥ 90% des PTR à texte exploitable ; reste → backlog avec raisons).
- Champs garantis zéro-manquant sur le périmètre, chaque exclusion comptée.
- Chaque règle de nettoyage journalisée (avant/après).
- Dédup transparente (comptes par règle) + vérifs manuelles.
- `reports/data_quality.md` à jour (couverture House + Sénat, frontières, backlog).
- **Note de recherche critique** : ce qui est solide / fragile / à surveiller pour le backtest (rappeler l'**alpha post-2012 contesté** : sur moyenne des membres, pas d'alpha clair dans la littérature post-STOCK Act).

## Champs garantis de la table finale
`declarant_name, chamber, party, committee_membership, transaction_date, disclosure_date, ticker, operation_type, amount_midpoint, asset_type` (+ `bioguide_id, source, provenance, owner, doc_id, source_url, natural_key_hash`).
