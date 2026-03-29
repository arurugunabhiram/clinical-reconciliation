"""POST /api/reconcile/medication"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.middleware.auth import verify_api_key
from core.cache import response_cache
from core.reconciler import reconcile_medications, sources_agree
from llm.client import AIServiceError, llm_reconcile
from llm.parser import LLMParseError
from schemas.reconcile import ReconcileRequest, ReconcileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reconcile", tags=["reconcile"])


@router.post("/medication", response_model=ReconcileResponse)
async def reconcile_medication(
    body: ReconcileRequest,
    _key: str = Depends(verify_api_key),
):
    cache_key = body.model_dump()

    cached = response_cache.get(cache_key)
    if cached is not None:
        return cached

    det_result = reconcile_medications(body.sources, body.patient_context)

    if not sources_agree(body.sources):
        try:
            result = await llm_reconcile(body.sources, body.patient_context)
        except (LLMParseError, AIServiceError) as exc:
            logger.warning("LLM failed, using deterministic fallback: %s", exc)
            result = det_result
        except Exception as exc:
            logger.exception("Unexpected error in reconciliation")
            raise HTTPException(status_code=500, detail="Internal server error") from exc
    else:
        result = det_result

    response_cache.set(cache_key, result)
    asyncio.create_task(dispatch("reconciliation.complete", result.model_dump()))
    return result
