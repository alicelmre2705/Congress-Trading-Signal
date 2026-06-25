# toutes_annees — House PTR multi-années (2020 → 2026)

Dossier **autonome** (modèle `../2025_test/`) : tout ce qu'il faut est embarqué dans `data_v1/`, **aucune
dépendance externe**. Digital + OCR. **Notebooks = source de vérité** ; les moteurs `.py` sont importés par eux.

> Le pilote figé Q1 2025 est dans **[`../2025_test/`](../2025_test/)**.

## 🎯 Statut rapide (2020 → 2026)

- ✅ **Digital** : 32 676 txns, **99,01 %** concordance Quiver, 9 vrais-absents (tous expliqués) — **FIGÉ**.
- ✅ **OCR échantillon A+B** : 3 876 txns (56 docs, ~10/an), **69 %** concordance, ticker 80 % — **FIGÉ**.
- ⛔ **Hors périmètre** : run OCR complet des 547 scannés, secteur GICS/ETF, avant-2020 (lot 2).
- 📖 Détail : [`SYNTHESE_PRESENTATION.md`](SYNTHESE_PRESENTATION.md) · Statut maître projet : [`../../ETAT_AVANCEMENT_PROJET.md`](../../ETAT_AVANCEMENT_PROJET.md)

## 📂 Structure

```
toutes_annees/
├── README.md  SYNTHESE_PRESENTATION.md            ← entrée + rapport détaillé
├── .env.example  .gitignore  requirements.txt      ← autonomie (clés / venv / kernel)
├── notebook_digital.ipynb                          ← piste digitale + concordance Quiver
├── notebook_ocr.ipynb                              ← OCR : census 547 + échantillon A+B + gate
├── house_multiyear.py   house_ocr_multiyear.py     ← moteurs (ancrés BASE_DIR, importés par les notebooks)
├── data_v1/
│   ├── pdfs/{année}/*.pdf            547 PDF scannés EMBARQUÉS (matière OCR)
│   ├── index/{année}FD.xml           index PTR embarqué
│   ├── reference/*.yaml + baseline   référentiel + baseline cross-check
│   ├── ocr_cache/{année}/*.json      cache OCR resumable (versionné prompt_sha+model)
│   └── tables/
│       ├── 00_quiver_q1style_status.csv   ★ dashboard concordance digitale (UNIQUE)
│       ├── _quiver_house_cache.csv        cache Quiver (100 333 lignes, vérif externe)
│       ├── _scan_census_547.csv           recensement des 547 scannés (clusters A/B/C)
│       ├── _ocr_echantillon_*.csv         échantillon OCR A+B : résultats + diff Quiver + par-doc
│       ├── _ocr_gate/                      résultats du gate de test OCR (38 docs)
│       └── {2020..2026}/                   sorties digitales/an (03,04,05,06_transactions,07_q1style,07b,07c,08)
└── _archive/                               jetables + 2025q1 + run OCR abandonné + dashboards périmés + secteur WIP
```

## 📍 Où on en est

| Morceau | Statut |
|---|---|
| **Autonomie** | ✅ embarqué, `grep "semaine 1"` = 0 |
| **Digital + concordance Quiver** | ✅ 32 676 txns, **99,01 %**, 9 vrais-absents tous expliqués |
| **Census 547 + OCR échantillon A+B + gate** | ✅ census A/B/C, échantillon 3 876 txns (deskew + validation honnête ±3 j) |
| **Passe LLM nom→ticker (échantillon)** | ✅ ticker 56 %→78 % (0 hallucination, ~90 % concordant Quiver) |
| **Run OCR complet des 547** | ⛔ hors périmètre (livrable = échantillon ; récup ciblée filers C = crédit API) |
| **Secteur GICS/ETF** | ⛔ différé sur toutes_annees (WIP parqué dans `_archive/sector_wip/`) |
| **Avant-2020 (lot 2, 2016-2019)** | ⛔ futur (extension digitale en arrière, réutilise `house_multiyear.py`) |

## ⚙️ Mise en route

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m ipykernel install --user --name jupiter-house-toutes-annees
cp .env.example .env   # renseigner ANTHROPIC_API_KEY
```
