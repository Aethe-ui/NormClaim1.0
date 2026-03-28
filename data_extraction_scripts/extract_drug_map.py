import re
from collections import Counter
from typing import Dict

from common import BACKEND_DATA_DIR, iter_dataset_texts, load_json, save_sorted_json, title_keep_caps


DRUG_MAP_PATH = BACKEND_DATA_DIR / "drug_map.json"

MANUAL_DRUG_NORMALIZATION: Dict[str, str] = {
    "PCM": "Paracetamol",
    "PANTOP": "Pantoprazole",
    "PANT": "Pantoprazole",
    "ONDEN": "Ondansetron",
    "ONDEM": "Ondansetron",
    "ONDAN": "Ondansetron",
    "ONDANSETRON": "Ondansetron",
    "METRO": "Metronidazole",
    "METROGYL": "Metronidazole",
    "AMOXYCLAV": "Amoxicillin+Clavulanate",
    "AUGMENTIN": "Amoxicillin+Clavulanate",
    "CEFUROXIME": "Cefuroxime",
    "CEFIXIME": "Cefixime",
    "CEFTRIAXONE": "Ceftriaxone",
    "PIPTAZ": "Piperacillin+Tazobactam",
    "AMIKACIN": "Amikacin",
    "TRAMADOL": "Tramadol",
    "ASPIRIN": "Aspirin",
    "ECOSPORIN": "Aspirin",
    "TELMESARTAN": "Telmisartan",
    "LOSARTAN": "Losartan",
    "ATORVASTATIN": "Atorvastatin",
    "ATORVAS": "Atorvastatin",
    "PROPRANOLOL": "Propranolol",
    "PROPANOLOL": "Propranolol",
    "FUROPED": "Furosemide",
    "FUROPAD": "Furosemide",
    "DICLO": "Diclofenac",
    "DICLOFENAC": "Diclofenac",
    "GLARGINE": "Insulin glargine",
    "REGULAR": "Regular insulin",
    "GLIMEPRIDE": "Glimepiride",
    "THYROXINE": "Levothyroxine",
    "ALPRAX": "Alprazolam",
    "LEVIPIL": "Levetiracetam",
    "HALOPERIDOL": "Haloperidol",
    "HALOPERIDOLE": "Haloperidol",
    "ZOLPIDEM": "Zolpidem",
    "ITRACONAZOLE": "Itraconazole",
    "GEFITINIB": "Gefitinib",
    "GEFITINB": "Gefitinib",
    "ZOLEDRONIC": "Zoledronic acid",
    "DEXAMETHASONE": "Dexamethasone",
    "DEXA": "Dexamethasone",
    "GABAPENTIN": "Gabapentin",
    "ETORICOXIB": "Etoricoxib",
    "LIOFEN": "Baclofen",
    "SERRATIOPEPTIDASE": "Serratiopeptidase",
    "CELECOXIB": "Celecoxib",
    "PREGABALIN": "Pregabalin",
    "DOMPERIDONE": "Domperidone",
    "ALFOZUCIN": "Alfuzosin",
    "THIAMINE": "Thiamine",
    "ACITROM": "Acenocoumarol",
    "POTKLOR": "Potassium chloride",
    "KCL": "Potassium chloride",
    "MGSO4": "Magnesium sulfate",
    "WARFARIN": "Warfarin",
    "TRANEXAMIC": "Tranexamic acid",
    "NITROFURANTOIN": "Nitrofurantoin",
    "ELDERVIT": "Multivitamin",
    "ELDEERVIT": "Multivitamin",
    "ELDERVET": "Multivitamin",
    "FORACORTO": "Formoterol+Budesonide",
    "TAXTM": "Cefotaxime",
    "DUOLIN": "Ipratropium+Salbutamol",
}

FORM_RE = re.compile(
    r"\b(?:TAB(?:LET)?|CAP(?:SULE)?|INJ(?:ECTION)?|SYR(?:UP)?|SYP|DROPS?|IV|IM|PO|NEB)\b\s*[:\-]?\s*([A-Za-z][A-Za-z0-9\-]{2,})",
    re.IGNORECASE,
)

BAD_TOKENS = {
    "EVERY",
    "DAY",
    "DAYS",
    "WAS",
    "FORMED",
    "RELEASE",
    "CANAL",
    "ANTIBIOTICS",
    "ANTIEPILEPTICS",
    "FLUIDS",
    "SOS",
    "TDS",
}


def _normalize_token(token: str) -> str:
    return token.strip().strip(".,:;()[]{}").upper()


def _valid_token(token: str) -> bool:
    if len(token) < 3:
        return False
    if token in BAD_TOKENS:
        return False
    if token.isdigit():
        return False
    return True


def build_drug_map() -> Dict[str, str]:
    drug_map = load_json(DRUG_MAP_PATH)
    token_counts: Counter[str] = Counter()

    for _, text in iter_dataset_texts():
        for token in FORM_RE.findall(text):
            norm = _normalize_token(token)
            if _valid_token(norm):
                token_counts[norm] += 1

    # Merge curated normalization first.
    for token, generic in MANUAL_DRUG_NORMALIZATION.items():
        drug_map.setdefault(title_keep_caps(token), generic)

    # Add dataset-confirmed curated aliases only.
    for token, count in token_counts.items():
        if count < 1:
            continue
        if token not in MANUAL_DRUG_NORMALIZATION:
            continue
        pretty = title_keep_caps(token)
        if pretty in drug_map:
            continue
        generic = MANUAL_DRUG_NORMALIZATION[token]
        drug_map[pretty] = generic

    return drug_map


def main() -> None:
    updated = build_drug_map()
    save_sorted_json(DRUG_MAP_PATH, updated)
    print(f"Saved {len(updated)} drug map entries to {DRUG_MAP_PATH}")


if __name__ == "__main__":
    main()
