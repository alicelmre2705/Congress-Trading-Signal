# Divulgations parlementaires — les réponses

> Réponse point par point au document de travail « vérifications et travaux à faire » : six
> vérifications (C1→C6) et deux travaux (T1, T2). Chaque section donne la question telle qu'elle a
> été posée, ce qu'elle supposait, ce qu'on a mesuré, et ce que le chiffre décide. **Les deux
> travaux sont livrés** ; quatre vérifications sont tranchées, une est instrumentée mais pas encore
> mesurable, une est diagnostiquée. Ce document ne défend aucune hypothèse : il les remplace par des
> quantités. Établi le **2026-08-26**, sur la table `data/clean/` du commit `22fb97fe`.

## Le tableau de bord

| # | la question | l'état | le chiffre qui tranche |
| --- | --- | --- | --- |
| **T2** | crawl quotidien d'horodatage | **livré** | 10 530 documents inscrits · job GitHub Actions prêt |
| **T1** | fonction de run en direct | **livré** | 12 champs de la table de référence · 0 table figée touchée |
| **C1** | `disclosure_date` = date de mise en ligne ? | **instrumenté**, mesure en cours | 90 dépôts House invisibles dans l'index embarqué |
| **C2** | délai transaction → divulgation | **mesuré** | médiane **27 j** (House) / **24 j** (Sénat) · **12,5 %** hors délai |
| **C3** | gestion déléguée : quelle date ? | **tranché** | l'élu n'est informé le jour même que dans **13,0 %** des cas |
| **C4** | rendement des manuscrits avant exclusion | **tranché** | l'effet est **entièrement porté par un seul déposant** |
| **C5** | fraîcheur du mapping des noms | **diagnostiqué** | source modifiée tous les **6 j** · copie locale vieille de 2 mois |
| **C6** | échange et autres types de transaction | **tranché** | **63,5 %** des échanges ne déclarent qu'une seule jambe |

*l'état dit ce qu'on peut faire aujourd'hui : « tranché » = la décision est prise et chiffrée · « diagnostiqué » = le défaut est établi, le correctif reste à écrire · « instrumenté » = la collecte tourne, la mesure demande du temps calendaire*

## Le vocabulaire : trois dates — il y en a quatre

Le document de travail en distingue trois. Le formulaire PTR de la Chambre en impose une
**quatrième**, et c'est elle qui répond à C3.

| date | ce qu'elle est | rôle | état |
| --- | --- | --- | --- |
| `transaction_date` | date de l'opération déclarée | descriptif seul, et ancienneté d'un lot (FIFO) | présente |
| `notification_date` | date à laquelle le déclarant dit avoir été **informé** | sépare la décision propre de la gestion déléguée | **récupérée le 2026-08-25** |
| `disclosure_date` | `FilingDate` de l'index Clerk / date de réception au Secrétariat du Sénat | candidate au timestamp de signal, à valider | présente |
| `first_seen_at` | date à laquelle **nous** voyons le document en ligne | seule date certainement publique | **collectée depuis le 2026-08-25** |

*« Date Notified of Transaction » est une colonne obligatoire du PTR House : les deux parseurs déterministes la capturaient depuis toujours (groupe `notif` de `TXN_RE` et `_LEGACY_TXN_RE`) sans jamais lire le groupe, et le prompt Vision la demandait explicitement sans l'exposer. Elle était donc déjà payée, des deux côtés.*

**La règle de fond est en place dans le code** : `common/live_run.py` écrit
`signal_date = max(disclosure_date, first_seen_at)`, jamais `transaction_date`. La protection ne
dépend donc pas du résultat de C1.

**Seule exception légitime à `transaction_date`** : l'ancienneté d'un lot dans le FIFO
(`02_recherche_backtest/tools/moteur.py :: tranches_vendues`) — la détention réelle de l'élu court
depuis la transaction, pas depuis la publication.

## T2 · Crawl quotidien d'horodatage — livré

**Ce qui était demandé.** « Un job quotidien qui n'a qu'un seul rôle, écrire
`(document_id, first_seen_at)` pour tout ce qui apparaît. »

**Ce qui existe.** `common/first_seen.py`, plus `.github/workflows/first_seen.yml` (cron quotidien
06:00 UTC + déclenchement manuel). Trois partis pris :

Le module **n'importe rien du pipeline** — `requests` et la bibliothèque standard, rien d'autre. Il
parse le XML du Clerk et poste la recherche eFD lui-même plutôt que d'appeler `house.digital` ou
`senate.digital`. C'est délibéré : la donnée de ce job ne se reconstitue pas, il ne doit jamais
tomber parce qu'un module lourd a bougé ailleurs.

Le fichier `data/first_seen/first_seen.csv` est en **append seul** : un `doc_id` déjà vu n'est
jamais réécrit, puisque c'est la *première* observation qui définit `first_seen_at`.

Le workflow fait un **sparse-checkout** : le dépôt pèse 727 Mo de `.git` et 1,5 Go de source
primaire, un checkout complet quotidien serait absurde. Le job ne récupère que `common/`, `senate/`
et `data/first_seen/`, et n'installe que `requests`.

| grandeur | valeur |
| --- | --- |
| documents inscrits | **10 530** — house 8 342 · senate 2 188 |
| dont amorçage (`backfill`) | 10 402 |
| dont rattrapage au premier passage | 128 |
| démarrage du crawl | **2026-08-25** (`data/first_seen/_meta.json`) |

*`backfill` = tout le corpus connu, inscrit à la date de l'amorçage · `rattrapage` = déposé avant le démarrage du crawl, donc déjà en ligne quand on l'a vu · **les deux sont exclus par construction** de toute statistique sur l'écart de mise en ligne : leur `first_seen_at` mesure notre retard de démarrage, pas le délai de publication.*

**Lecture.** Le journal existe et l'horloge tourne. Sa valeur analytique est nulle aujourd'hui et le
restera quelques semaines — c'est la nature de la mesure, pas un défaut. Le seul geste qui compte
maintenant est de **pousser la branche** : tant que le workflow n'est pas sur GitHub, chaque jour
qui passe est un jour d'horodatage perdu définitivement.

## T1 · Fonction de run en direct — livré

**Ce qui était demandé.** « Une fonction appelable qui, à chaque exécution, regarde les sources,
détecte les documents nouveaux, les fait passer par tout le pipeline et produit une ligne de données
au format exact de la table p. 31. »

**Ce qui existe.** `common/live_run.py`. Le format de sortie est bien celui de la p. 31 du deck
(slide « 8 · À quoi ressemble la valeur finale »), **12 champs garantis** : membre · chambre ·
parti · comités · date trade · date div. · sens · montant $ · type · ticker · secteur · ETF —
plus `first_seen_at`, `notification_date`, `doc_id`, `natural_key_hash` et `signal_date` pour la
traçabilité.

**Le choix d'architecture, et pourquoi il n'était pas évitable.** Le pipeline existant est bâti pour
reconstruire des **années entières** : `house.digital.run_year` re-parse tout l'index et réécrit
`data/house/tables/{Y}/` ; `senate.fusion` n'a pas d'option d'année (il globe tout, ré-enrichit le
corpus complet et réécrit les 13 tables FINAL du Sénat) ; les steps 6-8 relisent toujours les
26 FINAL. Or ces tables sont verrouillées à l'octet par le filet golden (230 + 138 fichiers). **Un
run quotidien qui passerait par là casserait le filet tous les jours.**

`live_run` ouvre donc une voie parallèle : il réutilise les fonctions pures (parseurs, clé
naturelle, matcher d'identité, ticker canonique, enrichissement point-in-time) et n'écrit que dans
`data/live/`. La réconciliation avec le corpus figé se fait au run de pipeline complet suivant.
`tests/regression/test_live_run.py` vérifie cette étanchéité en comparant le sha256 des **369
tables** avant et après : zéro modification.

**Deux limites, dites franchement.** Les documents **scannés** ne sont pas traités par le run
quotidien : ils exigent d'abord la classification (tapé/manuscrit), et `house/classify_scans.py`
n'est pas dans le pipeline — il se lance à la main. Côté Sénat, le classifieur n'est **pas versionné
du tout** : ses caches et son census existent, aucun script de `senate/` ne les produit. Les scans
sont donc signalés à chaque passage et restent « nouveaux » au suivant. Rien n'est perdu, mais le
trou est réel.

## C1 · La date de divulgation est-elle la date de mise en ligne ?

**La question.** « La `disclosure_date` inscrite sur le document correspond-elle exactement au jour
où le document apparaît sur le site ? »

**Ce que le pipeline supposait.** Que oui. Côté House, `disclosure_date` est le `FilingDate` de
l'index XML du Clerk (`house/digital.py :: load_ptr_index`) ; côté Sénat, la date de réception lue
dans le résultat de recherche eFD (`senate/digital.py :: fetch_ptr_list`). **Dans les deux cas c'est
une date portée par le document, pas une publication observée.** Rien, dans les données, ne disait
quand le document était devenu accessible.

**Ce qu'on peut mesurer aujourd'hui : rien — et c'est la réponse.** Le crawl a démarré le
2026-08-25 ; `first_seen.csv` ne porte qu'une seule date d'observation. La distribution
`first_seen_at − disclosure_date` demande plusieurs semaines de collecte. Aucun raccourci n'existe :
le journal d'acquisition (`data/house/pdfs/{Y}/00_download_log.csv`) ne porte aucun horodatage et
il est réécrit à chaque run ; les mtime des PDF valent tous la date de la dernière synchro disque.

**Le seul chiffre citable, et il est éloquent.** Au premier passage du crawl, l'index frais du Clerk
listait **364 PTR pour 2026** contre **274** dans l'index embarqué du dépôt, téléchargé le
3 juillet : **90 dépôts House invisibles** pendant sept semaines. La cause est identifiée —
`house/acquire.py :: download_index` fait `if dest.exists(): return`, donc un index déjà présent
n'est jamais rafraîchi et l'année en cours ne voit jamais ses nouveaux dépôts.

**Lecture.** C1 n'est pas tranché, mais il n'est plus aveugle : l'instrument est posé et le
`max(disclosure_date, first_seen_at)` protège le backtest en attendant. **Relecture à prévoir vers
le 2026-10-01** (~5 semaines de collecte). Critère de décision inchangé : écart nul dans plus de
99 % des cas, on peut utiliser `disclosure_date` ; sinon on garde le `max` et on publie la
distribution du décalage.

## C2 · Délai entre transaction et divulgation

**La question.** « Quelle est la distribution de `disclosure_date − transaction_date` ? »

**Ce qui existait déjà.** La colonne `lag_days` (`common/quality.py :: load_final`), les flags
`flag_late_filing` (> 45 j) et `flag_very_late_filing` (> 365 j), et le §3 du rapport avec la
ventilation ≤45 j / 45-75 j / >75 j. Ce qui manquait : le croisement **année × chambre**.

| année | house n | médiane | > 45 j | sénat n | médiane | > 45 j |
| --- | --- | --- | --- | --- | --- | --- |
| 2014 | 10 037 | 23 j | 7,4 % | 887 | 14 j | 7,7 % |
| 2015 | 9 842 | 22 j | 8,0 % | 1 431 | 19 j | **26,6 %** |
| 2016 | 7 503 | 25 j | 12,3 % | 1 407 | 21 j | 23,5 % |
| 2017 | 12 381 | 28 j | 15,0 % | 1 525 | 19 j | 9,0 % |
| 2018 | 14 349 | 27 j | 11,7 % | 1 873 | 24 j | 13,3 % |
| 2019 | 12 856 | 29 j | 14,6 % | 1 663 | 26 j | 19,3 % |
| 2020 | 16 198 | 30 j | 18,9 % | 1 909 | 24 j | 12,6 % |
| 2021 | 12 249 | 33 j | **30,4 %** | 912 | 29 j | 26,0 % |
| 2022 | 14 439 | 27 j | 7,8 % | 1 093 | 28 j | 3,9 % |
| 2023 | 10 459 | 27 j | 5,3 % | 1 129 | 29 j | **1,3 %** |
| 2024 | 8 955 | 25 j | 8,0 % | 1 028 | 28 j | 4,4 % |
| 2025 | 13 629 | 27 j | 9,8 % | 1 335 | 28 j | 5,8 % |
| 2026 | 6 176 | 22 j | 4,3 % | 781 | 23 j | 4,0 % |
| **total** | **149 073** | **27 j** | **12,5 %** | **16 973** | **24 j** | **12,8 %** |

*n = lignes dont le délai est CALCULABLE (les deux dates présentes et lisibles) · année = année de divulgation · « > 45 j » = part au-delà du délai réglementaire · les 274 délais négatifs (0,2 %) sont comptés dans n*

**Le délai réglementaire, à corriger.** Le code pose `LEGAL_DELAY_DAYS = 45`
(`common/quality.py:39`) sans citation. La règle du STOCK Act est en réalité **double** : au plus
tard 30 jours après avoir *été informé* de la transaction, et en tout état de cause **45 jours après
la transaction**. Le seuil de 45 j est donc le bon plafond, mais il masque la vraie contrainte — et
c'est exactement la distinction que `notification_date` permet enfin de mesurer (cf. C3).

**Le test anti-look-ahead : la spécification, et un cas réel déjà trouvé.** Le document demande
« un test qui échoue si une feature est calculée sur un axe temporel indexé par
`transaction_date` ». Il reste à écrire, mais son objet est cerné :

Dans le pipeline, aucun axe temporel n'est indexé sur `transaction_date` — l'entonnoir de
`backtest_clean` ne s'en sert que pour des filtres de plausibilité. **En aval, c'est différent** :
la famille *titre* (M3, le livrable) entre bien sur `disclosure_date`
(`02_recherche_backtest/tools/donnees.py`, index `ide`/`I_de`), mais la famille *membre*
(`tools/membre/`) entre en position sur `transaction_date`, renommée `traded`
(`membre/donnees.py`, exécution `membre/moteur.py :: eff_price`). C'est une convention assumée
d'une famille descriptive — les deux ne sont jamais mélangées, et `tools/README.md` le dit. **Mais
cela doit être tranché explicitement plutôt que rester implicite** : soit le test l'échoue et force
la décision, soit il l'accepte sur une liste blanche nommée et commentée, aux côtés du FIFO γ.

**Lecture.** La distribution est stable autour de 27 jours et le taux hors délai s'est **effondré
depuis 2022** (30,4 % en 2021 → 4,3 % en 2026 côté House). 2021 est l'année noire des deux chambres,
et 2015-2016 celle du Sénat. Le retard de déclaration est donc bien un signal sur le déclarant, mais
un signal **daté** : l'utiliser sans contrôler l'année reviendrait à mesurer un changement de régime
de conformité plutôt qu'un comportement individuel.

## C3 · Gestion déléguée : quelle est la date de transaction ?

**La question.** « Dans le cas d'un compte en gestion déléguée, la date de transaction déclarée
est-elle la date d'exécution par le gérant, ou la date de notification au parlementaire ? »

**La réponse était dans les documents depuis le début.** Le formulaire PTR House impose **deux**
dates par ligne. `transaction_date` est bien la date d'**exécution**. Et le formulaire porte une
seconde colonne — *Date Notified of Transaction* — qui existe précisément pour ce cas : elle dit
quand le déclarant a été **informé**. Les deux parseurs déterministes la capturaient depuis toujours
sans jamais lire le groupe ; l'OCR Vision la demandait et l'écrivait dans ses caches, où elle ne
servait que de repli mort.

**Ce qu'on a fait.** `common/notification_dates.py` la récolte depuis les PDF et les caches OCR
**déjà payés** — zéro appel API — dans un référentiel annexe (`data/reference/notification_dates.csv`,
153 885 lignes) appliqué à la **lecture**, pour ne pas réécrire les tables figées. Les colonnes
`notification_date` et `notif_lag` sont exposées dans `data/clean/`.

| sous-corpus | n | couverture | informé le jour même | ≤ 7 j | 8–30 j | > 30 j | médiane |
| --- | --- | --- | --- | --- | --- | --- | --- |
| House électronique | 58 701 | 100,0 % | **18,1 %** | 45,3 % | 41,7 % | 12,7 % | **10 j** |
| House OCR (papier) | 92 390 | 99,1 % | **9,7 %** | 20,6 % | 63,5 % | 15,4 % | **18 j** |
| **House, ensemble** | **151 091** | **99,4 %** | **13,0 %** | 30,2 % | 55,0 % | 14,3 % | **15 j** |

*couverture = part des lignes dont la 2e date est lisible · « ≤ 7 j » inclut « le jour même » · les trois derniers buckets somment à 99,5 % : le solde de 0,44 % est constitué des **666 lignes à `notif_lag` négatif**, non représentées · le **Sénat est absent** du tableau — son formulaire n'a qu'une colonne de date, ce n'est pas un défaut de collecte*

⚠️ **Ne jamais citer la moyenne de `notif_lag`** (18,0 j) : la colonne porte des dates OCR
aberrantes non filtrées (min −32 858 j, max +65 743 j). Médiane et parts seulement.

**Lecture.** La date déclarée est bien celle de l'**exécution**, et **87 % des lignes ne sont pas
notifiées le jour même** : la médiane est de 15 jours. La majorité des transactions déclarées ne
sont donc pas des décisions prises par l'élu en connaissance de cause au moment de l'ordre. L'écart
entre les deux voies est le second enseignement : le papier scanné n'informe l'élu le jour même que
dans **9,7 %** des cas contre **18,1 %** en électronique — le papier est le canal de la gestion
déléguée. `notif_lag` sépare désormais les deux populations ; **c'est le filtre à appliquer avant de
lire ces lignes comme un signal d'initié**, et il recoupe directement C4.

## C4 · Documents manuscrits : le rendement avant de figer l'exclusion

**La question.** « On a décidé de retirer les documents remplis à la main. Avant de figer cette
exclusion : quel est le rendement des opérations qu'ils contiennent ? » Deux hypothèses opposées
étaient posées : bruit administratif sans conséquence, ou bien **moyen de se soustraire aux
contrôles automatisés** — auquel cas l'exclusion retirerait le meilleur signal du dataset.

**La saisie manuelle proposée n'était pas nécessaire.** La table
`data/clean/transactions_gated_2014_2026.csv` porte déjà, pour ses **7 287 lignes**, le ticker
(100 % non vide), le sens, le montant et les deux dates. **5 590 lignes** ont une série de prix
exploitable, soit 76,7 %. L'event-study était donc mesurable immédiatement, sur la population
entière plutôt que sur un échantillon de 50 à 100 documents.

**La population, d'abord.** Le census classe **775 documents** en `C_manuscrit`, dont **582 sont
écartés** (775 − 33 documents hérités curés à la main − 160 documents de trois déposants récupérés
parce que Quiver les corrobore). **95 parlementaires** déposent du manuscrit, 85 parmi les écartés.
Mais compter en documents et compter en transactions ne désigne pas les mêmes personnes :

| | en documents (census) | en transactions (table écartée) |
| --- | --- | --- |
| tête | Marchant 83 · Polis 72 · Kelly 63 · Upton 56 | **McCaul 4 195 (57,6 %)** · Marchant 968 · Khanna 633 |
| concentration | 85 membres | 51 membres, **top 5 = 88,6 %** |

**La mesure.** Event-study relatif au marché, entrée à la **divulgation** (jamais à la transaction),
excès signé par le sens : un achat gagne quand le titre monte, une vente quand il baisse. Le groupe
de **contrôle** est la table publiée, mesurée exactement de la même façon — sans lui, un chiffre
isolé ne déciderait rien.

| population | 5 j | 21 j | 63 j | 126 j | 252 j |
| --- | --- | --- | --- | --- | --- |
| **contrôle — table publiée** (n≈116 000) | +0,04 (t 3,5) | +0,09 (t 3,5) | +0,06 (t 1,2) | −0,02 (t −0,3) | +0,16 (t 1,2) |
| manuscrits écartés, tout (n≈5 590) | +0,12 (t 2,4) | −0,05 (t −0,5) | +0,37 (t 2,0) | **+0,87 (t 3,3)** | +0,68 (t 1,7) |
| **McCaul seul** (n≈3 013) | +0,18 (t 3,2) | +0,24 (t 1,9) | **+0,94 (t 4,0)** | **+1,43 (t 4,1)** | +1,05 (t 2,1) |
| **manuscrits SANS McCaul** (n≈2 577) | +0,05 (t 0,6) | −0,39 (t −2,3) | −0,30 (t −1,0) | +0,22 (t 0,5) | +0,25 (t 0,4) |
| cluster `C_manuscrit` (n≈4 177) | +0,13 (t 2,4) | −0,12 (t −1,0) | +0,42 (t 2,0) | +0,95 (t 3,2) | +0,42 (t 0,9) |
| cluster `B_tape_tourne` (n≈1 413) | +0,10 (t 0,9) | +0,15 (t 0,6) | +0,21 (t 0,5) | +0,61 (t 1,1) | +1,47 (t 1,6) |
| écartés · détenus par l'élu (n≈532) | +0,11 (t 0,6) | −0,82 (t −1,9) | −0,75 (t −1,0) | +0,79 (t 0,8) | −0,54 (t −0,3) |
| écartés · conjoint/enfant/joint (n≈5 058) | +0,12 (t 2,4) | +0,03 (t 0,3) | +0,49 (t 2,6) | +0,87 (t 3,2) | +0,81 (t 1,9) |

*excès moyen en % au-delà du SPY sur la fenêtre, signé par le sens · t = Student · horizons en jours de bourse · n varie légèrement selon l'horizon (une fenêtre qui dépasse la fin du calendrier est écartée)*

**Lecture — l'hypothèse « échapper aux contrôles » est réfutée.** Les manuscrits affichent bien un
excès significatif à 6 mois (+0,87 %, t 3,3), très au-dessus du contrôle. Mais **il disparaît
entièrement dès qu'on retire un seul déposant** : sans McCaul, plus rien ne survit (+0,22 %, t 0,5),
et le 21 jours devient même négatif. McCaul seul porte +1,43 % à 126 j (t 4,1).

Or McCaul est précisément le cas de la gestion déléguée pure : le deck des données établit que
**0,0 %** de ses lignes sont passées par l'élu lui-même, et que **100 %** de ses dépôts sont en
papier scanné — une fortune familiale en trusts gérés par des professionnels, qui rebalancent en
micro-lignes à la taille minimale. Le sous-tableau par détenteur le confirme : les lignes détenues
**par l'élu** (532) ne montrent rien, celles du conjoint et des enfants portent tout l'effet.

**Ce que ça décide.** L'exclusion des manuscrits est **validée**, et pour une raison plus solide que
celle qui l'avait motivée : ce n'est pas seulement que Quiver ne corrobore que **12,9 %** du cluster
C (contre 88,0 % et 65,2 % pour A et B, §6.6 du rapport) ; c'est que le rendement mesurable de cette
population n'est pas un signal d'initié — c'est la performance d'un gérant professionnel, portée par
un seul foyer. L'exclure ne retire aucun signal informationnel. **Le chantier OCR sur cette
population n'est pas justifié.**

⚠️ **La réserve, à garder.** Sur le cluster C, Quiver ne confirme que 12,9 % des trades :
l'incertitude porte sur l'identité et le ticker, pas sur le prix. Un rendement mesuré sur des
tickers mal lus mesure du bruit — ce qui, ici, va dans le sens de la conclusion (le bruit ne crée
pas de t à 4) mais interdit de lire les chiffres de McCaul comme une estimation fine.

## C5 · Mapping des noms (`congress-legislators`)

**La question.** « À quelle fréquence la source de mapping est-elle mise à jour, et est-ce qu'on la
récupère en direct ou depuis une copie figée ? »

**Le diagnostic est plus embêtant qu'un mapping figé : il est asymétrique et silencieux.**

**House récupère en direct.** `common/reference.py` pointe les URL
`unitedstates.github.io/congress-legislators/*.json` et `house/digital.py` appelle
`load_reference(…, live=True)`. Mais le repli sur les YAML locaux se fait dans un `except Exception`
dont l'erreur capturée n'est **jamais relue** : une panne réseau bascule sur une copie figée sans
que rien ne le signale. Et **aucun SHA, aucun tag, aucune date d'extraction n'est enregistré** — le
pipeline House n'est donc pas reproductible à l'identique d'un jour sur l'autre pour l'identité.

**Le Sénat lit des YAML en dur** (`senate/identity.py :: load_reference`), sans option live. Les
copies embarquées sont datées des **23-26 juin 2026**.

**La fréquence de la source, mesurée.** Sur `legislators-current.yaml`, 500 commits depuis 2016 :

| grandeur | valeur |
| --- | --- |
| écart médian entre deux jours de modification | **6 jours** |
| écart moyen | 11,8 jours |
| commits par mois (12 derniers mois) | 1 à 6 |
| dernier commit | **2026-08-18** |
| modifications manquées par la copie locale (23 juin → 18 août) | **9** |

*jours distincts modifiés : 317 sur une fenêtre de 3 721 jours*

**Le taux de non-appariement n'est pas nul.** 52 lignes sur 170 920 sortent des tables FINAL sans
`bioguide_id` — Angela Dawn Craig (42), Chris Van Hollen (7), Thomas Udall (3). Elles sont
rattrapées **à la lecture** par `KNOWN_IDENTITY_FIXES_BY_DOC` (`common/schema.py`), sept `doc_id`
codés en dur. C'est ce rattrapage qui produit le « identité 100 % » du rapport. Le mécanisme
fonctionne, mais il est **manuel et muet** : chaque nouveau nom cassé exige une édition de code.

Pire, une erreur de mapping peut être **invisible au compteur** : le commentaire de
`common/schema.py:151` documente une collision d'homonyme — Bob Casey, sénateur de Pennsylvanie,
rattaché au représentant du Texas `C000228`. Un **mauvais** bioguide, pas un vide. Le matcher n'a
par ailleurs aucun rapprochement flou : cascade exacte, dictionnaire de 25 surnoms, repli par nom de
famille unique, puis `None`.

**Ce que ça décide.** Un rafraîchissement **hebdomadaire** suffit — la médiane de 6 jours ne
justifie pas le quotidien. Quatre correctifs, par ordre d'urgence : (1) enregistrer le SHA du commit
source dans les métadonnées du run, pour qu'un run rejoué refixe exactement le même mapping ;
(2) rendre le repli **bruyant** et faire figurer `source ∈ {live, local-yaml}` dans le rapport ;
(3) logger les noms non résolus dans un fichier et publier le taux de non-appariement **par mois** —
c'est l'indicateur qui doit rester à zéro ; (4) symétriser le Sénat, qui n'a aujourd'hui aucun accès
direct. Le test `tests/regression/test_identity.py` **imprime** les dérives de millésime sans jamais
échouer : il devrait échouer au-delà d'un seuil.

## C6 · Types de transaction : au-delà de l'achat et de la vente

**La question.** « Peut-on prendre en compte l'échange, et que faire des autres types présents dans
le champ ? »

**L'inventaire, sur les 26 tables FINAL.** Sept valeurs distinctes, pas cinq :

| valeur déclarée | lignes | part | d'où elle vient |
| --- | --- | --- | --- |
| `Purchase` | 88 065 | 51,52 % | les quatre voies |
| `Sale` | 66 246 | 38,76 % | House OCR 42 711 · House élec. 21 800 · Sénat OCR 1 735 |
| `Sale (Partial)` | 9 800 | 5,73 % | House élec. 6 731 · Sénat élec. 3 069 |
| `Sale (Full)` | 4 171 | 2,44 % | Sénat électronique seul |
| `Partial Sale` | 1 421 | 0,83 % | **House OCR seul — autre graphie du même concept** |
| `Exchange` | 1 211 | 0,71 % | House élec. 612 · House OCR 442 · Sénat élec. 132 · Sénat OCR 25 |
| `Dependent Child` | 6 | 0,00 % | **bug de parsing** : la valeur `owner` a fui dans le champ type |

*part du corpus brut (170 920 lignes, avant déduplication cross-année) · quatre graphies pour deux concepts : la vente totale s'écrit `Sale` ou `Sale (Full)`, la partielle `Sale (Partial)` ou `Partial Sale`, selon la voie*

**L'échange ne porte pas ses deux jambes.** C'est le point qui tranche. Le document supposait
« a priori un échange se modélise comme une vente plus un achat au même horodatage, mais il faut
vérifier que le document donne bien les deux jambes ». Vérification faite, en regroupant les
1 211 lignes `Exchange` par (document, date de transaction) :

| groupes (document × date) | nombre | part |
| --- | --- | --- |
| **une seule ligne** — une seule jambe déclarée | **352** | **63,5 %** |
| deux lignes | 103 | 18,6 % |
| trois lignes et plus | 99 | 17,9 % |

*554 groupes au total · ticker renseigné sur 72,5 % des lignes d'échange*

**Ce que ça décide.** Dans **près de deux tiers des cas, le document ne donne qu'une jambe** :
l'échange n'est pas reconstructible en vente + achat. Il doit rester **« ignoré », et cette
catégorie est désormais assumée et chiffrée** — 1 211 lignes, 0,71 % du corpus, dont 826 sortent à
l'étape C de l'entonnoir (les autres étaient déjà écartées en amont pour date ou ticker). Les 103
groupes à deux lignes seraient reconstructibles, soit ~206 lignes sur 170 920 : le gain ne paie pas
le risque de fabriquer une jambe absente.

**Le vrai sujet n'est pas l'échange, ce sont les ventes partielles.** `Sale (Partial)` +
`Partial Sale` = **11 221 lignes**, soit neuf fois le volume des échanges. Elles sont aujourd'hui
traitées comme des ventes **totales** : la table clean ne conserve que `direction ∈ {buy, sell}` et
`operation_type` n'y remonte pas. C'est une **surestimation systématique de la taille des sorties**,
et c'est le seul point de C6 qui déplace vraiment un chiffre.

**Table de correspondance proposée** — type déclaré → effet sur la position :

| type déclaré | effet | lignes | statut |
| --- | --- | --- | --- |
| `Purchase` | entrée longue | 88 065 | retenu |
| `Sale`, `Sale (Full)` | sortie totale | 70 417 | retenu |
| `Sale (Partial)`, `Partial Sale` | **sortie partielle** — taille non déclarée | 11 221 | retenu, mais traité comme total ⚠ |
| `Exchange` | indéterminé — une seule jambe dans 63,5 % des cas | 1 211 | **ignoré, assumé** |
| `Dependent Child` | aucun — erreur de parsing | 6 | **ignoré** (sort déjà à l'étape A, dates vides) |

**Deux bugs à corriger, indépendamment.** Les 6 lignes où `owner` a fui dans `operation_type`
(document `8220046`, House OCR) ; et `common/crosscheck.py :: _sens`, qui teste
`startswith("sale")` — donc **`Partial Sale` y devient `?`** et n'est jamais apparié dans la
corroboration externe du §8. Les deux autres normalisations (`quality.op_class`,
`house.quiver.norm_sense`) le rattrapent, celle-là non.

## Ce qui reste ouvert

**C1 attend le calendrier.** La distribution `first_seen_at − disclosure_date` sera lisible vers le
2026-10-01. D'ici là, `signal_date = max(...)` protège le backtest. **Condition impérative : la
branche doit être poussée**, sinon le workflow ne tourne pas et le compteur ne démarre jamais.

**C5 est diagnostiqué, pas corrigé.** Les quatre correctifs (SHA du run, repli bruyant, log des non
résolus, symétrie Sénat) sont spécifiés mais non écrits — ce document ne modifie pas le code.

**C2 : le test anti-look-ahead reste à écrire**, et avec lui la décision explicite sur
`tools/membre/`.

**C6 : les ventes partielles** — 11 221 lignes traitées comme des sorties totales. Normaliser les
quatre graphies en deux concepts et exposer la colonne dans la table clean est le correctif qui
déplace le plus de matière.

**C3b : la case « excepted / blind trust » n'est lue nulle part**, ni House ni Sénat — `SKIP_RE`
la jette comme bruit d'en-tête. Côté Sénat, les 18 dépôts de type « Blind Trusts » sont comptés puis
ignorés, et les **101 annexes courtier** du §9 (Boozman 66, Burr 25, Blumenthal 6) relèvent du même
sujet que C3. C'est le chantier de parsing le plus lourd, et le seul qui reste entier.

**Un correctif de documentation.** `data/clean/README.md` annonce encore 169 000 × 41 et
118 316 × 39 ; les tables font **43** et **41** colonnes depuis l'ajout de `notification_date` et
`notif_lag`.

## Annexe — rejouer les mesures

Les chiffres de C2, C3 et C6 se rejouent depuis le dépôt :

```
cd 00_recuperation_donnees
python -m common.quality          # regénère le rapport : §3 porte C2 et C3
python tests/regression/test_backtest_clean.py   # « ZÉRO ÉCART » = la table mesurée est celle publiée
```

L'event-study de C4 exige le cache de prix (`02_recherche_backtest/cache/prices_v2/`, non versionné,
reconstructible via yfinance). Sa méthode tient en quatre règles, à reproduire à l'identique :
entrée au premier jour de bourse **≥ `disclosure_date`** ; excès = rendement du titre moins celui du
SPY sur la même fenêtre ; signe **+1 pour un achat, −1 pour une vente** ; jointure du ticker déclaré
vers le ticker de marché par `common.schema :: canonical_ticker` puis
`data/reference/ticker_renames.csv`. Le groupe de contrôle est la table publiée, passée dans la même
fonction — c'est lui qui donne son sens au chiffre.

Le tableau des commits de C5 se rejoue par l'API GitHub, sur
`repos/unitedstates/congress-legislators/commits?path=legislators-current.yaml`.
