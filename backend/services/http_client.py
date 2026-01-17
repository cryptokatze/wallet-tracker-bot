"""공유 HTTP 클라이언트 - 연결 풀링"""
import httpx
from typing import Optional
from loguru import logger

_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """싱글톤 HTTP 클라이언트 반환"""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
            ),
        )
        logger.debug("HTTP client created")
    return _client


async def close_http_client():
    """HTTP 클라이언트 종료"""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        logger.info("HTTP client closed")
        _client = None
