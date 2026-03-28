"""
NormClaim — Human Review Service
Persists reviewer corrections for extracted outputs.
"""

import re
from typing import Dict, Optional

from models.schemas import HumanReview, CorrectionItem
from services.persistence_service import insert_review

# In-memory fallback cache for local dev when Supabase is not configured.
REVIEWS: Dict[str, HumanReview] = {}


def save_review(review: HumanReview, supabase_client: Optional[object] = None) -> HumanReview:
    """Persist a human review to Supabase (or in-memory fallback)."""
    REVIEWS[review.document_id] = review

    if supabase_client is not None:
        insert_review(review, supabase_client)

    return review


def get_review(document_id: str, supabase_client: Optional[object] = None) -> Optional[HumanReview]:
    """Fetch latest human review for a document."""
    if supabase_client is not None:
        resp = (
            supabase_client.table("human_reviews")
            .select("document_id, reviewer_notes, corrections_json, reviewed_at")
            .eq("document_id", document_id)
            .order("reviewed_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if rows:
            row = rows[0]
            corrections = [CorrectionItem(**c) for c in (row.get("corrections_json") or [])]
            return HumanReview(
                document_id=row["document_id"],
                reviewer_notes=row.get("reviewer_notes", ""),
                corrections=corrections,
                reviewed_at=row.get("reviewed_at", ""),
            )

    return REVIEWS.get(document_id)


def apply_corrections_to_result(result: Dict, review: HumanReview) -> Dict:
    """Apply review corrections into a nested extraction result dict."""
    updated = dict(result)

    for correction in review.corrections:
        _apply_field_path(
            updated,
            correction.field,
            correction.corrected_value,
        )

    return updated


def _apply_field_path(target: Dict, path: str, value: object) -> None:
    """Apply values to dot/index path, e.g. diagnoses[0].icd10_code."""
    tokens = re.findall(r"[^.\[\]]+|\[\d+\]", path)
    if not tokens:
        return

    current = target
    for i, token in enumerate(tokens):
        is_last = i == len(tokens) - 1

        if token.startswith("[") and token.endswith("]"):
            index = int(token[1:-1])
            if not isinstance(current, list) or index >= len(current):
                return
            if is_last:
                current[index] = value
                return
            current = current[index]
            continue

        key = token
        if is_last:
            if isinstance(current, dict):
                current[key] = value
            return

        next_token = tokens[i + 1]
        if isinstance(current, dict):
            if key not in current or current[key] is None:
                current[key] = [] if next_token.startswith("[") else {}
            current = current[key]
        else:
            return
