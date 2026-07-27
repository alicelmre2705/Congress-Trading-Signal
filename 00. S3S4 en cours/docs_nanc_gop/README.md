# Dossier documentaire — NANC et GOP

Toutes les pièces qui ont servi à établir le fonctionnement de ces deux ETF.
Chaque document est le document officiel tel que déposé ou publié, converti en PDF sans retouche.
Les renvois `[n p.X]` de **FICHE_NANC_GOP** pointent directement vers ces fichiers, à la page indiquée.

⚠️ Les fonds relèvent de **Tidal Trust I** (CIK 1742912) depuis fin 2024, et de **Series Portfolios Trust**
(CIK 1650149) avant : les dépôts SEC sont donc répartis sur deux identifiants.

| # | document | date | ce qu'il établit | page utile |
|---|---|---|---|---|
| 1 | Prospectus statutaire + SAI (485BPOS) | 27/01/2026 | la règle complète · les frais · la performance depuis création · le rôle du fournisseur de données | 7 · 5 · 13 · 34 |
| 2 | Prospectus d'origine (497K) | 03/02/2023 | « to create the Fund's **initial** portfolio » — la fenêtre 3 ans ne servait alors qu'au départ | 3 |
| 3 | Changement de méthode (497) | 02/08/2024 | Tidal devient gérant ; le portefeuille passe à 100–200 lignes | 3 |
| 4 | Rapport annuel FY2023 (N-CSR) | 30/09/2023 | rotation 44 % (NANC) et 46 % (GOP) ; note « not annualized » (exercice de 7,8 mois) | 74 · 76 |
| 5 | Rapport annuel FY2024 (N-CSR) | 30/09/2024 | « **eliminated 582 very small positions** » ; rotation 62 % / 54 % | 2 · 39 · 40 |
| 6 | Rapport annuel FY2025 (N-CSR) | 30/09/2025 | « croisé avec les **committee roles** » ; rotation **10 %** / 16 % ; NVIDIA 142 778 parts | 2 · 27 · 28 · 17 |
| 7 | Changement de code (497) | 18/03/2025 | KRUZ devient GOP — nécessaire pour retrouver les dépôts antérieurs | 1 |
| 8 | Fiches produit (NANC et GOP) | 30/06/2026 | encours, nombre de lignes, performance affichée | 1–2 |
| 9 | **La règle, écrite par le gérant** | 19/11/2023 | « **more dollars equals more votes** » · le **midpoint** des fourchettes · « this choice drives **all the relative allocations** » | 1 |
| 10 | **Podcast — Michael Venuto (Tidal)** | 06/12/2024 | la donnée est **publique** · sélection **discrétionnaire** (auditions, achats simultanés) · **le bruit de rebalancement est écarté** | 1 |
| 11 | Rapport semestriel (N-CSRS) | 31/03/2023 | lettre du gérant : « what matters is the **relative allocation** » | 3 |
| 12 | Proxy — comparaison des stratégies | 27/09/2024 | « 100 to 200 holdings **instead of the previous range of between 500 and 600** » | 57 |
| 13 | N-CEN FY2025 (extrait) | 30/09/2025 | **aucun indice** de référence ; créations en nature ; unité de création | 1 |
| 14 | Rapport semestriel (N-CSRS) | 31/03/2026 | rotation **5 %** (NANC, 99 lignes) et 2 % (GOP) : le livre est désormais quasi figé | 2 |
| 15 | Premier prospectus Tidal (485BPOS) | 27/11/2024 | c'est ici qu'apparaît « **to manage** the Fund's portfolio » et la règle de pondération | 6 |
| 16 | Papier académique — Baulkaran & Jain | 2025 | « **neither significantly outperforms market returns** » — confirmation indépendante | 1 |
| 17 | Cadence annoncée au lancement | 09/02/2023 | portefeuilles « **updated weekly** » ; 750–800 titres visés (ère Subversive) | 1 |

## Les deux documents les plus importants

**[9] et [10]** ne sont pas des documents réglementaires, et ce sont pourtant les seuls qui décrivent
la mécanique réelle :

- **[9] Cooper (2023)** donne la règle de l'ère Subversive : poids proportionnel aux **dollars déclarés**,
  milieu de fourchette, familles incluses.
- **[10] Venuto (2024)** décrit l'ère Tidal : la donnée est publique, mais un **gérant humain** cherche des
  motifs et **écarte le bruit** des comptes gérés automatiquement.

Ensemble, ils expliquent le changement de régime d'août 2024 : on passe d'une règle mécanique à un jugement.

## Données brutes associées (hors de ce dossier)

- `../cache/nport_holdings.csv` — le portefeuille **réel** des deux fonds à **13 dates** (03/2023 → 03/2026),
  reconstitué depuis les 26 états N-PORT déposés à la SEC (nombre de parts et poids par ligne).
- `../cache/NANC_holdings_20260724.csv` et `GOP_holdings_20260724.csv` — les portefeuilles publiés
  quotidiennement par l'administrateur.

## Note technique

Ces PDF sont produits par conversion des documents déposés. Si macOS refuse de les ouvrir
(« vous ne disposez pas de l'autorisation nécessaire »), c'est l'attribut de quarantaine :

```
cd docs_nanc_gop && for f in *.pdf; do cat "$f" > t && mv -f t "$f" && xattr -c "$f"; done
```
