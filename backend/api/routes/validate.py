"""POST /api/validate/data-quality"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.middleware.auth import verify_api_key
from core.cache import response_cache
from core.quality_scorer import score_record_quality
from llm.client import AIServiceError, llm_validate
from llm.parser import LLMParseError
from schemas.validate import PatientRecord, ValidateResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validate", tags=["validate"])


@router.post("/data-quality", response_model=ValidateResponse)
async def validate_data_quality(
    body: PatientRecord,
    _key: str = Depends(verify_api_key),
):
    cache_key = body.model_dump()

    cached = response_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        quality = await llm_validate(body)
    except (LLMParseError, AIServiceError) as llm_exc:
        logger.warning("LLM validation failed, falling back to deterministic: %s", llm_exc)
        try:
            quality = score_record_quality(body)
        except Exception as det_exc:
            logger.exception("Deterministic scorer also failed")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal error", "message": str(det_exc)},
            )
    except Exception as exc:
        logger.exception("Unexpected error in validation")
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    result = ValidateResponse(
        overall_score=quality.overall_score,
        breakdown=quality.breakdown,
        issues_detected=quality.issues_detected,
    )
    response_cache.set(cache_key, result)
    asyncio.create_task(dispatch("validation.complete", result.model_dump()))
    return result
