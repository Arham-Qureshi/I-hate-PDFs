import time
from collections import defaultdict
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from config import Settings

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

_rate_buckets: dict[str, list[float]] = defaultdict(list)


def get_settings() -> Settings:
    return Settings()


async def verify_api_key(
    key: str = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> str | None:
    if not settings.API_SECRET_KEY:
        return None

    if not key:
        raise HTTPException(
            status_code=401,
            detail="Missing or malformed Authorization header. Use: Authorization: Bearer <your-api-key>",
        )

    if not key.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or malformed Authorization header. Use: Authorization: Bearer <your-api-key>",
        )

    token = key[7:].strip()
    if token != settings.API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key.")

    return token


def _client_key(request: Request, settings: Settings) -> str:
    """Stable per-client identity for rate limiting.

    Defaults to the TCP peer address, which a client cannot forge. The
    X-Forwarded-For header is only consulted when explicitly trusted, and then
    only its first (proxy-appended) hop counts.
    """
    if not settings.TRUST_PROXY_HEADERS:
        return request.client.host if request.client else "unknown"

    forwarded = request.headers.get("X-Forwarded-For", "")
    first_hop = forwarded.split(",")[0].strip()
    if first_hop:
        return first_hop
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request, settings: Settings = Depends(get_settings)) -> bool:
    client_id = _client_key(request, settings)
    limit = settings.API_RATE_LIMIT
    now = time.time()
    window = 60.0

    _rate_buckets[client_id] = [t for t in _rate_buckets[client_id] if now - t < window]

    if len(_rate_buckets[client_id]) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {limit} requests/min.",
        )

    _rate_buckets[client_id].append(now)
    return True
