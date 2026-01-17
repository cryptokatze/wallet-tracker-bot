"""실시간 가격 조회 서비스 - CoinGecko API"""
import asyncio
from typing import Optional, Dict
from cachetools import TTLCache
from loguru import logger

from services.http_client import get_http_client

# 캐시: 5분 TTL, 최대 500개 항목
_price_cache: TTLCache = TTLCache(maxsize=500, ttl=300)
_cache_lock = asyncio.Lock()

# CoinGecko 체인 ID 매핑
COINGECKO_CHAIN_MAP = {
    "eth": {"id": "ethereum", "platform": "ethereum"},
    "bsc": {"id": "binancecoin", "platform": "binance-smart-chain"},
    "polygon": {"id": "matic-network", "platform": "polygon-pos"},
    "arb": {"id": "ethereum", "platform": "arbitrum-one"},  # Arbitrum uses ETH
    "base": {"id": "ethereum", "platform": "base"},  # Base uses ETH
    "op": {"id": "ethereum", "platform": "optimistic-ethereum"},  # Optimism uses ETH
    "avax": {"id": "avalanche-2", "platform": "avalanche"},
    "sol": {"id": "solana", "platform": "solana"},
}


class PriceService:
    """CoinGecko 가격 조회 서비스"""

    BASE_URL = "https://api.coingecko.com/api/v3"

    @classmethod
    async def get_native_price(cls, chain: str) -> float:
        """네이티브 토큰 USD 가격 조회 (ETH, SOL, BNB 등)"""
        cache_key = f"native:{chain}"

        async with _cache_lock:
            if cache_key in _price_cache:
                cached = _price_cache[cache_key]
                logger.debug(f"Cache hit for {chain} native: ${cached}")
                return cached

        chain_info = COINGECKO_CHAIN_MAP.get(chain)
        if not chain_info:
            logger.warning(f"Unknown chain for price lookup: {chain}")
            return 0.0

        try:
            client = await get_http_client()
            resp = await client.get(
                f"{cls.BASE_URL}/simple/price",
                params={
                    "ids": chain_info["id"],
                    "vs_currencies": "usd",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            price = data.get(chain_info["id"], {}).get("usd", 0.0)

            async with _cache_lock:
                _price_cache[cache_key] = price

            logger.info(f"Native price for {chain}: ${price}")
            return price

        except Exception as e:
            logger.error(f"Failed to get native price for {chain}: {e}")
            return 0.0

    @classmethod
    async def get_token_price(cls, chain: str, contract_address: str) -> float:
        """ERC20/SPL 토큰 USD 가격 조회"""
        if not contract_address:
            return 0.0

        # 주소 정규화
        address = contract_address.lower()
        cache_key = f"token:{chain}:{address}"

        async with _cache_lock:
            if cache_key in _price_cache:
                cached = _price_cache[cache_key]
                logger.debug(f"Cache hit for token {address[:10]}...: ${cached}")
                return cached

        chain_info = COINGECKO_CHAIN_MAP.get(chain)
        if not chain_info:
            logger.warning(f"Unknown chain for token price: {chain}")
            return 0.0

        try:
            client = await get_http_client()
            resp = await client.get(
                f"{cls.BASE_URL}/simple/token_price/{chain_info['platform']}",
                params={
                    "contract_addresses": address,
                    "vs_currencies": "usd",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            price = data.get(address, {}).get("usd", 0.0)

            async with _cache_lock:
                _price_cache[cache_key] = price

            if price > 0:
                logger.info(f"Token price for {address[:10]}... on {chain}: ${price}")
            else:
                logger.debug(f"Token {address[:10]}... not found on CoinGecko")

            return price

        except Exception as e:
            logger.error(f"Failed to get token price for {address[:10]}...: {e}")
            return 0.0

    @classmethod
    async def get_usd_value(
        cls,
        chain: str,
        amount: float,
        token_address: Optional[str] = None
    ) -> float:
        """금액의 USD 가치 계산"""
        if amount <= 0:
            return 0.0

        if token_address:
            price = await cls.get_token_price(chain, token_address)
        else:
            price = await cls.get_native_price(chain)

        usd_value = amount * price
        logger.debug(f"USD value: {amount} x ${price} = ${usd_value:.2f}")
        return usd_value

    @classmethod
    async def batch_get_native_prices(cls) -> Dict[str, float]:
        """모든 네이티브 토큰 가격 일괄 조회 (효율적)"""
        coin_ids = list(set(info["id"] for info in COINGECKO_CHAIN_MAP.values()))

        try:
            client = await get_http_client()
            resp = await client.get(
                f"{cls.BASE_URL}/simple/price",
                params={
                    "ids": ",".join(coin_ids),
                    "vs_currencies": "usd",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            prices = {}
            async with _cache_lock:
                for chain, info in COINGECKO_CHAIN_MAP.items():
                    price = data.get(info["id"], {}).get("usd", 0.0)
                    prices[chain] = price
                    _price_cache[f"native:{chain}"] = price

            logger.info(f"Batch price update: {len(prices)} chains")
            return prices

        except Exception as e:
            logger.error(f"Failed to batch get prices: {e}")
            return {}

    @classmethod
    def clear_cache(cls):
        """캐시 초기화"""
        _price_cache.clear()
        logger.info("Price cache cleared")
