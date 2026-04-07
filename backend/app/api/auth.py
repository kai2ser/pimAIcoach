"""
API-key authentication dependency for admin and ingestion endpoints.
"""

from __future__ import annotations

import hmac
import logging

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

logger = logging.getLogger(__name__)

# Scheme declarations (auto_error=False so we can check both and give clear messages)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer_scheme = HTTPBearer(auto_error=False)


async def require_api_key(
    api_key: str | None = Security(_api_key_header),
    bearer: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> str:
    """
    Validate the request carries a valid admin API key.

    Accepts either:
      - X-API-Key: <key>
      - Authorization: Bearer <key>

    Returns the validated key string.

    Raises:
        HTTPException 401 if no credentials provided.
        HTTPException 403 if credentials are invalid.
        HTTPException 500 if PIM_ADMIN_API_KEY is not configured.
    """
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server authentication is not configured",
        )

    # Prefer X-API-Key header, fall back to Bearer token
    provided_key: str | None = api_key
    if not provided_key and bearer:
        provided_key = bearer.credentials

    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide via X-API-Key header or Authorization: Bearer <key>.",
        )

    if not hmac.compare_digest(provided_key.encode(), settings.admin_api_key.encode()):
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return provided_key
