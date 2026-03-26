"""API key check dependency."""

from __future__ import annotations

import os

from fastapi import Header, HTTPException


async def verify_api_key(x_api_key: str = Header(...)) -> str:
    expected = os.getenv("API_KEY")
    if not expected:
        # No key configured → allow all (dev mode)
        return x_api_key
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
