from extract_abbreviations import build_abbreviation_map
from extract_drug_map import build_drug_map
from common import BACKEND_DATA_DIR, save_sorted_json


def main() -> None:
    abbrev_map = build_abbreviation_map()
    drug_map = build_drug_map()

    save_sorted_json(BACKEND_DATA_DIR / "abbrev_map.json", abbrev_map)
    save_sorted_json(BACKEND_DATA_DIR / "drug_map.json", drug_map)

    print(f"Updated abbreviations: {len(abbrev_map)}")
    print(f"Updated drug map entries: {len(drug_map)}")


if __name__ == "__main__":
    main()
