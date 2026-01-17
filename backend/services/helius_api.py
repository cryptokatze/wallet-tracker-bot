"""Helius Webhooks API 연동 (Solana) - HTTP 클라이언트 재사용"""
from typing import Optional
from loguru import logger

from config import settings
from services.http_client import get_http_client


class HeliusAPI:
    """Helius Webhooks API 클라이언트"""

    BASE_URL = "https://api.helius.xyz/v0"

    @classmethod
    async def create_webhook(cls, address: str, label: str) -> Optional[str]:
        """웹훅 생성"""
        if not settings.helius_api_key:
            logger.warning("Helius API key not set, skipping webhook creation")
            return None

        # 인증 토큰이 설정되어 있으면 URL에 추가
        webhook_url = f"http://{settings.webhook_host}:{settings.webhook_port}/webhook/helius"
        if settings.helius_webhook_secret:
            webhook_url += f"?auth={settings.helius_webhook_secret}"

        webhook_data = {
            "webhookURL": webhook_url,
            "transactionTypes": [
                "TRANSFER",
                "SWAP",
                "NFT_SALE",
                "NFT_LISTING",
            ],
            "accountAddresses": [address],
            "webhookType": "enhanced",
        }

        try:
            client = await get_http_client()
            resp = await client.post(
                f"{cls.BASE_URL}/webhooks",
                params={"api-key": settings.helius_api_key},
                json=webhook_data,
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            webhook_id = result.get("webhookID")
            logger.info(f"Helius webhook created: {webhook_id}")
            return webhook_id

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response'):
                error_msg = f"{e.response.status_code} - {e.response.text}"
            logger.error(f"Helius webhook creation failed: {error_msg}")
            return None

    @classmethod
    async def delete_webhook(cls, webhook_id: str) -> bool:
        """웹훅 삭제"""
        if not settings.helius_api_key:
            return False

        try:
            client = await get_http_client()
            resp = await client.delete(
                f"{cls.BASE_URL}/webhooks/{webhook_id}",
                params={"api-key": settings.helius_api_key},
                timeout=30,
            )
            resp.raise_for_status()
            logger.info(f"Helius webhook deleted: {webhook_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return False

    @classmethod
    async def get_webhooks(cls) -> list:
        """모든 웹훅 조회"""
        if not settings.helius_api_key:
            return []

        try:
            client = await get_http_client()
            resp = await client.get(
                f"{cls.BASE_URL}/webhooks",
                params={"api-key": settings.helius_api_key},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to get webhooks: {e}")
            return []
