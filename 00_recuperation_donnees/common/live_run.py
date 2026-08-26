#!/usr/bin/env python
"""Run en direct — les dépôts nouveaux, du document brut à la ligne de features.

CE QUE FAIT CE MODULE. À chaque exécution : il regarde ce que le crawl d'horodatage
(`common.first_seen`) a vu apparaître, retient ce qui n'est pas déjà dans le corpus, et fait passer
ces documents par TOUT le chemin — téléchargement, parsing, normalisation, mapping des noms,
mapping des tickers, déduplication, features — pour produire des lignes au format exact de la table
de référence (les 12 champs garantis, p. 31 du deck).

POURQUOI IL NE PASSE PAS PAR LE PIPELINE. `common.pipeline` est bâti pour reconstruire des ANNÉES
entières : `house.digital.run_year` re-parse tout l'index et réécrit `data/house/tables/{Y}/` ;
`senate.fusion` n'a même pas d'option d'année (il globe tout, ré-enrichit le corpus complet et
réécrit les 13 tables FINAL du Sénat) ; les steps 6-8 relisent toujours les 26 FINAL. Or ces tables
sont verrouillées à l'octet par le filet golden (230 + 138 fichiers). Un run quotidien qui passerait
par là casserait le filet tous les jours.

Ce module ouvre donc une VOIE PARALLÈLE : il réutilise les fonctions pures du pipeline (parseurs,
clé naturelle, matcher d'identité, ticker canonique, enrichissement point-in-time) et n'écrit que
dans `data/live/`. Il ne touche JAMAIS à `data/*/tables/` — un test le vérifie
(`tests/regression/test_live_run.py`). La réconciliation avec le corpus figé se fait au run de
pipeline complet suivant.

CE QU'IL NE FAIT PAS. Pas de validation Quiver, pas de cross-check : ce sont des mesures de
qualité, pas des étapes de production, et elles coûtent du réseau et une clé API à chaque passage.

Usage :
  python -m common.live_run --dry-run                 # ce qui serait produit, sans rien écrire
  python -m common.live_run                           # produit data/live/live_{date}.csv
  python -m common.live_run --chamber house --limit 20
"""
import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
LIVE_DIR = REPO / "data" / "live"
FIRST_SEEN_CSV = REPO / "data" / "first_seen" / "first_seen.csv"

# Les 12 champs garantis de la table de référence (deck des données, p. 31 : « À quoi ressemble la
# valeur finale »), dans l'ordre de la slide — membre · chambre · parti · comités · date trade ·
# date div. · sens · montant $ · type · ticker · secteur · ETF.
CHAMPS_P31 = ["member_name", "chamber", "party", "committees_key_flag",
              "transaction_date", "disclosure_date", "direction", "amount_midpoint",
              "asset_class", "ticker_yahoo", "sector_gics", "etf_proxy"]

# Traçabilité : d'où vient la ligne, et depuis quand l'information est publique.
CHAMPS_TRACE = ["doc_id", "natural_key_hash", "provenance",
                "first_seen_at", "notification_date", "signal_date"]

COLONNES = CHAMPS_P31 + CHAMPS_TRACE


# ───────────────────────────── détection de nouveauté ─────────────────────────────
def documents_du_corpus():
    """Les doc_id DÉJÀ traités : ceux des 26 tables FINAL, plus ceux d'un run live antérieur."""
    connus = set()
    for chambre in ("house", "senate"):
        for f in (REPO / "data" / chambre / "tables").glob("*/06_*_FINAL.csv"):
            with f.open(newline="", encoding="utf-8") as fh:
                connus |= {r["doc_id"].strip() for r in csv.DictReader(fh) if r.get("doc_id")}
    for f in LIVE_DIR.glob("live_*.csv"):
        with f.open(newline="", encoding="utf-8") as fh:
            connus |= {r["doc_id"].strip() for r in csv.DictReader(fh) if r.get("doc_id")}
    return connus


def nouveaux_documents(chamber="both", limit=None):
    """Ce que le crawl a vu et que le corpus n'a pas encore.

    La détection est déléguée à `first_seen.csv` : un seul endroit décide de ce qui est nouveau, et
    c'est celui qui tourne tous les jours. Éviter un second détecteur, c'est éviter deux vérités.
    """
    if not FIRST_SEEN_CSV.exists():
        raise SystemExit("data/first_seen/first_seen.csv absent — lancer d'abord "
                         "`python -m common.first_seen --backfill` puis le crawl.")
    connus = documents_du_corpus()
    with FIRST_SEEN_CSV.open(newline="", encoding="utf-8") as f:
        vus = list(csv.DictReader(f))
    out = [r for r in vus
           if r["doc_id"].strip() not in connus
           and (chamber == "both" or r["chamber"] == chamber)]
    # Le plus récemment déposé d'abord : si on limite, on traite ce qui a le plus de valeur.
    out.sort(key=lambda r: r["disclosure_date"] or "", reverse=True)
    return pd.DataFrame(out[:limit] if limit else out)


# ───────────────────────────── House ─────────────────────────────
def traiter_house(docs):
    """Télécharge (si besoin) et parse les PTR House nouveaux → lignes au schéma FINAL House.

    Rend (lignes, doc_id des scans non traités) — un scan exige l'OCR, donc la classification.
    """
    if docs.empty:
        return pd.DataFrame(), []
    import requests
    from house import acquire as ha, digital as hd
    from common.first_seen import ptr_index_frais
    from common.schema import natural_key_hash

    hd.build_reference()          # référentiel des élus (live, repli YAML) — requis par le matcher
    session = requests.Session()
    session.headers.update({"User-Agent": ha.SESSION.headers.get("User-Agent", "")})
    lignes = []
    for annee, groupe in docs.groupby(docs["disclosure_date"].str[:4]):
        if not annee:
            continue
        annee = int(annee)
        # L'index FRAIS, pas l'embarqué : un dépôt arrivé depuis le dernier téléchargement n'est
        # pas dans `data/house/index/{Y}FD.xml`, donc invisible à `load_ptr_index`. C'est
        # précisément le cas de tout ce que le crawl vient de découvrir.
        meta = {str(r["doc_id"]): r for r in ptr_index_frais(annee, session, save_snapshot=False)}
        parser = hd.parse_ptr_dual if annee <= 2019 else hd.parse_ptr

        for doc_id in groupe["doc_id"].astype(str):
            m = meta.get(doc_id)
            if m is None:
                continue                     # listé par le crawl mais absent de l'index relu
            chemin = hd.resolve_pdf_path(annee, doc_id)
            if chemin is None:
                resp = ha._get(hd.HOUSE_PDF_URL.format(year=annee, doc_id=doc_id))
                if resp.status_code != 200 or not resp.content:
                    continue                 # 404 : dépôt listé mais PDF pas encore publié
                dossier = ha.PDF_DIR / str(annee)
                dossier.mkdir(parents=True, exist_ok=True)
                (dossier / f"{doc_id}.pdf").write_bytes(resp.content)
                chemin = hd.resolve_pdf_path(annee, doc_id)
            texte = hd.extract_text(chemin)
            if not texte.strip():
                # Scan : il faut l'OCR, qui exige d'abord la classification (tapé/manuscrit).
                # Hors périmètre d'un run quotidien — signalé, pas traité en silence.
                lignes.append({"doc_id": doc_id, "_scan": True})
                continue
            for r in parser(texte):
                r.update({"doc_id": doc_id, "chamber": "house",
                          "declarant_name": m["declarant_name"],
                          "last": m["last"], "first": m["first"],
                          "state_district": m.get("state_district", ""),
                          "disclosure_date": m["disclosure_date"],
                          "provenance": "house-pdf-electronic"})
                lignes.append(r)

    df = pd.DataFrame([l for l in lignes if not l.get("_scan")])
    scans = [l["doc_id"] for l in lignes if l.get("_scan")]
    if df.empty:
        return pd.DataFrame(), scans

    df["ticker"] = df["ticker"].astype("string").str.upper()
    df["owner"] = df["owner"].fillna("SELF")
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce").dt.date
    df["disclosure_date"] = pd.to_datetime(df["disclosure_date"], errors="coerce").dt.date
    df["natural_key_hash"] = df.apply(lambda r: natural_key_hash(r, "house"), axis=1)
    df["bioguide_id"] = [hd.match_bioguide(l, f) for l, f in zip(df["last"], df["first"])]
    df["party"] = None
    df["sector_gics"] = None
    df["etf_proxy"] = None
    return df, scans


# ───────────────────────────── Sénat ─────────────────────────────
def traiter_senate(docs):
    """Récupère et parse les dépôts eFD électroniques nouveaux → lignes au schéma FINAL Sénat."""
    if docs.empty:
        return pd.DataFrame(), []
    from senate import digital as sd
    from senate.identity import load_reference, make_matcher, enrich as enrich_senate
    from senate.efd_session import accept_agreement

    accept_agreement(sd.SESSION)
    # 6 valeurs — même dépaquetage que senate/digital.py:277 (la source unique du Sénat)
    ref, name_exact, name_by_last, current_bios, bio_to_committees, key_flag = load_reference()
    match = make_matcher(ref, name_exact, name_by_last, current_bios)

    lignes, papier = [], []
    for _, d in docs.iterrows():
        uuid, kind = d["doc_id"], (d.get("kind") or "")
        if kind == "paper":
            papier.append(uuid)          # scan : hors périmètre d'un run quotidien
            continue
        url, html = sd.fetch_report(uuid)
        if not html:
            continue
        for t in sd.parse_electronic(html):
            t.update({"doc_id": uuid, "source_url": url,
                      "declarant_name": d.get("declarant_name", ""),
                      "disclosure_date": d["disclosure_date"],
                      "provenance": "senate-efd-electronic"})
            lignes.append(t)

    if not lignes:
        return pd.DataFrame(), papier
    df = enrich_senate(pd.DataFrame(lignes), ref, bio_to_committees, key_flag, match)
    df["sector_gics"] = df.get("sector_gics")
    df["etf_proxy"] = df.get("etf_proxy")
    return df, papier


# ───────────────────────────── assemblage ─────────────────────────────
def ligne_p31(df):
    """Applique les correctifs read-time et l'enrichissement, puis rend les 12 champs + traçabilité."""
    from common import backtest_clean as bc, quality as q, schema

    df = schema.apply_txn_date_fixes(df)
    df = schema.apply_identity_fixes(df)
    df = schema.apply_notification_dates(df, REPO)
    df["_td"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    dd = pd.to_datetime(df["disclosure_date"], errors="coerce")
    df["lag_days"] = (dd - df["_td"]).dt.days
    df["amount_midpoint"] = pd.to_numeric(df["amount_midpoint"], errors="coerce")
    df = schema.apply_amount_range_fixes(df)
    df["op"] = df["operation_type"].map(q.op_class)
    df, _n_fp = bc.apply_ticker_false_positive_fixes(df)   # rend (df, n_corrigés)
    df = bc.unify_amounts(df)
    df = bc.enrich(df, corrections=True)

    df["member_name"] = df["declarant_name"]
    df["direction"] = df["op"]
    # Timestamp de signal : l'information n'est exploitable qu'à partir du moment où elle est
    # RÉELLEMENT accessible. Tant que C1 n'est pas tranché, c'est le plus tardif des deux —
    # jamais `transaction_date`.
    fs = pd.to_datetime(df.get("first_seen_at"), errors="coerce")
    df["signal_date"] = pd.concat([dd, fs], axis=1).max(axis=1).dt.date
    for c in COLONNES:
        if c not in df.columns:
            df[c] = pd.NA
    return df[COLONNES]


def run(chamber="both", limit=None, dry_run=False):
    """Un passage complet. Retourne le DataFrame produit (vide si rien de nouveau)."""
    docs = nouveaux_documents(chamber, limit)
    if docs.empty:
        print("  aucun document nouveau — le corpus est à jour")
        return pd.DataFrame(columns=COLONNES)
    print(f"  {len(docs)} document(s) à traiter "
          f"({dict(docs['chamber'].value_counts())})")

    morceaux, scans, papier = [], [], []
    if chamber in ("both", "house"):
        h, scans = traiter_house(docs[docs["chamber"] == "house"])
        if len(h):
            morceaux.append(h)
    if chamber in ("both", "senate"):
        s, papier = traiter_senate(docs[docs["chamber"] == "senate"])
        if len(s):
            morceaux.append(s)

    if scans:
        print(f"  ⚠ {len(scans)} PTR House scannés : l'OCR exige d'abord la classification "
              f"(`python -m house.classify_scans`) — non traités ici, pas perdus (ils restent "
              f"nouveaux au prochain passage)")
    if papier:
        print(f"  ⚠ {len(papier)} dépôts Sénat papier — même raison")

    if not morceaux:
        print("  rien d'exploitable dans ces documents")
        return pd.DataFrame(columns=COLONNES)

    brut = pd.concat(morceaux, ignore_index=True)
    fs = dict(zip(docs["doc_id"].astype(str), docs["first_seen_at"]))
    brut["first_seen_at"] = brut["doc_id"].astype(str).map(fs)
    out = ligne_p31(brut)

    if not dry_run:
        LIVE_DIR.mkdir(parents=True, exist_ok=True)
        cible = LIVE_DIR / f"live_{datetime.now(timezone.utc).date().isoformat()}.csv"
        # Un second passage le même jour complète le fichier du jour sans écraser le premier.
        out.to_csv(cible, mode="a", header=not cible.exists(), index=False)
        print(f"→ {cible}")
    return out


def main():
    ap = argparse.ArgumentParser(description="Run en direct : les dépôts nouveaux → lignes de features.")
    ap.add_argument("--chamber", choices=["house", "senate", "both"], default="both")
    ap.add_argument("--limit", type=int, default=None, help="ne traiter que les N plus récents")
    ap.add_argument("--dry-run", action="store_true", help="montre sans écrire")
    args = ap.parse_args()

    print("Run en direct" + (" [DRY-RUN]" if args.dry_run else ""))
    out = run(args.chamber, args.limit, args.dry_run)
    if len(out):
        print(f"\n→ {len(out)} transaction(s) produite(s) au format de la table de référence")
        apercu = out.head(8)[["member_name", "chamber", "transaction_date", "disclosure_date",
                              "direction", "ticker_yahoo", "sector_gics"]]
        print(apercu.to_string(index=False))
    if args.dry_run:
        print("(dry-run : rien écrit)")


if __name__ == "__main__":
    main()
