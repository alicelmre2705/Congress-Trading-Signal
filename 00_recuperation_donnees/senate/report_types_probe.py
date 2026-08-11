#!/usr/bin/env python
"""Types de dépôts Sénat — le COLLECTEUR (réseau, opt-in, hors pipeline).

⚠️ OUTIL HORS PIPELINE : le portail eFD ne se rejoue pas hors-ligne, donc la mesure est faite
ICI, datée, et VERSIONNÉE ; le rapport (`common/quality.py` §10) ne lit que les CSV — jamais le
réseau. Relancer ce module = rafraîchir la mesure (les chiffres du §10 suivront au prochain
`python -m common.quality`).

Écrit (sous `data/senate/`) :
  - `_report_types_2014_2026.csv`  — dépôts par Report Type (Annual, PTR, Extension, Blind Trusts)
  - `_filer_types_2014_2026.csv`   — dépôts et PTR par Filer Type (Senator, Former, Candidate)
  - `_report_types_meta.csv`       — scrape_date + totaux de contrôle (fenêtre et all-time)

Politesse identique au reste du dépôt : agrément accepté une fois, PAUSE entre requêtes, aucune
évasion, lecture seule (`recordsTotal` uniquement — 10 requêtes en tout).

Usage : `python -m senate.report_types_probe`
"""
import time
from datetime import date
from pathlib import Path

import pandas as pd

from senate.census_probe import EFD_DATA, EFD_SEARCH, PAUSE, SESSION, accept_agreement

OUT = Path(__file__).resolve().parent.parent / "data" / "senate"

# Codes internes du portail eFD (formulaire de recherche).
RT_CODES = [("Annual", 7), ("Periodic Transactions", 11),
            ("Due Date Extension", 10), ("Blind Trusts", 14)]
FT_CODES = [("Senator", 1), ("Former Senator", 5), ("Candidate", 4)]


def efd_count(report_types="[]", filer_types="[]", start="01/01/2014", end="12/31/2026"):
    """`recordsTotal` d'une recherche eFD (une requête + pause polie)."""
    tok = SESSION.cookies.get("csrftoken", "")
    h = {"Referer": EFD_SEARCH, "X-CSRFToken": tok, "X-Requested-With": "XMLHttpRequest"}
    p = {"draw": "1", "start": "0", "length": "1", "search[value]": "", "search[regex]": "false",
         "order[0][column]": "4", "order[0][dir]": "desc",
         "report_types": report_types, "filer_types": filer_types,
         "submitted_start_date": f"{start} 00:00:00", "submitted_end_date": f"{end} 23:59:59",
         "candidate_state": "", "senator_state": "", "office_id": "",
         "first_name": "", "last_name": ""}
    r = SESSION.post(EFD_DATA, data=p, headers=h, timeout=60)
    r.raise_for_status()
    time.sleep(PAUSE)
    return int(r.json()["recordsTotal"])


def main():
    if not accept_agreement():
        raise RuntimeError("accord eFD refusé — arrêt propre.")

    total = efd_count("[]", "[]")                                        # fenêtre 2014-2026
    alltime = efd_count("[]", "[]", start="01/01/2000", end="12/31/2030")  # contrôle du filtre
    assert alltime > total, "le filtre de date semble IGNORÉ (all-time == fenêtre) !"

    rt = (pd.DataFrame([{"report_type": n, "code": c, "dépôts": efd_count(f"[{c}]", "[]")}
                        for n, c in RT_CODES])
            .sort_values("dépôts", ascending=False).reset_index(drop=True))
    rt["part_%"] = (100 * rt["dépôts"] / total).round(1)
    assert int(rt["dépôts"].sum()) == total, "la partition par Report Type ne somme pas au total !"
    ptr = int(rt.loc[rt["report_type"] == "Periodic Transactions", "dépôts"].iloc[0])

    ft = pd.DataFrame([{"filer_type": n, "code": c,
                        "dépôts": efd_count("[]", f"[{c}]"),
                        "dont_PTR": efd_count("[11]", f"[{c}]")} for n, c in FT_CODES])
    ft["part_%"] = (100 * ft["dépôts"] / total).round(1)
    ft["part_du_PTR_%"] = (100 * ft["dont_PTR"] / ptr).round(1)
    assert int(ft["dépôts"].sum()) == total, "les déposants ne somment pas au total !"
    assert int(ft["dont_PTR"].sum()) == ptr, "les PTR par déposant ne somment pas au PTR total !"

    meta = pd.DataFrame([{"scrape_date": date.today().isoformat(),
                          "total_2014_2026": total, "total_alltime": alltime}])
    rt.to_csv(OUT / "_report_types_2014_2026.csv", index=False)
    ft.to_csv(OUT / "_filer_types_2014_2026.csv", index=False)
    meta.to_csv(OUT / "_report_types_meta.csv", index=False)
    print(f"mesure du {date.today().isoformat()} : {total} dépôts 2014-2026 (all-time {alltime}), "
          f"{ptr} PTR = {100 * ptr / total:.1f} %")
    print(f"écrits : {OUT / '_report_types_2014_2026.csv'}")
    print(f"         {OUT / '_filer_types_2014_2026.csv'}")
    print(f"         {OUT / '_report_types_meta.csv'}")


if __name__ == "__main__":
    main()
