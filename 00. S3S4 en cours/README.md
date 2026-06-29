# Congress Trading Signal — Recherche stratégie (Semaines 3-4)

**Toute la recherche tient dans un seul notebook autonome : [`Congress_Trading_Signal_Recherche.ipynb`](Congress_Trading_Signal_Recherche.ipynb).**

On le lit de haut en bas et on comprend tout — **aucun fichier `.py` à ouvrir** : la **Partie 0** définit
l'intégralité du moteur (chargement, prix, event-study, portefeuille, métriques, sélection) en cellules
courtes et expliquées ; les **Parties I-IX** racontent la recherche (contexte → données → event-study →
chasse au signal → backtest générique → stratégie Ramify V1 actions → V2 ETF → approfondissement →
littérature → verdict). Déjà exécuté (sorties + graphiques sauvegardés), relançable sur le kernel
*S3S4 (.venv)*.

- **Seules dépendances** : `numpy / pandas / scipy / scikit-learn / matplotlib / pyyaml` (aucun module maison).
- **Données** (lecture seule) : journal **et** enrichissement = [`table_congres_2014_2026.csv`](table_congres_2014_2026.csv)
  (**HYBRIDE**, voir ci-dessous) ; prix dans `cache/` (gitignoré).
- **Recherche ISOLÉE** : écriture uniquement dans ce dossier ; rien du travail finalisé n'est touché.

## Construction de la table HYBRIDE 2014-2026 — [`02_construction_table_2014_2026.ipynb`](02_construction_table_2014_2026.ipynb)

La table est **HYBRIDE** (≈ **138 557** lignes × 22 colonnes) :
- **2020-2026 = le golden** (le travail « partie 1 » : sources officielles + OCR papier + non-coté, **90 487** txns) — réutilisé tel quel ;
- **2014-2019 = Quiver** (reconstruit depuis l'API, identité/secteur/commissions, **48 070** txns) — l'extension passé.
- **Commissions recalculées point-in-time sur TOUTE la période** (snapshots git par Congrès 113→119), y compris sur
  le golden (qui était sur le snapshot *actuel*). Frontière propre (Quiver `filed ≤ 2019`, golden `disclosure ≥ 2020`),
  pas de double-comptage ; colonne `source` pour tracer.

> **Pourquoi hybride** : Quiver **sous-compte 2020-2026** (~65 k vs 90 k golden) car il ne suit pas le non-coté ni tout
> le papier OCR. On garde donc le golden pour 2020-26 (le backtest profite de ~10 k actions de plus) et Quiver pour 2014-19.
> **Limite assumée** : 2014-2019 = Quiver seul (pas de papier OCR ni non-coté) — à compléter plus tard avec la
> méthodo OCR de la partie 1. Concordance Quiver↔golden vérifiée sur 2020-26 : secteur ≈ 98 %, parti 100 %.

### Deux caches distincts (ne pas confondre)

| Dossier | Appartient à | Contenu | Statut |
|---|---|---|---|
| **`build_cache/`** | `02_construction_table…` | Quiver brut, référentiels `legislators`, snapshots de commissions, `ticker_sector.json` | gitignoré, régénérable |
| **`cache/`** | `Congress_Trading_Signal_Recherche` | cours yfinance (`prices/`) + facteurs Fama-French | gitignoré, régénérable |

Aucun des deux notebooks ne lit le cache de l'autre. *Note secteur :* les ETF/fonds diversifiés ou obligataires
(SPY, QQQ, VOO, TIP…) restent volontairement sans secteur GICS (`none`) ; seules les actions (y compris délistées
connues : TWTR, ANTM…) sont mappées.

**Verdict** : alpha actions positif mais non significatif (V1), dilué en ETF (V2), aucune version ne bat SPY
en risque-ajusté → produit thématique livrable (à la NANC/KRUZ), pas un générateur d'alpha.

*Les versions antérieures (notebook `01_quiver_partie_A`, notebooks séparés, modules `.py`, notes) sont conservées dans `_archive/`.*
