"""Nettoyage backtest — produit les tables de recherche depuis les FINAL (100 % offline).

Quatre sorties dans data/clean/ :
  - transactions_brut_2014_2026.csv   : TOUT le corpus assemblé (dédup cross-année + fixes
    read-time), rien d'écarté — chaque ligne porte le verdict de l'entonnoir
    (exclusion_etape ∈ {A,B,C,D,E,F} ou vide, exclusion_motif) et tous les enrichissements ;
  - transactions_backtest_2014_2026.csv : la table CLEAN (entonnoir A→F + corrections) —
    la table que la recherche consomme ; depuis le 2026-08-12, elle est PROPRE au sens plein :
    E écarte les trades hors fenêtre 2013-2026, F les tickers sans série de prix exploitable
    (référentiel versionné data/reference/couverture_prix_*.csv) — les filtres que chaque
    notebook de recherche rejouait localement vivent désormais ici ;
  - transactions_gated_2014_2026.csv  : les transactions des scans manuscrits gated
    (cluster C/B), récupérées par une passe OCR une-fois (cache non régénérable
    data/house/ocr_gated_recovered.csv) — exportées pour que rien ne soit écarté en silence ;
  - commissions_membre_congres.csv    : annexe — texte complet des commissions et
    sous-commissions par élu × Congrès (normalisé hors des lignes de transaction).

La logique de l'entonnoir et des enrichissements vient du notebook
Nettoyage_Backtest_2014_2026.ipynb (2026-07-03, archivé — `_archive/` de la branche presentation) ;
les étapes sont recensées au §7 de RAPPORT_DONNEES.md (régénéré par `python -m common.quality`).
`corrections=False` rejoue le schéma v1 (36 colonnes, commissions inline) — la reproduction
octet pour octet de la table du 2026-07-04 a été prouvée avant les corrections des référentiels
(elle se rejoue en restaurant `ticker_renames.csv`/`ticker_sector_map.csv` d'époque depuis git) ;
`corrections=True` (défaut du pipeline) applique en plus les correctifs documentés dans
NOTE_DIFF_TABLE_CLEAN.md (branche presentation : renommages complétés, tickers faux-positifs,
carte corrigée, colonnes owner_n / member_name_canon / ticker_groupe / amount_open_bracket,
sous-commissions résolues).

Usage : python -m common.backtest_clean            (écrit les quatre tables + le résumé)
        python -m common.backtest_clean --v1       (mode reproduction, table clean seule)
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

try:
    from yaml import CSafeLoader as _YL
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _YL

from common.quality import load_final, _asset_bucket
from common.quiver_diagnosis import _quiver_untradeable
from common.schema import canonical_ticker

REPO = Path(__file__).resolve().parent.parent
REF = REPO / "data" / "reference"

NON_COTE = {"bond", "muni", "gov", "option", "autre"}
# Commissions « clés » : patterns LARGES (fiscalité + défense + renseignement + banque).
KEY_PATTERNS = ("Financial Services", "Committee on Finance", "Ways and Means",
                "Banking", "Armed Services", "Intelligence")

# Fusion des classes d'actions d'un même émetteur (clé émetteur pour la recherche —
# la même table que le nb 11/16 déclaraient localement).
FUSION_CLASSES = {"GOOGL": "GOOG", "BRK-A": "BRK-B", "FOXA": "FOX", "NWSA": "NWS"}

# Normalisation du champ owner (couverture 100 % vérifiée par assertion à l'export).
OWNER_N = {"Spouse": "conjoint", "SP": "conjoint", "spouse": "conjoint",
           "SELF": "élu", "Self": "élu", "self": "élu",
           "Joint": "joint", "JT": "joint", "joint": "joint", "Joint Tenancy": "joint",
           "Child": "enfant", "DC": "enfant", "dependent": "enfant", "Dependent": "enfant",
           "Dependent Child": "enfant"}

# Couverture prix : référentiel VERSIONNÉ et DATÉ (extrait du cache de la recherche par
# `python -m tools.couverture_prix`, 02_recherche_backtest — le pipeline reste hors-ligne).
# Étape F de l'entonnoir : un trade sur un ticker sans série de prix exploitable n'est pas
# backtestable — verdict en table brute, exclu de la clean. Les tickers ABSENTS du référentiel
# (postérieurs à son extraction) ne sont pas exclus : ré-extraire pour les couvrir.
COUVERTURE_PRIX = REF / "couverture_prix_v20260812.csv"
# Fenêtre de la table clean (étape E) : les trades exécutés avant 2013 (déclarés dans des
# dépôts 2014+) sortent de la clean — la fenêtre que toute la recherche applique.
FENETRE = (2013, 2026)

COLS = ["bioguide_id", "member_name", "party", "chamber", "state_district",
        "committee_membership", "committees_key_flag", "congress",
        "owner", "occurrence_index", "lot_size",
        "ticker", "ticker_yahoo", "flag_ticker", "is_delisted", "delist_type", "flag_price_caution",
        "asset_class", "asset_type", "is_broad_etf", "sector_gics", "etf_proxy",
        "direction", "amount_midpoint", "amount_range", "amount_range_repaired",
        "transaction_date", "disclosure_date", "lag_days", "flag_late_filing", "flag_very_late_filing",
        "doc_id", "provenance", "ticker_source", "natural_key_hash", "asset_description"]
# Colonnes ajoutées par les corrections (v2) — à la suite, pour ne pas déplacer les 36 de la v1.
COLS_V2 = ["owner_n", "member_name_canon", "ticker_groupe", "amount_open_bracket"]


# ───────────────────────── montants (convention unifiée) ─────────────────────────

def _mid_exact(a):
    nums = [int(x.replace(",", "")) for x in re.findall(r"\$([\d,]+)", str(a))]
    return (nums[0] + nums[1]) / 2 if len(nums) == 2 else None


def unify_amounts(df):
    """Plancher du palier ouvert « > $50M » + midpoint (lo+hi)/2 exact re-dérivé d'amount_range."""
    palier = df["amount_range"].astype(str).str.strip().eq("Over $50,000,000")
    df.loc[palier, "amount_midpoint"] = 50_000_000.0
    mid = df["amount_range"].map(_mid_exact)
    maj = mid.notna() & (df["amount_midpoint"] != mid) & ~palier
    df.loc[maj, "amount_midpoint"] = mid[maj]
    df["amount_open_bracket"] = palier  # la sentinelle devient une colonne (fin du np.isclose aval)
    return df


# ───────────────────────── entonnoir A→D (verdicts, sans rien jeter) ─────────────────────────

def funnel_verdicts(df):
    """Retourne (exclusion_etape, exclusion_motif) par ligne — l'ordre A→B→C→D, une seule cause."""
    fy = pd.to_numeric(df["file_year"], errors="coerce")
    ok_A = df["lag_days"].notna() & (df["lag_days"] >= 0) & (df["txn_year"] >= 2012) & (df["txn_year"] <= fy)
    mask_ticker = df["ticker"].map(lambda t: canonical_ticker(t)[0]) != ""
    mask_tradable = ~df["ticker"].map(_quiver_untradeable)
    fam = df["asset_type"].map(_asset_bucket)
    mask_famille = ~fam.isin(NON_COTE)
    ok_B = mask_ticker & mask_tradable & mask_famille
    ok_C = df["op"].isin(["buy", "sell"])
    ok_D = df["amount_midpoint"].notna()

    etape = pd.Series("", index=df.index, dtype="object")
    motif = pd.Series("", index=df.index, dtype="object")
    etape[~ok_A] = "A"
    motif[~ok_A] = "dates absentes ou incohérentes (divulgation < transaction, année implausible)"
    mB = ok_A & ~ok_B
    etape[mB] = "B"
    motif[mB & ~mask_ticker] = "ticker vide (aucun symbole → pas de prix)"
    motif[mB & mask_ticker & ~mask_tradable] = "ticker malformé ($, espace, fragment OCR)"
    motif[mB & mask_ticker & mask_tradable & ~mask_famille] = "option / obligation (famille non cotée)"
    mC = ok_A & ok_B & ~ok_C
    etape[mC] = "C"
    motif[mC] = "direction hors {achat, vente} (échange, autre)"
    mD = ok_A & ok_B & ok_C & ~ok_D
    etape[mD] = "D"
    motif[mD] = "montant absent"
    return etape, motif


# ───────────────────────── enrichissements point-in-time ─────────────────────────

def _party_spans():
    ppl = []
    for f in ("legislators-current.yaml", "legislators-historical.yaml"):
        ppl += yaml.load((REPO / "data" / "house" / "reference" / f).read_text(), Loader=_YL)
    spans_by_bio = {}
    for p in ppl:
        bio = (p.get("id") or {}).get("bioguide")
        if not bio:
            continue
        spans = []
        for t in (p.get("terms") or []):
            st, en = t.get("start"), t.get("end") or "2100-01-01"
            if not st:
                continue
            affs = t.get("party_affiliations")
            if affs:
                for a in affs:
                    spans.append((pd.Timestamp(a.get("start") or st),
                                  pd.Timestamp(a.get("end") or en), a.get("party")))
            else:
                spans.append((pd.Timestamp(st), pd.Timestamp(en), t.get("party")))
        if spans:
            spans_by_bio[bio] = sorted(spans)
    return spans_by_bio


def congress_of(d):
    # Un Congrès commence le 3 JANVIER des années impaires : les trades des 1-2 janvier d'une
    # année impaire appartiennent encore au Congrès sortant.
    if pd.isna(d):
        return None
    y = d.year
    start = y if y % 2 == 1 else y - 1
    if y % 2 == 1 and (d.month, d.day) < (1, 3):
        start -= 2
    return 113 + (start - 2013) // 2


def _committee_snapshots(resolve_subcommittees=False):
    """Par Congrès : bioguide → 'commission; commission…'. Avec resolve_subcommittees, les codes
    de sous-commissions (HSAS03…) sont résolus en « Parent — Sous-commission » (patch 9)."""
    snaps = {}
    for cg in range(113, 120):
        d = REF / "committees_snapshots" / str(cg)
        mem = yaml.load((d / "membership.yaml").read_text(), Loader=_YL)
        com = yaml.load((d / "committees.yaml").read_text(), Loader=_YL)
        code_to_name = {c["thomas_id"]: c["name"] for c in com if "thomas_id" in c}
        if resolve_subcommittees:
            for c in com:
                parent, pname = c.get("thomas_id"), c.get("name")
                for sub in (c.get("subcommittees") or []):
                    sid = sub.get("thomas_id")
                    if parent and sid:
                        code_to_name[parent + sid] = f"{pname} — {sub.get('name', sid)}"

        def _resolve(code_):
            if code_ in code_to_name:
                return code_to_name[code_]
            # repli : sous-commission absente du committees.yaml de ce Congrès, mais parent connu
            if resolve_subcommittees and len(code_) > 4 and code_[:4] in code_to_name:
                return f"{code_to_name[code_[:4]]} — sous-commission {code_[4:]}"
            return code_

        bio2c = defaultdict(set)
        for code_, members in mem.items():
            cname = _resolve(code_)
            for m in members:
                if m.get("bioguide"):
                    bio2c[m["bioguide"]].add(cname)
        snaps[cg] = {b: "; ".join(sorted(cs)) for b, cs in bio2c.items()}
    return snaps


def enrich(df, corrections=True):
    """Parti PIT, commissions PIT, ticker canonique + renames, carte secteur, flags, colonnes v2.
    Opérations ligne à ligne : identiques que l'on enrichisse le brut entier ou la clean seule."""
    renames = pd.read_csv(REF / "ticker_renames.csv")
    sector_map = pd.read_csv(REF / "ticker_sector_map.csv").set_index("ticker")

    # 1) parti point-in-time
    spans = _party_spans()

    def party_at(bio, d):
        s = spans.get(bio)
        if not s or pd.isna(d):
            return None
        for st, en, pty in s:
            if st <= d <= en:
                return pty
        before = [x for x in s if x[0] <= d]
        return (before[-1] if before else s[0])[2]

    df["party"] = [party_at(b, d) or old for b, d, old in zip(df["bioguide_id"], df["_td"], df["party"])]

    # 2) commissions point-in-time. En mode corrections, le TEXTE des commissions est normalisé
    #    dans la table annexe commissions_membre_congres.csv (jointure bioguide_id × congress) —
    #    l'inliner sur chaque ligne, avec les sous-commissions résolues, faisait passer les tables
    #    au-dessus de la limite GitHub (100 Mo). La ligne garde congress + committees_key_flag.
    snaps = _committee_snapshots(resolve_subcommittees=corrections)
    df["congress"] = pd.array([congress_of(d) for d in df["_td"]], dtype="Int64")
    _get = lambda b, cg: (snaps.get(cg) or {}).get(b) if pd.notna(cg) and cg in snaps else None
    _mem = [_get(b, cg) for b, cg in zip(df["bioguide_id"], df["congress"])]
    df["committees_key_flag"] = [any(p in m for p in KEY_PATTERNS) if isinstance(m, str) else pd.NA
                                 for m in _mem]
    if not corrections:
        df["committee_membership"] = _mem

    # 3) ticker canonique + renommages/délistages — `ticker` reste FIDÈLE à la déclaration
    canon = df["ticker"].map(canonical_ticker)
    df["ticker_yahoo"] = [c[0] for c in canon]
    df["flag_ticker"] = [c[1] for c in canon]
    ren = renames.set_index("ticker_ancien")
    map_new = ren.loc[ren["ticker_nouveau"].notna() & (ren["ticker_nouveau"] != ""), "ticker_nouveau"]
    df["ticker_yahoo"] = df["ticker_yahoo"].map(lambda t: map_new.get(t, t))
    df["delist_type"] = df["ticker_yahoo"].map(ren["type"]).where(
        df["ticker_yahoo"].isin(ren.index[ren["ticker_nouveau"].isna() | (ren["ticker_nouveau"] == "")]))
    caution = set(ren.index[(ren.get("historique_valide") == "post_fusion_seulement")]) | \
        set(ren.index[ren["type"] == "recyclage_attention"])
    orig_canon = pd.Series([c[0] for c in canon], index=df.index)
    df["flag_price_caution"] = orig_canon.isin(caution) | df["ticker_yahoo"].isin(caution)
    df["is_delisted"] = df["delist_type"].notna()

    # 4) classe d'actif / secteur — carte transverse ; jamais de trou créé
    key = orig_canon
    df["asset_class"] = key.map(sector_map["asset_class"]).fillna("unknown")
    sec_new = key.map(sector_map["sector_gics"])
    etf_new = key.map(sector_map["etf_proxy"])
    known = key.isin(sector_map.index)
    df["sector_gics"] = sec_new.where(known & sec_new.notna() & (sec_new != ""), df["sector_gics"])
    df.loc[known & df["asset_class"].isin(["etf_broad", "etf_sector"]), "sector_gics"] = pd.NA
    df["etf_proxy"] = etf_new.where(known & etf_new.notna() & (etf_new != ""), df["etf_proxy"])
    df["is_broad_etf"] = df["asset_class"] == "etf_broad"

    # 5) flags de traçabilité (lot_size est calculé par table exportée, pas ici)
    df["flag_late_filing"] = df["lag_days"] > 45
    df["flag_very_late_filing"] = df["lag_days"] > 365

    if corrections:
        df["owner_n"] = df["owner"].map(OWNER_N).fillna("autre/inconnu")
        name_canon = df.groupby("bioguide_id")["declarant_name"].transform(lambda s: s.mode().iat[0])
        df["member_name_canon"] = name_canon
        df["ticker_groupe"] = df["ticker_yahoo"].map(lambda t: FUSION_CLASSES.get(t, t))
    return df


# ───────────────────────── corrections v2 : tickers faux-positifs ─────────────────────────

def apply_ticker_false_positive_fixes(df):
    """Corrige, AVANT l'entonnoir, les tickers extraits à tort d'une parenthèse descriptive
    (« (IRA) », « - ADR », suffixe de classe « CL-A »…). Table déclarative versionnée :
    data/reference/ticker_false_positives.csv (motif de description → ticker corrigé ou vide).
    Le figé sur disque n'est jamais muté — correction read-time, comme les fixes de schema.py."""
    p = REF / "ticker_false_positives.csv"
    if not p.exists():
        return df, 0
    fixes = pd.read_csv(p).fillna("")
    n = 0
    desc_lc = df["asset_description"].astype(str).str.lower()
    for _, r in fixes.iterrows():
        m = (df["ticker"].astype(str) == r["ticker_errone"]) & desc_lc.str.contains(r["motif_description"].lower(), regex=False)
        if not m.any():
            continue
        df.loc[m, "ticker"] = r["ticker_corrige"] if r["ticker_corrige"] else np.nan
        if r["ticker_corrige"]:
            df.loc[m, "ticker_source"] = "false_positive_fixed"
        n += int(m.sum())
    return df, n


# ───────────────────────── la table gated (rien d'écarté en silence) ─────────────────────────

def build_gated():
    """Les transactions des scans manuscrits gated (politique house/ocr.py), récupérées par une
    passe OCR une-fois. Cache : data/house/ocr_gated_recovered.csv (non régénérable sans re-payer
    l'OCR — même statut que les autres caches Vision versionnés)."""
    p = REPO / "data" / "house" / "ocr_gated_recovered.csv"
    if not p.exists():
        return None
    g = pd.read_csv(p, parse_dates=["tau", "delta"])
    out = pd.DataFrame({
        "member_name": g["member_name"], "party": g["party"], "owner": g.get("owner"),
        "ticker": g["tk"], "direction": g["op"], "amount_midpoint": g["A"],
        "amount_code": g.get("amount_code"),
        "transaction_date": g["tau"], "disclosure_date": g["delta"], "doc_id": g["doc_id"],
        "gating_cluster": g["cluster"],
    })
    out["gating_reason"] = out["gating_cluster"].map(
        {"C_manuscrit": "scan manuscrit — politique de gating house/ocr.py (Quiver ne corrobore que 12,9 %)",
         "B_tape_tourne": "scan tapé/tourné hors périmètre OCR de production"}).fillna("gated")
    out["lag_days"] = (out["disclosure_date"] - out["transaction_date"]).dt.days
    return out


# ───────────────────────── construction et export ─────────────────────────

def commissions_table():
    """La table annexe : une ligne par (congress, bioguide) des snapshots 113-119, avec le texte
    complet des commissions ET sous-commissions résolues. Jointure : bioguide_id × congress."""
    snaps = _committee_snapshots(resolve_subcommittees=True)
    rows = [{"congress": cg, "bioguide_id": b, "committee_membership": m}
            for cg, d in snaps.items() for b, m in sorted(d.items())]
    return pd.DataFrame(rows)


def build_tables(corrections=True, verbose=True):
    """Retourne (brut, clean, gated, funnel) — brut = tout le corpus avec verdicts d'entonnoir."""
    log = print if verbose else (lambda *a, **k: None)
    df = load_final(REPO)
    n0 = len(df)
    log(f"{n0:,} transactions uniques chargées (load_final)")

    n_fp = 0
    if corrections:
        df, n_fp = apply_ticker_false_positive_fixes(df)
        log(f"tickers faux-positifs corrigés (read-time) : {n_fp} lignes")

    df = unify_amounts(df)
    etape, motif = funnel_verdicts(df)
    df["exclusion_etape"] = etape
    df["exclusion_motif"] = motif
    df = enrich(df, corrections=corrections)

    if corrections:
        # étapes E (fenêtre) et F (couverture prix) — APRÈS enrich : F se juge sur ticker_yahoo.
        # « La table propre, c'est : tu épures les tickers qui ne fonctionnent pas, et les dates
        # qui ne fonctionnent pas non plus. » Verdict en brute, exclusion de la clean.
        libre = df["exclusion_etape"] == ""
        hors_fenetre = libre & ~df["txn_year"].between(*FENETRE)
        df.loc[hors_fenetre, "exclusion_etape"] = "E"
        df.loc[hors_fenetre, "exclusion_motif"] = \
            f"hors fenêtre {FENETRE[0]}-{FENETRE[1]} (transaction antérieure, déclarée dans un dépôt ultérieur)"
        couv = pd.read_csv(COUVERTURE_PRIX).set_index("ticker_yahoo")["statut_prix"]
        statut = df["ticker_yahoo"].map(couv)
        libre = df["exclusion_etape"] == ""
        sans_px = libre & statut.eq("sans_prix")
        corrompu = libre & statut.eq("prix_corrompu")
        df.loc[sans_px, "exclusion_etape"] = "F"
        df.loc[sans_px, "exclusion_motif"] = "aucune série de prix exploitable (référentiel couverture_prix)"
        df.loc[corrompu, "exclusion_etape"] = "F"
        df.loc[corrompu, "exclusion_motif"] = "série de prix corrompue (< 0,10 $ ou saut > 300 %/j)"
        n_inconnus = int((libre & statut.isna()).sum())
        if n_inconnus:
            log(f"⚠ {n_inconnus:,} lignes sur des tickers hors référentiel couverture_prix — gardées "
                f"(ré-extraire tools.couverture_prix pour les statuer)")

    funnel = (df["exclusion_etape"].replace("", "∅ (gardée)").value_counts().sort_index())
    log("entonnoir :", dict(funnel))

    keep = df["exclusion_etape"] == ""
    clean = df[keep].copy()
    clean["lot_size"] = clean.groupby("natural_key_hash")["natural_key_hash"].transform("size")
    df["lot_size"] = df.groupby("natural_key_hash")["natural_key_hash"].transform("size")

    if corrections:
        cols = [c for c in COLS if c != "committee_membership"] + COLS_V2
    else:
        cols = COLS
        clean = clean.drop(columns=["amount_open_bracket"], errors="ignore")

    def _export(d, extra=()):
        e = d.rename(columns={"declarant_name": "member_name", "op": "direction"})
        return e.reindex(columns=list(cols) + list(extra))

    clean_x = _export(clean)
    assert clean_x["bioguide_id"].notna().all() and (clean_x["bioguide_id"] != "").all(), "bioguide manquant"
    assert clean_x["ticker"].notna().all(), "ticker manquant"
    assert clean_x["amount_midpoint"].notna().all(), "montant manquant"
    assert clean_x["direction"].isin(["buy", "sell"]).all(), "direction invalide"
    assert (clean_x["lag_days"] >= 0).all(), "chronologie incohérente"
    assert clean_x["natural_key_hash"].notna().all(), "hash manquant"

    brut_x = _export(df, extra=("exclusion_etape", "exclusion_motif")) if corrections else None
    gated = build_gated() if corrections else None
    return brut_x, clean_x, gated, funnel


def write_tables(corrections=True):
    out_dir = REPO / "data" / "clean"
    out_dir.mkdir(parents=True, exist_ok=True)
    brut, clean, gated, funnel = build_tables(corrections=corrections)
    clean.to_csv(out_dir / "transactions_backtest_2014_2026.csv", index=False)
    print(f"clean : {len(clean):,} × {clean.shape[1]} → transactions_backtest_2014_2026.csv")
    if brut is not None:
        brut.to_csv(out_dir / "transactions_brut_2014_2026.csv", index=False)
        print(f"brut  : {len(brut):,} × {brut.shape[1]} → transactions_brut_2014_2026.csv")
    if gated is not None:
        gated.to_csv(out_dir / "transactions_gated_2014_2026.csv", index=False)
        print(f"gated : {len(gated):,} × {gated.shape[1]} → transactions_gated_2014_2026.csv")
    if corrections:
        com = commissions_table()
        com.to_csv(out_dir / "commissions_membre_congres.csv", index=False)
        print(f"commissions : {len(com):,} × {com.shape[1]} → commissions_membre_congres.csv "
              f"(jointure bioguide_id × congress)")
    return brut, clean, gated


if __name__ == "__main__":
    write_tables(corrections="--v1" not in sys.argv)
