"""Enrichissement post-FINAL : colonne `years_in_office` (ancienneté du déposant) — métadonnée Ramify S2.

Ajoute aux tables FINAL des deux chambres l'ancienneté en poste à la date de chaque transaction,
calculée OFFLINE depuis les `terms[].start` des YAML congress-legislators déjà embarqués (aucun
appel réseau ni API). C'est une passe POST-assemblage (les schémas d'assemblage restent inchangés) :
le pipeline unifié l'exécute en dernière étape.

Garanties :
  - **Préservation byte-à-byte** : la colonne est APPENDUE en fin de chaque ligne ; les octets
    existants (et la newline finale) sont laissés intacts → seul `years_in_office` apparaît au diff.
  - **Idempotent** : si la colonne existe déjà, le fichier est laissé tel quel.

Usage : python -m common.enrich_tenure
"""
from pathlib import Path

import pandas as pd

from common import reference
from common.schema import FINAL_POST_ENRICH

REPO = Path(__file__).resolve().parent.parent
YEARS = range(2020, 2027)
COLUMN = FINAL_POST_ENRICH[0]   # "years_in_office" — source unique du nom de colonne


def final_files(repo: Path):
    """Itère (chamber, year, path) sur les tables FINAL présentes (les deux sous data/{chambre}/tables/)."""
    for y in YEARS:
        p = repo / "data" / "house" / "tables" / str(y) / f"06_house_{y}_FINAL.csv"
        if p.exists():
            yield "house", y, p
    for y in YEARS:
        p = repo / "data" / "senate" / "tables" / str(y) / f"06_senate_{y}_FINAL.csv"
        if p.exists():
            yield "senate", y, p


def _fmt(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(int(v))


def enrich_file(path: Path, ref: reference.Reference) -> bool:
    """Append `years_in_office` à un FINAL, byte-préservant. Renvoie False si déjà enrichi."""
    raw = path.read_text(encoding="utf-8")
    ends_nl = raw.endswith("\n")
    body = raw[:-1] if ends_nl else raw
    lines = body.split("\n")
    header = lines[0]
    if COLUMN in header.split(","):
        return False
    df = pd.read_csv(path, dtype=str)
    n_data = len(lines) - 1
    if len(df) != n_data:
        raise ValueError(f"{path.name}: {len(df)} enregistrements vs {n_data} lignes physiques "
                         "(newline dans un champ ?) — append non sûr")
    vals = reference.add_years_in_office(df, ref)[COLUMN].tolist()
    new = [header + "," + COLUMN]
    for line, v in zip(lines[1:], vals):
        new.append(line + "," + _fmt(v))
    path.write_text("\n".join(new) + ("\n" if ends_nl else ""), encoding="utf-8")
    return True


def main():
    refs = {}
    n_done = n_skip = 0
    for chamber, year, path in final_files(REPO):
        if chamber not in refs:
            refs[chamber] = reference.load_reference(REPO / "data" / chamber / "reference",
                                                    chamber=chamber, live=False)
        changed = enrich_file(path, refs[chamber])
        if changed:
            cov = pd.read_csv(path, dtype=str)[COLUMN]
            pct = round(100 * cov.notna().sum() / len(cov), 1) if len(cov) else 0.0
            print(f"  ✅ {chamber} {year} : +{COLUMN} ({pct}% renseigné)")
            n_done += 1
        else:
            print(f"  ⏭  {chamber} {year} : déjà enrichi")
            n_skip += 1
    print(f"\n{n_done} enrichis, {n_skip} inchangés.")


if __name__ == "__main__":
    main()
