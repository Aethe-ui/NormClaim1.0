import io
import json
import re
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Tuple

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "DataSet"
BACKEND_DATA_DIR = ROOT / "backend" / "data"


def iter_pdf_paths(dataset_dir: Path = DATASET_DIR) -> Iterator[Path]:
    for path in sorted(dataset_dir.rglob("*.pdf")):
        if path.is_file():
            yield path


def extract_text_from_pdf_path(path: Path) -> str:
    try:
        file_bytes = path.read_bytes()
        text_parts: List[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts).strip()
    except Exception:
        return ""


def iter_dataset_texts() -> Iterator[Tuple[Path, str]]:
    for pdf_path in iter_pdf_paths():
        text = extract_text_from_pdf_path(pdf_path)
        if text:
            yield pdf_path, text


def normalize_spacing(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_json(path: Path) -> Dict[str, str]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {str(k): str(v) for k, v in data.items()}


def save_sorted_json(path: Path, mapping: Dict[str, str]) -> None:
    sorted_mapping = dict(sorted(mapping.items(), key=lambda kv: kv[0].lower()))
    with path.open("w", encoding="utf-8") as f:
        json.dump(sorted_mapping, f, ensure_ascii=False, indent=2)
        f.write("\n")


def title_keep_caps(text: str) -> str:
    words = []
    for token in text.split():
        if token.isupper() and len(token) <= 5:
            words.append(token)
        else:
            words.append(token.capitalize())
    return " ".join(words)


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
