"""Diagnostic Quiver « qui a raison ? » — recompute OFFLINE, lecture seule, jamais réinjecté.

Le §6 de RAPPORT_QUALITE.md confronte nos trades à Quiver par **strictesse croissante** : inclusion
date-AGNOSTIQUE (`ticker_inclusion`, §6.2 — a-t-on le trade), réconciliation date-ANCRÉE 1-à-1
(`reconcile_dates`, §6.3 — le même trade à la même date, apparié par dépôt), puis **verdicts
actionnables** (ci-dessous, §6.5). Tout est recalculé depuis les tables FINAL + le cache Quiver
(offline, prouvé identique aux 07c/07g/07h figés). Chaque transaction reçoit un verdict :

  côté NOUS (chaque transaction FINAL confrontée à Quiver) :
    CONCORDANT          présent des deux côtés, même date           → rien à corriger
    ECART_DATE          Quiver a le trade (bio×ticker×sens), date ≠ → OCR / amendement
    ECART_TICKER        Quiver a bio×date×sens, ticker ≠/manquant   → NOTRE erreur (corrigible) ;
                        inclut une ACTION (asset_type=Stock) sans ticker que Quiver confirme ce jour-là
                        (ticker récupérable — N'EST PAS du non-coté, donc pas STRUCTUREL).
    STRUCTUREL          notre trade NON COTÉ (muni, obligation…)    → hors périmètre Quiver
    ON_EST_PLUS_COMPLET notre action absente de Quiver              → on est plus complet

  côté QUIVER (chaque trade Quiver qu'on n'a pas — `only_quiver`) :
    ECART_DATE          on a bio×ticker×sens à une autre date       → OCR / amendement
    ECART_TICKER        on a bio×date×sens, ticker ≠                → NOTRE erreur (corrigible)
    MANQUANT_PAPIER     déposant qu'on OCR, cette ligne ratée       → OCR incomplet (corrigible)
    NON_COTE            « ticker » Quiver = CUSIP/préf./fragment OCR → hors périmètre Quiver-actions
    NOTRE_MANQUE        dépôt coté qu'on n'a PAS DU TOUT            → vrai trou (corrigible)

Le corpus FINAL est dédupliqué cross-année (clé naturelle + occurrence_index, keep-first) AVANT la
classification — une re-divulgation tardive (même trade re-déposé une autre année) n'est comptée qu'une
fois (Sénat : 8 841 → 8 245). Sans ça la copie tardive tombait à tort en ON_EST_PLUS_COMPLET.

Sorties : un dict de tables agrégées (consommé par common.quality, §6) + des annexes actionnables
sous `docs/quiver_validation/` (hors golden). Aucun appel API ; tout est offline.

Réutilise les briques de prod : `house.quiver.{reconcile,norm_ticker,norm_sense,low_bound}` (identiques
au Sénat) et `common.quiver_scopes.reconcile_scopes`. La clé d'appariement et la fenêtre Quiver sont
celles de `house/ocr.py` et `senate/fusion.py` (filed-year), pour reproduire les chiffres figés.
"""
from pathlib import Path

import pandas as pd

from house import quiver as hq            # norm_ticker/norm_sense/low_bound/reconcile (source unique)
from senate import quiver as sq           # reconcile (clés common_senators / ticker_per_sen)
from common.quiver_scopes import reconcile_scopes
from common import schema

YEARS = list(range(2020, 2027))

# Verdicts → faut-il corriger ? (drapeau du livrable « est-ce nous »). NON_COTE = un « ticker » Quiver
# qui n'est pas une action appariable (CUSIP, préférentielle, fragment OCR) → hors périmètre, pas un trou.
A_CORRIGER = {
    "CONCORDANT": False, "STRUCTUREL": False, "ON_EST_PLUS_COMPLET": False, "NON_COTE": False,
    "ECART_DATE": True, "ECART_TICKER": True, "MANQUANT_PAPIER": True, "NOTRE_MANQUE": True,
}
OUR_ORDER = ["CONCORDANT", "ECART_DATE", "ECART_TICKER", "STRUCTUREL", "ON_EST_PLUS_COMPLET"]
QUIVER_ORDER = ["ECART_DATE", "ECART_TICKER", "MANQUANT_PAPIER", "NON_COTE", "NOTRE_MANQUE"]


# ───────────────────────────── Chargement (offline) ─────────────────────────────
def _paths(repo, chamber, year):
    base = repo / "data" / chamber / "tables" / str(year)
    return (base / f"06_{chamber}_{year}_transactions.csv",
            base / f"06b_{chamber}_{year}_ocr_transactions.csv",
            base / f"06_{chamber}_{year}_FINAL.csv")


def _load_quiver(repo, chamber):
    """Cache Quiver complet (jamais réinjecté). House : colonnes traded/filed minuscules → renommées
    Traded/Filed pour reconcile (parité house/ocr.py:530)."""
    p = repo / "data" / chamber / "tables" / f"_quiver_{chamber}_cache.csv"
    if not p.exists():
        return None
    q = pd.read_csv(p)
    if chamber == "house":
        q = q.rename(columns={"traded": "Traded", "filed": "Filed"})
    q["_filed"] = pd.to_datetime(q["Filed"], errors="coerce")
    q["_traded"] = pd.to_datetime(q["Traded"], errors="coerce")
    return q


def _qwin(qfull, year):
    """Fenêtre = dépôts (Filed) de l'année (parité prod : filed ∈ [year-01-01, year-12-31])."""
    return qfull[qfull["_filed"].dt.year == year].copy()


# ───────────────────────────── Clés normalisées ─────────────────────────────
def _our_keys(df):
    """Ensembles de clés de NOS transactions tickérisables : exacte, sans-date, sans-ticker."""
    d = df.copy()
    d["_tk"] = d["ticker"].map(hq.norm_ticker)
    d["_s"] = d["operation_type"].map(hq.norm_sense)
    d["_d"] = pd.to_datetime(d["transaction_date"], errors="coerce").dt.date
    e = d[d["_tk"] != ""]
    return {
        "exact": set(zip(e["bioguide_id"], e["_tk"], e["_d"], e["_s"])),
        "no_date": set(zip(e["bioguide_id"], e["_tk"], e["_s"])),
        "no_ticker": set(zip(e["bioguide_id"], e["_d"], e["_s"])),
        "bios": set(d["bioguide_id"].dropna()),
    }


def _quiver_keys(qwin):
    """Ensembles de clés Quiver tickérisables (mêmes 3 granularités)."""
    q = qwin.copy()
    q["_tk"] = q["Ticker"].map(hq.norm_ticker)
    q["_s"] = q["Transaction"].map(hq.norm_sense)
    q["_d"] = q["_traded"].dt.date
    e = q[q["_tk"] != ""]
    return {
        "exact": set(zip(e["BioGuideID"], e["_tk"], e["_d"], e["_s"])),
        "no_date": set(zip(e["BioGuideID"], e["_tk"], e["_s"])),
        "no_ticker": set(zip(e["BioGuideID"], e["_d"], e["_s"])),
        "bios": set(q["BioGuideID"].dropna()),
    }


# ───────────────────────────── Classification ─────────────────────────────
def _quiver_untradeable(tk):
    """Vrai si le « ticker » Quiver n'est PAS une action cotée appariable : fragment OCR de description
    (espace, ':' ou '/'), action préférentielle ('$'), bon du Trésor (MATUR/WEEK/MONTH) ou CUSIP / mot
    tronqué (>5 car.). Un vrai ticker action fait ≤5 caractères alphanumériques sans séparateur. Sert à
    ne PAS classer en NOTRE_MANQUE un non-coté que Quiver liste mais qui est hors de son périmètre actions."""
    t = str(tk).upper().strip()
    if not t:
        return True
    if any(c in t for c in (" ", ":", "/", "$")):
        return True
    if "MATUR" in t or "WEEK" in t or "MONTH" in t:
        return True
    return len(t.replace("_", "")) > 5


def _verdict_our_row(bio, tk, d, s, qk, asset_type):
    """Verdict d'UNE de nos transactions vs les ensembles Quiver `qk` (full window)."""
    if tk == "":
        # Une ACTION (asset_type=Stock) sans ticker résolu N'EST PAS du non-coté : si Quiver a le trade
        # tickerisé le même jour (bio,date,sens), le ticker est récupérable → ECART_TICKER (corrigible).
        # Tout autre cas sans ticker (muni, obligation, fonds… ou action que Quiver n'a pas) → STRUCTUREL.
        if str(asset_type).strip().lower() == "stock" and (bio, d, s) in qk["no_ticker"]:
            return "ECART_TICKER"
        return "STRUCTUREL"
    if (bio, tk, d, s) in qk["exact"]:
        return "CONCORDANT"
    if (bio, tk, s) in qk["no_date"]:
        return "ECART_DATE"
    if (bio, d, s) in qk["no_ticker"]:
        return "ECART_TICKER"
    return "ON_EST_PLUS_COMPLET"


def _verdict_quiver_key(bio, tk, d, s, ok, paper_bios):
    """Verdict d'UN trade Quiver qu'on n'a pas (only_quiver) vs nos ensembles `ok`."""
    if (bio, tk, s) in ok["no_date"]:
        return "ECART_DATE"
    if (bio, d, s) in ok["no_ticker"]:
        return "ECART_TICKER"
    if _quiver_untradeable(tk):
        return "NON_COTE"          # CUSIP / préférentielle / fragment OCR → hors périmètre Quiver-actions
    if bio in paper_bios:
        return "MANQUANT_PAPIER"
    return "NOTRE_MANQUE"


def classify_our_side(final_df, qwin):
    """Classe CHAQUE transaction FINAL (couvre le non-coté → STRUCTUREL). Renvoie le df + colonne
    `verdict` (aligné sur 07g : CONCORDANT+ECART_DATE = exact+date_mismatch ; STRUCTUREL = non_equity)."""
    qk = _quiver_keys(qwin)
    d = final_df.copy()
    d["_tk"] = d["ticker"].map(hq.norm_ticker)
    d["_s"] = d["operation_type"].map(hq.norm_sense)
    d["_d"] = pd.to_datetime(d["transaction_date"], errors="coerce").dt.date
    d["verdict"] = [_verdict_our_row(b, t, dt, s, qk, at)
                    for b, t, dt, s, at in zip(d["bioguide_id"], d["_tk"], d["_d"], d["_s"], d["asset_type"])]
    return d


def classify_quiver_side(final_df, qwin, paper_bios):
    """Classe les trades Quiver qu'on n'a pas (only_quiver, restreint aux déposants communs +
    tickérisables = parité reconcile/07c). Renvoie un DataFrame [bioguide, name, ticker, date, sense,
    verdict]."""
    ok = _our_keys(final_df)
    qk_df = qwin.copy()
    qk_df["_tk"] = qk_df["Ticker"].map(hq.norm_ticker)
    qk_df["_s"] = qk_df["Transaction"].map(hq.norm_sense)
    qk_df["_d"] = qk_df["_traded"].dt.date
    # parité reconcile : déposants communs + tickérisables, clés dédupliquées
    common = ok["bios"] & set(qk_df["BioGuideID"].dropna())
    qo = qk_df[qk_df["BioGuideID"].isin(common) & (qk_df["_tk"] != "")]
    quiv_k = set(zip(qo["BioGuideID"], qo["_tk"], qo["_d"], qo["_s"]))
    onlyq = quiv_k - ok["exact"]
    name_by_q = qo.drop_duplicates("BioGuideID").set_index("BioGuideID")["Name"]
    rows = []
    for bio, tk, d, s in sorted(onlyq, key=lambda x: (str(x[0]), str(x[1]), str(x[2]), str(x[3]))):
        rows.append({"bioguide": bio, "name": name_by_q.get(bio, bio), "ticker": tk,
                     "date": d, "sense": s,
                     "verdict": _verdict_quiver_key(bio, tk, d, s, ok, paper_bios)})
    return pd.DataFrame(rows, columns=["bioguide", "name", "ticker", "date", "sense", "verdict"])


def field_disagreements(final_df, qwin):
    """Accord sens & montant (borne basse) sur les cellules (bio×ticker×date) présentes des DEUX côtés,
    mesuré par APPARTENANCE ENSEMBLISTE : un de nos trades « concorde » s'il existe un trade Quiver de
    même `sens` (resp. `(sens, borne basse)`) dans la même cellule. Robuste aux différences de
    granularité de lots (Quiver agrège parfois plusieurs lots d'un même jour) — contrairement à l'ancien
    `merge` bio×ticker×date qui faisait un produit cartésien (n_paires gonflé ~+40 %, accord sous-estimé).
    Renvoie (n, accord_sens_pct, accord_montant_pct, désaccords) ; `désaccords` = nos trades NON corroborés,
    typés `sens` (direction absente côté Quiver) ou `montant` (bonne direction, montant absent côté
    Quiver = vraie erreur d'extraction sur une donnée pourtant captée)."""
    d = final_df.copy()
    d["_tk"] = d["ticker"].map(hq.norm_ticker)
    d["_s"] = d["operation_type"].map(hq.norm_sense)
    d["_d"] = pd.to_datetime(d["transaction_date"], errors="coerce").dt.date
    d["_lb"] = d["amount_range"].map(hq.low_bound)
    o = d[d["_tk"] != ""][["bioguide_id", "declarant_name", "_tk", "_d", "_s", "_lb"]]

    q = qwin.copy()
    q["_tk"] = q["Ticker"].map(hq.norm_ticker)
    q["_s"] = q["Transaction"].map(hq.norm_sense)
    q["_d"] = q["_traded"].dt.date
    q["_qlb"] = pd.to_numeric(q["Trade_Size_USD"], errors="coerce")
    qo = q[q["_tk"] != ""][["BioGuideID", "_tk", "_d", "_s", "_qlb"]].rename(columns={"BioGuideID": "bioguide_id"})
    if not len(o) or not len(qo):
        return 0, None, None, pd.DataFrame()

    qmap = {k: (set(g["_s"]), set(zip(g["_s"], g["_qlb"])),
                "/".join(sorted({str(x) for x in g["_s"]})),
                "/".join(sorted({str(int(x)) for x in g["_qlb"] if pd.notna(x)})))
            for k, g in qo.groupby(["bioguide_id", "_tk", "_d"])}
    n = sense_match = amt_match = 0
    bad_rows = []
    for k, og in o.groupby(["bioguide_id", "_tk", "_d"]):
        qinfo = qmap.get(k)
        if qinfo is None:
            continue
        q_senses, q_pairs, qs, qa = qinfo
        n += len(og)
        for _, r in og.iterrows():
            s_ok = r["_s"] in q_senses
            a_ok = (r["_s"], r["_lb"]) in q_pairs
            sense_match += s_ok
            amt_match += a_ok
            if not a_ok:
                bad_rows.append({"bioguide_id": r["bioguide_id"], "declarant_name": r["declarant_name"],
                                 "ticker": r["_tk"], "date": r["_d"],
                                 "type_desaccord": "montant" if s_ok else "sens",
                                 "notre_sens": r["_s"], "notre_montant_bas": r["_lb"],
                                 "quiver_sens_dispo": qs, "quiver_montants_dispo": qa})
    sense_pct = round(100 * sense_match / n, 1) if n else None
    amt_pct = round(100 * amt_match / n, 1) if n else None
    return n, sense_pct, amt_pct, pd.DataFrame(bad_rows)


# ───────────────────────── Inclusion Quiver ⊆ nous (LA métrique de la thèse) ─────────────────────────
def _concat_final_raw(repo, chamber):
    """Concatène les FINAL multi-années (corrections de dates appliquées), SANS dédup. Renvoie
    (df, n_lignes_brutes). Brique partagée par _load_final_dedup et reconciliation (anti-dérive)."""
    fins = []
    for y in YEARS:
        _, _, fp = _paths(repo, chamber, y)
        if fp.exists():
            f = schema.apply_txn_date_fixes(pd.read_csv(fp, dtype=str)); f["_year"] = y
            fins.append(f)
    if not fins:
        return pd.DataFrame(), 0
    raw = pd.concat(fins, ignore_index=True)
    return raw, len(raw)


def _load_final_dedup(repo, chamber):
    """FINAL multi-années dédupliqué cross-année (même invariant que build_diagnosis/load_final),
    avec corrections de dates connues appliquées."""
    F, _ = _concat_final_raw(repo, chamber)
    if not len(F):
        return pd.DataFrame()
    if {"natural_key_hash", "occurrence_index"}.issubset(F.columns):
        F = (F.assign(_o=pd.to_numeric(F["occurrence_index"], errors="coerce"))
             .sort_values("_year", kind="stable")
             .drop_duplicates(["natural_key_hash", "_o"], keep="first").reset_index(drop=True))
    return F


def reconciliation(repo_root) -> pd.DataFrame:
    """Réconciliation lignes brutes FINAL → transactions uniques (la dédup cross-année des re-divulgations
    tardives). Par chambre + ligne TOTAL. Source régénérable des nombres 90 483 / 631 / 89 852."""
    repo = Path(repo_root)
    rows = []
    for ch in ("house", "senate"):
        raw, n_raw = _concat_final_raw(repo, ch)
        if not n_raw:
            continue
        ded = raw
        if {"natural_key_hash", "occurrence_index"}.issubset(raw.columns):
            ded = (raw.assign(_o=pd.to_numeric(raw["occurrence_index"], errors="coerce"))
                   .sort_values("_year", kind="stable")
                   .drop_duplicates(["natural_key_hash", "_o"], keep="first"))
        rows.append({"chamber": ch, "lignes_brutes": n_raw,
                     "re_divulgations_dedup": n_raw - len(ded), "transactions_uniques": len(ded)})
    df = pd.DataFrame(rows)
    if len(df):
        df = pd.concat([df, pd.DataFrame([{
            "chamber": "TOTAL", "lignes_brutes": int(df["lignes_brutes"].sum()),
            "re_divulgations_dedup": int(df["re_divulgations_dedup"].sum()),
            "transactions_uniques": int(df["transactions_uniques"].sum())}])], ignore_index=True)
    return df


# ───────────────── Réconciliation date 1-à-1 (remplace l'heuristique de collision) ─────────────────
# L'ancienne méthode était de l'appartenance ensembliste : « ma date exacte est-elle dans l'ensemble
# Quiver ? ». Elle ne peut pas gérer la multiplicité (un déposant qui trade un titre N fois vs M chez
# Quiver) → elle fabriquait un faux « écart-date » (99 % dit « collision »). Ici on fait une VRAIE
# réconciliation 1-à-1 par (bio, ticker, sens), ancrée au dépôt (disclosure ≈ Filed).
RECON_TOL_CLOSE = 10     # jours : bruit / convention de date acceptée (même trade) — absorbe le décalage de convention ~8j observé chez Quiver
RECON_MAX_PAIR = 90      # jours : mis-datage max plausible du MÊME trade (au-delà = 2 trades distincts)
RECON_FILING_TOL = 10    # jours : « même dépôt » = |disclosure − Filed| (médiane 0 j → signal fort)


def _reconcile_group(our, quiv):
    """Réconcilie UN groupe (bio,ticker,sens). `our` = [(date, disclosure, doc_id, declarant)],
    `quiv` = [(date, filed)]. Retire les matches date-exacte, puis apparie gloutonnement au plus proche
    dans RECON_MAX_PAIR. Renvoie (n_exact, n_close, ours_only, quiver_only, candidates) où candidates =
    [(notre_date, quiver_date, delta, meme_depot, doc_id, declarant)] pour TOL_CLOSE < delta ≤ MAX_PAIR."""
    from collections import Counter
    oc = Counter(o[0] for o in our); qc = Counter(q[0] for q in quiv)
    n_exact = 0
    for d in list(oc):
        m = min(oc[d], qc.get(d, 0))
        if m:
            n_exact += m; oc[d] -= m; qc[d] -= m
    seen = Counter(); left_o = []
    for o in sorted(our, key=lambda x: x[0]):
        if seen[o[0]] < oc[o[0]]:
            left_o.append(o); seen[o[0]] += 1
    qseen = Counter(); left_q = []
    for q in sorted(quiv, key=lambda x: x[0]):
        if qseen[q[0]] < qc[q[0]]:
            left_q.append(q); qseen[q[0]] += 1
    used = [False] * len(left_q)
    n_close = ours_only = 0; cands = []
    for od, odisc, doc, nm in left_o:
        bi, best = -1, None
        for j, (qd_, _qf) in enumerate(left_q):
            if used[j]:
                continue
            dist = abs((od - qd_).days)
            if best is None or dist < best:
                best, bi = dist, j
        if bi < 0 or best is None or best > RECON_MAX_PAIR:
            ours_only += 1
            continue
        used[bi] = True
        if best <= RECON_TOL_CLOSE:
            n_close += 1
        else:
            qd_, qf = left_q[bi]
            same = bool(pd.notna(odisc) and pd.notna(qf) and abs((odisc - qf).days) <= RECON_FILING_TOL)
            cands.append((od, qd_, best, same, doc, nm))
    quiver_only = sum(1 for u in used if not u)
    return n_exact, n_close, ours_only, quiver_only, cands


def reconcile_dates(repo_root):
    """Réconciliation 1-à-1 transaction-par-transaction (remplace date_artifact/collision). Pour chaque
    (bio, ticker, sens), apparie NOS trades à ceux de Quiver — date exacte d'abord, puis plus proche dans
    RECON_MAX_PAIR jours — et CLASSE chaque trade : exact / proche (bruit ≤ TOL_CLOSE) / candidat (écart de
    date à inspecter) / nous-seul (Quiver n'a PAS le trade) / quiver-seul (on a raté). Un vrai écart de date
    apparaît comme une PAIRE avec delta, pas comme un artefact d'empilement. Renvoie (résumé par chambre,
    candidats « même dépôt » triés par delta = les seuls candidats honnêtes d'erreur de date)."""
    repo = Path(repo_root)
    summ, cand_rows = [], []
    for ch in ("house", "senate"):
        F = _load_final_dedup(repo, ch); Q = _load_quiver(repo, ch)
        if not len(F) or Q is None:
            continue
        F = F.copy(); F["_tk"] = F["ticker"].map(hq.norm_ticker); F["_s"] = F["operation_type"].map(hq.norm_sense)
        F["_d"] = pd.to_datetime(F["transaction_date"], errors="coerce")
        F["_disc"] = pd.to_datetime(F["disclosure_date"], errors="coerce")
        Q = Q.copy(); Q["_tk"] = Q["Ticker"].map(hq.norm_ticker); Q["_s"] = Q["Transaction"].map(hq.norm_sense)
        Q["_d"] = pd.to_datetime(Q["_traded"], errors="coerce"); Q["_fy"] = Q["_filed"].dt.year
        Q = Q.drop_duplicates(["BioGuideID", "Ticker", "Traded", "Transaction"])   # doublons natifs Quiver
        common = set(F["bioguide_id"].dropna()) & set(Q["BioGuideID"].dropna())
        Fo = F[F["bioguide_id"].isin(common) & (F["_tk"] != "")].dropna(subset=["_d"])
        Qo = Q[Q["BioGuideID"].isin(common) & (Q["_tk"] != "")
               & (Q["_fy"].between(min(YEARS), max(YEARS)))].dropna(subset=["_d"])
        og, qg = {}, {}
        for b, t, s, d, di, doc, nm in zip(Fo["bioguide_id"], Fo["_tk"], Fo["_s"], Fo["_d"],
                                           Fo["_disc"], Fo["doc_id"], Fo["declarant_name"]):
            og.setdefault((b, t, s), []).append((d, di, doc, nm))
        for b, t, s, d, f in zip(Qo["BioGuideID"], Qo["_tk"], Qo["_s"], Qo["_d"], Qo["_filed"]):
            qg.setdefault((b, t, s), []).append((d, f))
        E = C = CA = OO = QO = MD = 0
        for k in set(og) | set(qg):
            e, c, oo, qo, cands = _reconcile_group(og.get(k, []), qg.get(k, []))
            E += e; C += c; OO += oo; QO += qo; CA += len(cands)
            for od, qd_, delta, same, doc, nm in cands:
                if same:
                    MD += 1
                    cand_rows.append({"chamber": ch, "declarant": str(nm)[:20], "ticker": k[1], "sens": k[2],
                                      "notre_date": od.date(), "quiver_date": qd_.date(),
                                      "delta_jours": int(delta), "doc_id": doc})
        n_app = E + C + CA + OO
        summ.append({"chamber": ch, "apparie_exact": E, "apparie_proche": C, "candidat_ecart": CA,
                     "dont_meme_depot": MD, "nous_seul": OO, "quiver_seul": QO,
                     "candidat_pct": round(100 * CA / n_app, 1) if n_app else None})
    summary = pd.DataFrame(summ)
    cands = pd.DataFrame(cand_rows)
    if len(cands):
        cands = cands.sort_values(["delta_jours", "chamber"], kind="stable").reset_index(drop=True)
    return summary, cands


def net_completeness_from_tallies(our_tally, quiver_tally) -> pd.DataFrame:
    """Bilan net « on est plus complet » : actions cotées qu'on a et que Quiver n'a pas
    (ON_EST_PLUS_COMPLET) vs vrais trous inverses (NOTRE_MANQUE), par chambre. Dérivé des tallies déjà
    calculés (ne recharge rien)."""
    def _by(dd, verdict):
        d = dd[dd["verdict"] == verdict]
        return {str(r["côté"]).split("(")[-1].rstrip(")").strip(): int(r["n"]) for _, r in d.iterrows()}
    plus, manque = _by(our_tally, "ON_EST_PLUS_COMPLET"), _by(quiver_tally, "NOTRE_MANQUE")
    rows = []
    for ch in ("house", "senate"):
        p, m = plus.get(ch, 0), manque.get(ch, 0)
        rows.append({"chamber": ch, "on_a_en_plus": p, "vrais_trous": m, "solde_net": p - m})
    return pd.DataFrame(rows)


def ticker_inclusion(repo_root) -> pd.DataFrame:
    """Mesure « Quiver ⊆ nous » au niveau (bioguide, ticker, sens), DATE-AGNOSTIQUE (donc non affectée par
    l'artefact de collision de date) et RESTREINTE À NOTRE FENÊTRE (Quiver Filed ∈ YEARS) — sinon
    l'historique pré-2020 de Quiver (qu'on ne couvre pas) fait chuter artificiellement le taux. C'est la
    métrique directe de la thèse « on a tout ce que Quiver a ». Le résidu (Quiver a, nous pas) est décomposé :
      ocr_recuperable  : déposant qu'on OCR (lignes papier ratées → re-OCR ciblé).
      quiver_non_cote  : « ticker » Quiver non appariable (CUSIP/préférentielle/fragment) → hors périmètre.
      credit_2jambes   : on a le trade sous un ticker 2-jambes (échange : « PFE  VTRS » couvre « PFE »).
      cross_chambre    : déposant présent dans l'AUTRE chambre (ex. Curtis Rep→Sén : ses trades Chambre
                         polluent le cache Sénat de Quiver) → hors périmètre de cette chambre.
      residu_cote_reel : le VRAI trou coté restant (à investiguer / corriger ponctuellement)."""
    repo = Path(repo_root)
    bios = {ch: set(_load_final_dedup(repo, ch).get("bioguide_id", pd.Series(dtype=str)).dropna())
            for ch in ("house", "senate")}
    lo, hi = min(YEARS), max(YEARS)
    rows = []
    for ch in ("house", "senate"):
        F = _load_final_dedup(repo, ch); Q = _load_quiver(repo, ch)
        if not len(F) or Q is None:
            continue
        other = "senate" if ch == "house" else "house"
        F["_tk"] = F["ticker"].map(hq.norm_ticker); F["_s"] = F["operation_type"].map(hq.norm_sense)
        Q = Q.copy(); Q["_tk"] = Q["Ticker"].map(hq.norm_ticker); Q["_s"] = Q["Transaction"].map(hq.norm_sense)
        Q["_fy"] = Q["_filed"].dt.year
        common = set(F["bioguide_id"].dropna()) & set(Q["BioGuideID"].dropna())
        Fo = F[F["bioguide_id"].isin(common) & (F["_tk"] != "")]
        qo = Q[Q["BioGuideID"].isin(common) & (Q["_tk"] != "") & (Q["_fy"].between(lo, hi))]
        ours3 = set(zip(Fo["bioguide_id"], Fo["_tk"], Fo["_s"]))
        quiv3 = set(zip(qo["BioGuideID"], qo["_tk"], qo["_s"]))
        inc, miss = quiv3 & ours3, quiv3 - ours3
        paper = set(F[F["provenance"].str.contains("ocr", na=False)]["bioguide_id"].dropna())
        legs = {}
        for b, tk in zip(Fo["bioguide_id"], Fo["_tk"]):
            if " " in tk:
                legs.setdefault(b, set()).update(tk.split())
        c = {"ocr": 0, "noncote": 0, "twoleg": 0, "cross": 0, "reel": 0}
        for b, t, s in miss:
            if b in paper:                      c["ocr"] += 1
            elif _quiver_untradeable(t):        c["noncote"] += 1
            elif t in legs.get(b, set()):       c["twoleg"] += 1
            elif b in bios[other]:              c["cross"] += 1
            else:                               c["reel"] += 1
        rows.append({"chamber": ch, "quiver_dans_fenetre": len(quiv3), "inclus": len(inc),
                     "inclusion_pct": round(100 * len(inc) / len(quiv3), 1) if quiv3 else None,
                     "residu": len(miss), "ocr_recuperable": c["ocr"], "quiver_non_cote": c["noncote"],
                     "credit_2jambes": c["twoleg"], "cross_chambre": c["cross"],
                     "residu_cote_reel": c["reel"]})
    return pd.DataFrame(rows)


# ───────────────────────────── Construction du diagnostic ─────────────────────────────
def _coverage_by_year(repo, chamber, qfull):
    """Table A : par année × scope — matched/quiver/ours, couverture (Quiver→nous) et precision
    (nous→Quiver). Réutilise reconcile_scopes (parité 07c)."""
    recon_fn = hq.reconcile if chamber == "house" else sq.reconcile
    rows = []
    for y in YEARS:
        dp, op, fp = _paths(repo, chamber, y)
        if not fp.exists():
            continue
        qwin = _qwin(qfull, y)
        scopes = {"digital": pd.read_csv(dp, dtype=str) if dp.exists() else None,
                  "ocr": pd.read_csv(op, dtype=str) if op.exists() else None,
                  "both": pd.read_csv(fp, dtype=str)}
        scopes = {k: (v if v is not None else scopes["both"].iloc[0:0]) for k, v in scopes.items()}
        txn, _field, _rb = reconcile_scopes(recon_fn, scopes, qwin)
        piv = txn.pivot_table(index="scope", columns="metric", values="value", aggfunc="first")
        for scope in ("digital", "ocr", "both"):
            if scope not in piv.index:
                continue
            matched = piv.loc[scope].get("matched")
            quiver = piv.loc[scope].get("quiver")
            ours = piv.loc[scope].get("ours_tickerizable")
            cov = round(100 * matched / quiver, 1) if quiver else None
            prec = round(100 * matched / ours, 1) if ours else None
            rows.append({"chamber": chamber, "year": y, "scope": scope,
                         "matched": int(matched or 0), "quiver": int(quiver or 0),
                         "ours_tickerizable": int(ours or 0),
                         "couverture_pct": cov, "precision_pct": prec})
    return pd.DataFrame(rows)


def _tally(series, order, label):
    """Compte + % par verdict, dans l'ordre donné, avec drapeau à_corriger."""
    vc = series.value_counts()
    tot = int(vc.sum())
    rows = [{"verdict": v, "n": int(vc.get(v, 0)),
             "pct": round(100 * int(vc.get(v, 0)) / tot, 1) if tot else None,
             "a_corriger": A_CORRIGER[v]} for v in order if vc.get(v, 0)]
    out = pd.DataFrame(rows)
    if len(out):
        out.insert(0, "côté", label)
    return out


def build_diagnosis(repo_root) -> dict:
    """Recalcule tout le diagnostic Quiver (offline) pour House+Sénat, 2020-2026. Écrit les annexes
    actionnables sous docs/quiver_validation/ et renvoie les tables agrégées pour le rapport."""
    repo = Path(repo_root)
    annex = repo / "docs" / "quiver_validation"
    annex.mkdir(parents=True, exist_ok=True)

    coverage, our_tally, quiver_tally, field_rows, synth_rows = [], [], [], [], []

    for chamber in ("house", "senate"):
        qfull = _load_quiver(repo, chamber)
        if qfull is None:
            continue
        coverage.append(_coverage_by_year(repo, chamber, qfull))

        # FINAL concaténé de toutes les années, PUIS dédup cross-année : une re-divulgation tardive
        # (même clé naturelle dans 2 fichiers d'années différentes — ex. Perdue ORCL 2020 re-divulgué
        # en 2021) est gardée UNE seule fois, dans son année de dépôt la plus ancienne. Sans ça le même
        # trade serait compté deux fois — CONCORDANT son année d'origine, puis faux ON_EST_PLUS_COMPLET
        # l'année de re-divulgation (hors fenêtre Quiver filed-year de cette année). Sénat : −596 lignes
        # (8 245 uniques) ; House : −35 (81 607 uniques). Même invariant que common/schema.dedup_canonical.
        fins = []
        for y in YEARS:
            _, _, fp = _paths(repo, chamber, y)
            if fp.exists():
                f = pd.read_csv(fp, dtype=str); f["_year"] = y
                fins.append(f)
        if not fins:
            continue
        final_all = schema.apply_txn_date_fixes(pd.concat(fins, ignore_index=True))   # 3 années-coquilles
        if {"natural_key_hash", "occurrence_index"}.issubset(final_all.columns):
            # occurrence_index : '0' vs '0.0' selon l'année → normaliser en numérique avant la dédup.
            final_all = (final_all.assign(_occ=pd.to_numeric(final_all["occurrence_index"], errors="coerce"))
                         .sort_values("_year", kind="stable")
                         .drop_duplicates(["natural_key_hash", "_occ"], keep="first")
                         .drop(columns="_occ").reset_index(drop=True))
        paper_bios = set(final_all[final_all["provenance"].str.contains("ocr", na=False)]["bioguide_id"].dropna())

        # côté NOUS + côté QUIVER, par année (sur le corpus dédupliqué), puis agrégé
        our_parts, q_parts, bad_parts = [], [], []
        n_pairs_tot = 0
        sense_w, amt_w = 0.0, 0.0
        for y in [yy for yy in YEARS if (final_all["_year"] == yy).any()]:
            f = final_all[final_all["_year"] == y]
            qwin = _qwin(qfull, y)
            our = classify_our_side(f, qwin); our["_year"] = y
            our_parts.append(our)
            qv = classify_quiver_side(f, qwin, paper_bios); qv["year"] = y
            q_parts.append(qv)
            npr, sa, aa, bad = field_disagreements(f, qwin)
            if npr:
                n_pairs_tot += npr; sense_w += sa * npr / 100; amt_w += aa * npr / 100
                bad["year"] = y; bad_parts.append(bad)

        our_all = pd.concat(our_parts, ignore_index=True)
        quiver_all = pd.concat(q_parts, ignore_index=True) if q_parts else pd.DataFrame(columns=["verdict"])

        our_tally.append(_tally(our_all["verdict"], OUR_ORDER, f"nous→Quiver ({chamber})"))
        quiver_tally.append(_tally(quiver_all["verdict"], QUIVER_ORDER, f"Quiver→nous ({chamber})"))

        # accord champs agrégé (pondéré par n_pairs)
        field_rows.append({"chamber": chamber, "n_paires_appariées": n_pairs_tot,
                           "accord_sens_pct": round(100 * sense_w / n_pairs_tot, 1) if n_pairs_tot else None,
                           "accord_montant_bas_pct": round(100 * amt_w / n_pairs_tot, 1) if n_pairs_tot else None})

        # synthèse : combien de NOS trades sont à corriger vs structurels vs on-est-plus-complet
        n_our = len(our_all)
        corrig = int(our_all["verdict"].isin([v for v in OUR_ORDER if A_CORRIGER[v]]).sum())
        struct = int((our_all["verdict"] == "STRUCTUREL").sum())
        plus = int((our_all["verdict"] == "ON_EST_PLUS_COMPLET").sum())
        # « ecart_brut_pct » = ECART_DATE + ECART_TICKER. NOTE : ce n'est PAS un taux d'erreur — l'ECART_DATE
        # est décomposé honnêtement par reconcile_dates (§6.3 : surtout du « nous-seul »/convention de date, pas
        # notre faute) et nos tickers concordent (cf. inclusion §6.2). Nommé « brut » exprès pour ne pas le
        # présenter comme « notre erreur ».
        synth_rows.append({"chamber": chamber, "nos_txns": n_our,
                           "concordant_pct": round(100 * (our_all["verdict"] == "CONCORDANT").sum() / n_our, 1),
                           "ecart_brut_pct": round(100 * corrig / n_our, 1),
                           "structurel_pct": round(100 * struct / n_our, 1),
                           "on_est_plus_complet_pct": round(100 * plus / n_our, 1)})

        # ── annexes actionnables (hors golden) ──
        et = our_all[our_all["verdict"] == "ECART_TICKER"][
            ["bioguide_id", "declarant_name", "ticker", "transaction_date", "operation_type", "asset_type", "_year"]]
        et.to_csv(annex / f"ecart_ticker_{chamber}.csv", index=False)
        pc = our_all[our_all["verdict"] == "ON_EST_PLUS_COMPLET"][
            ["bioguide_id", "declarant_name", "ticker", "transaction_date", "operation_type", "asset_type", "_year"]]
        pc.to_csv(annex / f"on_est_plus_complet_{chamber}.csv", index=False)
        quiver_all[quiver_all["verdict"] == "NOTRE_MANQUE"].to_csv(annex / f"notre_manque_{chamber}.csv", index=False)
        quiver_all[quiver_all["verdict"] == "MANQUANT_PAPIER"].to_csv(annex / f"manquant_papier_{chamber}.csv", index=False)
        quiver_all[quiver_all["verdict"] == "NON_COTE"].to_csv(annex / f"quiver_non_cote_{chamber}.csv", index=False)
        if bad_parts:
            pd.concat(bad_parts, ignore_index=True).to_csv(annex / f"desaccord_champ_{chamber}.csv", index=False)

        # top déposants par NOTRE_MANQUE (pour le rapport) — dédup par bioguide, nom canonique (FINAL),
        # tri stable (n desc, bioguide) pour un rendu déterministe
        _nm = final_all.drop_duplicates("bioguide_id").set_index("bioguide_id")["declarant_name"]
        _mq = quiver_all[quiver_all["verdict"] == "NOTRE_MANQUE"]
        _top = (_mq.groupby("bioguide").size().reset_index(name="n_notre_manque")
                .sort_values(["n_notre_manque", "bioguide"], ascending=[False, True]).head(8))
        _top["name"] = _top["bioguide"].map(
            lambda b: _nm.get(b) if pd.notna(_nm.get(b)) else _mq[_mq["bioguide"] == b]["name"].iloc[0])
        _top = _top[["bioguide", "name", "n_notre_manque"]]
        _top.insert(0, "chamber", chamber)
        synth_rows[-1]["_top_manque"] = _top  # transporté à part

    top_manque = pd.concat([s.pop("_top_manque") for s in synth_rows if "_top_manque" in s], ignore_index=True) \
        if any("_top_manque" in s for s in synth_rows) else pd.DataFrame()

    our_t = pd.concat([t for t in our_tally if len(t)], ignore_index=True) if our_tally else pd.DataFrame()
    quiv_t = pd.concat([t for t in quiver_tally if len(t)], ignore_index=True) if quiver_tally else pd.DataFrame()
    date_recon, date_cands = reconcile_dates(repo)   # réconciliation 1-à-1 (remplace collision/isolés)
    # annexe actionnable (hors golden) : candidats d'écart de date « même dépôt » = les seuls à inspecter
    if len(date_cands):
        date_cands.to_csv(annex / "candidats_ecart_date_meme_depot.csv", index=False)

    return {
        "coverage_by_year": pd.concat(coverage, ignore_index=True) if coverage else pd.DataFrame(),
        "synthesis": pd.DataFrame(synth_rows) if synth_rows else pd.DataFrame(),
        "our_tally": our_t,
        "quiver_tally": quiv_t,
        "field_agreement": pd.DataFrame(field_rows) if field_rows else pd.DataFrame(),
        "top_notre_manque": top_manque,
        "ticker_inclusion": ticker_inclusion(repo),
        "date_reconciliation": date_recon,
        "date_candidates": date_cands,
        "reconciliation": reconciliation(repo),
        "net_completeness": net_completeness_from_tallies(our_t, quiv_t) if len(our_t) and len(quiv_t) else pd.DataFrame(),
        "annex_dir": str(annex),
    }


def main():
    repo = Path(__file__).resolve().parent.parent
    d = build_diagnosis(repo)
    print("=== Synthèse (côté NOUS) ===")
    print(d["synthesis"].to_string(index=False) if len(d["synthesis"]) else "(vide)")
    print("\n=== Verdicts nous→Quiver ===")
    print(d["our_tally"].to_string(index=False) if len(d["our_tally"]) else "(vide)")
    print("\n=== Verdicts Quiver→nous ===")
    print(d["quiver_tally"].to_string(index=False) if len(d["quiver_tally"]) else "(vide)")
    print("\n=== Accord champs ===")
    print(d["field_agreement"].to_string(index=False) if len(d["field_agreement"]) else "(vide)")
    print("\nAnnexes →", d["annex_dir"])


if __name__ == "__main__":
    main()
