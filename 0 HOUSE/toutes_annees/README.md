# toutes_annees — House PTR multi-années (2020 → 2026)

Dossier **autonome** (modèle `../2025_test/`) : tout ce qu'il faut est embarqué dans `data_v1/`, **aucune
dépendance externe**. Digital + OCR. **Notebooks = source de vérité** ; les moteurs `.py` sont importés par eux.

> Le pilote figé Q1 2025 est dans **[`../2025_test/`](../2025_test/)**.

## 📂 Structure

```
toutes_annees/
├── README.md  RAPPORT_DIGITAL_2020-2026.md  BACKLOG_OCR.md
├── ANALYSE_ETAT_DES_LIEUX.md  PLAN_ATTAQUE.md      ← état des lieux + plan de reconstruction
├── .env.example  .gitignore  requirements.txt      ← autonomie (clés / venv / kernel)
├── notebook_digital.ipynb                          ← piste digitale + concordance Quiver
├── notebook_ocr.ipynb                              ← OCR : census + échantillons + gate  (Stage 4)
├── house_multiyear.py   house_ocr_multiyear.py     ← moteurs (ancrés BASE_DIR, importés par les notebooks)
├── data_v1/
│   ├── pdfs/{année}/*.pdf            547 PDF scannés EMBARQUÉS (pour le run OCR)
│   ├── index/{année}FD.xml           index PTR embarqué
│   ├── reference/*.yaml + baseline   référentiel + baseline cross-check
│   ├── ocr_cache/{année}/*.json      cache OCR resumable (versionné prompt_sha+model)
│   └── tables/
│       ├── 00_quiver_q1style_status.csv   ★ dashboard concordance digitale
│       ├── _quiver_house_cache.csv        cache Quiver (100 333 lignes, vérif externe)
│       ├── _scan_census_547.csv           recensement des 547 scannés (clusters)
│       ├── _ocr_gate/                      résultats du gate de test OCR (38 docs)
│       └── {2020..2026}/                   sorties par année (03,04,06,06b,06_FINAL…)
└── _archive/                               scripts one-shot + intermédiaires + 2025q1 (rien perdu)
```

## 📍 Où on en est (cf. [`PLAN_ATTAQUE.md`](PLAN_ATTAQUE.md))

| Morceau | Statut |
|---|---|
| **Autonomie** (Stage 1) | ✅ embarqué, `grep "semaine 1"` = 0 |
| **Digital + concordance** (Stage 2) | ✅ 32 676 txns, **99,01 %** Quiver, 9 vrais-absents |
| **Passe LLM nom→ticker** (Stage 3) | ⬜ à porter de `2025_test` (ticker OCR 46 %→90 %) |
| **Notebook OCR** (Stage 4) | ⬜ census + échantillons + gate |
| **Run OCR complet 2021-2025** (Stage 5) | ⬜ le seul gros reste (2020 + 2026 déjà complets) |

## ⚙️ Mise en route

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m ipykernel install --user --name jupiter-house-toutes-annees
cp .env.example .env   # renseigner ANTHROPIC_API_KEY
```
