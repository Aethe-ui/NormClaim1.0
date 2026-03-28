"""
NormClaim — FHIR Router
Proxies extraction data to the Java HAPI FHIR service to generate FHIR R4 Bundles.
"""

import logging

from fastapi import APIRouter, HTTPException
from services.fhir_client import generate_fhir_bundle, check_fhir_health
from services.fhir_mapper import build_fhir_bundle_local, validate_fhir_bundle
from services.persistence_service import insert_fhir_bundle
from routers.extract import EXTRACTIONS

router = APIRouter(prefix="/api/fhir", tags=["FHIR"])
logger = logging.getLogger(__name__)

# In-memory FHIR bundle cache
FHIR_BUNDLES: dict = {}


def _get_supabase_client():
    try:
        from main import supabase
        return supabase
    except Exception:
        return None


@router.post("/{document_id}")
async def create_fhir_bundle(document_id: str):
    """Generate a FHIR R4 Bundle from extraction results."""
    if document_id not in EXTRACTIONS:
        raise HTTPException(
            status_code=404,
            detail="Extract first: POST /api/extract/{id}"
        )

    extraction = EXTRACTIONS[document_id]

    # Prefer Java HAPI service when available, otherwise use local fallback.
    fhir_healthy = await check_fhir_health()
    if fhir_healthy:
        try:
            bundle = await generate_fhir_bundle(extraction)
        except Exception:
            bundle = build_fhir_bundle_local(extraction)
            bundle.setdefault("meta", {})["tag"] = [{"code": "local-fallback"}]
    else:
        bundle = build_fhir_bundle_local(extraction)
        bundle.setdefault("meta", {})["tag"] = [{"code": "local-fallback"}]

    if not validate_fhir_bundle(bundle):
        raise HTTPException(status_code=500, detail="Generated FHIR bundle failed validation")

    FHIR_BUNDLES[document_id] = bundle
    try:
        insert_fhir_bundle(document_id, bundle, _get_supabase_client())
    except Exception as e:
        logger.warning("FHIR bundle persistence failed for %s: %s", document_id, e)
    return bundle


@router.get("/{document_id}")
async def get_fhir_bundle(document_id: str):
    """Retrieve a previously generated FHIR bundle."""
    if document_id not in FHIR_BUNDLES:
        raise HTTPException(status_code=404, detail="No FHIR bundle found")
    return FHIR_BUNDLES[document_id]
