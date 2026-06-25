# toutes_annees — House PTR multi-années (2020 → 2026)

Généralisation de la méthode du pilote `../2025_test/` à toutes les années. **Notebook = source de
vérité** ; on travaille période par période.

> Le pilote fiable (Q1 2025) est dans **[`../2025_test/`](../2025_test/)**.

---

## 📂 Structure

```
toutes_annees/
├── README.md                          ← ce fichier
├── notebook_v2_house_multiyear.ipynb  ← notebook multi-années (digital), autonome
├── RAPPORT_DIGITAL_2020-2026.md       ← rapport méthodo digital
├── BACKLOG_OCR.md                     ← inventaire des PDF scannés à OCR plus tard
├── data_v1/
│   ├── ocr_cache/{année}/*.json       cache OCR (réutilisable)
│   └── tables/
│       ├── 00_year_status.csv             ★ dashboard (validation honnête)
│       ├── 00_quiver_q1style_status.csv   ★ dashboard (validation standard-Q1)
│       ├── 00_backlog_ocr.csv             inventaire PDF scannés
│       ├── _quiver_house_cache.csv        cache Quiver
│       └── {2020..2026}/ + 2025q1/        une sortie par période
└── _moteurs_py/                       ← ARCHIVE des scripts .py (fallback CLI, ne pas éditer)
```

---

## 📤 Où vont les sorties

Table de référence par année : **`data_v1/tables/{année}/06_house_{année}_FINAL.csv`**

**Dans chaque dossier d'année, toujours les mêmes préfixes :**

| Préfixe | Contenu |
|---|---|
| `03` | index des PTR de la période |
| `04` | manifeste de téléchargement (lisible / scanné / absent) |
| `05` | échecs de parsing (vide = 0 échec) |
| `06` | transactions **digitales** (PDF lisibles) |
| `06b` | transactions **OCR** (PDF scannés) |
| `06c` | échecs OCR + flags QA (vide = 0 échec) |
| `06d` | comparaison **OCR ↔ Quiver** |
| `07` | comparaison **digital ↔ Quiver** (`07b` trades manqués, `07c` vraiment absents) |
| `08` | cross-check vs l'ancien parser semaine 1 |
| **`…_FINAL`** | **digital + OCR fusionnés ⇒ LA table à utiliser** |

> Un fichier **vide** (`05`, `06c`) est un marqueur « 0 échec », c'est le résultat attendu.

---

## 📍 Où on en est

| Morceau | Statut |
|---|---|
| **Digital 2020→2026** | ✅ Fait pour les 7 années |
| **OCR 2020→2026** | 🟡 Partiel (fait sauf 2023) |
| **Fusion FINAL** | 🟡 Faite sauf **2023** |

---

## 🚧 Chantiers ouverts

1. **Notebook OCR multi-années** : l'OCR multi-années vivait dans `_moteurs_py/house_ocr_multiyear.py`.
   Pour rester « notebook-only », l'adapter depuis `../2025_test/notebook_v1_house_2025q1_ocr.ipynb`
   (déjà autonome) avec une boucle par année. Pas urgent : les données OCR sont déjà sur disque.
2. **Trou 2023** : il manque `06_house_2023_FINAL.csv`, `06b`, `06d`.
3. **Deux validations Quiver** coexistent (`07_quiver_comparison.csv` « honnête » vs
   `07_quiver_q1style.csv` « standard-Q1 », et leurs 2 dashboards `00_*`). À unifier un jour.
