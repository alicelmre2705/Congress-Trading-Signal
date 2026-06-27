# Rapport V2 — explications (pour COMPRENDRE, sans changer le rapport)

> Notions que tu voulais comprendre, mais qui sont **correctes / suffisantes telles quelles** dans le
> rapport (cat. 3). Aucune édition du rapport requise. Si tu décides qu'une mérite quand même d'être
> dans le rapport, on la déplace vers [`RAPPORT_V2_A_CORRIGER.md`](RAPPORT_V2_A_CORRIGER.md).

---

## §4.1 — résolution d'identité

### YAML et « embarqués »
- **Le référentiel** = un annuaire officiel public de tous les parlementaires : le projet open-source
  *congress-legislators* (pour chaque élu : bioguide, nom, parti, État, mandats, commissions).
- **YAML** = un simple **format de fichier texte** pour stocker des données en `clé: valeur` (comme
  JSON, mais plus lisible). L'annuaire et les commissions sont distribués sous cette forme → on en
  croise beaucoup.
- **« embarqués »** = on garde une **copie locale** de ces fichiers dans le dépôt
  (`data/house/reference/legislators-current.yaml`, etc.).
- **« repli »** = on télécharge l'annuaire en ligne ; **si le réseau échoue**, on retombe sur ces
  copies → le pipeline marche même hors-ligne.
- *Code* : `congress_core/identity.py:_load_people`, `:_load_committees`.

### Les variantes de noms (second prénom / premier mot du nom officiel / dernier mot d'un nom composé)
On indexe ces variantes **en plus** de `(nom, prénom)`, pour retrouver l'élu même si le PTR écrit son
nom autrement que l'annuaire :
- **second prénom** (le *middle name*) : « John **Quincy** Adams » → on indexe aussi « Quincy ».
- **premier mot du nom officiel** : l'annuaire a un « nom officiel complet » dont le 1er mot peut
  différer du champ prénom. Ex. prénom = « Jim », nom officiel = « **James** E. Banks » → on indexe
  aussi « James ».
- **dernier mot d'un nom composé** : si le nom de famille a plusieurs mots, on indexe aussi le dernier.
  Ex. « **Van Taylor** » → aussi « Taylor » ; « García Pérez » → aussi « Pérez ».
- *Code* : `congress_core/identity.py:load_reference`.

### `make_matcher` (la cascade override → exact → nom unique)
`make_matcher` **fabrique une fonction** `match(nom, prénom)` qui rend le bon bioguide. Pour un nom
déposé, elle essaie **dans l'ordre** :
1. **Override manuel** : courte liste de cas irréductibles **codés à la main** (un seul aujourd'hui :
   « Nicholas V. Taylor » = Van Taylor → `T000479`).
2. **Correspondance exacte** : cherche `(nom, prénom)` **et toutes les variantes ci-dessus** (surnoms
   compris, richard↔rick) dans l'index. Si trouvé → gagné.
3. **Repli par nom de famille unique** : si l'exact échoue mais qu'**un seul** élu porte ce nom de
   famille, on le prend.
Si rien ne marche → pas de bioguide (les 4 lignes manuscrites non rattachées).
- *Code* : `congress_core/identity.py:make_matcher`.

### Pourquoi `years_in_office` (ancienneté) est calculé *après*
Nuance : l'**année de 1re entrée en fonction** de chaque élu est **bien calculée ici** (au chargement
du référentiel, = minimum des dates de début de mandat). Ce qui est **différé**, c'est juste la
**soustraction par transaction** : `years_in_office = année(transaction) − année(1re entrée)`. Cette
colonne est ajoutée **tout à la fin** par `enrich_tenure`, parce que :
- c'est une **métadonnée post-assemblage** : on l'ajoute après avoir figé la table, pour ne pas
  perturber les schémas d'assemblage (sinon `house.ocr`/`senate.fusion`, qui réindexent sur un schéma
  fixe, créeraient une colonne vide) ;
- l'ajout est **octet-préservant** et idempotent (on n'ajoute qu'une colonne en bout de ligne).
- *Code* : `congress_core/schema.py:FINAL_POST_ENRICH`, `congress_core/enrich_tenure.py`.

### House vs Senate : quand est-ce distingué ?
La chambre **n'est pas devinée** depuis le nom : elle est **connue par construction**. Le pipeline
Chambre passe `chamber="house"`, celui du Sénat `chamber="senate"` (`enrich_identity` pose
`df["chamber"] = ce paramètre`). Pour les cas **ambigus** (même nom dans les deux chambres, ou élu
passé de l'une à l'autre), le matcher du Sénat privilégie la bonne chambre / le titulaire en exercice
(paramètre `chamber_priority`, `None` côté Chambre). Les **délégués** non-votants sont exclus côté
Sénat.
- *Code* : `congress_core/identity.py:enrich_identity`, `senate/identity.py`.

### `bioguide_id` et l'« historique »
- **`bioguide_id`** = identifiant unique officiel d'un parlementaire (`P000197` = Pelosi). Calculé
  **au moment du matching** (`enrich_identity` applique `make_matcher`).
  *(Note : sa **définition** manque dans le rapport → c'est le seul point de cette liste qui est aussi
  passé en cat. 2 « à compléter ».)*
- **« historique »** : le référentiel charge les élus **actuels ET historiques**
  (`legislators-current` + `legislators-historical`) → même un **ancien** membre est retrouvé, d'où la
  couverture complète 2020–2026.

---

## §2 — sources & acquisition

### Qu'est-ce que « eFD » ?
**eFD = Electronic Financial Disclosure** : c'est le **portail public en ligne du Sénat**
(`efdsearch.senate.gov`) où les sénateurs déposent leurs déclarations et où le public peut les
chercher/consulter. C'est l'équivalent Sénat du site du *House Clerk* côté Chambre. (Le rapport le
définit une fois en §2, mais sans dire que c'est « le site web du Sénat ».)

### « OCR », « paper », « .gif » : trois aspects, pas trois choses
Pour une déclaration **papier** du Sénat, ces trois mots décrivent **le même document** sous trois angles :
- **paper** = la **nature** du dépôt (le sénateur a déposé sur papier, pas en ligne) ;
- **`.gif`** = le **format de fichier** sous lequel l'eFD sert ce papier scanné (une **image**, une ou
  plusieurs par rapport) ;
- **OCR** = la **technique** qu'on emploie pour **lire** cette image (Optical Character Recognition, via
  Claude Vision).
Donc : un dépôt *papier* → servi en *.gif* → lu par *OCR*. (Côté Chambre, même idée, mais le scan est un
**PDF-image** plutôt qu'un `.gif`.)

### Le parcours d'acquisition, concrètement
- **Chambre** (ton souvenir est juste) : le *Clerk* publie un **ZIP par année** → il contient l'**index
  XML** `{an}FD.xml` (une ligne par dépôt : `DocID`, nom, État/district, type, date) → on garde les
  PTR (`FilingType=P`) → chaque `DocID` pointe vers un **PDF** → on télécharge, puis on **ouvre** le PDF
  pour savoir s'il est lisible (texte) ou scanné (image).
- **Sénat** (ton souvenir est juste, à un détail près) : sur l'eFD, une **recherche** renvoie une
  **liste** de rapports → on clique un rapport → soit ses détails sont en **HTML** (dépôt électronique,
  lien `…/view/ptr/…`), soit c'est un **scan** (dépôt papier, lien `…/view/paper/…`). Le scan est servi
  en **`.gif`** (images), **pas en PDF** — c'est la seule correction à ta mémoire.

### Pourquoi un fichier `04_` côté Chambre et pas côté Sénat ?
- **Chambre** : pour savoir si un dépôt est lisible ou scanné, il faut **ouvrir le PDF et regarder**
  (`bool(text.strip())`). C'est un **verdict calculé** → on le matérialise dans
  `04_download_manifest.csv` (lisible / non\_lisible / absent).
- **Sénat** : la distinction est **donnée gratuitement** par la liste eFD (le lien est `ptr` ou
  `paper`). Rien à calculer, donc **pas de manifeste `04_`**.
- *Réf :* `house/digital.py:build_manifest` vs `senate/digital.py:fetch_ptr_list` (champ `kind`).

---

## §4.3 — piste digitale Chambre

### Pourquoi une « clé naturelle » et un `occurrence_index` ?
- **Le problème** : une même transaction peut apparaître **deux fois** — typiquement un PTR re-déposé
  (amendement) reprend les mêmes lignes → doublon **entre documents**. Il faut dédupliquer.
- **La clé naturelle** = une **empreinte** de la transaction sur 7 champs (chambre, déclarant, date,
  description d'actif, opération, fourchette, propriétaire). Deux lignes identiques sur ces 7 champs =
  « la même transaction ». On s'en sert pour **repérer les doublons**. *(Elle exclut le ticker, ajouté
  plus tard à l'enrichissement : l'inclure rendrait la clé instable.)*
- **Le piège** : un **même** PTR liste parfois **légitimement** la même transaction plusieurs fois
  (ex. la même vente via 3 comptes, le même jour → 3 lignes identiques mais **réelles**). Dédupliquer
  sur la seule clé les écraserait. L'`occurrence_index` **numérote** ces répétitions **dans** un
  document (0, 1, 2…). On déduplique alors sur le **couple** `(clé, occurrence_index)` → on retire les
  doublons **entre** documents, mais on **préserve** les lots réels **dans** un document.
- *Le rapport explique ça en §4.8 ; en §4.3 les termes apparaissent juste avant → on ajoutera un renvoi.*
- *Réf :* `congress_core/schema.py:natural_key_hash`, `add_occurrence_index`, `dedup_canonical`.

### « taux de parsing élevé (99–100 %) », ça veut dire quoi ?
- **Parsing** = la lecture automatique du **texte** d'un PDF lisible pour en extraire les transactions
  (par expressions régulières, `parse_ptr`).
- **Taux de parsing** = parmi les PDF **lisibles**, la part dont on a **réussi à extraire** au moins une
  transaction. **99–100 %** = quasiment tous ; les rarissimes qui ne donnent rien sont tracés dans
  `05_parse_failures.csv`.

### « Pas de souci de ticker » pour la Chambre digitale ?
- **Presque** : dans un PTR électronique, le **ticker est imprimé** (entre parenthèses, ex. « (AMZN) »)
  → `explicit_ticker` le capte directement, **sans dictionnaire ni LLM**. Donc peu de soucis côté digital.
- **Nuance** : certaines lignes n'ont **pas** de ticker même en digital — pas par échec, mais parce que
  l'actif **n'est pas coté** (obligation, fonds, muni) : aucun symbole n'existe. Le vrai « problème » de
  ticker (qui exige dictionnaire + LLM) concerne surtout l'**OCR** (papier sans ticker imprimé).

---

## §4.4 — piste digitale Sénat (HTML eFD)

### Le flux Sénat, vérifié (ton modèle est juste)
1. On accepte le garde-fou **CSRF** → on obtient une session.
2. `fetch_ptr_list` interroge l'**API de recherche** de l'eFD (`report_types=[11]` = PTR). Pour un
   humain, ça affiche une **grande table de résultats HTML** (≈ l'équivalent de l'index XML de la
   Chambre) ; pour le code, c'est la **même** chose servie en **JSON** (DataTables). → une **liste** de
   rapports.
3. On **trie** cette liste : chaque entrée pointe vers un rapport de type **`ptr`** (électronique) ou
   **`paper`** (scanné).
4. On « clique » (`fetch_report`) :
   - **`ptr`** → une page **HTML** contenant les **tableaux** de transactions → lue par `pd.read_html`.
   - **`paper`** → une page HTML qui **affiche des images `.gif` scannées** (**pas un PDF**) → part à l'OCR.
- **Correction de ta mémoire** : dans les **deux** cas on atterrit sur une **page HTML** ; la différence
  est ce qu'elle **contient** (un tableau structuré, ou des images `.gif`). Aucun PDF côté Sénat.
- *Réf :* `senate/digital.py:fetch_ptr_list` (champ `kind`), `fetch_report` ;
  `senate/ocr_engine.py:report_gif_urls` (les `.gif` du `paper`).

### Ce que §4.4 explique vraiment (tu as bien compris)
Une fois la liste obtenue, §4.4 décrit comment on **lit** l'électronique (`parse_electronic` via
`pd.read_html`, `_find_col` pour retrouver les bonnes colonnes malgré des en-têtes irréguliers), puis
comment on **rattache à l'identité** (`senate/identity.py:enrich`) — c'est bien « comment on trouve les
transactions et comment on les réassocie à la bonne personne ».

---

## §4.6 — OCR Sénat : est-ce « la même chose » que House ?

**Oui, le même principe** — c'est pour ça qu'on ne redit pas tout :
- On donne les images `.gif` à **Claude Vision** avec `tool_choice` **forcé** sur l'outil
  `record_transactions` (le modèle *doit* répondre en JSON structuré), et on **cache** le résultat
  versionné par `prompt_sha` — exactement comme l'OCR Chambre (§4.5).
- **Différence** : pas de **deskew** au Sénat. Le deskew (montrer la page aux 4 rotations) servait à
  redresser les scans **couchés** de la Chambre (cluster B). Les `.gif` du Sénat sont **droits** (formulaires
  typographiés), donc inutile.
- Détail d'implémentation : House et Sénat ont chacun leur module OCR (`house/ocr.py`,
  `senate/ocr_engine.py`, un « moteur figé Q1 »), tous deux descendant du même principe ; la version
  partagée/consolidée est `congress_core/vision_ocr.py`.
- *Réf :* `senate/ocr_engine.py:_call_vision` (`tool_choice` forcé), `PROMPT_SHA`.

---

## §4.5 / §4.7 — résolution du ticker (ton modèle est exact)

Pour une ligne **sans** symbole, on essaie **3 voies, dans l'ordre** (pareil Chambre et Sénat) :
1. **explicite** : le symbole est déjà là (imprimé dans le PTR, ou colonne Ticker de l'eFD) → `explicit`.
2. **dictionnaire** : on construit un annuaire `nom d'actif → ticker` à partir des lignes **déjà
   tickées** (souvent l'électronique), et on l'applique aux lignes qui n'ont qu'un nom → `elec_dict`.
   *(C'est ton « on compare aux tickers digital qui existent ».)*
3. **passe LLM** : sur le **reliquat**, un **appel à Claude** qui, à partir du **nom de l'actif**,
   propose le symbole boursier — **filtré aux actions** (`is_equity`, pour ne jamais tickeriser une
   obligation/muni), **caché et versionné** → `llm`. *(C'est ta « passerelle ».)*
- Détail Sénat : on **n'extrait pas** un « (XXX) » en fin de description (au Sénat, les parenthèses
  finales sont des **codes d'État** « (DE) », « (NY) », pas des tickers).
- *Réf :* `senate/ticker_resolve.py:resolve_tickers`, `house/ocr.py:llm_resolve_tickers`.

### « Couverture ticker / secteur », ça veut dire quoi ?
- **Couverture = taux de remplissage** = la **part des lignes** pour lesquelles le champ est renseigné.
  Ex. *ticker 85,3 %* = 85,3 % des lignes ont un symbole ; *secteur 83,2 %* = 83,2 % ont un secteur GICS.
- **Pourquoi pas 100 % ?** Parce que beaucoup d'actifs **ne sont pas cotés** (obligations, munis, fonds)
  → ils n'ont **légitimement** ni ticker ni secteur. La couverture mesure donc « combien on a pu
  enrichir », pas « combien on a raté » : les trous sont en grande partie **normaux**.

---

## §4.7 — secteur GICS → ETF SPDR (depuis zéro)

### Les briques de base
- **Action** (*stock*) = une **part** d'une entreprise cotée. Son **ticker** = son code court
  (`AAPL` = Apple, `NVDA` = Nvidia).
- **Secteur** = on **range** les entreprises par grand domaine. Le standard utilisé partout en finance
  s'appelle **GICS** (*Global Industry Classification Standard*) : **11 secteurs** (Technologie, Santé,
  Énergie, Finance, Industrie, Consommation…). Le « secteur GICS d'un ticker » = à quel de ces 11
  secteurs appartient l'entreprise. Ex. `NVDA` → *Information Technology*.
- **ETF** (*Exchange-Traded Fund*) = un **fonds** qui détient un **panier** d'actions et qui s'achète/se
  vend **comme une seule action**. Un **ETF sectoriel** détient les grandes entreprises d'**un** secteur
  → l'acheter, c'est s'exposer au **secteur entier** (pas à une seule entreprise).
- **SPDR Select Sector** = une **famille d'ETF** (gérée par State Street) avec **un ETF par secteur
  GICS** : **XLK** = Technologie, **XLE** = Énergie, **XLV** = Santé, **XLF** = Finance, **XLY** = Conso
  discrétionnaire… (11 ETF, un par secteur).

### Pourquoi on fait ça (« pourquoi l'ETF ? »)
La stratégie Ramify a **deux versions**. La **version 2** ne trade **pas les actions individuelles** mais
des **ETF sectoriels** (l'univers d'investissement habituel de Ramify). Donc au lieu de « copier l'achat
de NVDA », elle fait « acheter l'ETF du secteur de NVDA » = **XLK**. Pour ça, il faut traduire chaque
ticker déclaré : **ticker → secteur GICS → ETF SPDR**. Ex. **NVDA → Information Technology → XLK**.

### Comment on le gère (le paragraphe « comment »)
Pour chaque ticker, `enrich_sectors` trouve son secteur **en cascade** :
1. **yfinance** : une base financière publique donne le secteur **factuel** du ticker ;
2. **repli LLM** : si yfinance ne connaît pas le ticker (délisté, fusionné…), on **demande à Claude** le
   secteur (parmi la liste GICS stricte) ;
3. **overrides** : quelques corrections manuelles pour des cas connus.
On **trace** qui a tranché (`sector_source` = yfinance / llm / manual). Puis on **mappe** secteur → ETF
SPDR (table 1:1).

### Les résultats (« 83,2 % / 62,1 % »)
C'est la **couverture** (taux de remplissage) du secteur : **83,2 %** des lignes Chambre et **62,1 %**
au Sénat ont reçu un secteur (donc un ETF). **Pas 100 %** car seules les **actions cotées** ont un
secteur : les **obligations / munis / fonds** n'en ont pas → ni secteur ni ETF, **légitimement**. Le
Sénat est plus bas car il détient **plus d'obligations** (surtout 2025-26).
- *Réf :* `congress_core/sector_enrich.py:enrich_sectors`, `resolve_yfinance`, `resolve_llm`.
