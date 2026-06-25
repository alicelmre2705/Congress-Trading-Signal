#!/usr/bin/env python
"""Finalisation + validation du pipeline Sénat Q1 2025 (eFD direct), au standard House Q1.

Ce script reprend la table électronique déjà extraite (`senate_2025q1_transactions.csv`,
280 transactions issues de 37 PTR eFD) et l'amène au niveau de la version figée House Q1 :

1. Identité (bioguide) fiabilisée — nettoyage suffixes/initiales/virgules + table de surnoms +
   désambiguïsation par chambre (sénat) puis par titulaire en exercice (legislators-current).
   Récupère les 4 sénateurs non rattachés (McCormick M001243, McConnell M000355, Banks B001299,
   Hagerty H000601).
2. Enrichissement ticker — quand la colonne Ticker eFD est vide ('--'), le symbole est souvent
   dans l'Asset Name (« LLY », « CRWD PUT »). Récupération déterministe (aucun Quiver injecté).
3. Validation Quiver — 1 appel bulk, filtré Chamber=Senate, fenêtre de *divulgation* Q1 2025,
   comparaison par sénateur (compte) + contrôle transaction-à-transaction. Quiver = vérification
   externe uniquement, jamais réinjecté dans la table.
4. Restructuration au format House : tables numérotées 01→07 + qa_flags, + Excel multi-onglets.

Pas d'accès eFD ici (aucune évasion) : on travaille sur la sortie déjà extraite + les rapports
HTML déjà cachés. Seul appel réseau : Quiver (vérification).
"""
import os
import re
import json
import hashlib
import unicodedata
from collections import defaultdict, Counter
from pathlib import Path

import pandas as pd
import requests
import yaml

HERE = Path(__file__).resolve().parent
OUT = HERE / "data_v1_senate"
TAB = OUT / "tables"
REF = OUT / "reference"   # référentiel législateurs vendu localement (dossier 100 % autonome)
TAB.mkdir(parents=True, exist_ok=True)

WIN_START = pd.Timestamp("2025-01-01")
WIN_END = pd.Timestamp("2025-03-31")
QUIVER_URL = "https://api.quiverquant.com/beta/bulk/congresstrading"
KEY_COMMITTEES = ("Finance", "Armed Services", "Intelligence", "Banking")

SCHEMA = ["bioguide_id", "declarant_name", "chamber", "party", "state_district",
          "committee_membership", "committees_key_flag", "transaction_date", "disclosure_date",
          "ticker", "asset_description", "asset_type", "operation_type", "amount_range",
          "amount_midpoint", "amount_split_flag", "owner", "doc_id", "source_url",
          "natural_key_hash", "provenance", "ticker_source", "occurrence_index"]


# --------------------------------------------------------------------------- identité
def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))


def norm(s):
    s = strip_accents(s or "").lower()
    s = re.sub(r"[^a-z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


SUFFIX = {"jr", "sr", "ii", "iii", "iv", "v"}


def split_name(declarant):
    """« First [Middle…] Last[, Suffix] » → (last, first, [middle_tokens])."""
    s = (declarant or "").split(",")[0]
    toks = [t for t in re.split(r"\s+", s.strip()) if t and norm(t) not in SUFFIX]
    if not toks:
        return "", "", []
    return toks[-1], toks[0], [norm(t) for t in toks[:-1]]


def load_reference():
    cur = yaml.safe_load(open(REF / "legislators-current.yaml"))
    his = yaml.safe_load(open(REF / "legislators-historical.yaml"))
    current_bios = {p["id"]["bioguide"] for p in cur if p.get("id", {}).get("bioguide")}

    ref, name_exact, name_by_last = {}, {}, defaultdict(list)
    for p in cur + his:
        bio = p.get("id", {}).get("bioguide")
        if not bio:
            continue
        nm = p.get("name", {})
        last, first, nick = nm.get("last", ""), nm.get("first", ""), nm.get("nickname", "")
        lt = (p.get("terms") or [{}])[-1]
        chamber = "senate" if lt.get("type") == "sen" else "house"
        ref.setdefault(bio, {"full": nm.get("official_full") or f"{first} {last}".strip(),
                             "party": lt.get("party"), "state": lt.get("state"),
                             "chamber": chamber, "first": first, "nick": nick})
        name_exact.setdefault((norm(last), norm(first)), bio)
        if nick:
            name_exact.setdefault((norm(last), norm(nick)), bio)
        name_by_last[norm(last)].append(bio)

    # commissions (flag clé)
    bio_to_committees, key_flag = defaultdict(set), {}
    try:
        committees = yaml.safe_load(open(REF / "committees-current.yaml"))
        membership = yaml.safe_load(open(REF / "committee-membership-current.yaml"))
        code_to_name = {c["thomas_id"]: c["name"] for c in committees if "thomas_id" in c}
        for code, members in membership.items():
            cname = code_to_name.get(code, code)
            for mem in members:
                if mem.get("bioguide"):
                    bio_to_committees[mem["bioguide"]].add(cname)
        key_flag = {b: any(any(k in cn for k in KEY_COMMITTEES) for cn in cs)
                    for b, cs in bio_to_committees.items()}
    except Exception as e:
        print("  commissions non chargées (flag=False) :", e)

    return ref, name_exact, name_by_last, current_bios, bio_to_committees, key_flag


def make_matcher(ref, name_exact, name_by_last, current_bios):
    def match(declarant):
        last, first, middles = split_name(declarant)
        nl, nf = norm(last), norm(first)
        if (nl, nf) in name_exact:                      # 1) (last, first/nick) exact
            return name_exact[(nl, nf)]
        cands = name_by_last.get(nl, [])
        sen = [b for b in cands if ref[b]["chamber"] == "senate"]
        pool = sen if sen else cands                    # 2) on privilégie la chambre Sénat
        if len(pool) == 1:
            return pool[0]
        cur_pool = [b for b in pool if b in current_bios]   # 3) titulaire en exercice
        if len(cur_pool) == 1:
            return cur_pool[0]
        base = cur_pool or pool                         # 4) désambiguïsation prénom/initiale
        toks = set([nf] + middles)
        fp = [b for b in base
              if any(cf and t and (cf.startswith(t[:3]) or t.startswith(cf[:3]))
                     for cf in {norm(ref[b]["first"]), norm(ref[b]["nick"])} for t in toks)]
        return fp[0] if len(fp) == 1 else None
    return match


# --------------------------------------------------------------------------- ticker
TICK_RE = re.compile(r"^([A-Z]{1,5})(?:\.[A-Z])?(?:\s+(?:PUT|CALL))?$")


def recover_ticker(desc):
    """Récupère le symbole quand l'Asset Name *est* un ticker (« LLY », « CRWD PUT »)."""
    if not isinstance(desc, str):
        return None
    m = TICK_RE.match(desc.strip())
    return m.group(1) if m else None


# --------------------------------------------------------------------------- main
def main():
    print("=== Finalisation Sénat Q1 2025 ===")
    ref, name_exact, name_by_last, current_bios, bio_to_committees, key_flag = load_reference()
    match = make_matcher(ref, name_exact, name_by_last, current_bios)
    print(f"Référentiel : {len(ref)} législateurs ({sum(v['chamber']=='senate' for v in ref.values())} sénateurs)")

    df = pd.read_csv(OUT / "senate_2025q1_transactions.csv", dtype=str)
    n0 = len(df)

    # 1) identité ----------------------------------------------------------------
    df["bioguide_id"] = df["declarant_name"].map(match)
    unmatched = sorted(df[df["bioguide_id"].isna()]["declarant_name"].dropna().unique())
    df["party"] = df["bioguide_id"].map(lambda b: ref.get(b, {}).get("party"))
    df["state_district"] = df["bioguide_id"].map(lambda b: ref.get(b, {}).get("state"))
    df["committee_membership"] = df["bioguide_id"].map(
        lambda b: "; ".join(sorted(bio_to_committees.get(b, []))) if b else "")
    df["committees_key_flag"] = df["bioguide_id"].map(lambda b: bool(key_flag.get(b, False)))
    matched = df["bioguide_id"].notna().sum()
    print(f"Identité : {matched}/{n0} rattachées ({100*matched/n0:.0f}%) | non rattachés : {unmatched}")

    # 2) enrichissement ticker ---------------------------------------------------
    raw = df["ticker"].astype(str).str.strip().str.upper()
    has_tick = df["ticker"].notna() & ~raw.isin(["--", "NAN", "NONE", ""])
    df["ticker"] = df["ticker"].where(has_tick, df["asset_description"].map(recover_ticker))
    df["ticker"] = df["ticker"].astype("string").str.upper()
    # provenance déterministe & idempotente : 'asset_name' quand l'Asset Name EST le ticker
    rec_final = df["asset_description"].map(recover_ticker)
    df["ticker_source"] = "none"
    df.loc[df["ticker"].notna(), "ticker_source"] = "explicit"
    df.loc[df["ticker"].notna() & (rec_final == df["ticker"]), "ticker_source"] = "asset_name"
    after = int(df["ticker"].notna().sum())
    print(f"Ticker : {after}/{n0} ({100*after/n0:.0f}%) | sources={df['ticker_source'].value_counts().to_dict()}")

    # natural_key_hash : recalcul (inchangé en pratique — n'inclut pas le ticker)
    def nk(r):
        raw = "|".join(str(r[c]) for c in ["chamber", "declarant_name", "transaction_date",
                                           "asset_description", "operation_type", "amount_range", "owner"])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    df["natural_key_hash"] = df.apply(nk, axis=1)
    df["amount_midpoint"] = pd.to_numeric(df["amount_midpoint"], errors="coerce")
    # parité schéma House : l'eFD fournit une fourchette unique par ligne (jamais éclatée sur
    # plusieurs lignes comme les PDF House) → amount_split_flag toujours False côté Sénat.
    df["amount_split_flag"] = False
    # occurrence_index : préservé depuis l'extraction (lots répétés intra-rapport, ex. Moody
    # SYM/NCLH/SMCI CALL vendus 2× le même jour). Dédup non destructrice. 0 par défaut.
    if "occurrence_index" not in df.columns:
        df["occurrence_index"] = 0
    df["occurrence_index"] = pd.to_numeric(df["occurrence_index"], errors="coerce").fillna(0).astype(int)
    df = df.reindex(columns=SCHEMA)

    # écriture table ÉLECTRONIQUE (fichier de travail idempotent + table numérotée 06)
    df.to_csv(OUT / "senate_2025q1_transactions.csv", index=False)
    df.to_csv(TAB / "06_senate_2025q1_transactions.csv", index=False)
    print(f"→ table électronique : {len(df)} lignes, {df['declarant_name'].nunique()} sénateurs")

    # 2b) fusion OCR papier (si senate_ocr.py a produit 06b) — table FINALE digital + OCR
    n_elec = len(df)
    ocr_path = TAB / "06b_senate_2025q1_ocr_transactions.csv"
    if ocr_path.exists():
        ocr = pd.read_csv(ocr_path, dtype=str)
        ocr["amount_midpoint"] = pd.to_numeric(ocr["amount_midpoint"], errors="coerce")
        ocr["amount_split_flag"] = ocr["amount_split_flag"].map(lambda x: str(x).strip().lower() == "true")
        ocr["committees_key_flag"] = ocr["committees_key_flag"].map(lambda x: str(x).strip().lower() == "true")
        ocr["occurrence_index"] = pd.to_numeric(ocr["occurrence_index"], errors="coerce").fillna(0).astype(int)
        df = pd.concat([df, ocr.reindex(columns=SCHEMA)], ignore_index=True)
        # dédup inter-sources (filet) sur (natural_key_hash, occurrence_index)
        df = df.drop_duplicates(["natural_key_hash", "occurrence_index"], keep="first").reset_index(drop=True)
        print(f"→ fusion digital+OCR : {len(df)} lignes ({n_elec} électro + {len(df) - n_elec} OCR papier)")
    df.to_csv(OUT / "senate_2025q1_FINAL.csv", index=False)
    df.to_csv(TAB / "06_senate_2025q1_FINAL.csv", index=False)

    # 3) validation Quiver -------------------------------------------------------
    token = os.environ.get("QUIVER_API_KEY")
    envf = HERE / ".env"   # secrets locaux au dossier (autonome) — voir .env.example
    if not token and envf.exists():
        for line in open(envf):
            if line.startswith("QUIVER_API_KEY="):
                token = line.split("=", 1)[1].strip() or None
    cmp_df = None
    if not token:
        print("QUIVER_API_KEY absent → validation sautée (table inchangée).")
    else:
        print("Quiver : appel bulk congresstrading…")
        q = pd.DataFrame(requests.get(QUIVER_URL, headers={"Authorization": f"Bearer {token}"},
                                      timeout=180).json())
        q["Filed"] = pd.to_datetime(q["Filed"], errors="coerce")
        q["Traded"] = pd.to_datetime(q["Traded"], errors="coerce")
        # NB : filtrer sur l'égalité exacte — « repreSENtatives » contient « sen » !
        sen = q[q["Chamber"].astype(str).str.strip().str.lower() == "senate"].copy()
        keep = [c for c in ["BioGuideID", "Name", "Ticker", "Transaction", "Traded", "Filed",
                            "Trade_Size_USD", "Party", "State"] if c in sen.columns]
        sen[keep].to_csv(TAB / "_quiver_senate_cache.csv", index=False)
        print(f"  cache Quiver Sénat : {len(sen)} lignes → tables/_quiver_senate_cache.csv")

        qwin = sen[(sen["Filed"] >= WIN_START) & (sen["Filed"] <= WIN_END)]
        nous = df.groupby("bioguide_id").size()
        quiv = qwin.groupby("BioGuideID").size()
        bios = sorted(set(df["bioguide_id"].dropna()) | set(qwin["BioGuideID"]),
                      key=lambda b: -int(nous.get(b, 0)))
        rows = []
        for b in bios:
            n = int(nous.get(b, 0))
            qv = int(quiv.get(b, 0))
            name = (df[df["bioguide_id"] == b]["declarant_name"].iloc[0] if n
                    else qwin[qwin["BioGuideID"] == b]["Name"].iloc[0])
            if n == 0:
                verdict = "quiver_seul"
            elif n == qv:
                verdict = "concordant"
            elif qv == 0:
                verdict = "quiver_sans_donnee"
            elif n > qv:
                verdict = "nous_plus"
            else:
                verdict = "quiver_plus_a_verifier"
            rows.append({"bioguide_id": b, "name": name, "nous": n, "quiver": qv,
                         "delta": n - qv, "verdict": verdict})
        cmp_df = pd.DataFrame(rows)
        cmp_df.to_csv(TAB / "07_quiver_comparison.csv", index=False)
        print("  comparaison par sénateur → tables/07_quiver_comparison.csv")
        print(cmp_df.to_string(index=False))
        print(f"  TOTAL nous={cmp_df.nous.sum()} quiver={cmp_df.quiver.sum()} "
              f"delta={cmp_df.delta.sum()} | verdicts={dict(Counter(cmp_df.verdict))}")

        # contrôle transaction-à-transaction : Quiver a-t-il des trades (ticker,date) qu'on n'a pas ?
        def kset(d, bcol, tcol, dcol):
            s = set()
            for _, r in d.iterrows():
                t = str(r[tcol]).upper().strip()
                if t in ("", "NAN", "NONE", "--"):
                    continue
                dd = pd.to_datetime(r[dcol], errors="coerce")
                if pd.isna(dd):
                    continue
                s.add((r[bcol], t, dd.date()))
            return s
        ours_k = kset(df, "bioguide_id", "ticker", "transaction_date")
        qwin_our = qwin[qwin["BioGuideID"].isin(set(df["bioguide_id"].dropna()))]
        gaps = sorted(kset(qwin_our, "BioGuideID", "Ticker", "Traded") - ours_k)
        pd.DataFrame(gaps, columns=["bioguide_id", "ticker", "traded_date"]).to_csv(
            TAB / "07b_quiver_ticker_gaps.csv", index=False)
        print(f"  écarts ticker-niveau (Quiver a / nous non) : {len(gaps)} "
              f"→ tables/07b_quiver_ticker_gaps.csv")

    # 4) tables annexes ----------------------------------------------------------
    # 01 référentiel complet
    ref_uni = pd.DataFrame([{"bioguide_id": b, "declarant_name": v["full"], "party": v["party"],
                             "chamber": v["chamber"], "state": v["state"]} for b, v in ref.items()])
    ref_uni.to_csv(TAB / "01_ref_universe.csv", index=False)
    # 02 sénateurs en commissions clés
    sen_key = [{"bioguide_id": b, "declarant_name": ref[b]["full"], "state": ref[b]["state"],
                "committees": "; ".join(sorted(bio_to_committees.get(b, [])))}
               for b, v in ref.items()
               if v["chamber"] == "senate" and key_flag.get(b)]
    pd.DataFrame(sen_key).to_csv(TAB / "02_ref_senate_key.csv", index=False)
    # 03 index PTR — kind dérivé de la provenance (électronique / papier OCRisé / backlog restant)
    perdoc = (df.groupby("doc_id").agg(declarant_name=("declarant_name", "first"),
                                       disclosure_date=("disclosure_date", "first"),
                                       source_url=("source_url", "first"),
                                       n_txns=("doc_id", "size"),
                                       provenance=("provenance", "first")).reset_index())
    perdoc["kind"] = perdoc["provenance"].map(lambda p: "paper_ocr" if "ocr" in str(p) else "ptr")
    have = set(perdoc["doc_id"])
    backlog = pd.read_csv(OUT / "backlog.csv") if (OUT / "backlog.csv").exists() else pd.DataFrame()
    paper_rows = [{"doc_id": r["uuid"], "declarant_name": None, "disclosure_date": None,
                   "source_url": r["url"], "n_txns": 0, "kind": "paper"}
                  for _, r in backlog.iterrows() if r["uuid"] not in have]
    cols_idx = ["doc_id", "declarant_name", "disclosure_date", "source_url", "n_txns", "kind"]
    ptr_index = pd.concat([perdoc[cols_idx], pd.DataFrame(paper_rows, columns=cols_idx)],
                          ignore_index=True)
    ptr_index.to_csv(TAB / "03_ptr_index.csv", index=False)
    # 04 manifest
    manifest = ptr_index[["doc_id", "kind", "n_txns"]].copy()
    manifest["statut"] = manifest["kind"].map({"ptr": "electronique_parsé", "paper_ocr": "ocr_parsé",
                                               "paper": "backlog_ocr"})
    manifest.to_csv(TAB / "04_report_manifest.csv", index=False)
    n_elec_docs = int((perdoc["kind"] == "ptr").sum())
    n_ocr_docs = int((perdoc["kind"] == "paper_ocr").sum())
    # 05 échecs de parsing (aucun électronique en échec)
    pd.DataFrame(columns=["doc_id", "raison"]).to_csv(TAB / "05_parse_failures.csv", index=False)

    # 06c QA flags : anomalies réelles (champ obligatoire vide)
    qa = []
    for _, r in df.iterrows():
        probs = [c for c in ["transaction_date", "amount_range", "owner", "operation_type",
                             "asset_description"] if not str(r[c]).strip() or str(r[c]) == "nan"]
        if probs:
            qa.append({"doc_id": r["doc_id"], "declarant_name": r["declarant_name"],
                       "asset_description": r["asset_description"], "flags": ",".join(probs)})
    pd.DataFrame(qa, columns=["doc_id", "declarant_name", "asset_description", "flags"]).to_csv(
        TAB / "06c_qa_flags.csv", index=False)
    print(f"QA flags : {len(qa)}  |  PTR index : {len(ptr_index)} "
          f"({n_elec_docs} élec + {n_ocr_docs} papier OCR + {len(paper_rows)} backlog)")

    # 5) Excel multi-onglets -----------------------------------------------------
    write_excel(df, cmp_df, qa, ptr_index, sen_key)
    print("→ senate_2025q1_FINAL.xlsx")
    return df, cmp_df


def write_excel(df, cmp_df, qa, ptr_index, sen_key):
    path = TAB / "senate_2025q1_FINAL.xlsx"
    n_elec = int((df["provenance"] == "senate-efd-electronic").sum())
    n_ocr = int((df["provenance"] == "senate-efd-ocr").sum())
    lisez = pd.DataFrame({"Sénat — PTR Q1 2025": [
        "Transactions boursières déclarées par les sénateurs (eFD direct), 1er trim. 2025.",
        f"{len(df)} transactions ({n_elec} électroniques + {n_ocr} OCR papier) · "
        f"{df['declarant_name'].nunique()} sénateurs · {len(ptr_index)} PTR.",
        "Rapports papier traités par OCR (Claude Vision) — provenance=senate-efd-ocr.",
        "Quiver = vérification externe seulement (jamais réinjecté). Voir onglet validation_quiver.",
        "Onglet transactions = table de référence. Colonnes : voir README.md.",
    ]})
    synth = (df.assign(midp=pd.to_numeric(df["amount_midpoint"], errors="coerce"))
             .groupby(["bioguide_id", "declarant_name", "party", "state_district"], dropna=False)
             .agg(n_txns=("doc_id", "size"),
                  n_achats=("operation_type", lambda s: (s == "Purchase").sum()),
                  n_ventes=("operation_type", lambda s: s.str.startswith("Sale").sum()),
                  tickers=("ticker", lambda s: s.dropna().nunique()),
                  valeur_estimee=("midp", "sum"))
             .reset_index().sort_values("n_txns", ascending=False))
    with pd.ExcelWriter(path, engine="openpyxl") as xl:
        lisez.to_excel(xl, sheet_name="LISEZMOI", index=False)
        df.to_excel(xl, sheet_name="transactions", index=False)
        synth.to_excel(xl, sheet_name="synthese_membres", index=False)
        (cmp_df if cmp_df is not None else pd.DataFrame({"info": ["validation non exécutée"]})
         ).to_excel(xl, sheet_name="validation_quiver", index=False)
        (pd.DataFrame(qa) if qa else pd.DataFrame({"info": ["aucune anomalie"]})
         ).to_excel(xl, sheet_name="qa_flags", index=False)
        ptr_index.to_excel(xl, sheet_name="ptr_index", index=False)


if __name__ == "__main__":
    main()
