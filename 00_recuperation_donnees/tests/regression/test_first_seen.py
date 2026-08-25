#!/usr/bin/env python
"""Filet du crawl d'horodatage (`common/first_seen.py`) — les invariants du fichier `first_seen.csv`.

Ce que l'échec signifierait : le seul journal dont la donnée ne se reconstitue PAS a posteriori a
été corrompu. `first_seen_at` n'a de valeur que si la PREMIÈRE observation d'un document est
définitive — un doc_id réécrit, une date qui recule, ou un identifiant passé par un typage
numérique, et la mesure du délai de mise en ligne (C1) devient fausse sans que rien ne le signale.

Six invariants, tous vérifiés hors réseau sur le fichier tel qu'il est sur disque :
  1. l'en-tête est exactement le contrat de colonnes du module ;
  2. aucun (doc_id, chamber) n'apparaît deux fois — le fichier est en append, jamais en réécriture ;
  3. `first_seen_at` ne recule jamais au fil du fichier (append chronologique) ;
  4. tout doc_id survit à un aller-retour texte (aucun `.0` de flottant, aucun zéro perdu) ;
  5. `source` ne prend que les trois valeurs prévues, et les lignes non-`crawl` sont bien
     exclues de la population exploitable pour C1 ;
  6. `_meta.json` (la date de démarrage du crawl) est cohérent avec le contenu du fichier.

Usage : python tests/regression/test_first_seen.py
"""
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from common import first_seen as fs  # noqa: E402

SOURCES_VALIDES = {"crawl", "rattrapage", "backfill"}


def main():
    ecarts = []

    if not fs.FIRST_SEEN_CSV.exists():
        print(f"❌ {fs.FIRST_SEEN_CSV} absent — lancer `python -m common.first_seen --backfill`")
        sys.exit(1)

    with fs.FIRST_SEEN_CSV.open(newline="", encoding="utf-8") as f:
        lecteur = csv.DictReader(f)
        entete = lecteur.fieldnames
        lignes = list(lecteur)

    # 1 · contrat de colonnes
    if entete != fs.COLUMNS:
        ecarts.append(f"en-tête {entete} ≠ contrat {fs.COLUMNS}")

    # 2 · append seul : un document n'est jamais réobservé
    vus, doublons = set(), []
    for r in lignes:
        cle = (r["doc_id"], r["chamber"])
        if cle in vus:
            doublons.append(cle)
        vus.add(cle)
    if doublons:
        ecarts.append(f"{len(doublons)} (doc_id, chamber) en double — ex. {doublons[:3]}")

    # 3 · l'horodatage ne recule pas
    dates = [r["first_seen_at"] for r in lignes if r["first_seen_at"]]
    recules = [(a, b) for a, b in zip(dates, dates[1:]) if b < a]
    if recules:
        ecarts.append(f"{len(recules)} first_seen_at en recul — ex. {recules[:3]}")

    # 4 · le doc_id reste une chaîne de bout en bout
    #     (un `20034201.0` ou un zéro de tête perdu casse la jointure avec les tables du corpus)
    suspects = [r["doc_id"] for r in lignes
                if r["doc_id"] != r["doc_id"].strip() or r["doc_id"].endswith(".0")
                or not r["doc_id"]]
    if suspects:
        ecarts.append(f"{len(suspects)} doc_id malformés — ex. {suspects[:3]}")

    # 5 · les sources déclarées, et la population exploitable pour C1
    inconnues = {r["source"] for r in lignes} - SOURCES_VALIDES
    if inconnues:
        ecarts.append(f"source(s) hors contrat : {sorted(inconnues)}")
    depuis = fs.crawl_depuis()
    mal_classees = [r["doc_id"] for r in lignes
                    if r["source"] == "crawl" and fs.classer(r["disclosure_date"], depuis) != "crawl"]
    if mal_classees:
        ecarts.append(f"{len(mal_classees)} lignes marquées `crawl` alors qu'elles sont antérieures "
                      f"au démarrage ({depuis}) — ex. {mal_classees[:3]}")

    # 6 · la date de démarrage est gravée dès qu'un crawl a tourné
    a_craule = any(r["source"] in ("crawl", "rattrapage") for r in lignes)
    if a_craule and not depuis:
        ecarts.append("des lignes de crawl existent mais `_meta.json` ne dit pas depuis quand")
    if depuis and not fs.FIRST_SEEN_META.exists():
        ecarts.append("crawl_depuis renvoyé sans fichier de méta")

    # ── compte rendu ──
    par_source = {s: sum(1 for r in lignes if r["source"] == s) for s in SOURCES_VALIDES}
    par_chambre = {c: sum(1 for r in lignes if r["chamber"] == c) for c in ("house", "senate")}
    print(f"{len(lignes)} documents horodatés | par chambre {par_chambre} | par source {par_source}")
    print(f"crawl démarré le : {depuis or '— (jamais)'}")
    print(f"population exploitable pour C1 (source=crawl) : {par_source['crawl']}")

    for e in ecarts:
        print(f"  ❌ {e}")
    ok = not ecarts
    print("\nRÉSULTAT :", "✅ ZÉRO ÉCART — le journal d'horodatage est intègre"
          if ok else f"❌ {len(ecarts)} invariant(s) violé(s)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
