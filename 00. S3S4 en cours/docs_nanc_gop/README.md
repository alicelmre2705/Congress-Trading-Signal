# Dossier documentaire — NANC et GOP

Toutes les pièces qui ont servi à établir le fonctionnement de ces deux ETF.
Chaque document est le document officiel tel que déposé ou publié, converti en PDF sans retouche.
**Les numéros suivent l'importance** : [1]–[3] établissent la règle, [4]–[8] le changement de régime d'août 2024,
[9]–[12] les chiffres publiés, [13]–[17] le contexte.
Les renvois `[n p.X]` de **FICHE_NANC_GOP** pointent directement vers ces fichiers, à la page indiquée.

⚠️ Les fonds relèvent de **Tidal Trust I** (CIK 1742912) depuis fin 2024, et de **Series Portfolios Trust**
(CIK 1650149) avant : les dépôts SEC sont donc répartis sur deux identifiants.

| # | document | date | ce qu'il établit | page utile |
|---|---|---|---|---|
| **A. La règle — ce que le fonds fait** ||||
| **1** | **Prospectus statutaire + SAI** (485BPOS) | 27/01/2026 | **la règle complète** (univers, fenêtre 3 ans, **midpoint**, netting, exécution à la divulgation, 100–200 lignes) · frais · performance depuis création · publication **quotidienne** du portefeuille · rôle du fournisseur de données | **7** · 5 · 15 · 13 · 24 · **33** · 34 |
| **2** | **Cooper — la règle écrite par le gérant** | 19/11/2023 | **« more dollars equals more votes »** · le **midpoint** des fourchettes · « this choice drives **all the relative allocations** » | 1 |
| **3** | **Podcast Venuto (Tidal)** — Meb Faber #560 | 06/12/2024 | la donnée est **publique** · sélection **discrétionnaire** (auditions, achats simultanés) · **le bruit de rebalancement est écarté** · la thèse assumée du fonds · **amende de ~250 \$** pour non-déclaration | 1–2 |
| **B. Le changement de régime (août 2024)** ||||
| 4 | Changement de méthode (497) | 02/08/2024 | Tidal devient gérant ; le portefeuille passe à 100–200 lignes | 3 |
| 5 | Rapport annuel FY2024 (N-CSR) | 30/09/2024 | « **eliminated 582 very small positions** » ; rotation 62 % / 54 % | 2 · 39 · 40 |
| 6 | Proxy — comparaison des stratégies | 27/09/2024 | « 100 to 200 holdings **instead of the previous range of between 500 and 600** » | 57 |
| 7 | Prospectus d'origine (497K) | 03/02/2023 | « to create the Fund's **initial** portfolio » — la fenêtre 3 ans ne servait alors qu'au départ | 3 |
| 8 | Premier prospectus Tidal (485BPOS) | 27/11/2024 | c'est ici qu'apparaît « **to manage** the Fund's portfolio » | 6 |
| **C. Les chiffres publiés** ||||
| 9 | Rapport annuel FY2025 (N-CSR) | 30/09/2025 | « *cross referenced against the ... **committee roles*** » ; rotation **10 %** / 16 % ; encours FY23/24/25 ; NVIDIA 142 778 parts | 2 · 27 · 28 · 17 |
| 10 | Rapport annuel FY2023 (N-CSR) | 30/09/2023 | rotation 44 % / 46 % ; définition SEC de la rotation ; note « **not annualized** » (exercice de 7,8 mois) | 74 · 76 |
| 11 | Rapport semestriel (N-CSRS) | 31/03/2026 | rotation **5 %** (NANC, 99 lignes) et 2 % (GOP) : le livre est quasi figé | 2 |
| 12 | Fiches produit (NANC **et** GOP) | 30/06/2026 | encours, nombre de lignes, performance affichée | 1 |
| **D. Contexte et pièces secondaires** ||||
| 13 | **Papier académique — Baulkaran & Jain**, *Economics Letters* 250 (2025) 112263 | 03/2025 | régression 5 facteurs sur les rendements **des ETF eux-mêmes** (01/02/2023–31/01/2024) : α non significatif dans les 8 spécifications ; **β 1,07–1,09 (NANC) et 0,88–0,91 (KRUZ)** — à comparer aux 1,06 et 0,93 de nos répliques | 1 · 2 · 4 |
| 14 | Cadence annoncée au lancement | 09/02/2023 | portefeuilles « **updated weekly** » ; 750–800 titres visés (ère Subversive) | 1 |
| 15 | N-CEN FY2025 (extrait) | 30/09/2025 | **aucun indice** de référence ; créations en nature ; unité de création | 1 |
| 16 | Rapport semestriel (N-CSRS) | 31/03/2023 | lettre du gérant : « *what will matter is the **relative allocation*** » | 3 |
| 17 | Changement de code (497) | 18/03/2025 | KRUZ devient GOP — nécessaire pour retrouver les dépôts antérieurs | 1 |

## Adresses d'origine

La fiche donne l'identifiant de dépôt EDGAR (`CIK/accession`) ; l'URL complète se reconstruit par
`https://www.sec.gov/Archives/edgar/data/<CIK>/<accession>/` — et les **URL complètes** de chaque pièce
figurent dans le tableau ci-dessus et dans l'historique git de ce README.

## Les deux documents les plus importants

**[2] et [3]** ne sont pas des documents réglementaires, et ce sont pourtant les seuls qui décrivent
la mécanique réelle :

- **[2] Cooper (2023)** donne la règle de l'ère Subversive : poids proportionnel aux **dollars déclarés**,
  milieu de fourchette, familles incluses.
- **[3] Venuto (2024)** décrit l'ère Tidal : la donnée est publique, mais un **gérant humain** cherche des
  motifs et **écarte le bruit** des comptes gérés automatiquement.

Ensemble, ils expliquent le changement de régime d'août 2024 : on passe d'une règle mécanique à un jugement.

## Données brutes associées (hors de ce dossier)

- `../cache/nport_holdings.csv` — le portefeuille **réel** des deux fonds à **13 dates** (03/2023 → 03/2026),
  reconstitué depuis les 26 états N-PORT déposés à la SEC (nombre de parts et poids par ligne).
- `../cache/NANC_holdings_20260724.csv` et `GOP_holdings_20260724.csv` — les portefeuilles publiés
  quotidiennement par l'administrateur.

## Note technique — pourquoi les liens ouvraient une erreur d'autorisation

Les renvois de la fiche étaient des liens **`/GoToR`** (« ouvre *un autre* fichier »). Aperçu a l'autorisation
sur la fiche, que vous avez ouverte vous-même, mais **aucune sur le fichier cible** : macOS refuse alors avec
« vous ne disposez pas de l'autorisation nécessaire pour l'afficher ». Retirer l'attribut de quarantaine ne
suffit pas — ce n'est pas lui le coupable.

**La solution retenue : `../FICHE_NANC_GOP_avec_sources.pdf`** — la fiche (3 p.) suivie des documents cités,
dans **un seul fichier**, avec les 52 renvois convertis en liens **internes**. Un seul fichier à autoriser,
et un clic tombe sur la page exacte, où le passage utilisé est **surligné en jaune**.

## Deux dossiers, deux usages

- **`docs_nanc_gop/`** (ici) — les documents officiels **sans aucune retouche**. C'est la version auditable.
- **`docs_nanc_gop_surlignes/`** — les mêmes, avec **113 passages surlignés en jaune** : exactement ce sur quoi
  la fiche s'appuie, page par page. C'est cette version qui est fusionnée dans le PDF auto-portant.

Les deux sont régénérables : `scratchpad/surligner.py` (surlignage, avec rapport d'échec par fragment) puis
`scratchpad/fiche_autoportante.py` (fusion et conversion des liens).

## Ce que le surlignage a vérifié au passage

Les 113 fragments ont **tous** été trouvés à la page que la fiche annonce : chaque renvoi `[n p.X]` pointe donc
bien sur une page qui contient réellement l'affirmation qu'il soutient.
