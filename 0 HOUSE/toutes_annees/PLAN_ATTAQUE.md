# Plan d'attaque — reconstruction propre & autonome de `toutes_annees`

Objectif : transformer `toutes_annees` en un dossier **propre, autonome et narré comme `2025_test`**
(0 dépendance externe, rien de perdu), avec digital + OCR (census/échantillons/gate) **déjà intégrés**,
pour qu'au final la **seule** chose restante soit le **run OCR complet** (2021-2025). 5 stades, chacun
avec une porte de sortie vérifiable. On ne lance PAS le run OCR coûteux avant d'avoir validé 1→4.

## Décisions retenues (défauts — dis si tu veux changer)
- **Embarquement PDF** : on copie **les 547 scannés** dans `data_v1/pdfs/` (nécessaires au run OCR restant).
  Le digital est **figé dans les tables `06`** → pas besoin d'embarquer les milliers de PDF digitaux
  (gain de centaines de Mo). *(Alternative : tout embarquer pour repro totale du parsing.)*
- **Notebooks** : 2 notebooks narrés (`notebook_digital`, `notebook_ocr`) qui **importent les 2 moteurs**
  `house_multiyear.py` / `house_ocr_multiyear.py` (à la racine, ancrés `BASE_DIR`) — DRY, moteurs déjà testés.
  *(Alternative : tout inliner comme 2025_test, plus lourd à maintenir.)*

---

## STAGE 1 — Squelette autonome (structure + embarquement + chemins)
**Actions**
- Créer `.env.example`, `.gitignore`, `requirements.txt` (deps épinglées), `README` à jour.
- Ancrer les chemins par marqueur de fichier (`BASE_DIR`) dans les 2 moteurs + `load_dotenv(BASE_DIR/.env)`.
- **Embarquer** : copier les **547 PDF scannés** → `data_v1/pdfs/{année}/` ; copier les **YAML législateurs/comités**
  → `data_v1/reference/` ; le Quiver est déjà embarqué (`_quiver_house_cache.csv`, 100 333 lignes).
- Re-pointer `SEM1_*` → relatif `BASE_DIR`. Rendre le cross-check semaine1 (`08`) **optionnel** (`--no-crosscheck` existe).
- **Archiver sans rien perdre** dans `_archive/` : les 7 scripts jetables (build_notebook, cache_quiver,
  make_backlog, revalidate×2, test_ocr_clusters, test_prompt_durci) + sorties intermédiaires
  (05/06/06c/06d/07*/08, `_ocr_gate`, `_scan_census_547`) + le doublon `2025q1/`. Supprimer `__pycache__`.
- Corriger les 2 bugs de chemin (`HERE.parent`) si on garde cache_quiver/make_backlog pour rafraîchir.

**Porte de sortie** : `grep -rn "semaine 1" *.py data_v1` → **0 résultat** dans le code gardé ; les 2 moteurs
s'importent et résolvent un PDF + chargent Quiver **sans** `semaine 1`.

## STAGE 2 — Notebook DIGITAL propre + concordance à jour
**Actions**
- `notebook_digital.ipynb` narré (cellules markdown courtes) : importe le moteur, (re)génère les tables
  par année (ou réutilise `06`), produit la concordance **q1style** (dédup amendements, exclure papier,
  cross-check ticker-raté).
- Rafraîchir `RAPPORT_DIGITAL.md` avec la **vraie** colonne concordance (98-99,7 %), retirer l'ancien
  `quiver_coverage_pct` (35-74 %) trompeur.

**Porte de sortie** : le notebook tourne de bout en bout depuis le dossier propre ; tableau reproduit =
**99,01 % global, 9 vrais-absents**.

## STAGE 3 — Porter la passe LLM nom→ticker (de `2025_test`)
**Actions**
- Porter la résolution **LLM nom→ticker** (cache versionné `ticker_llm_cache.json`, `prompt_sha+model`)
  dans l'enrichissement OCR. L'appliquer aux sorties OCR **2020 + 2026** (déjà complètes) comme preuve.
- Produire l'audit type `06e` (tickers LLM ↔ Quiver).

**Porte de sortie** : ticker OCR **46 %→~90 %** sur 2020/2026 ; audit `06e` **~93 %** vs Quiver.

## STAGE 4 — Notebook OCR propre (census + échantillons + gate)
**Actions**
- `notebook_ocr.ipynb` narré qui raconte toute l'histoire OCR : **census 547** (tableaux clusters/orientation/
  legibility), **échantillons représentatifs montrés** (A/B/C, images), **analyse OCR sur l'échantillon = gate**
  (stabilité 2-runs + Quiver fenêtré), **stats par cluster + projection**. Intègre `_scan_census_547` + `_ocr_gate`.
- Conclusion du notebook : « tapé propre 85-100 %, queue dure cernée, prêt pour le run complet ».

**Porte de sortie** : le notebook reproduit census + échantillons + stats gate ; il ne reste qu'à lancer le run.

## STAGE 5 — Run OCR complet (LE SEUL GROS RESTE — APRÈS validation 1-4 + crédit)
**Actions** (NON fait maintenant)
- Lancer l'OCR sur **2021/2022/2023/2024/2025** (~395 docs, **resumable** : ne re-paie que les batches échoués).
- Appliquer la passe LLM ticker ; régénérer `06b/06_FINAL/06d` ; **validation Quiver par année ET par cluster**.
- **Queue dure** (manuscrit/munis/Yoho/illisibles) → **flag low-confidence**, pas jetée ; Quiver où dispo.

**Porte de sortie** : `06_FINAL` pour les 7 ans, Quiver/an ≥ baseline, tail flaggée et documentée, rapport final.

---

## Vérification transverse
À chaque stade : comptes avant/après journalisés (règle CLAUDE.md), notebooks rejouables depuis le dossier
propre, `grep "semaine 1"` vide. Rien supprimé (tout l'écarté est dans `_archive/`).
