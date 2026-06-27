"""Identité House — matcher bioguide (nom → identifiant officiel du membre).

Cascade House portée VERBATIM (`house_multiyear.match_bioguide`, cf. tests/regression/test_identity.py) :
override manuel → correspondance exacte (last, first/surnom/middle/nom composé) → repli par nom de
famille unique. Le référentiel partagé (chargement, normalisation, classe `Reference`) vit dans
`congress_core.reference` ; le Sénat a son propre matcher (`senate.identity`).
"""
import re

from congress_core.reference import norm, Reference

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
