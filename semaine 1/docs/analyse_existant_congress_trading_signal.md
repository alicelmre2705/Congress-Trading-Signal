# Congress Trading Signal — Phase d'analyse
### Audit critique de l'existant + cadrage du livrable « données »

**Date :** 23 juin 2026
**Objet :** Décider de la meilleure voie pour produire, en fin de semaine 1, une table de transactions **House + Sénat** propre, structurée et exploitable, en cohérence avec nos contraintes (code dans le notebook, pas d'API boîte noire comme source canonique, Quiver en vérification seulement, pas d'évasion anti-bot).
**Méthode :** recherche + lecture des sources, vérification contre les sources primaires (et non la mémoire), extension de la liste de départ. Cette phase ne produit aucun code et aucun plan d'attaque.

---

## Résumé exécutif (les conclusions d'abord)

1. **La couche données est un problème saturé.** Au moins une dizaine de pipelines open-source et quatre à cinq fournisseurs commerciaux font déjà exactement ça, pour les deux chambres, dont plusieurs en licence MIT réutilisable. Notre valeur n'est pas dans le scraping : elle est dans **la réutilisation transparente du meilleur code + une validation rigoureuse + une honnêteté sur la complétude**.
2. **House et Sénat sont deux problèmes de difficulté très différente.** La House se récupère proprement et intégralement par nous-mêmes (ZIP quotidien, pas d'Akamai, pas de gate). Le Sénat est la moitié dure : pas de bulk, appli derrière Akamai + gate d'agrément, et une part de PDF scannés/papier irréductible sans OCR.
3. **Le « LLM massif » du directeur n'est pas justifié pour l'extraction.** Les PTR House sont des PDF générés par machine, parsables de façon déterministe. Le LLM doit être rétrogradé en **fallback ciblé** : résolution ticker en texte libre, et éventuellement OCR de documents scannés.
4. **Deux drapeaux structurants.** (a) Légal : la restriction §105(c) interdit l'usage *commercial* de ces déclarations — à lever avec le directeur/le légal avant toute mise en production. (b) Le « 100% » est un mythe : viser « ère électronique, niveau Member, avec un backlog scanné documenté ».
5. **Quiver = vérification, et c'est aussi le bon réflexe technique** (l'auteur du meilleur pipeline open-source l'a lui-même abandonné comme source pour cause d'incohérences d'API).

---

## 1. Carte du marché (par familles)

### (a) Sources primaires officielles
- **House — `disclosures-clerk.house.gov`.** ZIP annuel `public_disc/financial-pdfs/<YEAR>FD.zip` republié **quotidiennement**, contenant un index XML `<YEAR>FD.xml` (un nœud `Member` par dépôt) + les PDF PTR à `public_disc/ptr-pdfs/<YEAR>/<DocID>.pdf`. **Accès propre : HTTPS simple, pas d'Akamai, pas de gate d'agrément.** `FilingType` ∈ {Candidate (C), Annual (A), Extension (X), Periodic Transaction = PTR (**P**), Termination (T), + quelques codes résiduels}. Les PTR sont générés par machine donc le texte est extractible — mais avec des artefacts d'encodage (glyphes/octets nuls) qu'il faut nettoyer (vérifié sur un vrai PTR Pelosi 2025 : le mot « Description » ressort encodé en symboles). Deux dates par transaction : *transaction date* et *notification/filing date*.
- **Sénat — `efdsearch.senate.gov`.** Reports **individuels uniquement**, **aucun format bulk lisible par machine**. Appli Django **derrière Akamai** + **gate d'agrément CSRF** (il faut accepter les conditions, ce qui pose un cookie de session). Deux régimes : dépôts **électroniques** (rendus en HTML propre) et **papier/scannés** (nécessitent OCR ou transcription humaine). Transactions dans les Parties 4a (résumé PTR) / 4b (transactions).
- **Note légale commune (§105(c) EIGA).** Pour les deux chambres : il est illégal d'obtenir/utiliser ces déclarations pour un *usage commercial*, hors médias pour diffusion au public. Pertinent pour un asset manager (Ramify/Valhyr). **Drapeau, pas décision** — je ne suis pas juriste.

### (b) Pipelines open-source qui récupèrent depuis l'officiel (code réutilisable)
- **seralifatih / Fatih İlhan (MIT, TypeScript)** — la référence la plus alignée. Deux acteurs Apify (House + Sénat) + un acteur de merge. House : ZIP→XML→filtre `FilingType='P'`→PDF→regex ancrée sur marqueurs `(TICKER) [TYPE]`→types P/S/S(partial)/E + fourchettes. Sénat : gère le gate Django. Dédup déterministe par **SHA-256 de la clé naturelle** (politicien+date+actif+montant). Fallback OCR pour scannés, enrichissement ticker pour obligations. **A explicitement abandonné Quiver comme source** (formats incohérents entre endpoints, 500 en séance, granularité derrière un tier payant) — ce qui valide notre choix de Quiver en vérif seulement.
- **burd5 (Python)** — ELT complet : Selenium + BeautifulSoup (House + Sénat) → Supabase → DBT → AWS Fargate hebdo. PDF via PDFPlumber (après échecs Camelot/Tabula). **Leçon clé : l'incohérence des noms** (« William / Bill / William Jr Cassidy ») gérée par CASE WHEN — confirme qu'il faut une clé d'identité robuste (BioGuideID).
- **kadoa-org (MIT, JS)** — agrège **trois** sources officielles : House Clerk + Sénat eFD + **OGE (exécutif/cabinet)**. **~54 000 transactions, 2012→présent, 380+ déclarants**, servies en **JSON statique** (donc inspectable, transparent). Limites assumées : saute les **PDF papier Sénat d'avant 2015** et prévoit un **résolveur de ticker LLM** pour les noms en texte libre.
- **Scrapers Sénat spécialisés** — jeremiak/us-senate-financial-disclosure-scraper (électronique + OCR papier → CSV), neelsomani/senator-filings (électronique seulement, **ignore les PDF scannés**), olgn/senate-finances (SQLite, snapshot ~2020), dannguyen/scrape-senate-financial-disclosures (distingue papier/électronique).
- **Autres acteurs Apify** (parseforge, johnvc, jungle_synthesizer) — variations du même pipeline officiel, certains très récents (maj 2026). Confirme la saturation du marché.

### (c) Datasets déjà parsés / open data (à consommer)
- **Senate Stock Watcher / House Stock Watcher** (Tim Carambat) — JSON/CSV transcrits par une communauté de bénévoles, schéma déjà transaction-level (nom, ticker, dates, type, fourchette, propriétaire, lien PTR). **Transparents** (données ouvertes inspectables, pas une boîte noire). **MAIS fraîcheur incertaine** : forte activité 2021-2022 (lancement House en avril 2021, podcast/mises à jour ~2022), snapshots observés s'arrêtant fin 2022 ; le site affiche « Updated Daily » mais c'est invérifiable côté maintenance. → **Excellents pour le socle historique + comme contre-référence transparente ; risqués pour la queue récente.**
- Mirrors Kaggle, pastrosd, noodleslove — dérivés des Stock Watcher.

### (d) API commerciales (vérification / fallback « boîte noire »)
- **Quiver Quant** — endpoint bulk `/beta/bulk/congresstrading` (V2), schéma complet, calcule même les rendements cumulés par politicien + leaderboard (avec disclaimer de backtest hypothétique). **On a un compte → couche de vérification.**
- **Capitol Trades (2iQ)** — la plus reconnue, House+Sénat, archive depuis 2012, fraîcheur en heures — **mais pas d'API publique.**
- **Financial Modeling Prep** — endpoints Senate + House, JSON, 250 appels/jour en gratuit, ~29$/mois.
- **Apify (pay-per-result)** — ~0,40-0,50$/1k résultats. Unusual Whales, Barchart, etc.
- Une revue 2026 (Lambda Finance) a comparé **12 fournisseurs** — c'est un marché établi.

### (e) Intégrations de backtest déjà packagées
- **QuantConnect/Lean — `Lean.DataSource.QuiverQuantCongressTrading`** : data source + **algorithme de sélection d'univers** congressional fourni en **C# et Python**. « Backtester le congress trading » est déjà packagé (branché sur Quiver).

### (f) Contexte académique (cadrage des attentes, pas le livrable)
- Pré-2012 : Ziobrowski 2004 (Sénat ~12%/an), 2011 (House ~6%/an) — **contesté**.
- Eggers & Hainmueller, *Capitol Losses* : sous-performance 2004-2008, membres « rather poor investors ».
- Huang & Xuan : l'avantage informationnel **disparaît après le STOCK Act**. Belmont et al. : sous-performance 2012-2020.
- Karadas : commissions + parti expliquent une partie de la surperformance (**pré-Act**).
- CEPR (déc. 2025) : alpha résiduel **seulement pour les dirigeants**, même en dates de publication. Cherry : pour les sénateurs, l'edge est dans le **timing des ventes**, pas les achats.
- **À retenir** : la prémisse (alpha exploitable) est contestée post-2012 et concentrée ; à ne pas oublier quand on dimensionnera la stratégie (semaines 3-4).

---

## 2. Tableau comparatif (sources les plus pertinentes)

| Source | Type | Chambres | Période / Fraîcheur | Granularité | Code dans notre notebook ? | Licence / Légal | Verdict pour nous |
|---|---|---|---|---|---|---|---|
| **House Clerk (officiel)** | Source primaire | House | 2008→, **quotidien** | Transaction (après parsing PDF) | **Oui — accès trivial, transparent** | Domaine public ; §105(c) | **Socle House canonique** |
| **Sénat eFD (officiel)** | Source primaire | Sénat | 2012→ | Transaction (HTML/PDF) | Partiel — Akamai + gate | Domaine public ; §105(c) | Provenance, accès direct **léger** seulement |
| **seralifatih** | Pipeline OSS | Les 2 | 2012→, à la demande | Transaction | **Oui (port TS→Python)** | MIT | **Logique de parsing à porter** |
| **burd5** | Pipeline OSS | Les 2 | live (hebdo) | Transaction | Oui (Python) | (à vérifier) | Référence d'archi + leçons noms |
| **kadoa** | Dataset OSS | Les 2 + OGE | **2012→présent** | Transaction (JSON statique) | Oui (consommation transparente) | MIT (« research/educational ») | **Socle Sénat + contre-référence** |
| **Senate/House Stock Watcher** | Dataset OSS | Les 2 (séparés) | 2012→~2022 (fraîcheur ?) | Transaction (JSON/CSV) | Oui (consommation transparente) | Open data | Socle **historique** + contre-référence |
| **unitedstates/congress-legislators** | Référentiel | Les 2 | maintenu | Identité + commissions | Oui | Domaine public | **Clé d'identité (BioGuideID) + commissions** |
| **Quiver** | API commerciale | Les 2 | live | Transaction + rendements | **Non (boîte noire)** | Abonnement | **Vérification uniquement** |
| **Capitol Trades** | Plateforme | Les 2 | live (heures) | Transaction | Non (pas d'API) | — | Référence visuelle seulement |
| **FMP** | API commerciale | Les 2 | live | Transaction | Non (boîte noire) | Abonnement | Vérif d'appoint optionnelle |
| **QuantConnect/Lean** | Framework backtest | Les 2 | via Quiver | Univers + signal | Oui (mais lié Quiver) | OSS | Pertinent **semaines 3-4** |

---

## 3. Évaluation critique

**Ce qui est solide / qu'on garde**
- L'**accès officiel House** : propre, complet sur l'ère électronique, totalement sous notre contrôle et transparent. C'est notre meilleur atout — on le récupère intégralement nous-mêmes.
- La **logique de parsing de seralifatih** (regex marqueurs + nettoyage octets nuls + dédup SHA-256) : éprouvée, MIT, à **porter en Python dans notre notebook** (transparence respectée — le code vit chez nous, pas dans une API).
- **BioGuideID via unitedstates/congress-legislators** : règle d'avance le problème nº1 de tous les projets (variantes de noms) et fournit parti + commissions Finance/Defense/Intelligence.
- **kadoa (54k tx, 2012→présent, MIT)** et **Stock Watcher** comme socle Sénat transparent et comme contre-références de validation.

**Ce qui est problématique / à manier avec prudence**
- **Le Sénat en self-scraping intégral.** Akamai + gate d'agrément poussent les autres vers des **proxys résidentiels d'évasion** — qu'on s'interdit. Conséquence : pour le Sénat, on s'appuie en partie sur des **données ouvertes transparentes** (Stock Watcher/kadoa) + un **lecteur direct léger et respectueux** des dépôts électroniques. À assumer explicitement : « récupérer soi-même » est total pour la House, partiel pour le Sénat.
- **Fraîcheur des Stock Watcher** : probablement périmés après ~2022 → ne pas s'en servir pour la queue récente. House récente = officiel (trivial) ; Sénat récent = eFD électronique ou kadoa (« présent »).
- **Encodage des PDF House** (glyphes/octets nuls) : normalisation obligatoire avant tout pattern-matching.
- **Tickers en texte libre / obligations / options** : nécessitent un résolveur ; c'est le **seul** endroit où un LLM se justifie (en fallback).
- **Cohérence des comptes** : mes PTR House extraits (~830 pour 2018) **collent au chiffre officiel de la commission d'éthique** (831 PTR de Members pour CY2018) → rassurant pour la couverture Member. Le total officiel ~2 205 inclut des PTR d'officiers/staff, **moins pertinents** pour un signal centré sur les élus.

**Ce qu'on jette (comme source)**
- **Quiver / Capitol Trades / FMP comme source canonique** : boîtes noires → vérification seulement (ou pas du tout pour celles sans API).
- **Le LLM en extraction massive** : inutile et coûteux sur des PDF déterministes.
- **QuantConnect/Lean pour la data** : c'est un outil de backtest (utile plus tard), pas une source.

---

## 4. Approche recommandée pour le livrable de la semaine 1

Objectif : **une table transactionnelle unifiée House + Sénat, ère électronique, niveau Member, propre, dédupliquée, avec identité + commissions, récupérée depuis des sources transparentes.**

1. **Identité d'abord** — charger `congress-legislators` (BioGuideID, nom canonique + alias, parti, chambre, état/district, **commissions**) comme table de référence. Règle le problème des noms en amont.
2. **House — auto-récupération intégrale (canonique)** — depuis le ZIP/XML/PDF officiel ; filtre `FilingType='P'` (en **vérifiant** si des PTR amendés se logent sous un autre code) ; extraction **déterministe** via la regex marqueurs **portée de seralifatih en Python, dans notre notebook**, avec nettoyage des octets nuls. PDF non extractibles (~13% observés) → backlog OCR.
3. **Sénat — socle ouvert + lecteur direct léger (pas d'évasion)** — socle historique via **dataset ouvert transparent** (Stock Watcher et/ou JSON kadoa) ; queue récente / provenance via un **lecteur in-notebook des dépôts électroniques eFD**, agrément accepté manuellement, faible volume, **sans proxy d'évasion** (si blocage : on reste sur la donnée ouverte). PDF scannés/papier antérieurs → backlog OCR explicite.
4. **Unification + nettoyage** — schéma unique, jointure BioGuideID, normalisation tickers/dates, **chaque règle documentée**, **dédup déterministe** (SHA-256 de la clé naturelle), à la seralifatih.
5. **LLM en fallback ciblé seulement** — résolution ticker texte-libre, et OCR éventuel ; **pas** d'extraction massive.
6. **Vérification (Quiver, notre compte)** — triangulation par année / déclarant / ticker + contrôles transaction-level, en croisant aussi kadoa. **Quiver n'entre jamais dans la table finale.**

**Plafond de complétude réaliste à annoncer :** « ère électronique, niveau Member, complet et vérifié pour la House ; raisonnablement complet pour le Sénat électronique ; backlog documenté pour le papier/scanné ancien (surtout Sénat < 2015). » C'est honnête et défendable devant le directeur.

---

## 5. Risques et drapeaux

| Risque / drapeau | Gravité | Mitigation |
|---|---|---|
| **Légal §105(c)** — usage commercial restreint (2 chambres) | **Élevée** | À remonter au directeur/légal **avant** mise en production ; ne bloque pas la construction technique. |
| Fraîcheur des datasets gratuits (Stock Watcher ~2022) | Moyenne | Queue récente via officiel (House) + eFD/kadoa ; Stock Watcher pour l'historique. |
| Accès Sénat fragile (Akamai + gate) | Moyenne | Socle données ouvertes + lecteur poli ; **pas d'évasion**. |
| Réconciliation d'identité (noms, conjoints, historiques) | Moyenne | BioGuideID + table d'alias. |
| Normalisation tickers (texte libre, obligations, options) | Moyenne | Mapping + LLM en fallback. |
| Encodage PDF (octets nuls/glyphes) | Faible-Moyenne | Normalisation avant parsing (vérifié sur PTR réel). |
| Dépendance fournisseur | Faible (par design) | Quiver en vérif seulement. |
| **Réalité du signal** (alpha contesté post-2012) | Hors data | À garder en tête pour les semaines 3-4 (sélection, ETF). |

---

## 6. Questions ouvertes à trancher avant le plan d'attaque

1. **Sénat** : tu valides « socle données ouvertes transparentes + lecteur eFD électronique léger, sans évasion anti-bot » ? Ou tu préfères **House d'abord, intégralement auto-récupérée**, et le Sénat en fast-follow ?
2. **§105(c)** : OK pour avancer techniquement en posant ce point comme un checkpoint explicite à lever avec ton directeur ?
3. **Période** : House 2013-2026, Sénat 2012/2014-2026 (ère électronique) — tu confirmes les bornes ?
4. **LLM** : d'accord pour le cantonner au **fallback ciblé** (ticker / scanné), pas d'extraction massive ?
5. **Complétude** : « ère électronique, niveau Member, backlog scanné documenté » est-elle une définition acceptable de « toute la donnée » pour la fin de semaine 1 ?
6. **Stockage** : CSV (simple/lisible) ou parquet/SQLite (plus robuste) pour la table finale ?

> Une fois ces six points tranchés, je rédige le **plan d'attaque** détaillé (architecture du notebook, cellule par cellule) pour produire le livrable.
