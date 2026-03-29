"""Application configuration loaded from environment variables.

Call validate() once at startup to fail fast when required variables are missing.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

PORT: int = int(os.getenv("PORT", "8080"))


def validate() -> None:
    """Raise ValueError if any required environment variable is absent.

    Called during FastAPI startup so the server refuses to start rather than
    silently serving broken responses.
    """
    missing: list[str] = []
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.getenv("API_KEY"):
        missing.append("API_KEY")
    if missing:
        raise ValueError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Set them in your .env file or export them before starting the server."
        )
