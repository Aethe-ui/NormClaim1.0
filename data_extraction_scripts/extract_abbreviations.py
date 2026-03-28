import re
from collections import Counter, defaultdict
from typing import Dict

from common import BACKEND_DATA_DIR, iter_dataset_texts, load_json, normalize_spacing, save_sorted_json


ABBREV_MAP_PATH = BACKEND_DATA_DIR / "abbrev_map.json"

# Conservative clinical abbreviations frequently present in discharge summaries.
MANUAL_ADDITIONS: Dict[str, str] = {
    "DOA": "date of admission",
    "DOD": "date of discharge",
    "DOB": "date of birth",
    "IPD": "in-patient department",
    "OPD": "out-patient department",
    "HPI": "history of present illness",
    "HOPI": "history of present illness",
    "PMA": "post-menstrual age",
    "AGA": "appropriate for gestational age",
    "LBW": "low birth weight",
    "LSCS": "lower segment cesarean section",
    "I/V/O": "in view of",
    "S/B": "seen by",
    "S/O": "son of",
    "D/O": "daughter of",
    "W/O": "wife of",
    "CRP": "C-reactive protein",
    "TLC": "total leukocyte count",
    "DLC": "differential leukocyte count",
    "RBC": "red blood cell count",
    "WBC": "white blood cell count",
    "HCT": "hematocrit",
    "MCV": "mean corpuscular volume",
    "MCH": "mean corpuscular hemoglobin",
    "MCHC": "mean corpuscular hemoglobin concentration",
    "RDW": "red cell distribution width",
    "PBS": "peripheral blood smear",
    "ANC": "absolute neutrophil count",
    "ALC": "absolute lymphocyte count",
    "ABHA": "Ayushman Bharat Health Account",
    "NICU": "neonatal intensive care unit",
    "MR": "mitral regurgitation",
    "MS": "mitral stenosis",
    "PAH": "pulmonary arterial hypertension",
    "WNL": "within normal limits",
    "PH": "potential of hydrogen",
    "PT-INR": "prothrombin time - international normalized ratio",
    "R/M": "routine and microscopy",
    "FNAC": "fine needle aspiration cytology",
    "LDH": "lactate dehydrogenase",
    "ELISA": "enzyme-linked immunosorbent assay",
    "CBNAAT": "cartridge based nucleic acid amplification test",
}

PAREN_RE = re.compile(r"([A-Za-z][A-Za-z\s\-/]{3,80}?)\s*\(([A-Za-z][A-Za-z0-9/\.-]{1,11})\)")

STOP_ABBR = {
    "THE",
    "AND",
    "FOR",
    "WITH",
    "FROM",
    "WAS",
    "ARE",
    "THIS",
    "THAT",
    "DAY",
    "ROOM",
    "UNIT",
    "PAGE",
    "NAME",
    "TYPE",
    "DATE",
    "NO",
    "YR",
    "LOW",
    "MEDIUM",
    "QUERY",
    "RANGE",
    "UNIT",
    "TEST",
    "METHOD",
}

ALLOW_LONG_ALPHA = {
    "ELISA",
    "CBNAAT",
    "CEPHEID",
}


def _looks_like_abbreviation(token: str) -> bool:
    if len(token) < 2:
        return False
    upper = token.upper()
    if upper in STOP_ABBR:
        return False
    if token.isdigit():
        return False
    if any(ch.isdigit() for ch in token):
        return False
    has_symbol = any(ch in token for ch in "/.-")
    alpha = sum(ch.isalpha() for ch in token)
    upper_alpha = sum(ch.isupper() for ch in token if ch.isalpha())
    if has_symbol:
        return True
    if token in ALLOW_LONG_ALPHA:
        return True
    return alpha >= 2 and upper_alpha == alpha and len(token) <= 5


def _normalize_abbr(token: str) -> str:
    token = token.strip().strip(".,:;()[]{}")
    if token.lower() in {"tab", "cap", "inj", "syp", "syr"}:
        return token.capitalize() + "."
    return token.upper()


def _normalize_long_form(text: str) -> str:
    cleaned = normalize_spacing(text).strip(" -:;,.()")
    return cleaned.lower()


def _long_form_quality_ok(long_form: str, abbr: str) -> bool:
    if len(long_form) < 5:
        return False
    words = [w for w in re.split(r"\s+", long_form) if w]
    if len(words) < 2 or len(words) > 10:
        return False
    if any(len(w) > 25 for w in words):
        return False
    if long_form == abbr.lower():
        return False
    if re.search(r"\d{4,}", long_form):
        return False
    return True


def build_abbreviation_map() -> Dict[str, str]:
    result = load_json(ABBREV_MAP_PATH)
    result.update(MANUAL_ADDITIONS)

    long_form_votes: defaultdict[str, Counter[str]] = defaultdict(Counter)

    for _, text in iter_dataset_texts():
        for long_form, abbr in PAREN_RE.findall(text):
            abbr_norm = _normalize_abbr(abbr)
            if not _looks_like_abbreviation(abbr_norm):
                continue
            lf_norm = _normalize_long_form(long_form)
            if not _long_form_quality_ok(lf_norm, abbr_norm):
                continue
            long_form_votes[abbr_norm][lf_norm] += 1

    for abbr, candidates in long_form_votes.items():
        best_long_form, votes = candidates.most_common(1)[0]
        if votes >= 2:
            result.setdefault(abbr, best_long_form)

    return result


def main() -> None:
    updated = build_abbreviation_map()
    save_sorted_json(ABBREV_MAP_PATH, updated)
    print(f"Saved {len(updated)} abbreviations to {ABBREV_MAP_PATH}")


if __name__ == "__main__":
    main()
