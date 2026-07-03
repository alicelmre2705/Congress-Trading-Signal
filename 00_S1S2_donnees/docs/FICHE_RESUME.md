# Fiche récapitulative — Congress Trading Signal · la couche données (2014-2026)

*Résumé explicatif : vision d'ensemble et résultats clés, sans le détail des fonctions. Le détail
technique complet est dans [RAPPORT_QUALITE.md](RAPPORT_QUALITE.md) ; l'audit-réparation du
2026-07-03 est tracé dans [AUDIT_DONNEES_2014_2026.md](AUDIT_DONNEES_2014_2026.md).*

---

## 1. Le problème
- Depuis le **STOCK Act (2012)**, les membres du Congrès américain doivent **déclarer publiquement** leurs transactions boursières, en principe sous **45 jours** (rapports appelés *PTR*).
- Hypothèse de recherche (littérature : Ziobrowski, Karadas) : par leur position (commissions clés, accès à l'information), ces déclarations pourraient contenir un **signal exploitable**.
- L'idée à terme : une stratégie de **copy-trading** qui réplique ces trades **après** leur publication (jamais avant — principe *anti-look-ahead*).
- **Mais** avant toute stratégie, il faut une **couche de données irréprochable**. C'est mon livrable.

## 2. Le livrable en une phrase
- Une base **propre, traçable et honnêtement validée** de **169 000 transactions uniques de membres élus** (170 920 lignes brutes − 1 920 re-divulgations dédupliquées), sur les **2 chambres**, **2014–2026** — et sa déclinaison prête-recherche : la **table canonique de backtest, 134 464 lignes × 36 colonnes** (`data/clean/transactions_backtest_2014_2026.csv`).

## 3. D'où viennent les données
- **Chambre** : le site public du *House Clerk* → un index annuel officiel → les **PDF** des déclarations. **100 % des 8 252 PTR listés par le Clerk 2014-2026 sont traités** (parsés, OCRisés, ou écartés par une règle écrite).
- **Sénat** : le portail *eFD* → soit une **page web**, soit un **scan papier** ; les 25 dépôts sans transaction ont chacun une raison documentée (`06d_docs_sans_transaction.csv`).
- **Référentiel public des élus** (identité, parti, commissions) + **référentiels transverses** créés à l'audit (`data/reference/` : renommages/délistages de tickers, carte secteurs, snapshots de commissions par Congrès).
- **Deux services externes** : **Claude Vision** (lire les scans) et **Quiver** (valider — *jamais réinjecté*). S'y ajoutent deux sources de cross-validation indépendantes (senate-stock-watcher, mirror house-stock-watcher).
- **Deux dates** par déclaration : date du **trade** et date de **divulgation**. Tout usage aval entre sur la divulgation → anti-look-ahead.

## 4. Le défi central : électronique vs scanné
- Une déclaration arrive sous **2 formes** : du **texte** exploitable directement, ou une **image** qu'il faut « lire ».
- C'est la **fourche** du projet → **4 sous-corpus** : Chambre électronique **58 728**, Chambre OCR **93 261**, Sénat électronique **13 026**, Sénat OCR **3 985**.
- Point marquant : **~61 % des lignes de la Chambre viennent de scans** — de gros déposants (Khanna, McCaul) déclarent exclusivement sur papier.

## 5. La construction, étape par étape

### 5.1 — Qui a déclaré ? (résolution d'identité)
- Nom libre → **identifiant officiel unique** (bioguide) via référentiel + matcher tolérant (surnoms, homonymes — le sénateur Casey n'est plus confondu avec son père depuis l'audit).
- **Résultat : 100 % des lignes rattachées, les deux chambres** (les 52 lignes orphelines — Craig, Van Hollen, Udall — réparées à l'audit).

### 5.2 — Trier les formats
- Chambre : test de la couche texte de chaque PDF ; Sénat : le portail indique le type. Cette fourche fixe la composition du §4.

### 5.3 — Chambre électronique (PDF lisibles)
- Parsing déterministe qui **reconstitue** chaque transaction (lignes recollées, motif « opération + 2 dates + montant »).
- **Résultat : 58 728 transactions.** L'audit 2026-07-03 a corrigé deux causes de sous-comptage majeures : la police pré-2018 (petites capitales → **les ventes étaient massivement perdues** ; parité achats/ventes restaurée) et le routage des gabarits mixtes (union des deux parseurs).

### 5.4 — Sénat électronique (pages HTML)
- Tableaux web à en-têtes irréguliers → appariement flou des colonnes. **Résultat : 13 026 transactions.**

### 5.5 — Chambre scannée (OCR Claude Vision)
- **753 scans recensés et classifiés** (tapé droit / tapé tourné / manuscrit) ; redressement par reconnaissance d'orientation ; lecture structurée avec cache versionné (un re-run ne re-paie rien).
- **Manuscrit (cluster C) exclu par défaut** (dates trop incertaines) — politique **rejouable** : 582 docs gated documentés, avec exceptions explicites (3 déposants à forte perte corroborée + 33 docs hérités curés à la main).
- **Résultat : 93 261 lignes**, très concentrées (Khanna + McCaul + Renacci ≈ 48 % du House).

### 5.6 — Sénat papier (images)
- Même moteur Vision ; **3 985 lignes**, surtout Blumenthal, massivement des obligations municipales (non cotées — d'où la couverture ticker plus basse du Sénat).

### 5.7 — Secteur (GICS → ETF)
- Cascade factuelle (yfinance) → LLM → corrections manuelles, source tracée. Depuis l'audit : les **ETF diversifiés n'ont plus de faux secteur** (requalifiés `etf_broad` dans la carte transverse) et les symboles recyclés sont datés.
- **Couverture** (= remplissage, pas exactitude ; le non-coté n'a ni ticker ni secteur par nature) : ticker **84,1 % (Chambre) / 77,9 % (Sénat)** ; secteur **79,8 % / 70,4 %**. Dans la table canonique de backtest : secteur actions **100 %**.

### 5.8 — Les tables finales
- **Clé naturelle de 7 champs** (sans ticker ni date de divulgation) + rang d'occurrence → dédup **non destructrice** (les lots multi-comptes réels Self/Spouse/Joint sont préservés — ne jamais `drop_duplicates()`).
- **FINAL par année** : 28 colonnes, 12 champs « métier » garantis sur les 2 chambres. Commissions = photo actuelle dans les FINAL ; la **table canonique** ajoute parti **et** commissions **point-in-time** (à la date du trade, Congrès par Congrès), tickers canoniques Yahoo avec renommages, flags de traçabilité (dépôts tardifs, délistés, lots).

## 6. Les résultats clés
- **169 000** transactions uniques (House 151 989 + Sénat 17 011) · 2 chambres · 13 ans.
- **Complétude prouvée** : 100 % de l'index officiel House traité ; Sénat = sur-ensemble strict de senate-stock-watcher (6 231 transactions externes 2014-2020 : **100 % retrouvées** hors représentation des échanges).
- **Identité : 100 %** ; montants renseignés 99,4 % (7 996 fourchettes tronquées réparées — montants ×2 corrigés).
- **Table de recherche canonique : 134 464 lignes × 36 colonnes**, invariants garantis par asserts (bioguide, ticker, montant, direction, chronologie, hash).

## 7. La validation externe
- **Quiver** (vérité-terrain, jamais réinjectée) : électronique quasi parfait (98-99 %) ; dans notre fenêtre on retrouve **93,5 % (House) / 92,1 % (Sénat)** des trades Quiver ; on est **plus complet** que Quiver (+26 524 combinaisons cotées).
- Les « doublons » apparents de Quiver sont élucidés : ce sont majoritairement des **lots multi-comptes réels** (le champ owner, que Quiver ne publie pas, les distingue chez nous).
- **Sources indépendantes** : senate-stock-watcher (100 % couvert) et mirror house-stock-watcher (99,5 % post-2018) — les manques qu'ils révélaient pré-2018 ont été corrigés à l'audit.

## 8. Qualité & reproductibilité
- **Rapport qualité automatique** régénérable offline (`python -m common.quality`), désormais déterministe, avec section « couverture vs univers officiel ».
- **Golden octet-à-octet** : **230 fichiers Chambre + 138 Sénat** ; **10/10 tests** de régression verts ; chaque transformation reproduite depuis les colonnes figées.

## 9. Les limites assumées
- **Manuscrit exclu** par défaut (dates incertaines) — documenté, rejouable, avec exceptions explicites.
- **Pas de ticker/secteur pour le non-coté** (par nature) ; ~758 lignes OCR récentes à ticker non résolu (candidates à une future passe).
- **Prix des titres délistés** : plus aucune source gratuite (Yahoo purge, Stooq verrouillé) → traitement PAR TYPE via `ticker_renames.csv` (faillite ≈ perte totale, rachat = clôture à la date du deal) au lieu d'une disparition silencieuse.
- **Commissions des FINAL** = photo actuelle (le point-in-time est dans la table canonique).
- Cutoff de collecte : **2026-07-03** (House) / 2026-06-25 (Sénat, 3 dépôts postérieurs documentés).

## 10. Conclusion & suite
- Une couche de données **complète (prouvée contre l'univers officiel), identifiée, enrichie, corrigée, validée par trois sources externes et reproductible** — prête pour la recherche.
- **Suite (phases S3-S4)** : basculer la recherche sur la table canonique et appliquer [PATCHS_S3S4_A_APPLIQUER.md](PATCHS_S3S4_A_APPLIQUER.md).
