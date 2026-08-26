# Congress Trading Signal

Extraction, validation et exploitation des déclarations boursières (PTR, *STOCK Act*) des membres
du Congrès américain — **Chambre des représentants + Sénat, 2014 → 2026**.

Sources officielles : *House Clerk* (PTR PDF) et Sénat *eFD*, **électroniques** (parsing
déterministe) **et scannées** (OCR Claude Vision). La source primaire des deux chambres est
embarquée dans le dépôt : chaque ligne des tables est re-vérifiable contre son document, sans rien
télécharger. Quiver Quantitative sert de **vérification externe uniquement**, jamais réinjecté.

> `main` ne garde que **ce qui se montre** — supports de présentation, documents de référence,
> donnée certifiée. Le brief de mission, les documents de travail, les archives et l'historique
> complet vivent sur la branche `presentation`.

## Les trois parties

| | le dossier | par où entrer | ce qu'on y trouve |
|---|---|---|---|
| **0 · les données** | [`00_recuperation_donnees/`](00_recuperation_donnees/README.md) | [`RAPPORT_DONNEES.md`](00_recuperation_donnees/RAPPORT_DONNEES.md) | le pipeline des deux chambres et les 4 tables livrées. Le rapport est **régénérable** : relancer le pipeline recalcule chaque chiffre depuis la donnée. |
| **1 · au-delà des PTR** | [`01_autres_filing_types/`](01_autres_filing_types/) | [`SYNTHESE_EXTRACTION_HOUSE.pdf`](01_autres_filing_types/SYNTHESE_EXTRACTION_HOUSE.pdf) | Schedule A/B, rapports annuels, photos d'entrée, portefeuilles House reconstruits — ce qui a été extrait, et avec quelles garanties. |
| **2 · la stratégie** | [`02_recherche_backtest/`](02_recherche_backtest/README.md) | [`FICHE_M3.pdf`](02_recherche_backtest/3_livrable_M3/FICHE_M3.pdf) | **LE livrable** : noter les titres plutôt que copier les élus. M3, sa version ETF, et le portefeuille final à deux poches. |

Les autres documents, par partie :

- **0** — [`SLIDES_DONNEES.pdf`](00_recuperation_donnees/SLIDES_DONNEES.pdf) (107 p.) ·
  [`REPONSES_VERIFICATIONS.md`](00_recuperation_donnees/REPONSES_VERIFICATIONS.md), le tableau de
  bord des six vérifications C1→C6 et des deux travaux T1/T2, chacun avec le chiffre qui tranche.
- **1** — [`FICHE_HOUSE.pdf`](01_autres_filing_types/FICHE_HOUSE.pdf) et les deux decks de
  [`slides/`](01_autres_filing_types/slides/) (39 p. et 35 p.).
- **2** — [`SLIDES_RECHERCHE.pdf`](02_recherche_backtest/SLIDES_RECHERCHE.pdf) (25 p.) ·
  [`PISTES_TESTEES.md`](02_recherche_backtest/PISTES_TESTEES.md), l'inventaire des ~90 pistes
  testées avec leur résultat chiffré, pour ne jamais ré-explorer une piste morte · et, autour de
  la fiche, `PAPIER_METHODE` · `FICHE_NOTER_LES_TITRES` · `AUDIT_FONDS_NANC_GOP` ·
  `ETAT_DE_L_ART_STRATEGIES`.

## Les commandes qui servent

```bash
python3.12 -m venv .venv && ./.venv/bin/pip install -e .
```

Les suivantes se lancent depuis `00_recuperation_donnees/` :

```bash
python -m common.pipeline --years 2014-2026       # tout reconstruire — hors ligne, source embarquée
python -m common.pipeline --years 2026 --acquire  # compléter une année nouvelle (idempotent)

python -m common.first_seen                       # horodater ce qui apparaît en ligne
python -m common.live_run                         # les dépôts nouveaux -> lignes au format de la table

python tests/regression/check_golden.py           # « ZÉRO ÉCART » = rien n'a bougé
```

Les deux entrées **en direct** sont hors du chemin par années et n'écrivent jamais dans les tables
gelées, verrouillées à l'octet par le filet golden — le détail et les autres tests :
[le README de la partie 0](00_recuperation_donnees/README.md#démarrage-rapide--les-cinq-commandes-qui-servent).

`first_seen` tourne **tout seul** depuis GitHub Actions
([`.github/workflows/first_seen.yml`](.github/workflows/first_seen.yml)) : cron quotidien à 06:00
UTC, et le job commite le CSV qu'il produit. C'est la seule donnée du dépôt qui **ne se reconstitue
pas** a posteriori — chaque jour sans passage est un jour perdu définitivement.

## La donnée livrée

Dans `00_recuperation_donnees/data/clean/` — **brute** (`169 000 × 43`, tout le corpus avec le
verdict d'entonnoir par ligne), **clean** (`transactions_backtest_2014_2026.csv`,
**118 316 × 41** — la table de recherche canonique, celle que la partie 2 consomme) et **gated**
(7 287 manuscrites écartées, avec leur motif), plus la table annexe des commissions.

**Quatre dates**, et il faut les distinguer :

| date | ce qu'elle est |
|---|---|
| `transaction_date` | l'opération déclarée — descriptif seul, et l'ancienneté d'un lot en FIFO |
| `notification_date` | quand le déclarant dit avoir été **informé** — sépare la décision propre de la gestion déléguée |
| `disclosure_date` | le dépôt officiel |
| `first_seen_at` | quand **nous** voyons le document en ligne — la seule certainement publique |

**Anti-look-ahead** : le signal entre sur `signal_date = max(disclosure_date, first_seen_at)`,
jamais sur `transaction_date` (`common/live_run.py`). Délai médian transaction → divulgation :
**27 j** côté House, 24 j au Sénat.

## Chiffres clés

| Chambre | FINAL (uniques) | brut = digital + OCR | Identité | Concordance Quiver |
|---|---|---|---|---|
| **House** | **151 989** | 152 081 = 58 756 + 93 325 | 100 % (367 bioguides) | in-window **93,5 %** |
| **Sénat** | **17 011** | 18 839 = 14 813 + 4 026 | 100 % (78 bioguides) | in-window **92,1 %** |

**169 000 transactions uniques de membres élus**, après dédup cross-année des re-divulgations
tardives. **100 % des 8 252 PTR listés par l'index officiel du Clerk 2014-2026 sont traités** —
parsés, OCRisés, ou écartés par une règle écrite. Les scans **manuscrits** sont exclus par une
politique uniforme et rejouable (582 documents). Avant ~2017, Quiver est mince : nos actions « en
plus » sont réelles mais peu corroborables. Les preuves derrière chaque nombre sont dans
[`RAPPORT_DONNEES.md`](00_recuperation_donnees/RAPPORT_DONNEES.md).

Compter **~1 Go au clone** — c'est le prix de l'autonomie. Re-exécuter les notebooks des parties 1
et 2 exige en plus des caches de prix non versionnés (ils se reconstruisent via yfinance) ; les
sorties des notebooks restent lisibles dans les `.ipynb` sans rien exécuter.

## Avertissement

Les données proviennent de documents **publics officiels** (STOCK Act — déclarations obligatoires
des élus) ; elles restent **nominatives** et sont fournies telles que déclarées, avec leurs limites
documentées. Ce dépôt est un **travail de recherche** : rien ici ne constitue un conseil en
investissement.
