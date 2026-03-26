"""POST /api/validate/data-quality"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.middleware.auth import verify_api_key
from core.quality_scorer import score_record_quality
from schemas.validate import ValidateRequest, ValidateResponse

router = APIRouter(prefix="/validate", tags=["validate"])


@router.post("/data-quality", response_model=ValidateResponse)
async def validate_data_quality(
    body: ValidateRequest,
    _key: str = Depends(verify_api_key),
):
    quality = score_record_quality(body.record)
    return ValidateResponse(
        patient_id=body.record.patient_id,
        quality=quality,
        llm_used=False,
    )
