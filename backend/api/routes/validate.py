"""POST /api/validate/data-quality"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.middleware.auth import verify_api_key
from core.quality_scorer import score_record_quality
from llm.client import llm_validate
from llm.parser import LLMParseError
from schemas.validate import ValidateRequest, ValidateResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validate", tags=["validate"])


@router.post("/data-quality", response_model=ValidateResponse)
async def validate_data_quality(
    body: ValidateRequest,
    _key: str = Depends(verify_api_key),
):
    llm_used = False

    try:
        quality = llm_validate(body.record)
        llm_used = True
    except (LLMParseError, RuntimeError) as exc:
        logger.warning("LLM validation failed, falling back to deterministic: %s", exc)
        quality = score_record_quality(body.record)

    return ValidateResponse(
        patient_id=body.record.patient_id,
        quality=quality,
        llm_used=llm_used,
    )
