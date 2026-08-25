#!/usr/bin/env python
"""Filet du run en direct (`common/live_run.py`) — format de sortie et ÉTANCHÉITÉ.

Ce que l'échec signifierait, selon l'invariant touché :
  · format — la ligne produite en direct ne serait plus celle que la recherche consomme : les 12
    champs garantis de la table de référence (deck des données, p. 31) sont un contrat, pas une
    convention interne ;
  · étanchéité — le run en direct aurait écrit dans `data/*/tables/`. Ces 368 tables sont
    verrouillées à l'octet par le golden ; un run quotidien qui les touche casse le filet tous les
    jours et rend le corpus non reproductible. C'est LA raison d'être de la voie parallèle ;
  · anti-look-ahead — `signal_date` ne serait plus le plus tardif de (disclosure_date,
    first_seen_at), donc on daterait un signal d'un moment où l'information n'était pas publique.

Le test s'exécute SANS RÉSEAU : il rejoue `ligne_p31` sur des lignes tirées du corpus figé, au lieu
d'aller chercher de nouveaux dépôts.

Usage : python tests/regression/test_live_run.py
"""
import hashlib
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from common import live_run as lr  # noqa: E402


def _empreintes():
    """sha256 de chaque table figée — l'état que le run en direct ne doit jamais changer."""
    return {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((REPO / "data").glob("*/tables/**/*.csv"))}


def main():
    ecarts = []

    # ── un échantillon du corpus figé, remis dans la forme d'entrée de ligne_p31 ──
    src = REPO / "data" / "house" / "tables" / "2024" / "06_house_2024_FINAL.csv"
    if not src.exists():
        print(f"❌ {src} absent")
        sys.exit(1)
    ech = pd.read_csv(src, dtype=str).head(200).copy()
    ech["first_seen_at"] = "2026-08-25"        # postérieur à la divulgation : force le max
    ech["op"] = None

    avant = _empreintes()
    out = lr.ligne_p31(ech)
    apres = _empreintes()

    # 1 · le contrat de colonnes
    if list(out.columns) != lr.COLONNES:
        ecarts.append(f"colonnes {list(out.columns)} ≠ contrat {lr.COLONNES}")
    manquants = [c for c in lr.CHAMPS_P31 if c not in out.columns]
    if manquants:
        ecarts.append(f"champs de la table de référence absents : {manquants}")

    # 2 · étanchéité — aucune table figée touchée, aucune créée
    modifies = [k for k, v in avant.items() if apres.get(k) != v]
    nouveaux = sorted(set(apres) - set(avant))
    if modifies:
        ecarts.append(f"{len(modifies)} table(s) figée(s) MODIFIÉE(S) — ex. {modifies[:3]}")
    if nouveaux:
        ecarts.append(f"{len(nouveaux)} table(s) créée(s) dans data/*/tables/ — ex. {nouveaux[:3]}")

    # 3 · anti-look-ahead : signal_date = max(disclosure_date, first_seen_at), jamais la transaction
    sd = pd.to_datetime(out["signal_date"], errors="coerce")
    dd = pd.to_datetime(out["disclosure_date"], errors="coerce")
    td = pd.to_datetime(out["transaction_date"], errors="coerce")
    fs = pd.to_datetime(out["first_seen_at"], errors="coerce")
    attendu = pd.concat([dd, fs], axis=1).max(axis=1)
    faux = int((sd.notna() & attendu.notna() & (sd != attendu)).sum())
    if faux:
        ecarts.append(f"{faux} signal_date ≠ max(disclosure_date, first_seen_at)")
    avant_txn = int((sd.notna() & td.notna() & (sd < td)).sum())
    if avant_txn:
        ecarts.append(f"{avant_txn} signal_date ANTÉRIEURE à la transaction — look-ahead")

    # 4 · la sortie est exploitable : un sens, un montant, une date de signal
    if len(out):
        sans_sens = int((~out["direction"].isin(["buy", "sell", "exchange", "other"])).sum())
        if sans_sens:
            ecarts.append(f"{sans_sens} lignes sans direction reconnue")

    print(f"{len(out)} lignes rejouées | {len(avant)} tables figées surveillées")
    print(f"colonnes : {len(out.columns)} ({len(lr.CHAMPS_P31)} champs de référence "
          f"+ {len(lr.CHAMPS_TRACE)} de traçabilité)")
    print(f"tables modifiées : {len(modifies)} | créées : {len(nouveaux)}")

    for e in ecarts:
        print(f"  ❌ {e}")
    ok = not ecarts
    print("\nRÉSULTAT :", "✅ ZÉRO ÉCART — format conforme, tables figées intactes"
          if ok else f"❌ {len(ecarts)} invariant(s) violé(s)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
