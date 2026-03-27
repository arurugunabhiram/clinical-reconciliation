"""POST /api/reconcile/medication"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.middleware.auth import verify_api_key
from core.cache import reconcile_cache
from core.reconciler import reconcile_medications, sources_agree
from llm.client import llm_reconcile
from llm.parser import LLMParseError
from schemas.reconcile import ReconcileRequest, ReconcileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reconcile", tags=["reconcile"])


@router.post("/medication", response_model=ReconcileResponse)
async def reconcile_medication(
    body: ReconcileRequest,
    _key: str = Depends(verify_api_key),
):
    # Check cache
    cache_key = body.model_dump()
    cached = reconcile_cache.get(cache_key)
    if cached:
        return cached

    # Deterministic baseline (always available as fallback)
    det_result = reconcile_medications(body.sources, body.patient_context)
    llm_used = False

    if not sources_agree(body.sources):
        # Sources conflict → try LLM for clinical reasoning
        try:
            result = llm_reconcile(body.sources, body.patient_context)
            llm_used = True
        except (LLMParseError, RuntimeError) as exc:
            logger.exception("LLM reconciliation failed, using deterministic fallback")
            result = det_result
    else:
        result = det_result

    response = ReconcileResponse(
        patient_id=body.patient_id,
        result=result,
        source_count=len(body.sources),
        llm_used=llm_used,
    )
    reconcile_cache.set(cache_key, response)
    return response
