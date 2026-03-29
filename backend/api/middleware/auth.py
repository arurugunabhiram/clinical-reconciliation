"""API key authentication dependency."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Header


class UnauthorizedException(Exception):
    """Raised when X-API-Key is missing or does not match API_KEY env var."""

    def __init__(self, message: str = "Valid X-API-Key header required") -> None:
        super().__init__(message)
        self.message = message


async def verify_api_key(x_api_key: Optional[str] = Header(default=None)) -> str:
    expected = os.getenv("API_KEY")
    if not x_api_key:
        raise UnauthorizedException()
    if not expected or x_api_key != expected:
        raise UnauthorizedException()
    return x_api_key
