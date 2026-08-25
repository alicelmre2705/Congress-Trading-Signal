#!/usr/bin/env python
"""Récolte de `notification_date` — la deuxième date du PTR House, jusqu'ici captée puis jetée.

CE QUE C'EST. Le formulaire PTR de la Chambre impose DEUX dates par ligne : *Date of Transaction*
et *Date Notified of Transaction*. La seconde existe précisément pour les comptes que l'élu ne
pilote pas lui-même (gestion déléguée, trust, mandat) : elle dit quand le gérant l'a INFORMÉ.
L'écart entre les deux est donc la mesure directe du contenu informationnel d'une ligne — un écart
nul dit que le déclarant savait au moment de l'ordre ; un écart de plusieurs semaines dit qu'il l'a
appris après coup, et qu'il n'a rien décidé.

POURQUOI ELLE N'ÉTAIT PAS DANS LES TABLES. Les deux parseurs déterministes la CAPTURENT depuis
toujours (groupe `notif` de `TXN_RE` / `_LEGACY_TXN_RE`) sans jamais lire le groupe ; l'OCR Vision
la demande explicitement et l'écrit dans les caches `data/house/ocr_cache/{Y}/{doc_id}.json`, où
elle ne sert que de repli mort. Elle est donc DÉJÀ PAYÉE, des deux côtés.

POURQUOI UN RÉFÉRENTIEL ANNEXE PLUTÔT QU'UNE COLONNE. Les 230 tables de `data/house/tables/` sont
verrouillées à l'octet par le filet golden ; y ajouter une colonne les réécrirait toutes. On suit
donc le pattern déjà établi du dépôt (`common/schema.py :: apply_*_fixes`) : le figé sur disque
n'est jamais modifié, l'information est jointe à la LECTURE.

COÛT : zéro appel API. Le digital est re-parsé depuis les PDF embarqués (CPU local, hors ligne) ;
l'OCR est relu depuis ses caches. Aucune écriture hors `data/reference/notification_dates.csv`.

Usage :
  python -m common.notification_dates                 # toutes les années
  python -m common.notification_dates --years 2024    # une année
  python -m common.notification_dates --dry-run
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
SORTIE = REPO / "data" / "reference" / "notification_dates.csv"
OCR_CACHE_ROOT = REPO / "data" / "house" / "ocr_cache"
ANNEES = list(range(2014, 2027))

# La clé de jointure est celle du corpus : (doc_id, natural_key_hash). `occurrence_index` n'y entre
# pas — les lots multi-comptes d'un même dépôt partagent forcément la même date de notification.
COLONNES = ["doc_id", "natural_key_hash", "notification_date", "provenance"]


def _iso(raw):
    """`MM/DD/YYYY` ou `YYYY-MM-DD` → ISO. Illisible → '' : on ne fabrique jamais une date."""
    d = pd.to_datetime(str(raw or "").strip(), errors="coerce")
    return "" if pd.isna(d) else d.date().isoformat()


def recolte_digital(year, tmpdir):
    """Rejoue le parsing des PDF lisibles de l'année et rend (doc_id, hash, notification_date).

    ⚠️ `build_manifest` et `parse_docs` écrivent leurs sous-produits (`04_download_manifest.csv`,
    `05_parse_failures.csv`) dans le dossier qu'on leur passe : on leur donne un dossier TEMPORAIRE,
    jamais `data/house/tables/{year}` — sans quoi le golden sauterait.
    """
    from house import digital as hd
    ptr_index, _ = hd.load_ptr_index(year)
    doc_texts, _manifest = hd.build_manifest(year, ptr_index, tmpdir)
    parser = hd.parse_ptr_dual if year <= 2019 else hd.parse_ptr
    parsed_rows, _f, _r, _y = hd.parse_docs(doc_texts, tmpdir, parser=parser)
    if not parsed_rows:
        return pd.DataFrame(columns=COLONNES)

    # On ne passe PAS par `join_identity` : il exige le référentiel des élus (donc le réseau) pour
    # résoudre les bioguides, alors que la clé naturelle n'en dépend pas — ses sept champs sont
    # chamber, declarant_name, transaction_date, asset_description, operation_type, amount_range,
    # owner. Seul `declarant_name` vient de l'index, et il y est déjà. La récolte reste hors ligne
    # et reproductible.
    df = pd.DataFrame(parsed_rows).merge(ptr_index[["doc_id", "declarant_name"]],
                                         on="doc_id", how="left")
    df["chamber"] = "house"
    # Reproduit EXACTEMENT la normalisation de `finalize` avant le calcul de clé : le hash porte
    # sur transaction_date normalisée et owner imputé, pas sur les valeurs brutes du parseur.
    df["ticker"] = df["ticker"].str.upper()
    df["owner"] = df["owner"].fillna("SELF")
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce").dt.date
    df["natural_key_hash"] = df.apply(hd._legacy_key, axis=1)
    df["notification_date"] = df["notification_date"].map(_iso)
    df["provenance"] = "house-pdf-electronic"
    return df[df["notification_date"] != ""][COLONNES]


def recolte_ocr(year):
    """Relit les caches Vision de l'année — aucun appel API, la donnée est déjà payée."""
    from house import digital as hd, ocr as ho
    cache_dir = OCR_CACHE_ROOT / str(year)
    ydir = hd.TABROOT / str(year)
    index_path = ydir / "03_ptr_index.csv"
    if not cache_dir.exists() or not index_path.exists():
        return pd.DataFrame(columns=COLONNES)

    ptr = pd.read_csv(index_path, dtype={"doc_id": str})
    meta_par_doc = {r["doc_id"]: r.to_dict() for _, r in ptr.iterrows()}

    lignes = []
    for cache_file in sorted(cache_dir.glob("*.json")):
        try:
            obj = json.loads(cache_file.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        doc_id = str(obj.get("doc_id") or cache_file.stem)
        meta = meta_par_doc.get(doc_id)
        if not meta:
            continue
        for txn in obj.get("transactions", []):
            if not isinstance(txn, dict):
                continue
            notif = _iso(txn.get("notification_date"))
            if not notif:
                continue
            # `normalize` calcule le natural_key_hash exactement comme le pipeline OCR de prod.
            ligne = ho.normalize(txn, meta, year)
            lignes.append({"doc_id": doc_id, "natural_key_hash": ligne["natural_key_hash"],
                           "notification_date": notif, "provenance": "house-pdf-ocr"})
    return pd.DataFrame(lignes, columns=COLONNES)


def build(years=ANNEES, dry_run=False, verbose=True):
    """Récolte les deux voies sur toutes les années et écrit le référentiel annexe."""
    morceaux = []
    with tempfile.TemporaryDirectory(prefix="notif_dates_") as tmp:
        tmpdir = Path(tmp)
        for y in years:
            d = recolte_digital(y, tmpdir)
            o = recolte_ocr(y)
            morceaux += [d, o]
            if verbose:
                print(f"  {y} : digital {len(d):6}  |  OCR {len(o):6}")

    out = pd.concat(morceaux, ignore_index=True) if morceaux else pd.DataFrame(columns=COLONNES)
    # Un même (doc_id, hash) peut sortir des deux voies (dépôt lisible ET scanné) : le digital
    # est déterministe, il gagne — même politique que la fusion du pipeline (house/ocr.py:560).
    out = (out.sort_values("provenance")           # 'house-pdf-electronic' < 'house-pdf-ocr'
              .drop_duplicates(["doc_id", "natural_key_hash"], keep="first")
              .sort_values(["doc_id", "natural_key_hash"])
              .reset_index(drop=True))
    if not dry_run:
        SORTIE.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(SORTIE, index=False)
    return out


def main():
    ap = argparse.ArgumentParser(description="Récolte notification_date (référentiel annexe).")
    ap.add_argument("--years", default="", help="ex: 2024 ou 2014-2019 (défaut : toutes)")
    ap.add_argument("--dry-run", action="store_true", help="calcule sans écrire")
    args = ap.parse_args()

    if args.years.strip():
        spec = args.years.strip()
        years = (list(range(int(spec.split("-")[0]), int(spec.split("-")[1]) + 1))
                 if "-" in spec and "," not in spec
                 else [int(x) for x in spec.split(",") if x.strip()])
    else:
        years = ANNEES

    print(f"Récolte notification_date — années {years[0]}-{years[-1]}"
          + (" [DRY-RUN]" if args.dry_run else ""))
    out = build(years, dry_run=args.dry_run)

    if len(out):
        par_prov = out["provenance"].value_counts().to_dict()
        print(f"\n→ {len(out)} lignes | {par_prov}")
    else:
        print("\n→ aucune ligne récoltée")
    print("(dry-run : rien écrit)" if args.dry_run else f"→ {SORTIE}")


if __name__ == "__main__":
    main()
