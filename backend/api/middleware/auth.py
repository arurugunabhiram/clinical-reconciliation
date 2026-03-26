"""API key check dependency with standardized error responses."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException, Request


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={
            "error": {
                "code": "UNAUTHORIZED",
                "message": message,
                "details": None,
            }
        },
    )


async def verify_api_key(x_api_key: Optional[str] = Header(default=None)) -> str:
    expected = os.getenv("API_KEY")
    if not expected:
        # No key configured → allow all (dev mode)
        return x_api_key or ""
    if not x_api_key:
        raise _unauthorized("Missing X-API-Key header")
    if x_api_key != expected:
        raise _unauthorized("Invalid API key")
    return x_api_key
