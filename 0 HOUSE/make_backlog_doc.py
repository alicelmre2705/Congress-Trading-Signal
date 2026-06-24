#!/usr/bin/env python
"""Génère BACKLOG_OCR.md (lisible humain) à partir de data_v1/tables/00_backlog_ocr.csv.

Liste les PTR scannés NON LISIBLES, par année, à traiter ultérieurement via la méthode
OCR PDF/Vision de Claude (notebook_v1_house_2025q1_ocr.ipynb). Ce périmètre est volontairement
HORS du pipeline digital de house_multiyear.py.
"""
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
TAB = HERE / "data_v1" / "tables"

bk = pd.read_csv(TAB / "00_backlog_ocr.csv", dtype={"doc_id": str})
# Exclure le tag de test de parité 2025q1 (ses PDF sont déjà comptés dans l'année 2025 pleine)
bk = bk[bk["year"].astype(str) != "2025q1"].copy()
status_path = TAB / "00_year_status.csv"
status = pd.read_csv(status_path) if status_path.exists() else None

bk["year"] = bk["year"].astype(str)
by_year = bk.groupby("year").agg(n_pdf=("doc_id", "count"),
                                 n_declarants=("declarant_name", "nunique"),
                                 n_pages=("n_pages", "sum")).reset_index()

lines = []
lines.append("# Backlog OCR — PTR House scannés (non lisibles)\n")
lines.append("> **Statut : NON TRAITÉ (différé).** Ces PDF n'ont pas de couche texte "
             "(scans/dépôts papier, DocID commençant par `8`/`9`). Le pipeline digital "
             "`house_multiyear.py` les **inventorie mais ne les extrait pas**.\n")
lines.append("> **Méthode prévue (ultérieure) :** OCR PDF/Vision de Claude "
             "(`claude-sonnet-4-6`, tool_use `record_transactions`), cf. "
             "`notebook_v1_house_2025q1_ocr.ipynb` qui le fait déjà pour 2025 T1.\n")
lines.append(f"\n**Total inventorié : {len(bk)} PDF / {bk['declarant_name'].nunique()} déclarants distincts.**\n")

lines.append("\n## Volume par année\n")
lines.append("| Année | PDF non lisibles | Déclarants | Pages (≈ coût OCR) |")
lines.append("|---|---|---|---|")
for _, r in by_year.iterrows():
    pg = int(r["n_pages"]) if pd.notna(r["n_pages"]) else 0
    lines.append(f"| {r['year']} | {int(r['n_pdf'])} | {int(r['n_declarants'])} | {pg} |")
tot_pages = int(bk["n_pages"].fillna(0).sum())
lines.append(f"| **Total** | **{len(bk)}** | — | **{tot_pages}** |")
lines.append(f"\n_Estimation coût OCR Claude Vision ≈ {tot_pages} pages × ~0,006 $ ≈ "
             f"**{tot_pages*0.006:.0f} $**._\n")

# Gros déposants papier (les plus prioritaires pour l'OCR — gros volumes manquants)
top = (bk.groupby("declarant_name").agg(n_pdf=("doc_id", "count"),
                                        n_pages=("n_pages", "sum"))
       .sort_values("n_pdf", ascending=False).head(20).reset_index())
lines.append("\n## Top déposants papier (priorité OCR)\n")
lines.append("| Déclarant | PDF scannés | Pages |")
lines.append("|---|---|---|")
for _, r in top.iterrows():
    pg = int(r["n_pages"]) if pd.notna(r["n_pages"]) else 0
    lines.append(f"| {r['declarant_name']} | {int(r['n_pdf'])} | {pg} |")

lines.append("\n## Détail complet\n")
lines.append("Voir `data_v1/tables/00_backlog_ocr.csv` (year, doc_id, declarant_name, "
             "state_district, disclosure_date, n_pages).\n")

out = HERE / "BACKLOG_OCR.md"
out.write_text("\n".join(lines))
print(f"→ {out} ({len(bk)} PDF, {tot_pages} pages, ~{tot_pages*0.006:.0f}$ OCR estimé)")
