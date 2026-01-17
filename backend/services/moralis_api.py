"""Moralis Streams API 연동 - HTTP 클라이언트 재사용"""
from typing import Optional
from loguru import logger

from config import settings, SUPPORTED_CHAINS
from services.http_client import get_http_client


class MoralisAPI:
    """Moralis Streams API 클라이언트"""

    BASE_URL = "https://api.moralis.io/streams/evm"

    @classmethod
    def _headers(cls) -> dict:
        return {
            "X-API-Key": settings.moralis_api_key,
            "Content-Type": "application/json",
        }

    @classmethod
    async def create_stream(
        cls, chain: str, address: str, label: str
    ) -> Optional[str]:
        """스트림 생성 및 주소 추가"""
        if not settings.moralis_api_key:
            logger.warning("Moralis API key not set, skipping stream creation")
            return None

        chain_info = SUPPORTED_CHAINS.get(chain)
        if not chain_info or chain == "sol":
            logger.error(f"Invalid chain for Moralis: {chain}")
            return None

        webhook_url = f"http://{settings.webhook_host}:{settings.webhook_port}/webhook/moralis"

        # 1. 스트림 생성
        stream_data = {
            "webhookUrl": webhook_url,
            "description": f"Wallet Tracker: {label}",
            "tag": label,
            "chainIds": [chain_info["chain_id"]],
            "includeNativeTxs": True,
            "includeContractLogs": True,
            "includeInternalTxs": True,
            "getNativeBalances": [{"selectors": ["$fromAddress", "$toAddress"]}],
        }

        try:
            client = await get_http_client()

            # 스트림 생성
            resp = await client.post(
                cls.BASE_URL,
                headers=cls._headers(),
                json=stream_data,
                timeout=30,
            )
            resp.raise_for_status()
            stream = resp.json()
            stream_id = stream["id"]
            logger.info(f"Moralis stream created: {stream_id}")

            # 주소 추가
            resp = await client.post(
                f"{cls.BASE_URL}/{stream_id}/address",
                headers=cls._headers(),
                json={"address": address},
                timeout=30,
            )
            resp.raise_for_status()
            logger.info(f"Address added to stream: {address[:10]}...")

            return stream_id

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response'):
                error_msg = f"{e.response.status_code} - {e.response.text}"
            logger.error(f"Moralis stream creation failed: {error_msg}")
            return None

    @classmethod
    async def delete_stream(cls, stream_id: str) -> bool:
        """스트림 삭제"""
        if not settings.moralis_api_key:
            return False

        try:
            client = await get_http_client()
            resp = await client.delete(
                f"{cls.BASE_URL}/{stream_id}",
                headers=cls._headers(),
                timeout=30,
            )
            resp.raise_for_status()
            logger.info(f"Moralis stream deleted: {stream_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete stream: {e}")
            return False

    @classmethod
    async def get_streams(cls) -> list:
        """모든 스트림 조회"""
        if not settings.moralis_api_key:
            return []

        try:
            client = await get_http_client()
            resp = await client.get(
                cls.BASE_URL,
                headers=cls._headers(),
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get("result", [])
        except Exception as e:
            logger.error(f"Failed to get streams: {e}")
            return []
