"""POST /api/reconcile/medication"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.middleware.auth import verify_api_key
from core.cache import reconcile_cache
from core.reconciler import reconcile_medications
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

    # Try deterministic path first
    result = reconcile_medications(body.sources, body.patient_context)
    llm_used = False

    if result is None:
        # Deterministic reconciler deferred → call LLM
        try:
            result = llm_reconcile(body.sources, body.patient_context)
            llm_used = True
        except (LLMParseError, RuntimeError) as exc:
            logger.error("LLM reconciliation failed: %s", exc)
            raise HTTPException(
                status_code=502,
                detail=f"LLM reconciliation failed: {exc}",
            )

    response = ReconcileResponse(
        patient_id=body.patient_id,
        result=result,
        source_count=len(body.sources),
        llm_used=llm_used,
    )
    reconcile_cache.set(cache_key, response)
    return response
