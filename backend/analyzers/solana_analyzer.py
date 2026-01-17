"""솔라나 체인 분석기"""
import asyncio
import structlog
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from typing import Optional

from analyzers.base import BaseAnalyzer
from config.chains import ChainConfig
from models.token import (
    TokenAnalysis,
    TokenBasicInfo,
    TokenSecurityInfo,
    TokenMarketInfo,
    RiskLevel
)
from services.contract_analysis.dexscreener import DEXScreenerService
from services.contract_analysis.goplus import GoPlusService

logger = structlog.get_logger()


class SolanaAnalyzer(BaseAnalyzer):
    """솔라나 체인 분석기"""

    def __init__(self, config: ChainConfig):
        self.config = config
        self.client = AsyncClient(config.rpc_url)

        # 서비스 초기화
        self.dexscreener = DEXScreenerService()
        self.goplus = GoPlusService()

    async def analyze(self, address: str) -> TokenAnalysis:
        """
        토큰 분석 실행

        Args:
            address: SPL 토큰 민트 주소

        Returns:
            TokenAnalysis 결과
        """
        logger.info(
            "solana_analysis_started",
            address=address
        )

        analysis = TokenAnalysis(
            chain="solana",
            chain_name="Solana",
            address=address
        )

        # 병렬로 모든 데이터 수집
        tasks = [
            self._get_basic_info(address),
            self._get_security_info(address),
            self._get_market_info(address),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 처리
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = f"Error in task {i}: {str(result)}"
                logger.error("analysis_task_error", task_index=i, error=str(result))
                analysis.errors.append(error_msg)
            elif result is not None:
                if i == 0:  # basic info
                    analysis.basic = TokenBasicInfo(**result)
                elif i == 1:  # security info
                    analysis.security = TokenSecurityInfo(**result)
                    if result.get("holder_count"):
                        analysis.basic.holder_count = result["holder_count"]
                elif i == 2:  # market info
                    analysis.market = TokenMarketInfo(**result)

        logger.info(
            "solana_analysis_completed",
            address=address,
            risk_level=analysis.security.risk_level.value,
            errors_count=len(analysis.errors)
        )

        return analysis

    async def _get_basic_info(self, address: str) -> Optional[dict]:
        """솔라나 RPC로 기본 정보 조회"""
        try:
            pubkey = Pubkey.from_string(address)

            # 토큰 공급량 조회
            supply_response = await self.client.get_token_supply(pubkey)

            if supply_response.value:
                supply_data = supply_response.value
                decimals = supply_data.decimals
                total_supply = float(supply_data.ui_amount or 0)

                # 큰 숫자 포맷팅
                if total_supply >= 1_000_000_000_000:
                    formatted = f"{total_supply / 1_000_000_000_000:.2f}T"
                elif total_supply >= 1_000_000_000:
                    formatted = f"{total_supply / 1_000_000_000:.2f}B"
                elif total_supply >= 1_000_000:
                    formatted = f"{total_supply / 1_000_000:.2f}M"
                elif total_supply >= 1_000:
                    formatted = f"{total_supply / 1_000:.2f}K"
                else:
                    formatted = f"{total_supply:.2f}"

                logger.debug(
                    "solana_basic_info_fetched",
                    decimals=decimals,
                    total_supply=total_supply
                )

                return {
                    "name": "Unknown",  # DEXScreener에서 가져옴
                    "symbol": "???",
                    "decimals": decimals,
                    "total_supply": total_supply,
                    "total_supply_formatted": formatted,
                }

            return None

        except Exception as e:
            logger.error("solana_basic_info_error", error=str(e), address=address)
            return None

    async def _get_security_info(self, address: str) -> Optional[dict]:
        """GoPlus로 보안 정보 조회"""
        try:
            data = await self.goplus.get_token_security("solana", address)

            if data:
                return self.goplus.parse_security_data(data)
            return {"risk_level": RiskLevel.UNKNOWN, "risk_items": [], "safe_items": []}

        except Exception as e:
            logger.error("solana_security_info_error", error=str(e), address=address)
            return None

    async def _get_market_info(self, address: str) -> Optional[dict]:
        """DEXScreener로 시장 정보 조회"""
        try:
            pairs = await self.dexscreener.get_token_pairs("solana", address)

            if pairs:
                market_data = self.dexscreener.parse_market_data(pairs)

                # DEXScreener에서 이름/심볼 가져오기
                if pairs and len(pairs) > 0:
                    best_pair = max(pairs, key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0))
                    base_token = best_pair.get("baseToken", {})

                    market_data["_name"] = base_token.get("name", "Unknown")
                    market_data["_symbol"] = base_token.get("symbol", "???")

                return market_data
            return {}

        except Exception as e:
            logger.error("solana_market_info_error", error=str(e), address=address)
            return None

    async def close(self):
        """리소스 정리"""
        await self.client.close()
        await self.dexscreener.close()
        await self.goplus.close()
