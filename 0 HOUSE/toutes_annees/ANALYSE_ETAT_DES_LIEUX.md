# Analyse complète — état des lieux `toutes_annees` (digital + OCR) + cible propre autonome

But : prendre du recul sur TOUT ce qui a été fait, sortir les stats de concordance (élec + OCR), et définir
la cible « propre et autonome comme `2025_test` » pour qu'au final la **seule** chose restante soit le run OCR.
Chiffres ci-dessous **recalculés sur disque** (4 lecteurs parallèles), pas seulement lus dans les rapports.

---

## 1. DIGITAL (élec) — FINI et VALIDÉ ✅

**32 676 transactions** 2020→2026, rendement parse 99-100 %, 0 dérive de format vs baseline semaine 1.

| Année | n_txns | déclarants | % ticker | concordance Quiver (txn) | vrais-absents |
|---|---|---|---|---|---|
| 2020 | 6 886 | 96 | 91,0 % | **99,71 %** | 0 |
| 2021 | 5 457 | 105 | 91,1 % | **99,68 %** | 1 |
| 2022 | 3 601 | 97 | 86,8 % | **98,88 %** | 0 |
| 2023 | 4 161 | 88 | 86,9 % | **98,10 %** | 3 |
| 2024 | 2 694 | 90 | 81,8 % | **98,01 %** | 2 |
| 2025 | 7 577 | 96 | 90,5 % | **98,93 %** | 1 |
| 2026 | 2 300 | 79 | 84,0 % | **98,64 %** | 2 |

- **Concordance Quiver globale (niveau transaction) : 99,01 %** (méthode honnête q1style : dédup amendements,
  exclure papier des 2 côtés, cross-check ticker-raté). `only-Quiver = 241`, dont **232 ticker-raté** (présents
  chez nous, ticker non extrait) + **9 vrais-absents sur 6 ans** (Malinowski/Schrader/Calhoun/Gottheimer/Pelosi).
- Ticker fill réel : **88,6 %** global (cible ~95 % en raffinant préférentielles/Trésor/MLP).
- **Verdict : digital prêt.** Reste cosmétique : rafraîchir le tableau de `RAPPORT_DIGITAL_2020-2026.md`
  (cite encore l'ancien `quiver_coverage_pct` 35-74 % trompeur au lieu de la colonne q1style 98-99,7 %).

---

## 2. OCR (scannés) — moteur VALIDÉ, mais le RUN est INCOMPLET ⚠️

**Census complet 547/547** (`_scan_census_547.csv`) — 3 clusters :

| Cluster | Docs | Part | Profil |
|---|---|---|---|
| A — tapé droit | 74 | 13,5 % | le plus propre (64 high) ; 2026 bascule 100 % ici |
| B — tapé tourné 90° | 322 | 58,9 % | le gros ; lisible après redressement |
| C — manuscrit | 151 | 27,6 % | le point dur ; concentré 2020-2021 ; Quiver quasi absent |

Cas durs : **6 illisibles** + **4 non-PTR** (2 relevés externes Yoho, 1 campaign-notice Reisdorf, 1 cover-only Sherman).

**Gate de test (38 docs, stabilité 2-runs + Quiver fenêtré) :**
- **Tapé propre = excellent** : prec_ticker 85-100 % (Khanna 2023 = 1,0 / dates 0,97 / stab 0,96 ; McCaul 2022 = 0,94).
- **Queue dure cernée** : vieux scans 2020-2021 denses (Harshbarger), munis sans ticker (Schrader),
  manuscrit (non vérifiable, pas de Quiver), Yoho externe. prec_ticker global 0,91 → on n'invente pas
  d'instrument ; l'écart est sur les **dates** des scans dégradés.

**État réel des sorties OCR (le point clé) :**

| Année | census | OCR complet ? | cause |
|---|---|---|---|
| 2020 | 125 | ✅ **complet** (7 764 txns) | — |
| 2026 | 27 | ✅ **complet** (3 850 txns) | — |
| 2021 | 109 | 🟡 partiel (67 docs) | crédit API épuisé |
| 2022 | 108 | 🟡 partiel (45 docs) | crédit API épuisé |
| 2024 | 48 | 🟡 partiel (2 docs) | crédit API épuisé |
| 2025 | 61 | 🟡 partiel (15 docs) | crédit API épuisé |
| 2023 | 69 | 🔴 **vide** | crédit API épuisé |

→ **La panne = épuisement du crédit API (429 puis 400), PAS un défaut moteur.** Le cache est resumable au
niveau batch : un re-run ne re-paie QUE les batches échoués. **Reste ≈ 395 docs à finir (2021-2025).**

---

## 3. Le gold-standard `2025_test` — ce qu'il a en PLUS (à répliquer)

1. **Autonomie 100 %** : `BASE_DIR` ancré par marqueur de fichier (pas de chemin en dur) ; `.env` local
   (+ repli walk-up) ; `.venv` + kernel nommé ; **Quiver CSV embarqué localement** (`data_v1/external/`,
   validation offline reproductible) ; caches versionnés par `prompt_sha`.
2. **★ Passe LLM nom→ticker** (`ticker_llm_cache.json`, 310 entrées) que `toutes_annees` **n'a PAS** :
   elle fait passer le **ticker OCR de 46 % à 90 %**, et donne l'audit `06e` à **93,2 % vs Quiver**.
   C'est le plus gros levier de qualité manquant côté multi-années.
3. Notebooks couplés proprement : l'OCR lit en lecture seule la sortie digitale et fusionne (`06_…_FINAL`).

---

## 4. Pourquoi `toutes_annees` n'est PAS propre aujourd'hui

- **Dépend de `Jupiter/semaine 1/`** (PDF, index XML, baseline `house_transactions.csv`, YAML législateurs)
  → pas autonome. C'est la dépendance structurante à casser (embarquer ces entrées localement).
- **9 scripts dans `_moteurs_py/`** dont 7 jetables/one-shot (build_notebook, cache_quiver, make_backlog,
  revalidate×2, test×2) + **bugs de chemin** (cache_quiver/make_backlog pointent `_moteurs_py/data_v1` inexistant
  depuis le déplacement) + tests qui hardcodent `/Users/...` et lisent `/tmp/`.
- **Sorties intermédiaires** mêlées aux canoniques (05/06/06c/06d/07*/08, `_ocr_gate`, `_scan_census_547`).
- **Doublon `2025q1/`** (run de parité) qui pollue même `00_backlog_ocr.csv` (17 lignes parasites).

---

## 5. Cible propre (modèle `2025_test`), sans rien perdre

```
toutes_annees/
├── README.md  RAPPORT_DIGITAL.md  BACKLOG_OCR.md  ANALYSE_ETAT_DES_LIEUX.md
├── .env.example  .gitignore  requirements.txt        ← autonomie (clés/venv)
├── notebook_digital.ipynb   notebook_ocr.ipynb       ← source de vérité (2 notebooks couplés)
├── house_multiyear.py  house_ocr_multiyear.py        ← moteurs (remontés à la racine)
├── data_v1/
│   ├── external/quiver_house_2020_2026.csv           ← Quiver EMBARQUÉ (offline)
│   ├── pdfs/{année}/…                                 ← PDF déjà téléchargés, COPIÉS ici (pas de semaine 1)
│   ├── ocr_cache/{année}/*.json                       ← cache précieux (ne pas perdre)
│   ├── ticker_llm_cache.json                          ← NOUVEAU (passe LLM portée de 2025_test)
│   └── tables/ 00_*  _quiver_cache  {année}/{03,04,06b,06_FINAL}
└── _archive/                                          ← TOUT le reste (rien supprimé)
    ├── scripts/   (les 7 one-shot + tests)
    ├── tables_intermediaires/  (05,06,06c,06d,07*,08, _ocr_gate, _scan_census_547)
    └── 2025q1/    (doublon de parité)
```

---

## 6. Donc ce qui reste à faire (ordre) — le « plan d'attaque » à venir

1. **Reconstruire `toutes_annees` autonome** : embarquer les PDF déjà téléchargés + index + Quiver CSV + YAML,
   ancrer les chemins (BASE_DIR), `.env`/`.venv`/requirements locaux, archiver les 7 scripts + intermédiaires + 2025q1.
2. **Porter la passe LLM nom→ticker** de `2025_test` (ticker OCR 46 %→90 %).
3. **Refaire la concordance digitale propre** (un notebook narré, tableau q1style à jour) — données déjà là.
4. **Refaire la partie OCR comme le gate** : census + échantillons représentatifs montrés + analyse OCR sur
   échantillon + comparaison Quiver + stats (déjà fait à 90 %, à intégrer proprement au notebook).
5. **SEUL gros reste : lancer l'OCR sur tout** (2021-2025, ≈395 docs, resumable) — **à faire APRÈS**, si validé.

**État : digital prêt (99 % Quiver) ; OCR moteur validé + census + gate faits ; manque l'autonomie, la passe
LLM ticker, et le run OCR complet (bloqué par le crédit, pas par la qualité).**
