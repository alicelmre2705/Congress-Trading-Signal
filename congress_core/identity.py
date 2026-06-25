"""★ Identité — Doc ID → législateur (bioguide). Priorité #1 du projet, partagée House/Sénat.

Réunit en UNE source : normalisation de noms (`strip_accents`/`norm`), chargement du référentiel
(legislators + commissions, live avec repli YAML), et résolution de bioguide. Le matcher House
(`match_bioguide(last, first)`, cascade exacte→nom→surnom→override) est porté VERBATIM ; le
contrat Sénat (chaîne déclarant → `split_name`) est offert en variante. `chamber_priority=None`
par défaut → comportement House préservé à l'identique (cf. test de reproduction des bioguides).
"""
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd


# ───────────────────────── Normalisation de noms (identique aux 2 chambres) ──────────────────
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))


def norm(s: str) -> str:
    s = strip_accents(s or "").lower()
    s = re.sub(r"[^a-z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# Surnoms / suffixes / overrides (copie VERBATIM de house_multiyear) ───────────────────────────
_TITLE_RE = re.compile(r"\b(dr|hon|rev|gen|col)\b\.?\s*", re.IGNORECASE)
_NICKNAMES = {
    "richard": "rick", "william": "bill", "james": "jim", "robert": "bob",
    "michael": "mike", "joseph": "joe", "thomas": "tom", "charles": "chuck",
    "edward": "ed", "daniel": "dan", "donald": "don", "timothy": "tim",
    "christopher": "chris", "steven": "steve", "stephen": "steve", "benjamin": "ben",
    "kenneth": "ken", "anthony": "tony", "matthew": "matt", "gregory": "greg",
    "gerald": "jerry", "lawrence": "larry", "patrick": "pat", "samuel": "sam",
    "alexander": "alex", "andrew": "andy", "nathaniel": "nate", "theodore": "ted",
    "jacob": "jake", "jonathan": "jon", "elizabeth": "lizzie",
}
_SUFFIX_TOKENS = {"jr", "sr", "ii", "iii", "iv", "md", "dds", "phd", "facs", "do", "esq", "mr", "mrs", "ms"}
_MANUAL_BIO = {("taylor", "nicholas"): "T000479"}  # « Nicholas V. Taylor » = Van Taylor

# Commissions clés par chambre (paramètre, jamais une liste unique figée).
KEY_COMMITTEES_HOUSE = ["Financial Services", "Armed Services", "Intelligence"]
KEY_COMMITTEES_SENATE = ["Finance", "Armed Services", "Intelligence", "Banking"]

# URLs live (repli sur YAML embarqué).
_LEG_CURRENT = "https://unitedstates.github.io/congress-legislators/legislators-current.json"
_LEG_HISTORICAL = "https://unitedstates.github.io/congress-legislators/legislators-historical.json"
_COMMITTEES = "https://unitedstates.github.io/congress-legislators/committees-current.json"
_COMMITTEE_MEMBERSHIP = "https://unitedstates.github.io/congress-legislators/committee-membership-current.json"

SUFFIX = {"jr", "sr", "ii", "iii", "iv", "v"}


def split_name(declarant):
    """« First [Middle…] Last[, Suffix] » → (last, first, [middle]). Contrat Sénat (chaîne déclarant)."""
    s = (declarant or "").split(",")[0]
    toks = [t for t in re.split(r"\s+", s.strip()) if t and norm(t) not in SUFFIX]
    if not toks:
        return "", "", []
    return toks[-1], toks[0], [norm(t) for t in toks[:-1]]


class Reference:
    """Référentiel des législateurs : universe (DataFrame indexé bioguide), index de noms, commissions.
    `name_exact` (last,first/nick/middle)→bioguide ; `name_by_last` last→[bioguide] ; `key_bios` =
    membres de commissions clés (calcul par chambre)."""

    def __init__(self, ref_universe, name_exact, name_by_last, bio_to_committees,
                 key_bios, current_bios, source):
        self.ref_universe = ref_universe
        self.name_exact = name_exact
        self.name_by_last = name_by_last
        self.bio_to_committees = bio_to_committees
        self.key_bios = key_bios
        self.current_bios = current_bios
        self.source = source

    def party(self, bio):
        return self.ref_universe["party"].get(bio) if bio in self.ref_universe.index else None

    def committees(self, bio):
        return "; ".join(sorted(self.bio_to_committees.get(bio, []))) if bio else ""

    def is_key_committee(self, bio):
        return bool(bio in self.key_bios) if bio else False


def _last_term_key(p):
    terms = p.get("terms") or [{}]
    end = (terms[-1] if terms else {}).get("end", "")
    if not end:
        return -9999
    try:
        return -int(str(end)[:4])
    except ValueError:
        return 0


def _load_people(reference_dir, live=True):
    """current + historical : live d'abord, repli YAML embarqué. Copie de house_multiyear._load_people."""
    if live:
        try:
            import requests
            sess = requests.Session()
            sess.headers.update({"User-Agent": "congress-trading-research/1.0 (poli, sans evasion)"})
            cur = sess.get(_LEG_CURRENT, timeout=30).json()
            try:
                hist = sess.get(_LEG_HISTORICAL, timeout=60).json()
            except Exception:
                hist = []
            return cur, hist, "live"
        except Exception as e:
            live_err = e
    import yaml
    cur = yaml.safe_load(open(Path(reference_dir) / "legislators-current.yaml"))
    try:
        hist = yaml.safe_load(open(Path(reference_dir) / "legislators-historical.yaml"))
    except Exception:
        hist = []
    return cur, hist, f"local-yaml{'' if live else ' (forcé)'}"


def _load_committees(reference_dir, live=True):
    if live:
        try:
            import requests
            sess = requests.Session()
            committees = sess.get(_COMMITTEES, timeout=30).json()
            membership = sess.get(_COMMITTEE_MEMBERSHIP, timeout=30).json()
            return committees, membership
        except Exception:
            pass
    import yaml
    committees = yaml.safe_load(open(Path(reference_dir) / "committees-current.yaml"))
    membership = yaml.safe_load(open(Path(reference_dir) / "committee-membership-current.yaml"))
    return committees, membership


def load_reference(reference_dir, key_committees=None, chamber="house", live=True) -> Reference:
    """Construit le référentiel. Porte VERBATIM house_multiyear.build_reference (mêmes variantes de
    noms : surnom, middle, full_first, nom composé). `key_committees` par chambre."""
    if key_committees is None:
        key_committees = KEY_COMMITTEES_HOUSE if chamber == "house" else KEY_COMMITTEES_SENATE
    cur, hist, src = _load_people(reference_dir, live=live)
    people = sorted(cur + hist, key=_last_term_key)
    current_bios = {p.get("id", {}).get("bioguide") for p in cur if p.get("id", {}).get("bioguide")}

    ref_rows, name_exact, name_by_last = [], {}, defaultdict(list)
    for p in people:
        bio = p.get("id", {}).get("bioguide")
        if not bio:
            continue
        nm = p.get("name", {})
        last, first = nm.get("last", ""), nm.get("first", "")
        nick, mid = nm.get("nickname", ""), nm.get("middle", "")
        full = nm.get("official_full") or f"{first} {last}".strip()
        last_term = (p.get("terms") or [{}])[-1]
        ch = "house" if last_term.get("type") == "rep" else "senate"
        ref_rows.append({"bioguide_id": bio, "declarant_name": full, "last": last, "first": first,
                         "party": last_term.get("party"), "chamber": ch,
                         "state": last_term.get("state"), "district": last_term.get("district")})
        name_exact.setdefault((norm(last), norm(first)), bio)
        if nick:
            name_exact.setdefault((norm(last), norm(nick)), bio)
        if mid:
            name_exact.setdefault((norm(last), norm(mid)), bio)
        full_first = full.split()[0] if full.split() else ""
        if full_first and norm(full_first) != norm(first):
            name_exact.setdefault((norm(last), norm(full_first)), bio)
        name_by_last[norm(last)].append(bio)
        if " " in last:
            lw = last.split()[-1]
            name_exact.setdefault((norm(lw), norm(first)), bio)
            if mid:
                name_exact.setdefault((norm(lw), norm(mid)), bio)
            if full_first and norm(full_first) != norm(first):
                name_exact.setdefault((norm(lw), norm(full_first)), bio)
            name_by_last[norm(lw)].append(bio)

    ref_universe = pd.DataFrame(ref_rows).drop_duplicates("bioguide_id").set_index("bioguide_id")

    committees, membership = _load_committees(reference_dir, live=live)
    code_to_name = {c["thomas_id"]: c["name"] for c in committees if "thomas_id" in c}
    bio_to_committees = defaultdict(set)
    for code, members in membership.items():
        cname = code_to_name.get(code, code)
        for mem in members:
            if mem.get("bioguide"):
                bio_to_committees[mem["bioguide"]].add(cname)

    def _key_cat(bio):
        cs = bio_to_committees.get(bio, set())
        return any(any(k in cn for k in key_committees) for cn in cs)

    in_chamber = ref_universe[ref_universe["chamber"] == chamber]
    key_bios = {b for b in in_chamber.index if _key_cat(b)}

    return Reference(ref_universe, name_exact, name_by_last, bio_to_committees,
                     key_bios, current_bios, src)


def make_matcher(ref: Reference, chamber_priority=None):
    """Renvoie `match(last, first) → bioguide|None`. Algorithme House porté VERBATIM
    (house_multiyear.match_bioguide). `chamber_priority` réservé au Sénat (désambiguïsation par
    chambre/titulaire) ; None → comportement House inchangé."""
    name_exact, name_by_last = ref.name_exact, ref.name_by_last

    def match(last, first):
        first_clean = re.sub(r"\s+", " ", _TITLE_RE.sub(" ", first or "")).strip()
        raw = re.sub(r"[.,]", " ", (last or "")).split()
        last_words = [w for w in raw if norm(w) and norm(w) not in _SUFFIX_TOKENS]
        last_cands = []
        for w in last_words + ([" ".join(last_words)] if len(last_words) > 1 else []):
            ln = norm(w)
            if ln and ln not in last_cands:
                last_cands.append(ln)
        fn0 = norm(first_clean.split()[0]) if first_clean.split() else ""
        for lw in last_cands:
            if (lw, fn0) in _MANUAL_BIO:
                return _MANUAL_BIO[(lw, fn0)]
        seen, keys = set(), []
        for l_n in last_cands:
            for f_str in ([first_clean] + (first_clean.split() if " " in first_clean else [])):
                f_n = norm(f_str)
                nick = _NICKNAMES.get(f_n)
                for candidate in ([nick] if nick else []) + [f_n]:
                    k = (l_n, candidate)
                    if k not in seen:
                        seen.add(k)
                        keys.append(k)
        for k in keys:
            if k in name_exact:
                return name_exact[k]
        for lw in last_cands:
            cands = name_by_last.get(lw, [])
            if len(cands) == 1:
                return cands[0]
        return None

    return match


def enrich_identity(df, ref: Reference, matcher, chamber, last_col="last", first_col="first"):
    """Bloc d'enrichissement identité partagé (bioguide + party + committees + key_flag).
    `matcher` prend (last, first). Si les colonnes last/first manquent, on dérive de declarant_name
    via split_name (contrat Sénat)."""
    df = df.copy()
    if last_col in df.columns and first_col in df.columns:
        df["bioguide_id"] = df.apply(lambda r: matcher(r[last_col], r[first_col]), axis=1)
    else:
        def _m(name):
            last, first, _ = split_name(name)
            return matcher(last, first)
        df["bioguide_id"] = df["declarant_name"].map(_m)
    df["chamber"] = chamber
    df["party"] = df["bioguide_id"].map(ref.party)
    df["committee_membership"] = df["bioguide_id"].map(ref.committees)
    df["committees_key_flag"] = df["bioguide_id"].map(ref.is_key_committee)
    return df
