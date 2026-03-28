"""
NormClaim — Persistence Service
Best-effort persistence wrappers for extraction, FHIR bundles, and reconciliation.
"""

import json
from typing import Any, Dict, List, Optional

from models.schemas import ExtractionResult, ReconciliationReport, HumanReview, FeedbackItem

# In-memory fallbacks for local/dev usage.
DOCUMENT_ROWS: Dict[str, Dict[str, Any]] = {}
EXTRACTION_ROWS: Dict[str, Dict[str, Any]] = {}
FHIR_ROWS: Dict[str, Dict[str, Any]] = {}
RECONCILIATION_ROWS: Dict[str, Dict[str, Any]] = {}
REVIEW_ROWS: Dict[str, Dict[str, Any]] = {}
FEEDBACK_ROWS: Dict[str, List[Dict[str, Any]]] = {}

REQUIRED_SUPABASE_TABLES = [
    "documents",
    "extractions",
    "fhir_bundles",
    "reconciliations",
    "human_reviews",
    "feedback",
]


def verify_supabase_database(supabase_client: Optional[object]) -> Dict[str, Any]:
    """Verify Supabase connectivity and required table availability."""
    status = {
        "connected": False,
        "missing_tables": [],
        "ok": False,
    }
    if supabase_client is None:
        status["missing_tables"] = list(REQUIRED_SUPABASE_TABLES)
        return status

    missing = []
    for table_name in REQUIRED_SUPABASE_TABLES:
        try:
            supabase_client.table(table_name).select("*", count="exact").limit(0).execute()
        except Exception:
            missing.append(table_name)

    status["connected"] = True
    status["missing_tables"] = missing
    status["ok"] = len(missing) == 0
    return status


def insert_document(
    metadata: Dict[str, Any],
    supabase_client: Optional[object] = None,
) -> Dict[str, Any]:
    """Persist uploaded document metadata to Supabase (or in-memory fallback)."""
    doc_id = str(metadata.get("id", ""))
    if doc_id:
        DOCUMENT_ROWS[doc_id] = dict(metadata)

    if supabase_client is not None:
        supabase_client.table("documents").insert(metadata).execute()

    return dict(metadata)


def insert_extraction(
    document_id: str,
    extraction: ExtractionResult,
    supabase_client: Optional[object] = None,
) -> Dict[str, Any]:
    """Persist extraction output to Supabase (or in-memory fallback)."""
    payload = {
        "document_id": document_id,
        "result_json": extraction.model_dump(),
    }
    EXTRACTION_ROWS[document_id] = payload

    if supabase_client is not None:
        supabase_client.table("extractions").insert(
            {
                "document_id": document_id,
                "result_json": json.dumps(payload["result_json"]),
            }
        ).execute()

    return payload


def insert_fhir_bundle(
    document_id: str,
    bundle: Dict[str, Any],
    supabase_client: Optional[object] = None,
) -> Dict[str, Any]:
    """Persist generated FHIR bundle to Supabase (or in-memory fallback)."""
    payload = {
        "document_id": document_id,
        "bundle_json": bundle,
    }
    FHIR_ROWS[document_id] = payload

    if supabase_client is not None:
        supabase_client.table("fhir_bundles").insert(
            {
                "document_id": document_id,
                "bundle_json": json.dumps(bundle),
            }
        ).execute()

    return payload


def insert_reconciliation(
    document_id: str,
    report: ReconciliationReport,
    supabase_client: Optional[object] = None,
) -> Dict[str, Any]:
    """Persist reconciliation report to Supabase (or in-memory fallback)."""
    payload = {
        "document_id": document_id,
        "report_json": report.model_dump(),
        "delta_inr": float(report.estimated_claim_delta_inr),
    }
    RECONCILIATION_ROWS[document_id] = payload

    if supabase_client is not None:
        supabase_client.table("reconciliations").insert(
            {
                "document_id": document_id,
                "report_json": json.dumps(payload["report_json"]),
                "delta_inr": payload["delta_inr"],
            }
        ).execute()

    return payload


def insert_review(
    review: HumanReview,
    supabase_client: Optional[object] = None,
) -> Dict[str, Any]:
    """Persist human review data to Supabase (or in-memory fallback)."""
    payload = {
        "document_id": review.document_id,
        "reviewer_notes": review.reviewer_notes,
        "corrections_json": [c.model_dump() for c in review.corrections],
        "reviewed_at": review.reviewed_at,
    }
    REVIEW_ROWS[review.document_id] = payload

    if supabase_client is not None:
        supabase_client.table("human_reviews").insert(payload).execute()

    return payload


def insert_feedback(
    item: FeedbackItem,
    supabase_client: Optional[object] = None,
) -> Dict[str, Any]:
    """Persist feedback item to Supabase (or in-memory fallback)."""
    payload = {
        "document_id": item.document_id,
        "was_correct": item.was_extraction_correct,
        "correction_type": item.correction_type,
        "details": item.details,
    }
    FEEDBACK_ROWS.setdefault(item.document_id, []).append(payload)

    if supabase_client is not None:
        supabase_client.table("feedback").insert(payload).execute()

    return payload
