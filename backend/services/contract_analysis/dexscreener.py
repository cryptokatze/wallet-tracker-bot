"""DEXScreener API 클라이언트"""
import aiohttp
import structlog
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


class DEXScreenerService:
    """DEXScreener API 서비스"""

    BASE_URL = "https://api.dexscreener.com"

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTP 세션 반환"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session

    async def close(self):
        """세션 종료"""
        if self._session and not self._session.closed:
            await self._session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True
    )
    async def get_token_pairs(self, chain: str, address: str) -> Optional[dict]:
        """
        토큰 페어 정보 조회

        Args:
            chain: 체인 ID (ethereum, bsc, solana 등)
            address: 토큰 컨트랙트 주소

        Returns:
            페어 정보 딕셔너리 또는 None
        """
        url = f"{self.BASE_URL}/token-pairs/v1/{chain}/{address}"

        logger.debug(
            "dexscreener_request",
            endpoint="token-pairs",
            chain=chain,
            address=address
        )

        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(
                        "dexscreener_response",
                        status=200,
                        pairs_count=len(data) if isinstance(data, list) else 0
                    )
                    return data
                else:
                    logger.warning(
                        "dexscreener_error",
                        status=response.status,
                        chain=chain,
                        address=address
                    )
                    return None
        except Exception as e:
            logger.error(
                "dexscreener_exception",
                error=str(e),
                chain=chain,
                address=address
            )
            raise

    def parse_market_data(self, pairs_data: list) -> dict:
        """
        페어 데이터에서 시장 정보 파싱

        Args:
            pairs_data: DEXScreener 페어 응답

        Returns:
            시장 정보 딕셔너리
        """
        if not pairs_data:
            return {}

        # 유동성이 가장 큰 페어 선택
        best_pair = max(pairs_data, key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0))

        price_change = best_pair.get("priceChange", {})
        txns = best_pair.get("txns", {}).get("h24", {})

        # LP 유동성 정보
        liquidity = best_pair.get("liquidity", {})
        base_token = best_pair.get("baseToken", {})
        quote_token = best_pair.get("quoteToken", {})

        return {
            "price_usd": self._safe_float(best_pair.get("priceUsd")),
            "price_native": self._safe_float(best_pair.get("priceNative")),
            "price_change_5m": self._safe_float(price_change.get("m5")),
            "price_change_1h": self._safe_float(price_change.get("h1")),
            "price_change_6h": self._safe_float(price_change.get("h6")),
            "price_change_24h": self._safe_float(price_change.get("h24")),
            "liquidity_usd": self._safe_float(liquidity.get("usd")),
            "liquidity_base": self._safe_float(liquidity.get("base")),
            "liquidity_quote": self._safe_float(liquidity.get("quote")),
            "base_token_symbol": base_token.get("symbol"),
            "quote_token_symbol": quote_token.get("symbol"),
            "fdv": self._safe_float(best_pair.get("fdv")),
            "market_cap": self._safe_float(best_pair.get("marketCap")),
            "volume_24h": self._safe_float(best_pair.get("volume", {}).get("h24")),
            "volume_1h": self._safe_float(best_pair.get("volume", {}).get("h1")),
            "volume_6h": self._safe_float(best_pair.get("volume", {}).get("h6")),
            "txns_24h_buys": txns.get("buys"),
            "txns_24h_sells": txns.get("sells"),
            "dex_name": best_pair.get("dexId"),
            "pair_address": best_pair.get("pairAddress"),
            "pair_url": best_pair.get("url"),
            "pair_created_at": best_pair.get("pairCreatedAt"),
        }

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """안전한 float 변환"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
