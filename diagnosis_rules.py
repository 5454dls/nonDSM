"""Rules that turn free-text discharge diagnoses into analysis groups.

family_of        first-listed diagnosis -> "SPR" (schizophrenia), "MDD" (major depressive disorder) or None
normalize        qualifier set of a diagnosis within a family (course, specifiers)
stage_of         a single stage label, or None when none or several match
classify_dx_group  first-listed diagnosis -> one of 8 diagnostic groups
comorbid_categories  diagnostic groups of the second- and third-listed diagnoses
"""
import re
import unicodedata

import pandas as pd

# ------------------------------------------------------------------ family
EXCLUDE_SPR = [
    "schizoaffective", "schizophreniform", "delusional disorder",
    "brief psychotic", "unspecified schizophrenia", "other specified schizophrenia",
    "unspecified psychotic", "other psychotic", "substance-induced psychotic",
    "substance induced psychotic", "psychotic disorder due to",
    "due to another medical condition",
]
EXCLUDE_MDD = [
    "persistent depressive", "dysthymi", "unspecified depressive",
    "other specified depressive", "depressive disorder nos", "depressive nos",
    "bipolar", "substance-induced depressive", "substance induced depressive",
    "depressive disorder due to", "due to another medical condition",
]
INCLUDE_SPR = ["schizophrenia"]
INCLUDE_MDD = ["major depressive"]


def _norm_text(s):
    t = unicodedata.normalize("NFKC", str(s)).lower()
    for d in (0x2013, 0x2014, 0x2010):                       # en dash, em dash, hyphen variants
        t = t.replace(chr(d), "-")
    return re.sub(r"\s+", " ", t).strip()


def family_of(dx):
    """Exclusion lists are checked first ("schizoaffective" contains "schizo")."""
    t = _norm_text(dx)
    if any(x in t for x in EXCLUDE_SPR) or any(x in t for x in EXCLUDE_MDD):
        return None
    if any(x in t for x in INCLUDE_SPR):
        return "SPR"
    if any(x in t for x in INCLUDE_MDD):
        return "MDD"
    return None


# ------------------------------------------------------------------ qualifiers
# (pattern, standard form); "multiple episode" means "multiple" in schizophrenia and "recurrent" in MDD
RULES = {
    "SPR": [
        (r"multiple episodic|multiple episodes?", "multiple"),
        (r"first episodes?", "first"),
        (r"currently in acute episode|acute episodes?|acute phase", "acute"),
        (r"continuous", "continuous"),
    ],
    "MDD": [
        (r"major depressive episode", "major depressive disorder"),
        (r"recurrent episodes?|recurrent|multiple episodes?", "recurrent"),
        (r"single episode|first episode", "single"),
        (r"atypical type|with atypical features", "with atypical features"),
        (r"with[- ]mood[- ]congruent", "with mood-congruent"),
        (r"psychotic features?", "psychotic features"),
        (r"anxious distress", "with anxious distress"),
        (r"melanchol\w*", "with melancholic features"),
    ],
}
NEGATED = {"psychotic features": "without psychotic features",
           "with good prognostic features": "without good prognostic features"}
_NEG = re.compile(r"(without|w/o|\bno\b|\bnot\b|\bnegative for\b)[\s,]{0,3}$")
SPR_STAGE = {"first": "first", "multiple": "multiple", "continuous": "continuous"}
MDD_STAGE = {"single": "single", "recurrent": "recurrent"}


def normalize(dx, family):
    """Standard forms found in a diagnosis; a form directly after a negation word is reported as negated."""
    t = _norm_text(dx)
    out = set()
    for pat, canon in RULES[family]:
        for m in re.finditer(pat, t):
            if _NEG.search(t[max(0, m.start() - 16):m.start()]):
                if canon in NEGATED:
                    out.add(NEGATED[canon])
                continue
            out.add(canon)
    return out


def stage_of(dx, family, stage_map):
    hit = normalize(dx, family) & set(stage_map)
    return stage_map[next(iter(hit))] if len(hit) == 1 else None


# ------------------------------------------------------------------ diagnostic group
BIPOLAR_KEYWORDS = ["bipolar", "manic", "mania", "hypomanic", "hypomania", "조증"]


def _boundary_regex(keywords):
    """ASCII keywords get word boundaries (re.ASCII, so a Roman numeral glued to "bipolar" still matches)."""
    ascii_kw = [k for k in keywords if k.isascii()]
    other_kw = [k for k in keywords if not k.isascii()]
    parts = [rf"\b{re.escape(k)}\b" for k in ascii_kw] + [re.escape(k) for k in other_kw]
    return re.compile("|".join(parts), re.I | re.ASCII)


BIPOLAR_RE = _boundary_regex(BIPOLAR_KEYWORDS)
DX_GROUPS = ["SCZ_spectrum", "Bipolar", "Depressive", "Anxiety",
             "Trauma_Stressor", "Somatic", "Sleep_Wake", "Other"]
_WITHOUT = re.compile(r",?\s*without[\s-]+(?:mood[- ]?(?:in)?congruent\s+)?psychotic\s+features?", re.I)
_WITH = re.compile(r",?\s*(?:with[\s-]+)?(?:mood[- ]?(?:in)?congruent\s+)?psychotic\s+features?", re.I)


def classify_dx_group(dx):
    """A psychotic-features specifier is removed first; the keyword groups are then tried in order."""
    dx = str(_WITH.sub("", _WITHOUT.sub("", str(dx)))).lower().strip()
    if any(k in dx for k in ["schizo", "schizoaff", "psychotic", "psychosis"]):
        return "SCZ_spectrum"
    if BIPOLAR_RE.search(dx):
        return "Bipolar"
    if any(k in dx for k in ["depress", "dysthym"]):
        return "Depressive"
    if any(k in dx for k in ["anxiety", "phobia", "panic", "agoraphobia", "gad"]):
        return "Anxiety"
    if any(k in dx for k in ["ptsd", "posttrauma", "stress", "adjustment"]):
        return "Trauma_Stressor"
    if any(k in dx for k in ["somatic", "somatoform", "conversion", "illness anxiety",
                             "hypochondr", "functional neurological"]):
        return "Somatic"
    if any(k in dx for k in ["insomnia", "sleep", "nightmare", "hypersomnolence"]):
        return "Sleep_Wake"
    return "Other"


def comorbid_categories(dx2, dx3):
    """Diagnostic groups of the second- and third-listed diagnoses (empty cells are skipped)."""
    return {classify_dx_group(d) for d in (dx2, dx3) if pd.notna(d) and str(d).strip()}
