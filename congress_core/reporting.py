"""Sorties & tableaux de bord partagés — nommage de tables unifié, QA flags, dashboard, Excel.

Définit UNE fois la convention de numérotation (les suffixes divergeaient : 06c_qa_flags vs
06c_ocr_qa_flags ; 07b_missing_trades vs 07b_ticker_gaps). Fonctions réutilisées par les deux chambres.
"""
import pandas as pd

# Convention canonique des tables (documentée une fois pour les deux chambres).
TABLE_NUMBERING = {
    "01": "ref_universe (référentiel législateurs)",
    "02": "ref_<chamber>_key (membres commissions clés)",
    "03": "ptr_index (index des dépôts + URLs)",
    "04": "manifest (download/report : lisible/non_lisible/absent)",
    "05": "parse_failures",
    "06": "transactions (digital) ; 06_FINAL = digital + OCR",
    "06b": "ocr_transactions (Vision)",
    "06c": "qa_flags / ocr_failures",
    "06d": "ocr_quiver_comparison",
    "06f": "sector_audit (GICS→ETF)",
    "07": "quiver_comparison (digital vs Quiver)",
    "07b": "quiver_gaps (ticker-niveau)",
    "07c": "quiver_txn_reconciliation",
    "07d": "quiver_field_agreement",
    "07e": "quiver_ticker_per_member",
    "07f": "quiver_only_quiver_txn",
    "00": "dashboards (year_status / final_status)",
}

QA_REQUIRED = ["transaction_date", "amount_range", "owner", "operation_type", "asset_description"]


def qa_flags(df, required=QA_REQUIRED):
    """Anomalies réelles : champ obligatoire vide. Port de senate_finalize.qa. Renvoie un DataFrame."""
    rows = []
    for _, r in df.iterrows():
        probs = [c for c in required if c in df.columns and (not str(r[c]).strip() or str(r[c]) == "nan")]
        if probs:
            rows.append({"doc_id": r.get("doc_id"), "declarant_name": r.get("declarant_name"),
                         "asset_description": r.get("asset_description"), "flags": ",".join(probs)})
    return pd.DataFrame(rows, columns=["doc_id", "declarant_name", "asset_description", "flags"])


def upsert_status(rows, path, key="year"):
    """Écrit/met à jour un dashboard en remplaçant les lignes de même `key` (idempotent par période).
    Port du motif house_multiyear.main / senat_multiyear / merge_ocr."""
    import pandas as pd
    status = pd.DataFrame(rows)
    path = str(path)
    try:
        old = pd.read_csv(path)
        if key in old.columns and key in status.columns:
            old = old[~old[key].astype(str).isin(status[key].astype(str))]
            status = pd.concat([old, status], ignore_index=True)
    except FileNotFoundError:
        pass
    status.to_csv(path, index=False)
    return status


def write_excel(path, sheets, lisezmoi=None):
    """Excel multi-onglets. `sheets` = dict {nom_onglet: DataFrame}. `lisezmoi` = liste de lignes
    (ajoutée en 1er onglet LISEZMOI). Généralise senate_finalize.write_excel."""
    with pd.ExcelWriter(str(path), engine="openpyxl") as xl:
        if lisezmoi:
            pd.DataFrame({"": list(lisezmoi)}).to_excel(xl, sheet_name="LISEZMOI", index=False)
        for name, df in sheets.items():
            (df if df is not None and len(df) else pd.DataFrame({"info": ["(vide)"]})).to_excel(
                xl, sheet_name=name[:31], index=False)
