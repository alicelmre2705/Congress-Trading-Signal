#!/usr/bin/env python
"""Génère notebook_v2_house_multiyear.ipynb : la logique digitale de house_multiyear.py
matérialisée en cellules narrées (markdown + code), conforme à la règle de transparence du projet
(« tout le code de transformation vit dans le notebook »). Le module reste comme miroir CLI testé.
"""
import re
import nbformat as nbf

SRC = open("house_multiyear.py").read().split("\n")

# Narratifs (une phrase) par section, dans l'esprit « le notebook se lit comme une histoire »
NARR = {
    "Chemins & constantes": "On réutilise les PDF + index déjà téléchargés dans `semaine 1/` (zéro re-téléchargement) ; toutes les sorties partent dans `data_v1/tables/{année}/`.",
    "Normalisation noms": "Deux helpers pour normaliser les noms (sans accents, minuscules) — base du rattachement déclarant → BioGuideID.",
    "Référentiel identité": "On charge l'annuaire complet des élus (current + historical) et les commissions, et on construit les tables de correspondance nom→bioguide.",
    "Patterns de parsing (port cellule 16)": "Les expressions régulières du parser. **Tolérantes à la casse** : les PDF pré-2021 rendent des majuscules en minuscules (`[sT]`, `(aos)`).",
    "Prétraitement lignes (port cellule 18)": "Recollage des lignes éclatées (montant ou actif sur la ligne suivante) et helpers de montant/opération.",
    "parse_ptr (port cellule 20)": "Le cœur : extrait chaque transaction d'un PDF lisible. Une transaction est validée par un code `[XX]` **ou** un ticker en continuation (cas des MLP « Limited Partner Interests » sans code).",
    "match_bioguide (port cellule 25)": "Rattachement robuste déclarant → BioGuideID (surnoms, noms composés, titres honorifiques).",
    "Index + manifeste par année": "Lecture de l'index XML (filtre `FilingType=P`), routage lisible/non-lisible (sans déplacer les PDF), parsing, jointure identité, puis **table finale dédupliquée** (dédup canonique per-lot : préserve les lots identiques intra-PTR via `occurrence_index`).",
    "Cross-check vs baseline semaine 1": "Détecteur de dérive de format : un PDF parsé par semaine 1 mais où nous sortons 0 ligne = signal à inspecter.",
    "Quiver (vérification externe)": "Validation **honnête** : comparaison per-lot (notre canonique vs Quiver brut) + recouvrement au niveau transaction. Quiver ne nourrit JAMAIS la table finale.",
    "Orchestration par année": "Assemble toutes les étapes pour une année et journalise les compteurs à chaque porte.",
}

# repérage des marqueurs de section et de def main()
markers = [(i, re.sub(r"^#\s*─+\s*|\s*─+\s*$", "", l).strip()) for i, l in enumerate(SRC) if l.startswith("# ─")]
main_idx = next(i for i, l in enumerate(SRC) if l.startswith("def main("))

# en-tête (avant le 1er marqueur) : shebang + docstring + imports
head_end = markers[0][0]
header = SRC[:head_end]
# retirer shebang
if header and header[0].startswith("#!"):
    header = header[1:]
# retirer le docstring module (premier bloc triple-quotes)
txt = "\n".join(header)
txt = re.sub(r'^\s*""".*?"""\s*', "", txt, count=1, flags=re.DOTALL).strip()
imports_code = txt

cells = []
cells.append(nbf.v4.new_markdown_cell(
    "# Pipeline House — piste DIGITALE multi-années (PDF lisibles)\n\n"
    "Extraction des transactions des PTR House à partir des **PDF lisibles uniquement** "
    "(`pdfplumber` + parser ancré). Les PDF scannés sont **différés** (cf. `BACKLOG_OCR.md` / "
    "`house_ocr_multiyear.py`). **Quiver = vérification externe uniquement.** "
    "`disclosure_date` = FilingDate de l'index (anti look-ahead).\n\n"
    "> Exécuter ce notebook **depuis le dossier `0 HOUSE/`**. Logique miroir testée : `house_multiyear.py`."))
cells.append(nbf.v4.new_markdown_cell("## Étape 0 — Imports"))
cells.append(nbf.v4.new_code_cell(imports_code))

# sections par marqueur (jusqu'à def main exclu)
bounds = [m[0] for m in markers] + [main_idx]
for k, (start, title) in enumerate(markers):
    end = bounds[k + 1]
    body = "\n".join(SRC[start + 1:end]).strip("\n")
    # adapter le chemin pour le notebook (pas de __file__)
    body = body.replace("HERE = Path(__file__).resolve().parent",
                        "HERE = Path.cwd()  # exécuter le notebook depuis 0 HOUSE/")
    narr = NARR.get(title, "")
    cells.append(nbf.v4.new_markdown_cell(f"## {title}\n\n{narr}" if narr else f"## {title}"))
    cells.append(nbf.v4.new_code_cell(body))

# cellule d'orchestration finale (remplace main())
cells.append(nbf.v4.new_markdown_cell(
    "## Exécution — référentiel puis boucle années 2020→2026\n\n"
    "`build_reference()` une fois, puis `run_year()` par année (écrit `06_house_{année}_transactions.csv`, "
    "`07/07b` Quiver, `08` cross-check). Décommenter pour lancer."))
cells.append(nbf.v4.new_code_cell(
    "import pandas as pd\n\n"
    "build_reference()\n"
    "YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]\n"
    "summaries = []\n"
    "for YEAR in YEARS:\n"
    "    s, df_year, backlog = run_year(YEAR)\n"
    "    summaries.append(s)\n"
    "\n"
    "# Parité (optionnel) : reproduire 2025 T1 et vérifier 1105 lignes legacy\n"
    "# s, df_q1, _ = run_year(2025, pd.Timestamp('2025-01-01'), pd.Timestamp('2025-03-31'), tag='2025q1')\n"))

nb = nbf.v4.new_notebook(cells=cells)
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
               "language_info": {"name": "python"}}
nbf.write(nb, "notebook_v2_house_multiyear.ipynb")
print(f"→ notebook_v2_house_multiyear.ipynb : {len(cells)} cellules "
      f"({sum(1 for c in cells if c.cell_type=='code')} code / {sum(1 for c in cells if c.cell_type=='markdown')} markdown)")
