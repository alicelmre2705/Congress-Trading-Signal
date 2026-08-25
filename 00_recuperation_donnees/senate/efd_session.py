#!/usr/bin/env python
"""Session eFD Sénat — la source unique de l'agrément et de la recherche de dépôts.

Le portail eFD impose un agrément (POST `prohibition_agreement` protégé CSRF) avant toute
recherche. Cette mécanique existait en TROIS copies identiques (`senate/digital.py`,
`senate/census_probe.py`, `senate/ocr.py`) ; elle vit désormais ici, et les trois y délèguent.

Ce module n'importe QUE `requests` — volontairement. Il est consommé par `common.first_seen`
(le crawl d'horodatage quotidien), dont la donnée n'est PAS reconstituable a posteriori : ce job
ne doit jamais tomber parce qu'un module lourd du pipeline a bougé. Pas de pandas, pas de
référentiel, pas de moteur OCR.

Chaque appelant garde SA propre session (`new_session()`) : les cookies ne sont pas mutualisés
entre modules, donc la délégation est une substitution stricte — aucun changement de
comportement pour `digital`/`census_probe`/`ocr`.
"""
import re
import time

import requests

EFD_BASE = "https://efdsearch.senate.gov"
EFD_HOME = f"{EFD_BASE}/search/home/"
EFD_SEARCH = f"{EFD_BASE}/search/"
EFD_DATA = f"{EFD_BASE}/search/report/data/"
EFD_PTR = f"{EFD_BASE}/search/view/ptr/{{uuid}}/"
EFD_PAPER = f"{EFD_BASE}/search/view/paper/{{uuid}}/"

USER_AGENT = "congress-trading-research/1.0 (poli, sans evasion)"
PAUSE = 1.5                    # s entre requêtes (politesse) — valeur historique des 3 copies

# Code eFD du type de dépôt « Periodic Transaction Report » (les autres : 7 Annual, 10 Due Date
# Extension, 14 Blind Trusts — cf. senate/report_types_probe.py et §10 du rapport).
REPORT_TYPE_PTR = 11

PTR_LINK_RE = re.compile(r'/search/view/(ptr|paper)/([0-9a-f\-]+)/', re.IGNORECASE)
DATE_RE = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')


def new_session():
    """Session HTTP avec l'en-tête du dépôt. Une par appelant (pas de cookie mutualisé)."""
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    return s


def accept_agreement(session):
    """Accepte l'agrément eFD (obligatoire avant toute recherche). True si la session est ouverte.

    Port VERBATIM des trois copies d'origine, la session devenant un paramètre au lieu d'un global.
    """
    r = session.get(EFD_HOME, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Accès eFD refusé (HTTP {r.status_code}) — arrêt propre.")
    token = session.cookies.get("csrftoken", "")
    session.post(EFD_HOME, data={"prohibition_agreement": "1", "csrfmiddlewaretoken": token},
                 headers={"Referer": EFD_HOME, "X-CSRFToken": token}, timeout=60)
    return "sessionid" in session.cookies or "csrftoken" in session.cookies


def search_filings(session, win_start, win_end, report_type=REPORT_TYPE_PTR, filter_dates=True):
    """Recherche les dépôts déposés entre `win_start` et `win_end` (format MM/DD/YYYY).

    Retourne une liste de dicts : declarant_name · kind ('ptr' | 'paper') · report_uuid ·
    disclosure_date (chaîne MM/DD/YYYY telle que lue). AUCUN rapport n'est téléchargé — seule
    la page de résultats est interrogée, ce qui rend l'appel très bon marché (1 POST / 100 lignes).

    ⚠️ `filter_dates` reproduit le refiltrage de `senate/digital.py:99-102` (ne garder que les
    dépôts dont la date PORTÉE tombe dans la fenêtre). Le crawl d'horodatage le met à False :
    un document mis en ligne aujourd'hui mais DATÉ d'il y a trois semaines est précisément le cas
    qu'on cherche à détecter — le refiltrer le rendrait invisible.
    """
    token = session.cookies.get("csrftoken", "")
    headers = {"Referer": EFD_SEARCH, "X-CSRFToken": token, "X-Requested-With": "XMLHttpRequest"}
    rows, start, length = [], 0, 100
    while True:
        payload = {"draw": "1", "start": str(start), "length": str(length),
                   "search[value]": "", "search[regex]": "false",
                   "order[0][column]": "4", "order[0][dir]": "desc",
                   "report_types": f"[{report_type}]", "filer_types": "[]",
                   "submitted_start_date": f"{win_start} 00:00:00",
                   "submitted_end_date": f"{win_end} 23:59:59",
                   "candidate_state": "", "senator_state": "", "office_id": "",
                   "first_name": "", "last_name": ""}
        r = session.post(EFD_DATA, data=payload, headers=headers, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"Recherche eFD bloquée (HTTP {r.status_code}) — arrêt propre.")
        j = r.json()
        data = j.get("data", [])
        if not data:
            break
        for cells in data:
            blob = " ".join(str(c) for c in cells)
            link = PTR_LINK_RE.search(blob)
            dates = DATE_RE.findall(blob)
            first = re.sub(r"<[^>]+>", "", str(cells[0])).strip() if len(cells) > 0 else ""
            last = re.sub(r"<[^>]+>", "", str(cells[1])).strip() if len(cells) > 1 else ""
            rows.append({"declarant_name": f"{first} {last}".strip(),
                         "kind": link.group(1).lower() if link else None,
                         "report_uuid": link.group(2) if link else None,
                         "disclosure_date": dates[-1] if dates else None})
        start += length
        total = j.get("recordsTotal", len(rows))
        time.sleep(PAUSE)
        if start >= total:
            break
    return rows
