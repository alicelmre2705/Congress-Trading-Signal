# `data/` — organisation de la couche données

Deux chambres, **même structure** :

```
data/{house,senate}/
    tables/              ← SORTIES du pipeline (CSV figés au golden)
        {2020..2026}/    ← une table par étape, par année (voir numérotation)
        00_*.csv         ← tableaux de bord (statut global)
        _*_cache.csv     ← cache Quiver (vérité-terrain figée pour les reproductions)
    reference/           ← ENTRÉES : YAML congress-legislators (+ commissions)
    ocr_cache/           ← cache Vision (re-run = 0 appel si inchangé)
    *.json               ← caches ticker / secteur
house/ uniquement :
    pdfs/ {y}/           ← 547 PDF scannés (source brute Chambre)
    index/ {y}FD.xml     ← index XML annuel du Clerk
```

## La numérotation = l'étape du pipeline
Le **préfixe** d'un fichier indique **où il se produit** dans la chaîne. On lit la couche données sans
documentation externe.

| Préfixe | Étape | Présent |
|---|---|---|
| `03_ptr_index` | index des dépôts retenus (fenêtre, `FilingType=P`) | House |
| `04_download_manifest` | verdict **lisible / scanné / absent** | House |
| `05_parse_failures` | dépôts lisibles dont l'extraction a échoué | les deux |
| `06_…_transactions` | table **digitale** (PDF/HTML lisibles) | les deux |
| `06b_…_ocr_transactions` | table **OCR** (scans / papier) | les deux |
| `06c_ocr_failures` | échecs OCR | les deux |
| `06d_ocr_quiver_comparison` | OCR confronté à Quiver | House |
| `06_…_FINAL` | digital + OCR **fusionnés** (table livrable) | les deux |
| `07_quiver_comparison` | comparaison Quiver par déposant (deltas) | les deux |
| `07b_quiver_missing_trades` | trades Quiver non retrouvés (clé brute, plancher) | House |
| `07c→07f_quiver_*` | réconciliation Quiver **fine** (txn, accord champs, ticker, only-quiver) | les deux |
| `08_crosscheck_semaine1` | recoupement vs baseline « semaine 1 » | House |
| `00_year_status` / `00_final_status` | tableaux de bord | Sénat |

## Asymétries de CONTENU — justifiées
La **structure** est symétrique ; ce sont les **fichiers présents** qui diffèrent, pour de bonnes raisons :
- **`04_` (House seul)** : la Chambre doit **ouvrir chaque PDF** pour décider lisible/scanné → un
  manifeste. Le Sénat reçoit le type (`kind` = `ptr`/`paper`) directement de la liste eFD → pas de `04_`.
- **Validation Quiver** : les **deux** chambres ont la réconciliation fine `07c→07f` (clé normalisée →
  couverture réelle + accord sens/date/montant) — **sur la piste DIGITALE seulement** (Quiver est aveugle
  au papier/OCR ; l'OCR↔Quiver est couvert par `06d` côté House). House garde EN PLUS `07`/`07b` (clé
  « brute » sans tolérance = un *plancher* conservateur, + ses « vrais-absents »).
- **`pdfs/` + `index/` (House seul)** : acquisition différente (la Chambre embarque ses PDF + l'index XML ;
  le Sénat récupère des images `.gif` servies à la volée, non stockées en brut).
- **Inventaire des scannés** : `_scan_census_547.csv` (House : census des 547 PDF, clusters A/B/C) vs
  `_paper_index_2020_2026.csv` (Sénat : index des PTR papier par UUID) — contenus différents, même rôle.

Le filet **golden** (`tests/regression/{,senate_}golden_manifest.json`) gèle toutes les sorties sous
`tables/` à l'octet (111 fichiers Chambre, 69 Sénat) — toute modif non voulue est détectée.
