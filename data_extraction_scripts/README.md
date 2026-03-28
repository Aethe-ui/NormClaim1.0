# Data Extraction Scripts

This directory contains scripts that extract and normalize data assets from PDFs in `DataSet/`.

## Scripts

- `common.py`: shared dataset/PDF helpers and JSON read-write utilities.
- `extract_abbreviations.py`: builds an expanded abbreviation map using:
  - existing `backend/data/abbrev_map.json`
  - parenthetical expansions found in dataset text (for example, `Complete Blood Count (CBC)`)
  - curated clinical additions.
- `extract_drug_map.py`: builds an expanded drug map using:
  - existing `backend/data/drug_map.json`
  - medicine mentions found in the dataset near dosage/form tokens (`Tab`, `Inj`, `IV`, etc.)
  - curated normalization aliases.
- `build_maps.py`: runs both extraction flows and updates `backend/data/abbrev_map.json` and `backend/data/drug_map.json`.

## Run

From project root:

```bash
/Users/naitikkanha/Workspace/NormClaim/venv/bin/python data_extraction_scripts/build_maps.py
```
