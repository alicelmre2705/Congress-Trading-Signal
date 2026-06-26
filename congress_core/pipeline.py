"""Pipeline end-to-end unifié — un seul point d'entrée pour produire les tables FINAL des 2 chambres.

Orchestre en séquence les modules existants (inchangés), via sous-processus :
  1. house.digital   PTR électroniques House  → 06_house_{y}_transactions.csv
  2. house.ocr       OCR scannés + fusion      → 06_house_{y}_FINAL.csv        [sauf --skip-ocr]
  3. senate.digital  eFD électroniques Sénat   → 06_senate_{y}_transactions.csv
  4. senate.ocr      PTR papier Sénat          → 06b_senate_{y}_ocr_*.csv      [sauf --skip-ocr]
  5. senate.fusion   fusion digital+OCR + enrichissement → 06_senate_{y}_FINAL.csv

Un run complet exige le réseau (scraping Clerk/eFD) et l'API Vision (OCR) : la commande livre
l'**orchestration** ; le coût vient des modules, pas d'ici. `--dry-run` imprime la séquence exacte
sans rien exécuter (vérification à coût nul).

Usage :
  python -m congress_core.pipeline --years 2020-2026
  python -m congress_core.pipeline --years 2024 --skip-ocr
  python -m congress_core.pipeline --years 2025,2026 --dry-run
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_years(spec: str):
    """Accepte « 2020-2026 » (intervalle), « 2025,2026 » (liste) ou « 2024 » (unique)."""
    spec = spec.strip()
    if "-" in spec and "," not in spec:
        a, b = spec.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in spec.split(",") if x.strip()]


def build_steps(years_csv, skip_ocr, force, no_quiver, senate_ocr_mode):
    """Construit la séquence (label, args-module) selon les options. Modules inchangés."""
    steps = []
    hq = ["--no-quiver"] if no_quiver else []
    steps.append(("House — PTR électroniques", ["house.digital", "--years", years_csv] + hq))
    if not skip_ocr:
        steps.append(("House — OCR + fusion FINAL",
                      ["house.ocr", "--years", years_csv] + (["--force"] if force else []) + hq))
    steps.append(("Sénat — eFD électroniques", ["senate.digital", "--years", years_csv]))
    if not skip_ocr:
        steps.append(("Sénat — OCR papier",
                      ["senate.ocr", "--mode", senate_ocr_mode, "--years", years_csv]
                      + (["--force"] if force else [])))
    steps.append(("Sénat — fusion FINAL", ["senate.fusion"]))
    # Post-FINAL (offline, gratuit, idempotent) : métadonnée « années en poste » sur les 2 chambres.
    steps.append(("Enrichissement — années en poste", ["congress_core.enrich_tenure"]))
    return steps


def main():
    ap = argparse.ArgumentParser(description="Pipeline end-to-end unifié House + Sénat.")
    ap.add_argument("--years", default="2020-2026", help="ex: 2020-2026 ou 2024 ou 2025,2026")
    ap.add_argument("--skip-ocr", action="store_true", help="ignore l'OCR (House/Sénat) → digital seul")
    ap.add_argument("--force", action="store_true", help="force le re-OCR (ignore le cache)")
    ap.add_argument("--no-quiver", action="store_true", help="désactive la validation Quiver (House)")
    ap.add_argument("--senate-ocr-mode", choices=["index", "pilote", "full"], default="full",
                    help="mode du moteur OCR Sénat (défaut: full)")
    ap.add_argument("--dry-run", action="store_true", help="imprime la séquence sans exécuter")
    args = ap.parse_args()

    years_csv = ",".join(str(y) for y in parse_years(args.years))
    steps = build_steps(years_csv, args.skip_ocr, args.force, args.no_quiver, args.senate_ocr_mode)

    banner = f"Pipeline unifié — années {years_csv} — {len(steps)} étapes"
    print(banner + (" [DRY-RUN]" if args.dry_run else ""))
    for i, (label, mod_args) in enumerate(steps, 1):
        cmd = [sys.executable, "-m"] + mod_args
        print(f"\n[{i}/{len(steps)}] {label}\n    $ {' '.join(cmd)}")
        if args.dry_run:
            continue
        r = subprocess.run(cmd, cwd=REPO_ROOT)
        if r.returncode != 0:
            print(f"!! Échec à l'étape {i} ({label}) — code {r.returncode}. Arrêt.")
            sys.exit(r.returncode)
    print("\n(dry-run : rien exécuté)" if args.dry_run else "\nTerminé.")


if __name__ == "__main__":
    main()
