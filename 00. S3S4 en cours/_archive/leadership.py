"""S3S4 / leadership — identifie les membres « puissants » (leadership de parti + chairs de commission).

Teste l'hypothèse de la littérature (Wei & Zhou NBER 2024 : +47 %/an pour les LEADERS, pas pour la base).
- **Leadership de parti** : champ `leadership_roles` (daté) des YAML congress-legislators → POINT-IN-TIME
  (un achat ne compte « leader » que s'il tombe dans une période de mandat de leadership).
- **Chairs de commission** : `committee-membership-current.yaml` (title = Chair) → snapshot courant
  (approximation : pas de dates historiques).
Lecture seule des référentiels du dépôt.
"""
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
REF = REPO / "data" / "house" / "reference"


def load_leaders():
    """Renvoie (tenures, chairs) : tenures = {bioguide: [(start, end), ...]} (leadership de parti daté) ;
    chairs = set(bioguide) des chairs de commission courants."""
    tenures = {}
    for fn in ("legislators-current.yaml", "legislators-historical.yaml"):
        people = yaml.safe_load(open(REF / fn))
        for p in people:
            bio = p.get("id", {}).get("bioguide")
            for lr in (p.get("leadership_roles") or []):
                s, e = lr.get("start"), lr.get("end")
                tenures.setdefault(bio, []).append(
                    (pd.Timestamp(s) if s else None, pd.Timestamp(e) if e else None))
    chairs = set()
    for ch in ("house", "senate"):
        mem = yaml.safe_load(open(REPO / "data" / ch / "reference" / "committee-membership-current.yaml"))
        for _code, members in mem.items():
            for m in members:
                t = str(m.get("title", "")).lower()
                if "chair" in t and "vice" not in t and "ranking" not in t and m.get("bioguide"):
                    chairs.add(m["bioguide"])
    return tenures, chairs


def leadership_mask(buys: pd.DataFrame, kind: str = "pit") -> pd.Series:
    """Masque sur les achats. kind:
       'pit'    = membre en leadership de parti À LA DATE de l'achat (point-in-time) ;
       'chairs' = membre chair de commission (snapshot courant) ;
       'any'    = union des deux."""
    tenures, chairs = load_leaders()

    def _pit(bio, d):
        for s, e in tenures.get(bio, []):
            if (s is None or d >= s) and (e is None or d <= e):
                return True
        return False

    if kind == "chairs":
        return buys["bioguide"].isin(chairs)
    pit = pd.Series([_pit(b, d) for b, d in zip(buys["bioguide"], buys["filed"])], index=buys.index)
    if kind == "any":
        return pit | buys["bioguide"].isin(chairs)
    return pit


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE))
    import data
    b = data.buy_signals(data.load_transactions())
    tenures, chairs = load_leaders()
    print(f"membres avec leadership de parti (daté) : {len(tenures)} | chairs courants : {len(chairs)}")
    for kind in ("pit", "chairs", "any"):
        m = leadership_mask(b, kind)
        n_mem = b[m]["bioguide"].nunique()
        print(f"  {kind:7s} : {m.sum():,} achats ({m.mean()*100:.1f}%), {n_mem} membres".replace(",", " "))
