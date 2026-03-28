"""
NormClaim — Reconciliation Router
Runs the ICD-10 claim gap analysis comparing extracted vs billed codes.
"""

import logging

from fastapi import APIRouter, HTTPException
from models.schemas import ReconciliationReport
from services.reconciler import reconcile
from services.persistence_service import insert_reconciliation
from routers.extract import EXTRACTIONS

router = APIRouter(prefix="/api/reconcile", tags=["Reconciliation"])
logger = logging.getLogger(__name__)

# In-memory report store
REPORTS: dict = {}


def _get_supabase_client():
    try:
        from main import supabase
        return supabase
    except Exception:
        return None


@router.post("/{document_id}", response_model=ReconciliationReport)
async def run_reconciliation(document_id: str):
    """Run reconciliation on an extracted document."""
    if document_id not in EXTRACTIONS:
        raise HTTPException(
            status_code=404,
            detail="Extract first: POST /api/extract/{id}"
        )
    report = reconcile(EXTRACTIONS[document_id])
    REPORTS[document_id] = report
    try:
        insert_reconciliation(document_id, report, _get_supabase_client())
    except Exception as e:
        logger.warning("Reconciliation persistence failed for %s: %s", document_id, e)
    return report


@router.get("/{document_id}", response_model=ReconciliationReport)
async def get_report(document_id: str):
    """Retrieve a previous reconciliation report."""
    if document_id not in REPORTS:
        raise HTTPException(status_code=404, detail="No report found")
    return REPORTS[document_id]
