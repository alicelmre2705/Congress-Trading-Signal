#!/usr/bin/env python
"""Crawl d'horodatage — écrit `first_seen_at` : la date à laquelle NOUS voyons un document en ligne.

POURQUOI CE MODULE EXISTE. Le corpus porte deux dates, toutes deux INSCRITES SUR LE DOCUMENT :
`transaction_date` (l'opération) et `disclosure_date` (le dépôt — `FilingDate` de l'index Clerk
côté House, date de réception au Secrétariat côté Sénat). Aucune des deux ne dit quand le document
est devenu PUBLIC. Si un document daté du jour J n'est mis en ligne que J+2, dater le signal en J
revient à trader sur une information qui n'était pas encore accessible — un look-ahead invisible au
backtest, parce qu'il ne vient pas du code mais de la donnée.

`first_seen_at` est la seule date dont on soit certain qu'elle est publique. Elle ne se reconstitue
PAS a posteriori : le journal d'acquisition (`data/house/pdfs/{Y}/00_download_log.csv`) ne porte
aucun horodatage et il est réécrit à chaque run ; les mtime des PDF valent tous la date de la
dernière synchro disque. Chaque jour sans crawl est un jour d'historique perdu pour toujours.

CONTRAT DU MODULE — délibérément minimal :
  - il n'importe RIEN du pipeline (ni pandas, ni pdfplumber, ni le référentiel des élus). Seuls
    `requests` et la stdlib. Un refactor ailleurs ne doit jamais pouvoir interrompre le seul job
    dont la donnée est irrécupérable ;
  - il n'écrit QUE `data/first_seen/first_seen.csv`, en APPEND SEUL. Il ne touche à aucune table,
    à aucun index versionné, à aucun cache ;
  - il ne télécharge aucun PDF, aucun rapport, aucune image : seuls l'index annuel du Clerk et la
    page de résultats eFD sont interrogés.

Usage :
  python -m common.first_seen                       # crawl du jour (House année courante + Sénat 90 j)
  python -m common.first_seen --dry-run             # montre ce qui serait écrit, n'écrit rien
  python -m common.first_seen --backfill            # amorçage : tout le connu, marqué `backfill`
  python -m common.first_seen --years 2025,2026 --days-back 120
"""
import argparse
import csv
import io
import json
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parent.parent          # <repo>/00_recuperation_donnees
FIRST_SEEN_DIR = REPO / "data" / "first_seen"
FIRST_SEEN_CSV = FIRST_SEEN_DIR / "first_seen.csv"
FIRST_SEEN_META = FIRST_SEEN_DIR / "_meta.json"
HOUSE_INDEX_DIR = REPO / "data" / "house" / "index"
HOUSE_INDEX_DAILY = HOUSE_INDEX_DIR / "daily"
SENATE_REPORTS = REPO / "data" / "senate" / "reports"

# Source de l'index annuel du Clerk (un ZIP contenant {year}FD.xml). Même URL que house.acquire —
# recopiée ici plutôt qu'importée : cf. « contrat du module » ci-dessus.
INDEX_ZIP_URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"
USER_AGENT = "congress-trading-research/1.0 (poli, sans evasion)"

# FilingType='P' = Periodic Transaction Report. L'index annuel liste TOUS les dépôts (Annual,
# Candidate, Extension…) ; seuls les PTR portent des transactions.
FILING_TYPE_PTR = "P"

COLUMNS = ["doc_id", "chamber", "first_seen_at", "disclosure_date", "kind",
           "declarant_name", "run_id", "source"]


# ───────────────────────────────── utilitaires ─────────────────────────────────
def _iso(raw):
    """Date déclarée → ISO `YYYY-MM-DD`. L'index Clerk écrit `M/D/YYYY` (non zéro-paddé), eFD
    `MM/DD/YYYY`. Une date illisible devient '' : on ne fabrique jamais une date."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def _run_id():
    """Identifiant du passage, en UTC — le job tourne en CI, jamais dans le fuseau du lecteur."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")


def _today():
    return datetime.now(timezone.utc).date().isoformat()


def crawl_depuis():
    """Date du PREMIER passage du crawl, ou None s'il n'a jamais tourné.

    Sert à distinguer une vraie primo-observation d'un simple rattrapage : un document DÉPOSÉ avant
    que le crawl n'existe était déjà en ligne quand on l'a vu pour la première fois. Son écart
    `first_seen_at − disclosure_date` ne mesure alors que notre retard de démarrage, pas le délai de
    mise en ligne — l'inclure dans la distribution C1 la fausserait entièrement.
    """
    if not FIRST_SEEN_META.exists():
        return None
    try:
        return json.loads(FIRST_SEEN_META.read_text(encoding="utf-8")).get("crawl_depuis")
    except (ValueError, OSError):
        return None


def _init_meta(jour):
    """Grave la date de démarrage du crawl, une fois pour toutes. Jamais réécrite."""
    if FIRST_SEEN_META.exists():
        return
    FIRST_SEEN_DIR.mkdir(parents=True, exist_ok=True)
    FIRST_SEEN_META.write_text(json.dumps({"crawl_depuis": jour}, indent=2) + "\n", encoding="utf-8")


def classer(disclosure_date, depuis):
    """`crawl` (primo-observation exploitable) vs `rattrapage` (déjà en ligne avant nous).

    Un dépôt sans date lisible est classé `rattrapage` : dans le doute, on l'exclut des stats
    plutôt que d'y injecter un écart qu'on ne sait pas interpréter.
    """
    if not depuis or not disclosure_date:
        return "rattrapage"
    return "crawl" if disclosure_date >= depuis else "rattrapage"


def load_seen():
    """Ensemble des (doc_id, chamber) DÉJÀ observés. `doc_id` reste une CHAÎNE : les DocID House
    font 7 ou 8 chiffres (préfixes 2/8/9) et les identifiants Sénat sont des UUID — un typage
    numérique corromprait la clé."""
    if not FIRST_SEEN_CSV.exists():
        return set()
    with FIRST_SEEN_CSV.open(newline="", encoding="utf-8") as f:
        return {(r["doc_id"].strip(), r["chamber"].strip()) for r in csv.DictReader(f)}


def record(observations, run_id, source=None, dry_run=False):
    """Ajoute les observations INCONNUES au CSV. Append seul — un doc_id déjà présent n'est JAMAIS
    réécrit : c'est la PREMIÈRE observation qui fait foi, par définition de `first_seen_at`.
    Sans `source` imposée, chaque ligne est classée `crawl` ou `rattrapage` (cf. `classer`).
    Retourne la liste des lignes nouvelles."""
    seen = load_seen()
    today, nouvelles = _today(), []
    depuis = crawl_depuis()
    for o in observations:
        doc_id = str(o.get("doc_id") or "").strip()
        chamber = o.get("chamber", "")
        if not doc_id or (doc_id, chamber) in seen:
            continue
        seen.add((doc_id, chamber))          # dédup intra-lot (un doc peut sortir 2 fois d'eFD)
        dd = o.get("disclosure_date", "")
        # `source` fixe (amorçage) ou décidé ligne à ligne selon l'ancienneté du dépôt (crawl).
        src = source if source else classer(dd, depuis)
        nouvelles.append({"doc_id": doc_id, "chamber": chamber, "first_seen_at": today,
                          "disclosure_date": dd, "kind": o.get("kind", ""),
                          "declarant_name": o.get("declarant_name", ""),
                          "run_id": run_id, "source": src})
    if dry_run or not nouvelles:
        return nouvelles
    FIRST_SEEN_DIR.mkdir(parents=True, exist_ok=True)
    entete = not FIRST_SEEN_CSV.exists()
    with FIRST_SEEN_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if entete:
            w.writeheader()
        w.writerows(nouvelles)
    return nouvelles


# ───────────────────────────────── House ─────────────────────────────────
def ptr_index_frais(year, session, save_snapshot=True):
    """Index annuel FRAIS du Clerk → la liste de ses PTR, avec leurs métadonnées.

    C'est la seule vue à jour : `house.digital.load_ptr_index` lit l'index EMBARQUÉ
    (`data/house/index/{Y}FD.xml`), figé au jour de son téléchargement — un dépôt arrivé depuis y
    est invisible. Le crawl comme le run en direct doivent donc passer par ici.
    """
    return _telecharger_index(year, session, save_snapshot)


def observe_house(year, session, save_snapshot=True):
    """Télécharge l'index {year}FD.zip du Clerk et rend les PTR qu'il liste.

    L'instantané du jour va dans `data/house/index/daily/` — JAMAIS par-dessus
    `data/house/index/{Y}FD.xml` : ces 13 XML sont irremplaçables (le Clerk purge les années
    anciennes), ils ne se promeuvent qu'à la main.

    NB : `house.acquire.download_index` ne re-télécharge jamais un index déjà présent — l'année en
    cours n'y voit donc jamais ses nouveaux dépôts. On ne le modifie pas, on le contourne.
    """
    return [{k: o[k] for k in ("doc_id", "chamber", "kind", "disclosure_date", "declarant_name")}
            for o in _telecharger_index(year, session, save_snapshot)]


def _telecharger_index(year, session, save_snapshot=True):
    """GET du ZIP, extraction du XML, lecture des Member de type PTR. Rend tous les champs utiles."""
    r = session.get(INDEX_ZIP_URL.format(year=year), timeout=90)
    if r.status_code != 200:
        raise RuntimeError(f"Index {year} indisponible (HTTP {r.status_code})")
    z = zipfile.ZipFile(io.BytesIO(r.content))
    noms = [n for n in z.namelist() if n.lower().endswith(".xml")]
    if not noms:
        raise RuntimeError(f"Index {year} : aucun .xml dans l'archive ({z.namelist()})")
    brut = z.read(noms[0])

    if save_snapshot:
        HOUSE_INDEX_DAILY.mkdir(parents=True, exist_ok=True)
        (HOUSE_INDEX_DAILY / f"{year}FD_{_today()}.xml").write_bytes(brut)

    root = ET.fromstring(brut)
    out = []
    for m in (root.findall("Member") or list(root)):
        g = lambda t: (m.findtext(t) or "").strip()
        if g("FilingType") != FILING_TYPE_PTR:
            continue
        last, first = g("Last"), g("First")
        out.append({"doc_id": g("DocID"), "chamber": "house", "kind": "ptr",
                    "disclosure_date": _iso(g("FilingDate")),
                    "declarant_name": f"{first} {last}".strip(),
                    "last": last, "first": first, "state_district": g("StateDst")})
    return out


# ───────────────────────────────── Sénat ─────────────────────────────────
def observe_senate(days_back, session):
    """Interroge la recherche eFD sur une fenêtre glissante et rend les dépôts listés.

    ⚠️ La fenêtre porte sur la date de dépôt PORTÉE par le document, pas sur la mise en ligne.
    Une fenêtre courte raterait un document publié aujourd'hui mais daté d'il y a trois semaines —
    c'est-à-dire exactement le décalage qu'on cherche à mesurer. D'où les 90 jours par défaut.
    """
    from senate.efd_session import accept_agreement, search_filings
    if not accept_agreement(session):
        raise RuntimeError("Agrément eFD incertain — arrêt propre.")
    fin = datetime.now(timezone.utc).date()
    debut = fin - timedelta(days=days_back)
    lignes = search_filings(session, debut.strftime("%m/%d/%Y"), fin.strftime("%m/%d/%Y"),
                            filter_dates=False)
    return [{"doc_id": r["report_uuid"], "chamber": "senate", "kind": r.get("kind") or "",
             "disclosure_date": _iso(r.get("disclosure_date")),
             "declarant_name": r.get("declarant_name", "")}
            for r in lignes if r.get("report_uuid")]


# ───────────────────────────────── amorçage ─────────────────────────────────
def backfill_observations():
    """Tout ce qu'on connaît DÉJÀ, lu sur disque, sans réseau.

    Ces lignes sont marquées `source='backfill'` et doivent être EXCLUES de toute statistique sur
    l'écart `first_seen_at − disclosure_date` : leur `first_seen_at` est la date de l'amorçage, pas
    une vraie primo-observation. Elles servent uniquement à ce que le premier crawl ne signale pas
    des milliers de fausses nouveautés.
    """
    out = []
    for xml_path in sorted(HOUSE_INDEX_DIR.glob("*FD.xml")):
        root = ET.fromstring(xml_path.read_bytes())
        for m in (root.findall("Member") or list(root)):
            g = lambda t: (m.findtext(t) or "").strip()
            if g("FilingType") != FILING_TYPE_PTR:
                continue
            out.append({"doc_id": g("DocID"), "chamber": "house", "kind": "ptr",
                        "disclosure_date": _iso(g("FilingDate")),
                        "declarant_name": f'{g("First")} {g("Last")}'.strip()})
    # Sénat : la source primaire embarquée est le cache des pages eFD, un fichier par dépôt.
    for html in sorted(SENATE_REPORTS.glob("*.html")):
        out.append({"doc_id": html.stem, "chamber": "senate", "kind": "",
                    "disclosure_date": ""})
    return out


# ───────────────────────────────── orchestration ─────────────────────────────────
def crawl(years, days_back, dry_run=False, snapshot=True):
    """Un passage : House (une requête par année) + Sénat (une recherche). Les deux chambres sont
    indépendantes — une panne d'un côté ne doit pas faire perdre l'observation de l'autre."""
    run_id, session = _run_id(), requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    observations, erreurs = [], []

    for y in years:
        try:
            obs = observe_house(y, session, save_snapshot=snapshot and not dry_run)
            observations += obs
            print(f"  house {y} : {len(obs)} PTR listés à l'index")
        except Exception as e:
            erreurs.append(f"house {y}: {e}")
            print(f"  ⚠ house {y} : {e}")
        time.sleep(1.0)

    try:
        obs = observe_senate(days_back, session)
        observations += obs
        print(f"  senate : {len(obs)} dépôts listés sur {days_back} j glissants")
    except Exception as e:
        erreurs.append(f"senate: {e}")
        print(f"  ⚠ senate : {e}")

    if erreurs and not observations:
        # Les deux chambres sont tombées : rien à écrire, et l'échec doit être visible en CI.
        raise RuntimeError("aucune chambre n'a répondu — " + " | ".join(erreurs))

    # Grave la date de démarrage AVANT le premier enregistrement : tout ce qui est déjà en ligne
    # ce jour-là est du rattrapage, et le sera pour toujours. (Un dry-run ne la consomme pas.)
    if not dry_run:
        _init_meta(_today())
    nouvelles = record(observations, run_id, dry_run=dry_run)
    return nouvelles, erreurs


def main():
    ap = argparse.ArgumentParser(description="Crawl d'horodatage : écrit first_seen_at.")
    ap.add_argument("--years", default=str(date.today().year),
                    help="années House à interroger (ex: 2026 ou 2025,2026). Défaut : année courante")
    ap.add_argument("--days-back", type=int, default=90,
                    help="fenêtre glissante Sénat, en jours (défaut 90 — voir observe_senate)")
    ap.add_argument("--backfill", action="store_true",
                    help="amorçage : inscrit tout le connu depuis le disque, marqué `backfill`")
    ap.add_argument("--no-snapshot", action="store_true",
                    help="n'archive pas l'index du jour dans data/house/index/daily/ "
                         "(à utiliser en CI : 423 Ko/jour versionnés seraient intenables)")
    ap.add_argument("--dry-run", action="store_true", help="montre sans écrire")
    args = ap.parse_args()

    if args.backfill:
        print("Amorçage (hors réseau) — lecture des index et des pages eFD embarqués…")
        obs = backfill_observations()
        nouvelles = record(obs, _run_id(), source="backfill", dry_run=args.dry_run)
        print(f"→ {len(obs)} documents connus | {len(nouvelles)} inscrits"
              + (" [DRY-RUN : rien écrit]" if args.dry_run else f" → {FIRST_SEEN_CSV}"))
        return

    annees = [int(x) for x in args.years.split(",") if x.strip()]
    print(f"Crawl d'horodatage — house {annees} | senate {args.days_back} j"
          + (" [DRY-RUN]" if args.dry_run else ""))
    nouvelles, erreurs = crawl(annees, args.days_back, dry_run=args.dry_run,
                               snapshot=not args.no_snapshot)

    vrais = [n for n in nouvelles if n["source"] == "crawl"]
    rattr = [n for n in nouvelles if n["source"] == "rattrapage"]
    print(f"\n→ {len(nouvelles)} document(s) vu(s) pour la première fois : "
          f"{len(vrais)} primo-observation(s) exploitable(s) + {len(rattr)} rattrapage(s)")
    if rattr:
        print("  (rattrapage = déposé avant le démarrage du crawl : déjà en ligne quand on l'a vu,"
              "\n   donc EXCLU de la distribution first_seen_at − disclosure_date)")
    for n in (vrais or nouvelles)[:20]:
        print(f"    {n['source']:10} {n['chamber']:7} {n['doc_id']:40} déposé {n['disclosure_date'] or '?'}")
    reste = len(vrais or nouvelles) - 20
    if reste > 0:
        print(f"    … et {reste} autres")
    if args.dry_run:
        print("(dry-run : rien écrit)")
    elif nouvelles:
        print(f"→ {FIRST_SEEN_CSV}")
    if erreurs:
        print("\n⚠ chambres en échec : " + " | ".join(erreurs))
        # Une chambre tombée n'annule pas l'écriture de l'autre, mais la CI doit le voir.
        sys.exit(2)


if __name__ == "__main__":
    main()
